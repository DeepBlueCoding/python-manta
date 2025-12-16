package main

/*
#include <stdlib.h>
*/
import "C"
import (
	"encoding/json"
	"fmt"
	"os"
	"strings"

	"github.com/dotabuff/manta"
	"github.com/dotabuff/manta/dota"
)

// EntitySnapshot represents the state of tracked entities at a specific tick
type EntitySnapshot struct {
	Tick        uint32                 `json:"tick"`
	GameTime    float32                `json:"game_time"`
	Heroes      []HeroSnapshot         `json:"heroes"`
	Creeps      []CreepSnapshot        `json:"creeps,omitempty"` // Only populated when IncludeCreeps=true
	Teams       []TeamState            `json:"teams"`
	RawEntities map[string]interface{} `json:"raw_entities,omitempty"`
}

// PlayerState represents a player's stats at a given tick
type PlayerState struct {
	PlayerID       int     `json:"player_id"`
	HeroID         int     `json:"hero_id"`
	HeroName       string  `json:"hero_name"`  // npc_dota_hero_* format (e.g., "npc_dota_hero_axe")
	Team           int     `json:"team"`
	LastHits       int     `json:"last_hits"`
	Denies         int     `json:"denies"`
	Gold           int     `json:"gold"`
	NetWorth       int     `json:"net_worth"`
	XP             int     `json:"xp"`
	Level          int     `json:"level"`
	Kills          int     `json:"kills"`
	Deaths         int     `json:"deaths"`
	Assists        int     `json:"assists"`
	PositionX      float32 `json:"position_x"`
	PositionY      float32 `json:"position_y"`
	Health         int     `json:"health"`
	MaxHealth      int     `json:"max_health"`
	Mana           float32 `json:"mana"`
	MaxMana        float32 `json:"max_mana"`
}

// TeamState represents team-level stats
type TeamState struct {
	TeamID     int `json:"team_id"`
	Score      int `json:"score"`
	TowerKills int `json:"tower_kills"`
}

// CreepSnapshot represents a creep's position and state
type CreepSnapshot struct {
	EntityID  int     `json:"entity_id"`
	ClassName string  `json:"class_name"` // e.g., "CDOTA_BaseNPC_Creep_Lane"
	Name      string  `json:"name"`       // e.g., "npc_dota_creep_goodguys_melee"
	Team      int     `json:"team"`       // 2=Radiant, 3=Dire, 0=Neutral
	X         float32 `json:"x"`
	Y         float32 `json:"y"`
	Health    int     `json:"health"`
	MaxHealth int     `json:"max_health"`
	IsNeutral bool    `json:"is_neutral"` // true for neutral creeps
	IsLane    bool    `json:"is_lane"`    // true for lane creeps
}

// EntityParseResult holds the result of entity state parsing
type EntityParseResult struct {
	Snapshots     []EntitySnapshot `json:"snapshots"`
	Success       bool             `json:"success"`
	Error         string           `json:"error,omitempty"`
	TotalTicks    uint32           `json:"total_ticks"`
	SnapshotCount int              `json:"snapshot_count"`
	GameStartTick uint32           `json:"game_start_tick"` // Tick when horn sounded (for game_time calculation)
}

// EntityParseConfig controls what and how often to capture
type EntityParseConfig struct {
	IntervalTicks  int      `json:"interval_ticks"`  // Capture every N ticks (default: 1800 = ~30 ticks/sec * 60 sec)
	MaxSnapshots   int      `json:"max_snapshots"`   // Max snapshots to capture (0 = unlimited)
	TargetTicks    []uint32 `json:"target_ticks"`    // Specific ticks to capture (overrides interval if set)
	TargetHeroes   []string `json:"target_heroes"`   // Filter by hero name (npc_dota_hero_* format from combat log)
	EntityClasses  []string `json:"entity_classes"`  // Classes to track (empty = default set)
	IncludeRaw     bool     `json:"include_raw"`     // Include raw entity data
	IncludeCreeps  bool     `json:"include_creeps"`  // Include lane and neutral creep positions
}

//export ParseEntities
func ParseEntities(filePath *C.char, configJSON *C.char) *C.char {
	goFilePath := C.GoString(filePath)
	goConfigJSON := C.GoString(configJSON)

	// Parse config
	config := EntityParseConfig{
		IntervalTicks: 1800, // Default: ~1 minute at 30 ticks/sec
		MaxSnapshots:  0,    // Unlimited by default
		IncludeRaw:    false,
	}
	if goConfigJSON != "" {
		json.Unmarshal([]byte(goConfigJSON), &config)
	}

	result, err := RunEntityParse(goFilePath, config)
	if err != nil {
		failure := &EntityParseResult{
			Snapshots: make([]EntitySnapshot, 0),
			Success:   false,
			Error:     err.Error(),
		}
		return marshalEntityResult(failure)
	}

	return marshalEntityResult(result)
}

