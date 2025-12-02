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
)

// EntitySnapshot represents the state of tracked entities at a specific tick
type EntitySnapshot struct {
	Tick       uint32                 `json:"tick"`
	GameTime   float32                `json:"game_time"`
	Players    []PlayerState          `json:"players"`
	Teams      []TeamState            `json:"teams"`
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

// EntityParseResult holds the result of entity state parsing
type EntityParseResult struct {
	Snapshots    []EntitySnapshot `json:"snapshots"`
	Success      bool             `json:"success"`
	Error        string           `json:"error,omitempty"`
	TotalTicks   uint32           `json:"total_ticks"`
	SnapshotCount int             `json:"snapshot_count"`
}

// EntityParseConfig controls what and how often to capture
type EntityParseConfig struct {
	IntervalTicks  int      `json:"interval_ticks"`  // Capture every N ticks (default: 1800 = ~30 ticks/sec * 60 sec)
	MaxSnapshots   int      `json:"max_snapshots"`   // Max snapshots to capture (0 = unlimited)
	TargetTicks    []uint32 `json:"target_ticks"`    // Specific ticks to capture (overrides interval if set)
	TargetHeroes   []string `json:"target_heroes"`   // Filter by hero name (npc_dota_hero_* format from combat log)
	EntityClasses  []string `json:"entity_classes"`  // Classes to track (empty = default set)
	IncludeRaw     bool     `json:"include_raw"`     // Include raw entity data
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
	gameStartTime := float32(0)  // When the actual game started (after pick phase)
	gameStartTick := uint32(0)   // Tick when game started

	// Build a set of target ticks for O(1) lookup
	targetTickSet := make(map[uint32]bool)
	for _, t := range config.TargetTicks {
		targetTickSet[t] = true
	}
	useTargetTicks := len(config.TargetTicks) > 0

	// Track which target ticks we've captured (to handle tick not exactly matching)
	capturedTargets := make(map[uint32]bool)

	// Entity handler to capture state at intervals or specific ticks
	parser.OnEntity(func(e *manta.Entity, op manta.EntityOp) error {
		// Safety check
		if e == nil {
			return nil
		}

		className := e.GetClassName()

		// Track game start time from game rules entity
		if strings.Contains(className, "CDOTAGamerulesProxy") {
			if gst, ok := e.GetFloat32("m_pGameRules.m_flGameStartTime"); ok && gst > 0 && gameStartTime == 0 {
				gameStartTime = gst
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

		// Calculate game time from tick (30 ticks per second)
		var gameTime float32 = 0
		if gameStartTick > 0 && currentTick > gameStartTick {
			gameTime = float32(currentTick-gameStartTick) / 30.0
		}

		// Capture snapshot
		snapshot := captureSnapshot(parser, gameTime, config)
		if snapshot != nil && len(snapshot.Players) > 0 {
			result.Snapshots = append(result.Snapshots, *snapshot)
			lastCaptureTick = currentTick
		}

		return nil
	})

	if err := parser.Start(); err != nil {
		return nil, fmt.Errorf("error parsing file: %w", err)
	}

	result.Success = true
	result.TotalTicks = parser.Tick
	result.SnapshotCount = len(result.Snapshots)
	return result, nil
}

// entityClassToHeroName converts entity class name to npc_dota_hero_* format
// Example: "CDOTA_Unit_Hero_Axe" -> "npc_dota_hero_axe"
func entityClassToHeroName(className string) string {
	// Remove prefix "CDOTA_Unit_Hero_"
	if !strings.HasPrefix(className, "CDOTA_Unit_Hero_") {
		return ""
	}
	heroName := strings.TrimPrefix(className, "CDOTA_Unit_Hero_")
	// Convert to lowercase and add prefix
	return "npc_dota_hero_" + strings.ToLower(heroName)
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
		Players:  make([]PlayerState, 0, 10),
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

	// Find hero entities for position data
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

	// Extract player data by combining PlayerResource and Data entities
	if playerResource != nil {
		for i := 0; i < 10; i++ {
			player := extractPlayerStateFromResource(playerResource, i)
			if player.HeroID > 0 { // Only add if player has a hero
				// Get team slot (0-4 for each team)
				teamSlot := i
				if i >= 5 {
					teamSlot = i - 5
				}

				// Extract LH/DN/gold from the appropriate Data entity
				if player.Team == 2 && dataRadiant != nil {
					extractPlayerStatsFromDataTeam(dataRadiant, teamSlot, &player)
				} else if player.Team == 3 && dataDire != nil {
					extractPlayerStatsFromDataTeam(dataDire, teamSlot, &player)
				}

				// Extract position and hero name from hero entity
				var heroClassName string
				// Look for hero entity by matching player index to hero handle
				if heroHandle, ok := playerResource.GetUint64(fmt.Sprintf("m_vecPlayerTeamData.%04d.m_hSelectedHero", i)); ok {
					if heroEntity, found := heroByHandle[heroHandle&0x3FFF]; found {
						extractHeroPosition(heroEntity, &player)
						heroClassName = heroEntity.GetClassName()
						player.HeroName = entityClassToHeroName(heroClassName)
					}
				}

				// If hero handle lookup failed, try matching by iterating through heroes
				if player.PositionX == 0 && player.PositionY == 0 {
					for _, hero := range heroEntities {
						if hero == nil {
							continue
						}
						// Match hero to player by checking team and hero ID
						if heroID, ok := hero.GetUint32("m_pEntity.m_nameStringableIndex"); ok && int(heroID) == player.HeroID {
							extractHeroPosition(hero, &player)
							heroClassName = hero.GetClassName()
							player.HeroName = entityClassToHeroName(heroClassName)
							break
						}
					}
				}

				// Apply target_heroes filter
				if len(config.TargetHeroes) > 0 {
					if !shouldIncludeHero(heroClassName, config.TargetHeroes) {
						continue // Skip this player
					}
				}

				snapshot.Players = append(snapshot.Players, player)
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

	return snapshot
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
