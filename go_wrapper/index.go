package main

/*
#include <stdlib.h>
*/
import "C"

import (
	"encoding/json"
	"fmt"
	"os"
	"sort"
	"strings"

	"github.com/dotabuff/manta"
	"github.com/dotabuff/manta/dota"
)

// Keyframe represents a point in the demo that can be used as a seek target
type Keyframe struct {
	Tick     int     `json:"tick"`
	NetTick  int     `json:"net_tick"`
	GameTime float32 `json:"game_time"`
}

// DemoIndex holds keyframes for seeking
type DemoIndex struct {
	Keyframes   []Keyframe `json:"keyframes"`
	TotalTicks  int        `json:"total_ticks"`
	GameStarted int        `json:"game_started"` // Tick when game clock started (horn)
	Success     bool       `json:"success"`
	Error       string     `json:"error,omitempty"`
}

// EntityStateSnapshot captures entity states at a specific tick
type EntityStateSnapshot struct {
	Tick     int            `json:"tick"`
	NetTick  int            `json:"net_tick"`
	GameTime float32        `json:"game_time"`
	Heroes   []HeroSnapshot `json:"heroes"`
	Success  bool           `json:"success"`
	Error    string         `json:"error,omitempty"`
}

// HeroSnapshot captures a hero's state
type HeroSnapshot struct {
	Index      int     `json:"index"`
	PlayerID   int     `json:"player_id"`
	HeroName   string  `json:"hero_name"`
	Team       int     `json:"team"`
	Level      int     `json:"level"`
	Health     int     `json:"health"`
	MaxHealth  int     `json:"max_health"`
	Mana       float32 `json:"mana"`
	MaxMana    float32 `json:"max_mana"`
	X          float32 `json:"x"`
	Y          float32 `json:"y"`
	IsClone    bool    `json:"is_clone,omitempty"`
	IsIllusion bool    `json:"is_illusion,omitempty"`
	// Combat stats
	Armor           float32 `json:"armor"`
	MagicResistance float32 `json:"magic_resistance"`
	DamageMin       int     `json:"damage_min"`
	DamageMax       int     `json:"damage_max"`
	AttackRange     int     `json:"attack_range"`
	// Attributes
	Strength  float32 `json:"strength"`
	Agility   float32 `json:"agility"`
	Intellect float32 `json:"intellect"`
}

// SnapshotConfig configures snapshot capture
type SnapshotConfig struct {
	TargetTick       int  `json:"target_tick"`
	IncludeIllusions bool `json:"include_illusions"`
}

// RangeParseConfig configures range-based parsing
type RangeParseConfig struct {
	StartTick  int  `json:"start_tick"`
	EndTick    int  `json:"end_tick"`
	CombatLog  bool `json:"combat_log"`
	Messages   bool `json:"messages"`
	GameEvents bool `json:"game_events"`
}

// RangeParseResult contains data from a tick range
type RangeParseResult struct {
	StartTick   int                      `json:"start_tick"`
	EndTick     int                      `json:"end_tick"`
	ActualStart int                      `json:"actual_start"`
	ActualEnd   int                      `json:"actual_end"`
	CombatLog   []map[string]interface{} `json:"combat_log,omitempty"`
	Messages    []map[string]interface{} `json:"messages,omitempty"`
	Success     bool                     `json:"success"`
	Error       string                   `json:"error,omitempty"`
}

//export BuildIndex
func BuildIndex(filePath *C.char, intervalTicks C.int) *C.char {
	path := C.GoString(filePath)
	interval := int(intervalTicks)

	if interval <= 0 {
		interval = 1800 // Default: every 60 seconds (30 ticks/sec * 60)
	}

	result := buildDemoIndex(path, interval)
	jsonResult, _ := json.Marshal(result)
	return C.CString(string(jsonResult))
}