// RunEntityParse executes entity parsing and returns the Go result directly
func RunEntityParse(filePath string, config EntityParseConfig) (*EntityParseResult, error) {
	result := &EntityParseResult{
		Snapshots: make([]EntitySnapshot, 0),
	}

	file, err := os.Open(filePath)
	if err != nil {
		return nil, fmt.Errorf("error opening file: %w", err)
	}
	defer file.Close()

	parser, err := manta.NewStreamParser(file)
	if err != nil {
		return nil, fmt.Errorf("error creating parser: %w", err)
	}

	// Track last capture tick to respect interval
	lastCaptureTick := uint32(0)
	gameStartTick := uint32(0) // Tick when game started (horn)

	// Build a set of target ticks for O(1) lookup
	targetTickSet := make(map[uint32]bool)
	for _, t := range config.TargetTicks {
		targetTickSet[t] = true
	}
	useTargetTicks := len(config.TargetTicks) > 0

	// Track which target ticks we've captured (to handle tick not exactly matching)
	capturedTargets := make(map[uint32]bool)

	// Detect game start from combat log (when game state becomes 5 = DOTA_GAMERULES_STATE_GAME_IN_PROGRESS)
	parser.Callbacks.OnCMsgDOTACombatLogEntry(func(m *dota.CMsgDOTACombatLogEntry) error {
		if m.GetType() == dota.DOTA_COMBATLOG_TYPES_DOTA_COMBATLOG_GAME_STATE {
			if m.GetValue() == 5 && gameStartTick == 0 {
				gameStartTick = parser.Tick
			}
		}
		return nil
	})

	// Entity handler to capture state at intervals or specific ticks
	parser.OnEntity(func(e *manta.Entity, op manta.EntityOp) error {
		// Safety check
		if e == nil {
			return nil
		}

		className := e.GetClassName()

		// Track game start time from game rules entity (check on ALL entity operations)
		if strings.Contains(className, "CDOTAGamerulesProxy") {
			if gst, ok := e.GetFloat32("m_pGameRules.m_flGameStartTime"); ok && gst > 0 && gameStartTick == 0 {
				gameStartTick = parser.Tick
			}
		}

		// Only capture on updates to PlayerResource entity
		if !op.Flag(manta.EntityOpUpdated) {
			return nil
		}

		// Only trigger snapshots on PlayerResource updates
		if !strings.Contains(className, "CDOTA_PlayerResource") {
			return nil
		}

		currentTick := parser.Tick

		// Determine if we should capture this tick
		shouldCapture := false

		if useTargetTicks {
			// Target tick mode: capture at or just after each target tick
			for targetTick := range targetTickSet {
				if !capturedTargets[targetTick] && currentTick >= targetTick {
					shouldCapture = true
					capturedTargets[targetTick] = true
					break
				}
			}
		} else {
			// Interval mode: capture every N ticks
			if config.IntervalTicks > 0 && currentTick-lastCaptureTick >= uint32(config.IntervalTicks) {
				shouldCapture = true
			} else if config.IntervalTicks == 0 {
				// If interval is 0, capture every update (not recommended for large files)
				shouldCapture = true
			}
		}

		if !shouldCapture {
			return nil
		}

		// Check max snapshots
		if config.MaxSnapshots > 0 && len(result.Snapshots) >= config.MaxSnapshots {
			return nil
		}

		// Capture snapshot with placeholder game_time (will be recalculated after parse)
		// Use tick=0 for game_time calculation since we don't know gameStartTick yet
		snapshot := captureSnapshot(parser, 0, config)
		if snapshot != nil && len(snapshot.Heroes) > 0 {
			result.Snapshots = append(result.Snapshots, *snapshot)
			lastCaptureTick = currentTick
		}

		return nil
	})

	if err := parser.Start(); err != nil {
		return nil, fmt.Errorf("error parsing file: %w", err)
	}

	// Post-process: recalculate game_time for all snapshots now that we know gameStartTick
	for i := range result.Snapshots {
		result.Snapshots[i].GameTime = TickToGameTime(result.Snapshots[i].Tick, gameStartTick)
	}

	result.Success = true
	result.TotalTicks = parser.Tick
	result.SnapshotCount = len(result.Snapshots)
	result.GameStartTick = gameStartTick
	return result, nil
}

// camelToSnake converts CamelCase to snake_case
// Example: "TrollWarlord" -> "troll_warlord", "FacelessVoid" -> "faceless_void"
func camelToSnake(s string) string {
	var result strings.Builder
	for i, r := range s {
		if i > 0 && r >= 'A' && r <= 'Z' {
			result.WriteByte('_')
		}
		result.WriteRune(r)
	}
	return strings.ToLower(result.String())
}

// entityClassToHeroName converts entity class name to npc_dota_hero_* format
// Example: "CDOTA_Unit_Hero_Axe" -> "npc_dota_hero_axe"
// Example: "CDOTA_Unit_Hero_TrollWarlord" -> "npc_dota_hero_troll_warlord"
// Example: "CDOTA_Unit_Hero_Shadow_Demon" -> "npc_dota_hero_shadow_demon" (not shadow__demon)
func entityClassToHeroName(className string) string {
	// Remove prefix "CDOTA_Unit_Hero_"
	if !strings.HasPrefix(className, "CDOTA_Unit_Hero_") {
		return ""
	}
	heroName := strings.TrimPrefix(className, "CDOTA_Unit_Hero_")
	// Convert CamelCase to snake_case and add prefix
	result := "npc_dota_hero_" + camelToSnake(heroName)
	// Normalize double underscores (e.g., Shadow_Demon -> shadow__demon -> shadow_demon)
	for strings.Contains(result, "__") {
		result = strings.ReplaceAll(result, "__", "_")
	}
	return result
}

// heroNameMatchesClass checks if a npc_dota_hero_* name matches an entity class
// Example: "npc_dota_hero_axe" matches "CDOTA_Unit_Hero_Axe"
func heroNameMatchesClass(heroName, className string) bool {
	// Extract hero part from npc_dota_hero_* format
	if !strings.HasPrefix(heroName, "npc_dota_hero_") {
		return false
	}
	heroSuffix := strings.TrimPrefix(heroName, "npc_dota_hero_")

	// Extract hero part from entity class
	if !strings.HasPrefix(className, "CDOTA_Unit_Hero_") {
		return false
	}
	classSuffix := strings.TrimPrefix(className, "CDOTA_Unit_Hero_")

	// Compare case-insensitively (axe vs Axe, shadow_shaman vs ShadowShaman)
	// Also handle underscore removal for comparison
	heroNormalized := strings.ToLower(strings.ReplaceAll(heroSuffix, "_", ""))
	classNormalized := strings.ToLower(strings.ReplaceAll(classSuffix, "_", ""))

	return heroNormalized == classNormalized
}

// shouldIncludeHero checks if a hero should be included based on target_heroes filter
func shouldIncludeHero(heroClassName string, targetHeroes []string) bool {
	if len(targetHeroes) == 0 {
		return true // No filter, include all
	}
	for _, target := range targetHeroes {
		if heroNameMatchesClass(target, heroClassName) {
			return true
		}
	}
	return false
}