func buildDemoIndex(filePath string, intervalTicks int) *DemoIndex {
	file, err := os.Open(filePath)
	if err != nil {
		return &DemoIndex{
			Success: false,
			Error:   fmt.Sprintf("Failed to open file: %v", err),
		}
	}
	defer file.Close()

	parser, err := manta.NewStreamParser(file)
	if err != nil {
		return &DemoIndex{
			Success: false,
			Error:   fmt.Sprintf("Failed to create parser: %v", err),
		}
	}

	index := &DemoIndex{
		Keyframes: make([]Keyframe, 0),
		Success:   true,
	}

	lastKeyframeTick := -intervalTicks
	var gameStartTick int
	var gameStartTime float32
	const ticksPerSecond = 30.0

	// Track game time and create keyframes
	parser.OnEntity(func(e *manta.Entity, op manta.EntityOp) error {
		if e == nil {
			return nil
		}

		className := e.GetClassName()
		currentTick := int(parser.Tick)

		// Track game start time from game rules entity
		if strings.Contains(className, "CDOTAGamerulesProxy") {
			if gst, ok := e.GetFloat32("m_pGameRules.m_flGameStartTime"); ok && gst > 0 && gameStartTime == 0 {
				gameStartTime = gst
				gameStartTick = currentTick
				index.GameStarted = currentTick
			}
		}

		// Only on updates, not creates/deletes
		if !op.Flag(manta.EntityOpUpdated) {
			return nil
		}

		// Add keyframe if enough ticks have passed
		if currentTick-lastKeyframeTick >= intervalTicks {
			// Calculate game time based on ticks elapsed since game start
			var gameTime float32
			if gameStartTick > 0 && currentTick >= gameStartTick {
				gameTime = float32(currentTick-gameStartTick) / ticksPerSecond
			}

			index.Keyframes = append(index.Keyframes, Keyframe{
				Tick:     currentTick,
				NetTick:  int(parser.NetTick),
				GameTime: gameTime,
			})
			lastKeyframeTick = currentTick
		}

		return nil
	})

	// Parse entire file
	if err := parser.Start(); err != nil {
		return &DemoIndex{
			Success: false,
			Error:   fmt.Sprintf("Parse failed: %v", err),
		}
	}

	index.TotalTicks = int(parser.Tick)

	return index
}

//export GetSnapshot
func GetSnapshot(filePath *C.char, configJSON *C.char) *C.char {
	path := C.GoString(filePath)
	configStr := C.GoString(configJSON)

	var config SnapshotConfig
	if err := json.Unmarshal([]byte(configStr), &config); err != nil {
		result := &EntityStateSnapshot{
			Success: false,
			Error:   fmt.Sprintf("Invalid config: %v", err),
		}
		jsonResult, _ := json.Marshal(result)
		return C.CString(string(jsonResult))
	}

	result := getEntitySnapshot(path, config)
	jsonResult, _ := json.Marshal(result)
	return C.CString(string(jsonResult))
}