// captureSnapshot captures current entity state
func captureSnapshot(parser *manta.Parser, gameTime float32, config EntityParseConfig) *EntitySnapshot {
	snapshot := &EntitySnapshot{
		Tick:     parser.Tick,
		GameTime: gameTime,
		Heroes:   make([]HeroSnapshot, 0, 10),
		Teams:    make([]TeamState, 0, 2),
	}

	if config.IncludeRaw {
		snapshot.RawEntities = make(map[string]interface{})
	}

	// Find CDOTA_PlayerResource for basic player info
	var playerResource *manta.Entity
	playerResources := parser.FilterEntity(func(e *manta.Entity) bool {
		if e == nil {
			return false
		}
		return strings.Contains(e.GetClassName(), "CDOTA_PlayerResource")
	})
	if len(playerResources) > 0 {
		playerResource = playerResources[0]
	}

	// Find CDOTA_DataRadiant and CDOTA_DataDire for LH/DN/gold stats
	var dataRadiant, dataDire *manta.Entity
	dataEntities := parser.FilterEntity(func(e *manta.Entity) bool {
		if e == nil {
			return false
		}
		className := e.GetClassName()
		return strings.Contains(className, "CDOTA_DataRadiant") ||
			strings.Contains(className, "CDOTA_DataDire")
	})
	for _, de := range dataEntities {
		if de == nil {
			continue
		}
		if strings.Contains(de.GetClassName(), "DataRadiant") {
			dataRadiant = de
		} else if strings.Contains(de.GetClassName(), "DataDire") {
			dataDire = de
		}
	}

	// Find hero entities
	heroEntities := parser.FilterEntity(func(e *manta.Entity) bool {
		if e == nil {
			return false
		}
		return strings.Contains(e.GetClassName(), "CDOTA_Unit_Hero_")
	})

	// Build a map of hero handles to hero entities for quick lookup
	heroByHandle := make(map[uint64]*manta.Entity)
	for _, hero := range heroEntities {
		if hero == nil {
			continue
		}
		heroByHandle[uint64(hero.GetIndex())] = hero
	}

	// Extract hero data by combining PlayerResource, Data entities, and Hero entities
	if playerResource != nil {
		for i := 0; i < 10; i++ {
			// Get hero ID from PlayerResource
			heroID := 0
			if hid, ok := playerResource.GetUint32(fmt.Sprintf("m_vecPlayerTeamData.%04d.m_nSelectedHeroID", i)); ok {
				heroID = int(hid)
			}

			if heroID <= 0 {
				continue // No hero selected for this player
			}

			// Determine team
			team := 2 // Radiant
			if i >= 5 {
				team = 3 // Dire
			}

			// Get team slot (0-4 for each team)
			teamSlot := i
			if i >= 5 {
				teamSlot = i - 5
			}

			// Find hero entity
			var heroEntity *manta.Entity
			var heroClassName string
			if heroHandle, ok := playerResource.GetUint64(fmt.Sprintf("m_vecPlayerTeamData.%04d.m_hSelectedHero", i)); ok {
				if found, exists := heroByHandle[heroHandle&0x3FFF]; exists {
					heroEntity = found
					heroClassName = heroEntity.GetClassName()
				}
			}

			// Apply target_heroes filter
			if len(config.TargetHeroes) > 0 {
				if !shouldIncludeHero(heroClassName, config.TargetHeroes) {
					continue
				}
			}

			// Extract economy data from PlayerResource and Data entities
			economy := extractEconomyData(playerResource, dataRadiant, dataDire, i, team, teamSlot)

			// Extract full hero snapshot with all data
			if heroEntity != nil {
				heroSnapshot := extractFullHeroSnapshot(heroEntity, i, heroID, parser, &economy)
				snapshot.Heroes = append(snapshot.Heroes, heroSnapshot)
			}
		}
	}

	// Find and extract team data
	dataTeams := parser.FilterEntity(func(e *manta.Entity) bool {
		if e == nil {
			return false
		}
		className := e.GetClassName()
		return strings.Contains(className, "CDOTA_DataRadiant") ||
			strings.Contains(className, "CDOTA_DataDire") ||
			strings.Contains(className, "CDOTATeam")
	})

	for _, team := range dataTeams {
		if team == nil {
			continue
		}
		teamState := extractTeamState(team)
		if teamState.TeamID > 0 {
			snapshot.Teams = append(snapshot.Teams, teamState)
		}
	}

	// Optionally capture raw entity data for specific classes
	if config.IncludeRaw && len(config.EntityClasses) > 0 {
		for _, className := range config.EntityClasses {
			entities := parser.FilterEntity(func(e *manta.Entity) bool {
				if e == nil {
					return false
				}
				return strings.Contains(e.GetClassName(), className)
			})
			for _, e := range entities {
				if e == nil {
					continue
				}
				key := fmt.Sprintf("%s_%d", e.GetClassName(), e.GetIndex())
				snapshot.RawEntities[key] = e.Map()
			}
		}
	}

	// Optionally capture creep positions
	if config.IncludeCreeps {
		snapshot.Creeps = captureCreepSnapshots(parser)
	}

	return snapshot
}

// captureCreepSnapshots captures all lane and neutral creep positions
func captureCreepSnapshots(parser *manta.Parser) []CreepSnapshot {
	creeps := make([]CreepSnapshot, 0, 100)

	// Find all creep entities
	creepEntities := parser.FilterEntity(func(e *manta.Entity) bool {
		if e == nil {
			return false
		}
		className := e.GetClassName()
		return strings.Contains(className, "CDOTA_BaseNPC_Creep_Lane") ||
			strings.Contains(className, "CDOTA_BaseNPC_Creep_Neutral")
	})

	for _, e := range creepEntities {
		if e == nil {
			continue
		}

		className := e.GetClassName()
		creep := CreepSnapshot{
			EntityID:  int(e.GetIndex()),
			ClassName: className,
			IsLane:    strings.Contains(className, "Creep_Lane"),
			IsNeutral: strings.Contains(className, "Creep_Neutral"),
		}

		// Get name (e.g., "npc_dota_creep_goodguys_melee")
		if name, ok := e.GetString("m_iszUnitName"); ok {
			creep.Name = name
		}

		// Get team (try both int32 and uint32 extraction)
		if team, ok := e.GetUint32("m_iTeamNum"); ok {
			creep.Team = int(team)
		} else if team, ok := e.GetInt32("m_iTeamNum"); ok {
			creep.Team = int(team)
		}

		// Get position
		if cellX, ok := e.GetUint32("CBodyComponent.m_cellX"); ok {
			if vecX, ok := e.GetFloat32("CBodyComponent.m_vecX"); ok {
				creep.X = float32(cellX)*128.0 + vecX - 16384.0
			}
		}
		if cellY, ok := e.GetUint32("CBodyComponent.m_cellY"); ok {
			if vecY, ok := e.GetFloat32("CBodyComponent.m_vecY"); ok {
				creep.Y = float32(cellY)*128.0 + vecY - 16384.0
			}
		}

		// Get health
		if health, ok := e.GetInt32("m_iHealth"); ok {
			creep.Health = int(health)
		}
		if maxHealth, ok := e.GetInt32("m_iMaxHealth"); ok {
			creep.MaxHealth = int(maxHealth)
		}

		// Only include alive creeps
		if creep.Health > 0 {
			creeps = append(creeps, creep)
		}
	}

	return creeps
}

// extractPlayerStateFromResource extracts basic player info from CDOTA_PlayerResource
func extractPlayerStateFromResource(pr *manta.Entity, playerIdx int) PlayerState {
	player := PlayerState{
		PlayerID: playerIdx,
	}

	// Team (2=Radiant slots 0-4, 3=Dire slots 5-9)
	if playerIdx < 5 {
		player.Team = 2
	} else {
		player.Team = 3
	}

	// Hero ID from PlayerResource (uint32 type)
	if heroID, ok := pr.GetUint32(fmt.Sprintf("m_vecPlayerTeamData.%04d.m_nSelectedHeroID", playerIdx)); ok {
		player.HeroID = int(heroID)
	}

	// Level from PlayerResource
	if level, ok := pr.GetInt32(fmt.Sprintf("m_vecPlayerTeamData.%04d.m_iLevel", playerIdx)); ok {
		player.Level = int(level)
	}

	// KDA from PlayerResource
	if kills, ok := pr.GetInt32(fmt.Sprintf("m_vecPlayerTeamData.%04d.m_iKills", playerIdx)); ok {
		player.Kills = int(kills)
	}
	if deaths, ok := pr.GetInt32(fmt.Sprintf("m_vecPlayerTeamData.%04d.m_iDeaths", playerIdx)); ok {
		player.Deaths = int(deaths)
	}
	if assists, ok := pr.GetInt32(fmt.Sprintf("m_vecPlayerTeamData.%04d.m_iAssists", playerIdx)); ok {
		player.Assists = int(assists)
	}

	return player
}

// extractPlayerStatsFromDataTeam extracts LH/DN/gold stats from CDOTA_DataRadiant or CDOTA_DataDire
func extractPlayerStatsFromDataTeam(dataEntity *manta.Entity, teamSlot int, player *PlayerState) {
	// Last hits from m_vecDataTeam
	if lh, ok := dataEntity.GetInt32(fmt.Sprintf("m_vecDataTeam.%04d.m_iLastHitCount", teamSlot)); ok {
		player.LastHits = int(lh)
	}

	// Denies
	if denies, ok := dataEntity.GetInt32(fmt.Sprintf("m_vecDataTeam.%04d.m_iDenyCount", teamSlot)); ok {
		player.Denies = int(denies)
	}

	// Net worth
	if nw, ok := dataEntity.GetInt32(fmt.Sprintf("m_vecDataTeam.%04d.m_iNetWorth", teamSlot)); ok {
		player.NetWorth = int(nw)
	}

	// Gold (reliable + unreliable)
	if gold, ok := dataEntity.GetInt32(fmt.Sprintf("m_vecDataTeam.%04d.m_iReliableGold", teamSlot)); ok {
		player.Gold = int(gold)
	}
	if unreliable, ok := dataEntity.GetInt32(fmt.Sprintf("m_vecDataTeam.%04d.m_iUnreliableGold", teamSlot)); ok {
		player.Gold += int(unreliable)
	}

	// Total XP
	if xp, ok := dataEntity.GetInt32(fmt.Sprintf("m_vecDataTeam.%04d.m_iTotalEarnedXP", teamSlot)); ok {
		player.XP = int(xp)
	}
}