func getEntitySnapshot(filePath string, config SnapshotConfig) *EntityStateSnapshot {
	file, err := os.Open(filePath)
	if err != nil {
		return &EntityStateSnapshot{
			Success: false,
			Error:   fmt.Sprintf("Failed to open file: %v", err),
		}
	}
	defer file.Close()

	parser, err := manta.NewStreamParser(file)
	if err != nil {
		return &EntityStateSnapshot{
			Success: false,
			Error:   fmt.Sprintf("Failed to create parser: %v", err),
		}
	}

	snapshot := &EntityStateSnapshot{
		Heroes:  make([]HeroSnapshot, 0),
		Success: true,
	}

	var gameStartTick int
	var gameStartTime float32
	reachedTarget := false
	const ticksPerSecond = 30.0

	// Track entities by their index (handle)
	heroByIndex := make(map[uint32]*manta.Entity)
	var playerResource *manta.Entity

	parser.OnEntity(func(e *manta.Entity, op manta.EntityOp) error {
		if e == nil || reachedTarget {
			return nil
		}

		className := e.GetClassName()
		currentTick := int(parser.Tick)

		// Track game start time
		if strings.Contains(className, "CDOTAGamerulesProxy") {
			if gst, ok := e.GetFloat32("m_pGameRules.m_flGameStartTime"); ok && gst > 0 && gameStartTime == 0 {
				gameStartTime = gst
				gameStartTick = currentTick
			}
		}

		// Track CDOTA_PlayerResource for hero handles
		if strings.Contains(className, "CDOTA_PlayerResource") {
			if op.Flag(manta.EntityOpCreated) || op.Flag(manta.EntityOpUpdated) {
				playerResource = e
			} else if op.Flag(manta.EntityOpDeleted) {
				playerResource = nil
			}
		}

		// Track hero entities by their entity index
		if strings.HasPrefix(className, "CDOTA_Unit_Hero_") {
			idx := uint32(e.GetIndex())
			if op.Flag(manta.EntityOpCreated) || op.Flag(manta.EntityOpUpdated) {
				heroByIndex[idx] = e
			} else if op.Flag(manta.EntityOpDeleted) {
				delete(heroByIndex, idx)
			}
		}

		// Check if we've reached target tick
		if currentTick >= config.TargetTick {
			reachedTarget = true
			snapshot.Tick = currentTick
			snapshot.NetTick = int(parser.NetTick)

			// Calculate game time
			if gameStartTick > 0 && currentTick >= gameStartTick {
				snapshot.GameTime = float32(currentTick-gameStartTick) / ticksPerSecond
			}

			// Build set of main hero entity indices
			mainHeroIndices := make(map[uint32]int) // entity index -> player index

			// Link players to heroes using PlayerResource handles
			if playerResource != nil {
				for playerIdx := 0; playerIdx < 10; playerIdx++ {
					// Get hero handle for this player
					heroHandle, ok := playerResource.GetUint64(fmt.Sprintf("m_vecPlayerTeamData.%04d.m_hSelectedHero", playerIdx))
					if !ok || heroHandle == 0 {
						continue
					}

					// Extract entity index from handle (lower 14 bits)
					heroEntityIdx := uint32(heroHandle & 0x3FFF)
					mainHeroIndices[heroEntityIdx] = playerIdx

					// Find the hero entity
					entity, found := heroByIndex[heroEntityIdx]
					if !found || entity == nil {
						continue
					}

					hero := extractHeroSnapshot(entity, playerIdx)
					snapshot.Heroes = append(snapshot.Heroes, hero)
				}
			}

			// If include_illusions is enabled, add clones/illusions
			if config.IncludeIllusions {
				for idx, entity := range heroByIndex {
					if entity == nil {
						continue
					}

					// Skip main heroes (already added)
					if _, isMain := mainHeroIndices[idx]; isMain {
						continue
					}

					// Get player ID for this clone
					playerID := -1
					if pid, ok := entity.GetInt32("m_iPlayerID"); ok {
						// Convert from Dota player ID format (0,2,4,6,8,10,12,14,16,18) to 0-9
						playerID = int(pid) / 2
					}

					hero := extractHeroSnapshot(entity, playerID)

					// Check if it's an illusion or clone
					if isIllusion, ok := entity.GetBool("m_bIsIllusion"); ok && isIllusion {
						hero.IsIllusion = true
					}
					// Check for replicating handle (MK soldiers, Morph replicate)
					if repHandle, ok := entity.GetUint64("m_hReplicatingOtherHeroModel"); ok && repHandle != 16777215 && repHandle != 0 {
						hero.IsClone = true
					}
					// If neither flag is set but it's not the main hero, mark as clone
					if !hero.IsIllusion && !hero.IsClone {
						hero.IsClone = true
					}

					snapshot.Heroes = append(snapshot.Heroes, hero)
				}
			}

			return fmt.Errorf("target reached") // Stop parsing
		}

		return nil
	})

	// Parse until target tick
	parser.Start()

	return snapshot
}