// extractHeroPosition extracts position from a hero entity using CBodyComponent
// World coordinates formula: worldX = (cellX * 128) + vecX - 16384
func extractHeroPosition(hero *manta.Entity, player *PlayerState) {
	if hero == nil {
		return
	}

	// Get cell coordinates (grid position)
	cellX, okCellX := hero.GetUint32("CBodyComponent.m_cellX")
	cellY, okCellY := hero.GetUint32("CBodyComponent.m_cellY")

	// Get vector offsets within the cell
	vecX, okVecX := hero.GetFloat32("CBodyComponent.m_vecX")
	vecY, okVecY := hero.GetFloat32("CBodyComponent.m_vecY")

	// Calculate world coordinates
	// Formula: world = (cell * 128) + vec - 16384
	// The -16384 centers the coordinate system (map is ~32768 units, center at 16384)
	if okCellX && okVecX {
		player.PositionX = float32(cellX)*128.0 + vecX - 16384.0
	}
	if okCellY && okVecY {
		player.PositionY = float32(cellY)*128.0 + vecY - 16384.0
	}

	// Also extract health and mana while we have the hero entity
	if health, ok := hero.GetInt32("m_iHealth"); ok {
		player.Health = int(health)
	}
	if maxHealth, ok := hero.GetInt32("m_iMaxHealth"); ok {
		player.MaxHealth = int(maxHealth)
	}
	if mana, ok := hero.GetFloat32("m_flMana"); ok {
		player.Mana = mana
	}
	if maxMana, ok := hero.GetFloat32("m_flMaxMana"); ok {
		player.MaxMana = maxMana
	}
}

// EconomyData holds economy stats extracted from PlayerResource and Data entities
type EconomyData struct {
	Level        int
	Kills        int
	Deaths       int
	Assists      int
	LastHits     int
	Denies       int
	Gold         int
	NetWorth     int
	XP           int
	CampsStacked int
}

// extractEconomyData extracts economy data from PlayerResource and Data entities
func extractEconomyData(playerResource, dataRadiant, dataDire *manta.Entity, playerIdx, team, teamSlot int) EconomyData {
	economy := EconomyData{}

	// From PlayerResource
	if playerResource != nil {
		if level, ok := playerResource.GetInt32(fmt.Sprintf("m_vecPlayerTeamData.%04d.m_iLevel", playerIdx)); ok {
			economy.Level = int(level)
		}
		if kills, ok := playerResource.GetInt32(fmt.Sprintf("m_vecPlayerTeamData.%04d.m_iKills", playerIdx)); ok {
			economy.Kills = int(kills)
		}
		if deaths, ok := playerResource.GetInt32(fmt.Sprintf("m_vecPlayerTeamData.%04d.m_iDeaths", playerIdx)); ok {
			economy.Deaths = int(deaths)
		}
		if assists, ok := playerResource.GetInt32(fmt.Sprintf("m_vecPlayerTeamData.%04d.m_iAssists", playerIdx)); ok {
			economy.Assists = int(assists)
		}
	}

	// From team Data entity
	var dataEntity *manta.Entity
	if team == 2 {
		dataEntity = dataRadiant
	} else if team == 3 {
		dataEntity = dataDire
	}

	if dataEntity != nil {
		if lh, ok := dataEntity.GetInt32(fmt.Sprintf("m_vecDataTeam.%04d.m_iLastHitCount", teamSlot)); ok {
			economy.LastHits = int(lh)
		}
		if denies, ok := dataEntity.GetInt32(fmt.Sprintf("m_vecDataTeam.%04d.m_iDenyCount", teamSlot)); ok {
			economy.Denies = int(denies)
		}
		if nw, ok := dataEntity.GetInt32(fmt.Sprintf("m_vecDataTeam.%04d.m_iNetWorth", teamSlot)); ok {
			economy.NetWorth = int(nw)
		}
		if gold, ok := dataEntity.GetInt32(fmt.Sprintf("m_vecDataTeam.%04d.m_iReliableGold", teamSlot)); ok {
			economy.Gold = int(gold)
		}
		if unreliable, ok := dataEntity.GetInt32(fmt.Sprintf("m_vecDataTeam.%04d.m_iUnreliableGold", teamSlot)); ok {
			economy.Gold += int(unreliable)
		}
		if xp, ok := dataEntity.GetInt32(fmt.Sprintf("m_vecDataTeam.%04d.m_iTotalEarnedXP", teamSlot)); ok {
			economy.XP = int(xp)
		}
		if stacks, ok := dataEntity.GetInt32(fmt.Sprintf("m_vecDataTeam.%04d.m_iCampsStacked", teamSlot)); ok {
			economy.CampsStacked = int(stacks)
		}
	}

	return economy
}

// extractTeamState extracts team-level stats
func extractTeamState(team *manta.Entity) TeamState {
	state := TeamState{}

	className := team.GetClassName()
	if strings.Contains(className, "Radiant") {
		state.TeamID = 2
	} else if strings.Contains(className, "Dire") {
		state.TeamID = 3
	} else if teamNum, ok := team.GetInt32("m_iTeamNum"); ok {
		state.TeamID = int(teamNum)
	}

	if score, ok := team.GetInt32("m_iScore"); ok {
		state.Score = int(score)
	}

	return state
}

// extractFullHeroSnapshot extracts complete hero state including abilities, talents, and economy
func extractFullHeroSnapshot(entity *manta.Entity, playerIdx int, heroID int, parser *manta.Parser, economy *EconomyData) HeroSnapshot {
	entityID := int(entity.GetIndex())
	hero := HeroSnapshot{
		HeroName:   entityClassToHeroName(entity.GetClassName()),
		HeroID:     heroID,
		EntityID:   entityID,
		Index:      entityID, // Deprecated: use entity_id
		PlayerID:   playerIdx,
		Abilities:  make([]AbilitySnapshot, 0),
		Talents:    make([]TalentChoice, 0),
		IsAlive:    true,
	}

	// Team based on player slot (0-4 = Radiant, 5-9 = Dire)
	if playerIdx >= 0 && playerIdx < 5 {
		hero.Team = 2 // Radiant
	} else if playerIdx >= 5 {
		hero.Team = 3 // Dire
	}

	// Economy data (from PlayerResource and Data entities)
	if economy != nil {
		hero.Level = economy.Level
		hero.Kills = economy.Kills
		hero.Deaths = economy.Deaths
		hero.Assists = economy.Assists
		hero.LastHits = economy.LastHits
		hero.Denies = economy.Denies
		hero.Gold = economy.Gold
		hero.NetWorth = economy.NetWorth
		hero.XP = economy.XP
		hero.CampsStacked = economy.CampsStacked
	}

	// Override level from hero entity if available (more accurate)
	if level, ok := entity.GetInt32("m_iCurrentLevel"); ok {
		hero.Level = int(level)
	}

	// Health/Mana
	if health, ok := entity.GetInt32("m_iHealth"); ok {
		hero.Health = int(health)
		hero.IsAlive = health > 0
	}
	if maxHealth, ok := entity.GetInt32("m_iMaxHealth"); ok {
		hero.MaxHealth = int(maxHealth)
	}
	if mana, ok := entity.GetFloat32("m_flMana"); ok {
		hero.Mana = mana
	}
	if maxMana, ok := entity.GetFloat32("m_flMaxMana"); ok {
		hero.MaxMana = maxMana
	}

	// Override team from entity if available
	if team, ok := entity.GetInt32("m_iTeamNum"); ok {
		hero.Team = int(team)
	}

	// Ability points (unspent)
	if pts, ok := entity.GetInt32("m_iAbilityPoints"); ok {
		hero.AbilityPoints = int(pts)
	}

	// Position from cell (world = cell * 128 + vec - 16384)
	if cellX, ok := entity.GetUint32("CBodyComponent.m_cellX"); ok {
		if vecX, ok := entity.GetFloat32("CBodyComponent.m_vecX"); ok {
			hero.X = float32(cellX)*128.0 + vecX - 16384.0
		}
	}
	if cellY, ok := entity.GetUint32("CBodyComponent.m_cellY"); ok {
		if vecY, ok := entity.GetFloat32("CBodyComponent.m_vecY"); ok {
			hero.Y = float32(cellY)*128.0 + vecY - 16384.0
		}
	}
	if cellZ, ok := entity.GetUint32("CBodyComponent.m_cellZ"); ok {
		if vecZ, ok := entity.GetFloat32("CBodyComponent.m_vecZ"); ok {
			hero.Z = float32(cellZ)*128.0 + vecZ - 16384.0
		}
	}

	// Combat stats
	if armor, ok := entity.GetFloat32("m_flPhysicalArmorValue"); ok {
		hero.Armor = armor
	}
	if magicRes, ok := entity.GetFloat32("m_flMagicalResistanceValue"); ok {
		hero.MagicResistance = magicRes
	}
	if dmgMin, ok := entity.GetInt32("m_iDamageMin"); ok {
		hero.DamageMin = int(dmgMin)
	}
	if dmgMax, ok := entity.GetInt32("m_iDamageMax"); ok {
		hero.DamageMax = int(dmgMax)
	}
	if atkRange, ok := entity.GetInt32("m_iAttackRange"); ok {
		hero.AttackRange = int(atkRange)
	}

	// Attributes (total values including bonuses)
	if str, ok := entity.GetFloat32("m_flStrengthTotal"); ok {
		hero.Strength = str
	}
	if agi, ok := entity.GetFloat32("m_flAgilityTotal"); ok {
		hero.Agility = agi
	}
	if intel, ok := entity.GetFloat32("m_flIntellectTotal"); ok {
		hero.Intellect = intel
	}

	// Extract abilities and talents
	if parser != nil {
		extractAbilitiesForSnapshot(entity, parser, &hero)
	}

	return hero
}