// extractHeroSnapshot extracts hero state from entity
func extractHeroSnapshot(entity *manta.Entity, playerIdx int) HeroSnapshot {
	hero := HeroSnapshot{
		HeroName: entity.GetClassName(),
		Index:    int(entity.GetIndex()),
		PlayerID: playerIdx,
	}

	// Team based on player slot (0-4 = Radiant, 5-9 = Dire)
	if playerIdx >= 0 && playerIdx < 5 {
		hero.Team = 2 // Radiant
	} else if playerIdx >= 5 {
		hero.Team = 3 // Dire
	}

	if level, ok := entity.GetInt32("m_iCurrentLevel"); ok {
		hero.Level = int(level)
	}
	if health, ok := entity.GetInt32("m_iHealth"); ok {
		hero.Health = int(health)
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

	return hero
}

//export ParseRange
func ParseRange(filePath *C.char, configJSON *C.char) *C.char {
	path := C.GoString(filePath)
	configStr := C.GoString(configJSON)

	var config RangeParseConfig
	if err := json.Unmarshal([]byte(configStr), &config); err != nil {
		result := &RangeParseResult{
			Success: false,
			Error:   fmt.Sprintf("Invalid config: %v", err),
		}
		jsonResult, _ := json.Marshal(result)
		return C.CString(string(jsonResult))
	}

	result := parseRange(path, config)
	jsonResult, _ := json.Marshal(result)
	return C.CString(string(jsonResult))
}

func parseRange(filePath string, config RangeParseConfig) *RangeParseResult {
	file, err := os.Open(filePath)
	if err != nil {
		return &RangeParseResult{
			Success: false,
			Error:   fmt.Sprintf("Failed to open file: %v", err),
		}
	}
	defer file.Close()

	parser, err := manta.NewStreamParser(file)
	if err != nil {
		return &RangeParseResult{
			Success: false,
			Error:   fmt.Sprintf("Failed to create parser: %v", err),
		}
	}

	result := &RangeParseResult{
		StartTick: config.StartTick,
		EndTick:   config.EndTick,
		Success:   true,
	}

	if config.CombatLog {
		result.CombatLog = make([]map[string]interface{}, 0)
	}
	if config.Messages {
		result.Messages = make([]map[string]interface{}, 0)
	}

	inRange := false
	pastRange := false

	// Helper to resolve string indices
	getName := func(idx uint32) string {
		if name, ok := parser.LookupStringByIndex("CombatLogNames", int32(idx)); ok {
			return name
		}
		return fmt.Sprintf("unknown_%d", idx)
	}

	// Combat log callback
	if config.CombatLog {
		parser.Callbacks.OnCMsgDOTACombatLogEntry(func(m *dota.CMsgDOTACombatLogEntry) error {
			tick := int(parser.Tick)
			if tick >= config.StartTick && tick <= config.EndTick {
				if !inRange {
					inRange = true
					result.ActualStart = tick
				}

				// Resolve string names
				targetName := getName(m.GetTargetName())
				attackerName := getName(m.GetAttackerName())
				inflictor := getName(m.GetInflictorName())
				sourceName := getName(m.GetDamageSourceName())

				entry := map[string]interface{}{
					"tick":               tick,
					"type":               m.GetType(),
					"target_name":        targetName,
					"attacker_name":      attackerName,
					"inflictor_name":     inflictor,
					"damage_source_name": sourceName,
					"value":              m.GetValue(),
					"health":             m.GetHealth(),
					"timestamp":          m.GetTimestamp(),
				}

				// Add additional fields if present
				if m.GetIsAttackerIllusion() {
					entry["is_attacker_illusion"] = true
				}
				if m.GetIsTargetIllusion() {
					entry["is_target_illusion"] = true
				}

				result.CombatLog = append(result.CombatLog, entry)
			} else if tick > config.EndTick {
				pastRange = true
			}
			return nil
		})
	}

	// Message callback
	if config.Messages {
		parser.Callbacks.OnCDOTAUserMsg_ChatMessage(func(m *dota.CDOTAUserMsg_ChatMessage) error {
			tick := int(parser.Tick)
			if tick >= config.StartTick && tick <= config.EndTick {
				if !inRange {
					inRange = true
					result.ActualStart = tick
				}
				result.Messages = append(result.Messages, map[string]interface{}{
					"tick":    tick,
					"type":    "CDOTAUserMsg_ChatMessage",
					"message": m.String(),
				})
			} else if tick > config.EndTick {
				pastRange = true
			}
			return nil
		})
	}

	// Track when we're done with range
	parser.OnEntity(func(e *manta.Entity, op manta.EntityOp) error {
		tick := int(parser.Tick)
		if tick > config.EndTick && pastRange {
			result.ActualEnd = tick
			return fmt.Errorf("range complete")
		}
		return nil
	})

	// Parse file
	parser.Start()

	if result.ActualEnd == 0 {
		result.ActualEnd = int(parser.Tick)
	}

	return result
}

//export FindKeyframe
func FindKeyframe(indexJSON *C.char, targetTick C.int) *C.char {
	indexStr := C.GoString(indexJSON)
	tick := int(targetTick)

	var index DemoIndex
	if err := json.Unmarshal([]byte(indexStr), &index); err != nil {
		result := map[string]interface{}{
			"success": false,
			"error":   fmt.Sprintf("Invalid index: %v", err),
		}
		jsonResult, _ := json.Marshal(result)
		return C.CString(string(jsonResult))
	}

	if len(index.Keyframes) == 0 {
		result := map[string]interface{}{
			"success": false,
			"error":   "No keyframes in index",
		}
		jsonResult, _ := json.Marshal(result)
		return C.CString(string(jsonResult))
	}

	// Binary search for keyframe with tick <= target
	keyframes := index.Keyframes
	idx := sort.Search(len(keyframes), func(i int) bool {
		return keyframes[i].Tick > tick
	})

	if idx == 0 {
		// Target is before first keyframe
		result := map[string]interface{}{
			"success":  true,
			"keyframe": keyframes[0],
			"exact":    keyframes[0].Tick == tick,
		}
		jsonResult, _ := json.Marshal(result)
		return C.CString(string(jsonResult))
	}

	// Return keyframe just before or at target
	kf := keyframes[idx-1]
	result := map[string]interface{}{
		"success":  true,
		"keyframe": kf,
		"exact":    kf.Tick == tick,
	}
	jsonResult, _ := json.Marshal(result)
	return C.CString(string(jsonResult))
}