// extractAbilitiesForSnapshot extracts ability and talent data from a hero entity
func extractAbilitiesForSnapshot(entity *manta.Entity, parser *manta.Parser, hero *HeroSnapshot) {
	// Track talent slots for tier detection
	talentSlots := make([]int, 0)
	talentsBySlot := make(map[int]struct {
		name  string
		level int32
	})

	// First pass: identify all abilities and separate talents
	for slot := 0; slot < 24; slot++ {
		key := fmt.Sprintf("m_vecAbilities.%04d", slot)
		val := entity.Get(key)

		handle, ok := val.(uint32)
		if !ok || handle == 16777215 { // 16777215 = invalid handle
			continue
		}

		abilityEntity := parser.FindEntityByHandle(uint64(handle))
		if abilityEntity == nil {
			continue
		}

		abilityName := abilityEntity.GetClassName()
		abilityLevel, _ := abilityEntity.GetInt32("m_iLevel")
		hidden, _ := abilityEntity.GetBool("m_bHidden")

		// Check if this is a talent (name-based detection)
		if strings.Contains(abilityName, "Special_Bonus") {
			talentSlots = append(talentSlots, slot)
			talentsBySlot[slot] = struct {
				name  string
				level int32
			}{abilityName, abilityLevel}
			continue
		}

		// Skip hidden abilities with no level
		if hidden && abilityLevel == 0 {
			continue
		}

		// Skip non-hero abilities (shared abilities)
		if strings.Contains(abilityName, "Capture") ||
			strings.Contains(abilityName, "Portal_Warp") ||
			strings.Contains(abilityName, "Lamp_Use") ||
			strings.Contains(abilityName, "Plus_HighFive") ||
			strings.Contains(abilityName, "Plus_GuildBanner") {
			continue
		}

		// Regular ability
		cooldown, _ := abilityEntity.GetFloat32("m_fCooldown")
		maxCooldown, _ := abilityEntity.GetFloat32("m_flCooldownLength")
		manaCost, _ := abilityEntity.GetInt32("m_iManaCost")
		charges, _ := abilityEntity.GetInt32("m_nAbilityCurrentCharges")

		ability := AbilitySnapshot{
			Slot:        slot,
			Name:        abilityName,
			Level:       int(abilityLevel),
			Cooldown:    cooldown,
			MaxCooldown: maxCooldown,
			ManaCost:    int(manaCost),
			Charges:     int(charges),
			IsUltimate:  slot == 5, // Slot 5 is typically the ultimate
		}
		hero.Abilities = append(hero.Abilities, ability)
	}

	// Second pass: process talents
	// Talents come in pairs, ordered by tier (10, 15, 20, 25)
	// Import sort for talent processing
	sortInts(talentSlots)

	tiers := []int{10, 15, 20, 25}
	tierIndex := 0
	for i := 0; i < len(talentSlots) && tierIndex < len(tiers); i += 2 {
		tier := tiers[tierIndex]
		tierIndex++

		// Check left talent (first of pair)
		if i < len(talentSlots) {
			leftSlot := talentSlots[i]
			leftData := talentsBySlot[leftSlot]
			if leftData.level > 0 {
				hero.Talents = append(hero.Talents, TalentChoice{
					Tier:   tier,
					Slot:   leftSlot,
					IsLeft: true,
					Name:   leftData.name,
				})
			}
		}

		// Check right talent (second of pair)
		if i+1 < len(talentSlots) {
			rightSlot := talentSlots[i+1]
			rightData := talentsBySlot[rightSlot]
			if rightData.level > 0 {
				hero.Talents = append(hero.Talents, TalentChoice{
					Tier:   tier,
					Slot:   rightSlot,
					IsLeft: false,
					Name:   rightData.name,
				})
			}
		}
	}
}

// sortInts sorts a slice of ints in ascending order (simple bubble sort for small slices)
func sortInts(a []int) {
	for i := 0; i < len(a); i++ {
		for j := i + 1; j < len(a); j++ {
			if a[i] > a[j] {
				a[i], a[j] = a[j], a[i]
			}
		}
	}
}

// marshalEntityResult converts result to JSON and returns as C string
func marshalEntityResult(result *EntityParseResult) *C.char {
	jsonResult, err := json.Marshal(result)
	if err != nil {
		errorResult := &EntityParseResult{
			Success: false,
			Error:   fmt.Sprintf("Error marshaling result: %v", err),
		}
		jsonResult, _ = json.Marshal(errorResult)
	}

	cStr := C.CString(string(jsonResult))
	return cStr
}
