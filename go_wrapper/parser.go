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

// Parse executes a single-pass parse with multiple collectors.
// This is the main entry point for the v2 API.
//
//export Parse
func Parse(filePath *C.char, configJSON *C.char) *C.char {
	goFilePath := C.GoString(filePath)
	goConfigJSON := C.GoString(configJSON)

	config := ParseConfig{}
	if goConfigJSON != "" {
		if err := json.Unmarshal([]byte(goConfigJSON), &config); err != nil {
			return marshalParseResult(&ParseResult{
				Success: false,
				Error:   fmt.Sprintf("Invalid config JSON: %v", err),
			})
		}
	}

	result, err := RunParse(goFilePath, config)
	if err != nil {
		return marshalParseResult(&ParseResult{
			Success: false,
			Error:   err.Error(),
		})
	}

	return marshalParseResult(result)
}

// RunParse executes a single-pass parse with all requested collectors.
func RunParse(filePath string, config ParseConfig) (*ParseResult, error) {
	result := &ParseResult{
		Success: true,
	}

	// Open file once
	file, err := os.Open(filePath)
	if err != nil {
		return nil, fmt.Errorf("error opening file: %w", err)
	}
	defer file.Close()

	// Create parser once
	parser, err := manta.NewStreamParser(file)
	if err != nil {
		return nil, fmt.Errorf("error creating parser: %w", err)
	}

	// Collector states - these accumulate data during parsing
	var headerInfo *HeaderInfo
	var gameInfo *CDotaGameInfo
	var combatLogRaw []rawCombatLogEntry
	var gameStartTime float32
	var gameStartTick uint32
	var entityState *entityCollectorState
	var gameEventsResult *GameEventsResult
	var modifiersResult *ModifiersResult
	var stringTablesResult *StringTablesResult
	var messagesResult *UniversalResult
	var parserInfoResult *ParserInfo
	var attacksResult *AttacksResult
	var entityDeathsResult *EntityDeathsResult

	// Hero level tracking for combat log enrichment
	// Maps hero name (e.g., "npc_dota_hero_axe") to current level
	heroLevels := make(map[string]int32)

	// Setup collectors based on config

	// Header collector
	if config.Header != nil && config.Header.Enabled {
		headerInfo = &HeaderInfo{Success: false}
		parser.Callbacks.OnCDemoFileHeader(func(m *dota.CDemoFileHeader) error {
			headerInfo.MapName = m.GetMapName()
			headerInfo.ServerName = m.GetServerName()
			headerInfo.ClientName = m.GetClientName()
			headerInfo.GameDirectory = m.GetGameDirectory()
			headerInfo.NetworkProtocol = m.GetNetworkProtocol()
			headerInfo.DemoFileStamp = m.GetDemoFileStamp()
			headerInfo.BuildNum = m.GetBuildNum()
			headerInfo.Game = m.GetGame()
			headerInfo.ServerStartTick = m.GetServerStartTick()
			headerInfo.Success = true
			return nil
		})
	}

	// Game info collector
	if config.GameInfo != nil && config.GameInfo.Enabled {
		gameInfo = &CDotaGameInfo{Success: false}
		parser.Callbacks.OnCDemoFileInfo(func(m *dota.CDemoFileInfo) error {
			gameInfo.PlaybackTime = m.GetPlaybackTime()
			gameInfo.PlaybackTicks = m.GetPlaybackTicks()
			gameInfo.PlaybackFrames = m.GetPlaybackFrames()

			if m.GetGameInfo() != nil && m.GetGameInfo().GetDota() != nil {
				dotaInfo := m.GetGameInfo().GetDota()
				gameInfo.MatchID = dotaInfo.GetMatchId()
				gameInfo.GameMode = dotaInfo.GetGameMode()
				gameInfo.GameWinner = dotaInfo.GetGameWinner()
				gameInfo.LeagueID = dotaInfo.GetLeagueid()
				gameInfo.EndTime = dotaInfo.GetEndTime()
				gameInfo.RadiantTeamID = dotaInfo.GetRadiantTeamId()
				gameInfo.DireTeamID = dotaInfo.GetDireTeamId()
				gameInfo.RadiantTeamTag = dotaInfo.GetRadiantTeamTag()
				gameInfo.DireTeamTag = dotaInfo.GetDireTeamTag()

				if dotaInfo.GetPlayerInfo() != nil {
					gameInfo.PlayerInfo = make([]CPlayerInfo, 0, len(dotaInfo.GetPlayerInfo()))
					for _, p := range dotaInfo.GetPlayerInfo() {
						gameInfo.PlayerInfo = append(gameInfo.PlayerInfo, CPlayerInfo{
							HeroName:     p.GetHeroName(),
							PlayerName:   p.GetPlayerName(),
							IsFakeClient: p.GetIsFakeClient(),
							SteamID:      p.GetSteamid(),
							GameTeam:     p.GetGameTeam(),
						})
					}
				}

				if dotaInfo.GetPicksBans() != nil {
					gameInfo.PicksBans = make([]CHeroSelectEvent, 0, len(dotaInfo.GetPicksBans()))
					for _, pb := range dotaInfo.GetPicksBans() {
						gameInfo.PicksBans = append(gameInfo.PicksBans, CHeroSelectEvent{
							IsPick: pb.GetIsPick(),
							Team:   pb.GetTeam(),
							HeroId: pb.GetHeroId(),
						})
					}
				}

				gameInfo.Success = true
			}
			return nil
		})
	}

	// Combat log collector
	if config.CombatLog != nil {
		combatLogRaw = make([]rawCombatLogEntry, 0)
		clConfig := config.CombatLog

		// Track hero levels from entity updates for combat log enrichment
		parser.OnEntity(func(e *manta.Entity, op manta.EntityOp) error {
			if e == nil {
				return nil
			}
			className := e.GetClassName()
			// Only process hero entities
			if !strings.Contains(className, "CDOTA_Unit_Hero_") {
				return nil
			}
			// Extract hero name from class name (e.g., "CDOTA_Unit_Hero_Axe" -> "npc_dota_hero_axe")
			parts := strings.Split(className, "CDOTA_Unit_Hero_")
			if len(parts) < 2 {
				return nil
			}
			heroName := "npc_dota_hero_" + strings.ToLower(parts[1])
			// Get current level from entity
			if level, ok := e.GetInt32("m_iCurrentLevel"); ok && level > 0 {
				heroLevels[heroName] = level
			}
			return nil
		})

		parser.Callbacks.OnCMsgDOTACombatLogEntry(func(m *dota.CMsgDOTACombatLogEntry) error {
			// Detect game start
			if m.GetType() == dota.DOTA_COMBATLOG_TYPES_DOTA_COMBATLOG_GAME_STATE {
				if m.GetValue() == 5 {
					gameStartTime = m.GetTimestamp()
					gameStartTick = parser.Tick
				}
			}

			if clConfig.MaxEntries > 0 && len(combatLogRaw) >= clConfig.MaxEntries {
				return nil
			}

			entryType := m.GetType()

			// Apply type filter
			if len(clConfig.Types) > 0 {
				found := false
				for _, t := range clConfig.Types {
					if t == int32(entryType) {
						found = true
						break
					}
				}
				if !found {
					return nil
				}
			}

			// NOTE: heroes_only filter is applied in finalizeCombatLog after name resolution
			// This allows checking both boolean flags AND name strings for hero detection

			// Capture hero levels from entity state at this tick
			// Normalize hero names to match entity format (e.g., "storm_spirit" -> "stormspirit")
			var attackerLevel, targetLevel int32
			if attackerName, ok := parser.LookupStringByIndex("CombatLogNames", int32(m.GetAttackerName())); ok {
				normalizedAttacker := normalizeHeroName(attackerName)
				if level, exists := heroLevels[normalizedAttacker]; exists {
					attackerLevel = level
				}
			}
			if targetName, ok := parser.LookupStringByIndex("CombatLogNames", int32(m.GetTargetName())); ok {
				normalizedTarget := normalizeHeroName(targetName)
				if level, exists := heroLevels[normalizedTarget]; exists {
					targetLevel = level
				}
			}

			combatLogRaw = append(combatLogRaw, rawCombatLogEntry{
				tick:              parser.Tick,
				netTick:           parser.NetTick,
				msg:               m,
				attackerHeroLevel: attackerLevel,
				targetHeroLevel:   targetLevel,
			})

			return nil
		})
	}

	// Entity snapshot collector
	if config.Entities != nil {
		entityState = newEntityCollectorState(config.Entities)
		setupEntityCollector(parser, entityState)
	}

	// Game events collector
	if config.GameEvents != nil {
		geConfig := config.GameEvents
		gameEventsResult = &GameEventsResult{
			Events:     make([]GameEventData, 0),
			EventTypes: make([]string, 0),
		}

		eventTypeNames := make(map[int32]string)
		eventTypeFields := make(map[string][]string)

		parser.Callbacks.OnCMsgSource1LegacyGameEventList(func(m *dota.CMsgSource1LegacyGameEventList) error {
			for _, d := range m.GetDescriptors() {
				eventTypeNames[d.GetEventid()] = d.GetName()
				if geConfig.CaptureTypes {
					gameEventsResult.EventTypes = append(gameEventsResult.EventTypes, d.GetName())
				}
				fieldNames := make([]string, len(d.GetKeys()))
				for i, k := range d.GetKeys() {
					fieldNames[i] = k.GetName()
				}
				eventTypeFields[d.GetName()] = fieldNames
			}
			return nil
		})

		parser.Callbacks.OnCMsgSource1LegacyGameEvent(func(m *dota.CMsgSource1LegacyGameEvent) error {
			if geConfig.MaxEvents > 0 && len(gameEventsResult.Events) >= geConfig.MaxEvents {
				return nil
			}

			eventName, ok := eventTypeNames[m.GetEventid()]
			if !ok {
				return nil
			}

			if geConfig.EventFilter != "" && !strings.Contains(eventName, geConfig.EventFilter) {
				return nil
			}

			fields := make(map[string]interface{})
			fieldNames := eventTypeFields[eventName]
			keys := m.GetKeys()

			for i, key := range keys {
				fieldName := fmt.Sprintf("field_%d", i)
				if i < len(fieldNames) {
					fieldName = fieldNames[i]
				}

				switch key.GetType() {
				case 1:
					fields[fieldName] = key.GetValString()
				case 2:
					fields[fieldName] = key.GetValFloat()
				case 3:
					fields[fieldName] = key.GetValLong()
				case 4:
					fields[fieldName] = key.GetValShort()
				case 5:
					fields[fieldName] = key.GetValByte()
				case 6:
					fields[fieldName] = key.GetValBool()
				case 7:
					fields[fieldName] = key.GetValUint64()
				}
			}

			gameEventsResult.Events = append(gameEventsResult.Events, GameEventData{
				Name:    eventName,
				Tick:    parser.Tick,
				NetTick: parser.NetTick,
				Fields:  fields,
			})

			return nil
		})
	}

	// Modifiers collector
	if config.Modifiers != nil {
		modConfig := config.Modifiers
		modifiersResult = &ModifiersResult{
			Modifiers: make([]ModifierEntry, 0),
		}

		parser.OnModifierTableEntry(func(m *dota.CDOTAModifierBuffTableEntry) error {
			if modConfig.MaxModifiers > 0 && len(modifiersResult.Modifiers) >= modConfig.MaxModifiers {
				return nil
			}

			isAura := m.GetAura()
			if modConfig.AurasOnly && !isAura {
				return nil
			}

			modifiersResult.Modifiers = append(modifiersResult.Modifiers, ModifierEntry{
				Tick:          parser.Tick,
				NetTick:       parser.NetTick,
				Parent:        m.GetParent(),
				Caster:        m.GetCaster(),
				Ability:       m.GetAbility(),
				ModifierClass: m.GetModifierClass(),
				SerialNum:     m.GetSerialNum(),
				Index:         m.GetIndex(),
				CreationTime:  m.GetCreationTime(),
				Duration:      m.GetDuration(),
				StackCount:    m.GetStackCount(),
				IsAura:        isAura,
				IsDebuff:      false,
			})

			return nil
		})
	}

	// String tables collector
	if config.StringTables != nil {
		stConfig := config.StringTables
		stringTablesResult = &StringTablesResult{
			Tables:     make(map[string][]StringTableData),
			TableNames: make([]string, 0),
		}

		shouldCaptureTable := func(name string) bool {
			if len(stConfig.TableNames) == 0 {
				return true
			}
			for _, tn := range stConfig.TableNames {
				if tn == name {
					return true
				}
			}
			return false
		}

		parser.Callbacks.OnCSVCMsg_CreateStringTable(func(m *dota.CSVCMsg_CreateStringTable) error {
			tableName := m.GetName()
			if shouldCaptureTable(tableName) {
				stringTablesResult.TableNames = append(stringTablesResult.TableNames, tableName)
				stringTablesResult.Tables[tableName] = make([]StringTableData, 0)
			}
			return nil
		})

		parser.Callbacks.OnCDemoStringTables(func(m *dota.CDemoStringTables) error {
			for _, table := range m.GetTables() {
				tableName := table.GetTableName()
				if !shouldCaptureTable(tableName) {
					continue
				}

				if stringTablesResult.Tables[tableName] == nil {
					stringTablesResult.Tables[tableName] = make([]StringTableData, 0)
					stringTablesResult.TableNames = append(stringTablesResult.TableNames, tableName)
				}

				for i, item := range table.GetItems() {
					if stConfig.MaxEntries > 0 && i >= stConfig.MaxEntries {
						break
					}
					stringTablesResult.Tables[tableName] = append(stringTablesResult.Tables[tableName], StringTableData{
						TableName: tableName,
						Index:     int32(i),
						Key:       item.GetStr(),
					})
					stringTablesResult.TotalEntries++
				}
			}
			return nil
		})
	}

	// Messages (universal) collector
	if config.Messages != nil {
		msgConfig := config.Messages
		messagesResult = &UniversalResult{
			Messages:      make([]MessageEvent, 0),
			CallbacksUsed: make([]string, 0),
		}

		setupAllCallbacks(parser, &messagesResult.Messages, msgConfig.Filter, msgConfig.MaxMessages)
	}

	// Parser info collector
	if config.ParserInfo != nil && config.ParserInfo.Enabled {
		parserInfoResult = &ParserInfo{
			StringTables: make([]string, 0),
		}

		parser.Callbacks.OnCSVCMsg_CreateStringTable(func(m *dota.CSVCMsg_CreateStringTable) error {
			parserInfoResult.StringTables = append(parserInfoResult.StringTables, m.GetName())
			return nil
		})

		parser.Callbacks.OnCSVCMsg_ServerInfo(func(m *dota.CSVCMsg_ServerInfo) error {
			parserInfoResult.GameBuild = m.GetProtocol()
			return nil
		})
	}

	// Attacks collector (from TE_Projectile)
	if config.Attacks != nil {
		attacksConfig := config.Attacks
		attacksResult = &AttacksResult{
			Events: make([]AttackEvent, 0),
		}

		parser.Callbacks.OnCDOTAUserMsg_TE_Projectile(func(m *dota.CDOTAUserMsg_TE_Projectile) error {
			// Only capture attack projectiles
			if !m.GetIsAttack() {
				return nil
			}

			if attacksConfig.MaxEvents > 0 && len(attacksResult.Events) >= attacksConfig.MaxEvents {
				return nil
			}

			sourceHandle := int64(m.GetSource())
			targetHandle := int64(m.GetTarget())

			// Convert handles to entity indices (lower 14 bits)
			sourceIndex := int(sourceHandle & 0x3FFF)
			targetIndex := int(targetHandle & 0x3FFF)

			attacksResult.Events = append(attacksResult.Events, AttackEvent{
				Tick:            int(parser.Tick),
				SourceIndex:     sourceIndex,
				TargetIndex:     targetIndex,
				SourceHandle:    sourceHandle,
				TargetHandle:    targetHandle,
				ProjectileSpeed: int(m.GetMoveSpeed()),
				Dodgeable:       m.GetDodgeable(),
				LaunchTick:      int(m.GetLaunchTick()),
			})

			return nil
		})
	}

	// Entity deaths collector (tracks entity removals)
	if config.EntityDeaths != nil {
		entityDeathsConfig := config.EntityDeaths
		entityDeathsResult = &EntityDeathsResult{
			Events: make([]EntityDeath, 0),
		}

		parser.OnEntity(func(e *manta.Entity, op manta.EntityOp) error {
			// Only track deletions
			if !op.Flag(manta.EntityOpDeleted) {
				return nil
			}
			if e == nil {
				return nil
			}

			if entityDeathsConfig.MaxEvents > 0 && len(entityDeathsResult.Events) >= entityDeathsConfig.MaxEvents {
				return nil
			}

			className := e.GetClassName()

			// Determine entity type
			isHero := strings.Contains(className, "CDOTA_Unit_Hero_")
			isLaneCreep := strings.Contains(className, "Creep_Lane") || strings.Contains(className, "BaseNPC_Creep_Lane")
			isNeutralCreep := strings.Contains(className, "Neutral") || strings.Contains(className, "NeutralCreep")
			isCreep := isLaneCreep || isNeutralCreep
			isBuilding := strings.Contains(className, "Tower") || strings.Contains(className, "Barracks") || strings.Contains(className, "Fort")
			isSummon := strings.Contains(className, "CDOTA_BaseNPC") && !isCreep && !isHero && !isBuilding

			// Skip items, abilities, and other non-unit entities
			if strings.HasPrefix(className, "CDOTA_Item") || strings.HasPrefix(className, "CDOTA_Ability") {
				return nil
			}

			// Apply filters
			if entityDeathsConfig.HeroesOnly {
				if !isHero {
					return nil
				}
			} else if entityDeathsConfig.CreepsOnly {
				if !isCreep {
					return nil
				}
			} else if entityDeathsConfig.IncludeCreeps {
				// Include heroes, creeps, buildings, summons
				if !isHero && !isCreep && !isBuilding && !isSummon {
					return nil
				}
			} else {
				// Default: only heroes and buildings
				if !isHero && !isBuilding {
					return nil
				}
			}

			// Extract entity data
			var name string
			if n, ok := e.GetString("m_iszUnitName"); ok {
				name = n
			} else if isHero {
				// Build hero name from class name
				parts := strings.Split(className, "CDOTA_Unit_Hero_")
				if len(parts) >= 2 {
					name = "npc_dota_hero_" + strings.ToLower(parts[1])
				}
			}

			var team int
			if t, ok := e.GetInt32("m_iTeamNum"); ok {
				team = int(t)
			}

			var x, y float32
			if cellX, ok := e.GetUint64("CBodyComponent.m_cellX"); ok {
				if cellY, ok2 := e.GetUint64("CBodyComponent.m_cellY"); ok2 {
					if vecX, ok3 := e.GetFloat32("CBodyComponent.m_vecX"); ok3 {
						if vecY, ok4 := e.GetFloat32("CBodyComponent.m_vecY"); ok4 {
							x = float32(cellX)*128.0 + vecX - 8192.0
							y = float32(cellY)*128.0 + vecY - 8192.0
						}
					}
				}
			}

			var health, maxHealth int
			if h, ok := e.GetInt32("m_iHealth"); ok {
				health = int(h)
			}
			if mh, ok := e.GetInt32("m_iMaxHealth"); ok {
				maxHealth = int(mh)
			}

			entityDeathsResult.Events = append(entityDeathsResult.Events, EntityDeath{
				Tick:       int(parser.Tick),
				EntityID:   int(e.GetIndex()),
				ClassName:  className,
				Name:       name,
				Team:       team,
				X:          x,
				Y:          y,
				Health:     health,
				MaxHealth:  maxHealth,
				IsHero:     isHero,
				IsCreep:    isCreep,
				IsBuilding: isBuilding,
				IsNeutral:  isNeutralCreep,
			})

			return nil
		})
	}

	// Run the parser ONCE
	if err := parser.Start(); err != nil {
		return nil, fmt.Errorf("error parsing file: %w", err)
	}

	// Finalize results

	if headerInfo != nil {
		result.Header = headerInfo
	}

	if gameInfo != nil {
		result.GameInfo = gameInfo
	}

	// Combat log: resolve names after parsing
	if combatLogRaw != nil {
		result.CombatLog = finalizeCombatLog(parser, combatLogRaw, gameStartTime, gameStartTick, config.CombatLog)
	}

	// Entity snapshots
	if entityState != nil {
		result.Entities = finalizeEntitySnapshots(entityState, parser.Tick)
	}

	// Game events
	if gameEventsResult != nil {
		gameEventsResult.Success = true
		gameEventsResult.TotalEvents = len(gameEventsResult.Events)
		result.GameEvents = gameEventsResult
	}

	// Modifiers
	if modifiersResult != nil {
		modifiersResult.Success = true
		modifiersResult.TotalModifiers = len(modifiersResult.Modifiers)
		result.Modifiers = modifiersResult
	}

	// String tables
	if stringTablesResult != nil {
		stringTablesResult.Success = true
		result.StringTables = stringTablesResult
	}

	// Messages
	if messagesResult != nil {
		messagesResult.Success = true
		messagesResult.TotalMessages = len(messagesResult.Messages)
		result.Messages = messagesResult
	}

	// Parser info
	if parserInfoResult != nil {
		parserInfoResult.Tick = parser.Tick
		parserInfoResult.NetTick = parser.NetTick
		entities := parser.FilterEntity(func(e *manta.Entity) bool {
			return e != nil
		})
		parserInfoResult.EntityCount = len(entities)
		parserInfoResult.Success = true
		result.ParserInfo = parserInfoResult
	}

	// Attacks
	if attacksResult != nil {
		// Post-process: add game time to events
		for i := range attacksResult.Events {
			attacksResult.Events[i].GameTime = TickToGameTime(uint32(attacksResult.Events[i].Tick), gameStartTick)
			attacksResult.Events[i].GameTimeStr = FormatGameTime(attacksResult.Events[i].GameTime)
		}
		attacksResult.TotalEvents = len(attacksResult.Events)
		result.Attacks = attacksResult
	}

	// Entity deaths
	if entityDeathsResult != nil {
		// Post-process: add game time to events
		for i := range entityDeathsResult.Events {
			entityDeathsResult.Events[i].GameTime = TickToGameTime(uint32(entityDeathsResult.Events[i].Tick), gameStartTick)
			entityDeathsResult.Events[i].GameTimeStr = FormatGameTime(entityDeathsResult.Events[i].GameTime)
		}
		entityDeathsResult.TotalEvents = len(entityDeathsResult.Events)
		result.EntityDeaths = entityDeathsResult
	}

	return result, nil
}

// rawCombatLogEntry stores combat log data before name resolution
type rawCombatLogEntry struct {
	tick             uint32
	netTick          uint32
	msg              *dota.CMsgDOTACombatLogEntry
	attackerHeroLevel int32  // Captured from entity state at this tick
	targetHeroLevel   int32  // Captured from entity state at this tick
}

// isHeroName checks if a name string indicates a hero
func isHeroName(name string) bool {
	return strings.Contains(name, "npc_dota_hero_")
}

// normalizeHeroName converts combat log hero names to entity class format.
// Combat log uses "npc_dota_hero_storm_spirit" while entities use "npc_dota_hero_stormspirit".
func normalizeHeroName(name string) string {
	if !strings.HasPrefix(name, "npc_dota_hero_") {
		return name
	}
	// Remove underscores from the hero name part (after "npc_dota_hero_")
	suffix := strings.TrimPrefix(name, "npc_dota_hero_")
	normalized := strings.ReplaceAll(suffix, "_", "")
	return "npc_dota_hero_" + normalized
}

// finalizeCombatLog resolves names and builds the final result
func finalizeCombatLog(parser *manta.Parser, rawEntries []rawCombatLogEntry, gameStartTime float32, gameStartTick uint32, clConfig *CombatLogConfig) *CombatLogResult {
	result := &CombatLogResult{
		Entries:       make([]CombatLogEntry, 0, len(rawEntries)),
		Success:       true,
		GameStartTime: gameStartTime,
		GameStartTick: gameStartTick,
	}

	getName := func(idx uint32) string {
		if name, ok := parser.LookupStringByIndex("CombatLogNames", int32(idx)); ok {
			return name
		}
		return fmt.Sprintf("unknown_%d", idx)
	}

	for _, raw := range rawEntries {
		m := raw.msg
		entryType := m.GetType()

		assistPlayers := make([]int32, len(m.GetAssistPlayers()))
		for i, ap := range m.GetAssistPlayers() {
			assistPlayers[i] = ap
		}

		valueName := ""
		if name, ok := parser.LookupStringByIndex("CombatLogNames", int32(m.GetValue())); ok {
			valueName = name
		}

		modifierAbilityName := ""
		if v := m.GetModifierAbility(); v > 0 {
			if name, ok := parser.LookupStringByIndex("CombatLogNames", int32(v)); ok {
				modifierAbilityName = name
			}
		}

		modifierPurgeAbilityName := ""
		if v := m.GetModifierPurgeAbility(); v > 0 {
			if name, ok := parser.LookupStringByIndex("CombatLogNames", int32(v)); ok {
				modifierPurgeAbilityName = name
			}
		}

		modifierPurgeNpcName := ""
		if v := m.GetModifierPurgeNpc(); v > 0 {
			if name, ok := parser.LookupStringByIndex("CombatLogNames", int32(v)); ok {
				modifierPurgeNpcName = name
			}
		}

		entry := CombatLogEntry{
			Tick:                     raw.tick,
			NetTick:                  raw.netTick,
			Type:                     int32(entryType),
			TypeName:                 dota.DOTA_COMBATLOG_TYPES_name[int32(entryType)],
			TargetName:               getName(m.GetTargetName()),
			TargetSourceName:         getName(m.GetTargetSourceName()),
			AttackerName:             getName(m.GetAttackerName()),
			DamageSourceName:         getName(m.GetDamageSourceName()),
			InflictorName:            getName(m.GetInflictorName()),
			IsAttackerIllusion:       m.GetIsAttackerIllusion(),
			IsAttackerHero:           m.GetIsAttackerHero(),
			IsTargetIllusion:         m.GetIsTargetIllusion(),
			IsTargetHero:             m.GetIsTargetHero(),
			IsVisibleRadiant:         m.GetIsVisibleRadiant(),
			IsVisibleDire:            m.GetIsVisibleDire(),
			Value:                    int32(m.GetValue()),
			ValueName:                valueName,
			Health:                   m.GetHealth(),
			GameTime:                 TickToGameTime(raw.tick, gameStartTick),
			StunDuration:             m.GetStunDuration(),
			SlowDuration:             m.GetSlowDuration(),
			IsAbilityToggleOn:        m.GetIsAbilityToggleOn(),
			IsAbilityToggleOff:       m.GetIsAbilityToggleOff(),
			AbilityLevel:             int32(m.GetAbilityLevel()),
			XP:                       int32(m.GetXpReason()),
			Gold:                     int32(m.GetGoldReason()),
			LastHits:                 int32(m.GetLastHits()),
			AttackerTeam:             int32(m.GetAttackerTeam()),
			TargetTeam:               int32(m.GetTargetTeam()),
			LocationX:                m.GetLocationX(),
			LocationY:                m.GetLocationY(),
			AssistPlayer0:            int32(m.GetAssistPlayer0()),
			AssistPlayer1:            int32(m.GetAssistPlayer1()),
			AssistPlayer2:            int32(m.GetAssistPlayer2()),
			AssistPlayer3:            int32(m.GetAssistPlayer3()),
			AssistPlayers:            assistPlayers,
			DamageType:               int32(m.GetDamageType()),
			DamageCategory:           int32(m.GetDamageCategory()),
			IsTargetBuilding:         m.GetIsTargetBuilding(),
			IsUltimateAbility:        m.GetIsUltimateAbility(),
			IsHealSave:               m.GetIsHealSave(),
			TargetIsSelf:             m.GetTargetIsSelf(),
			ModifierDuration:         m.GetModifierDuration(),
			StackCount:               int32(m.GetStackCount()),
			HiddenModifier:           m.GetHiddenModifier(),
			InvisibilityModifier:     m.GetInvisibilityModifier(),
			AttackerHeroLevel:        raw.attackerHeroLevel, // From entity state (protobuf value is always 0)
			TargetHeroLevel:          raw.targetHeroLevel,   // From entity state (protobuf value is always 0)
			XPM:                      int32(m.GetXpm()),
			GPM:                      int32(m.GetGpm()),
			EventLocation:            int32(m.GetEventLocation()),
			Networth:                 int32(m.GetNetworth()),
			ObsWardsPlaced:           int32(m.GetObsWardsPlaced()),
			NeutralCampType:          int32(m.GetNeutralCampType()),
			NeutralCampTeam:          int32(m.GetNeutralCampTeam()),
			RuneType:                 int32(m.GetRuneType()),
			BuildingType:             int32(m.GetBuildingType()),
			ModifierElapsedDuration:  m.GetModifierElapsedDuration(),
			SilenceModifier:          m.GetSilenceModifier(),
			HealFromLifesteal:        m.GetHealFromLifesteal(),
			ModifierPurged:           m.GetModifierPurged(),
			ModifierPurgeAbility:     int32(m.GetModifierPurgeAbility()),
			ModifierPurgeAbilityName: modifierPurgeAbilityName,
			ModifierPurgeNpc:         int32(m.GetModifierPurgeNpc()),
			ModifierPurgeNpcName:     modifierPurgeNpcName,
			RootModifier:             m.GetRootModifier(),
			AuraModifier:             m.GetAuraModifier(),
			ArmorDebuffModifier:      m.GetArmorDebuffModifier(),
			NoPhysicalDamageModifier: m.GetNoPhysicalDamageModifier(),
			ModifierAbility:          int32(m.GetModifierAbility()),
			ModifierAbilityName:      modifierAbilityName,
			ModifierHidden:           m.GetModifierHidden(),
			MotionControllerModifier: m.GetMotionControllerModifier(),
			SpellEvaded:              m.GetSpellEvaded(),
			LongRangeKill:            m.GetLongRangeKill(),
			TotalUnitDeathCount:      int32(m.GetTotalUnitDeathCount()),
			WillReincarnate:          m.GetWillReincarnate(),
			InflictorIsStolenAbility: m.GetInflictorIsStolenAbility(),
			SpellGeneratedAttack:     m.GetSpellGeneratedAttack(),
			UsesCharges:              m.GetUsesCharges(),
			AtNightTime:              m.GetAtNightTime(),
			AttackerHasScepter:       m.GetAttackerHasScepter(),
			RegeneratedHealth:        m.GetRegeneratedHealth(),
			KillEaterEvent:           int32(m.GetKillEaterEvent()),
			UnitStatusLabel:          int32(m.GetUnitStatusLabel()),
			TrackedStatId:            int32(m.GetTrackedStatId()),
		}

		// Apply heroes_only filter (checks both boolean flags AND name strings)
		if clConfig != nil && clConfig.HeroesOnly {
			isHeroRelated := entry.IsAttackerHero || entry.IsTargetHero ||
				isHeroName(entry.AttackerName) || isHeroName(entry.TargetName)
			if !isHeroRelated {
				continue
			}
		}

		result.Entries = append(result.Entries, entry)
	}

	result.TotalEntries = len(result.Entries)
	return result
}

// entityCollectorState manages entity snapshot collection during parsing
type entityCollectorState struct {
	config          *EntityParseConfig
	snapshots       []EntitySnapshot
	lastCaptureTick uint32
	gameStartTime   float32
	gameStartTick   uint32
	targetTickSet   map[uint32]bool
	capturedTargets map[uint32]bool
}

func newEntityCollectorState(config *EntityParseConfig) *entityCollectorState {
	state := &entityCollectorState{
		config:          config,
		snapshots:       make([]EntitySnapshot, 0),
		targetTickSet:   make(map[uint32]bool),
		capturedTargets: make(map[uint32]bool),
	}

	for _, t := range config.TargetTicks {
		state.targetTickSet[t] = true
	}

	return state
}

// setupEntityCollector registers entity callbacks for snapshot collection
func setupEntityCollector(parser *manta.Parser, state *entityCollectorState) {
	config := state.config
	useTargetTicks := len(config.TargetTicks) > 0

	parser.OnEntity(func(e *manta.Entity, op manta.EntityOp) error {
		if e == nil {
			return nil
		}

		className := e.GetClassName()

		// Track game start time (needs to run on all entities)
		if strings.Contains(className, "CDOTAGamerulesProxy") {
			if gst, ok := e.GetFloat32("m_pGameRules.m_flGameStartTime"); ok && gst > 0 && state.gameStartTime == 0 {
				state.gameStartTime = gst
				state.gameStartTick = parser.Tick
			}
			return nil // Not a PlayerResource, skip capture check
		}

		// Only capture on updates to PlayerResource entity (like RunEntityParse)
		// This ensures we have valid player data when capturing
		if !op.Flag(manta.EntityOpUpdated) {
			return nil
		}
		if !strings.Contains(className, "CDOTA_PlayerResource") {
			return nil
		}

		// Check max snapshots
		if config.MaxSnapshots > 0 && len(state.snapshots) >= config.MaxSnapshots {
			return nil
		}

		currentTick := parser.Tick
		shouldCapture := false

		if useTargetTicks {
			// Check if we should capture this tick
			for targetTick := range state.targetTickSet {
				if currentTick >= targetTick && !state.capturedTargets[targetTick] {
					shouldCapture = true
					state.capturedTargets[targetTick] = true
					break
				}
			}
		} else {
			// Interval-based capture
			interval := uint32(config.IntervalTicks)
			if interval == 0 {
				interval = 1800 // Default ~1 minute
			}
			if currentTick >= state.lastCaptureTick+interval {
				shouldCapture = true
			}
		}

		if shouldCapture {
			snapshot := captureEntitySnapshot(parser, config, state.gameStartTime, state.gameStartTick)
			// Only add snapshot if it has heroes
			if len(snapshot.Heroes) > 0 {
				state.snapshots = append(state.snapshots, snapshot)
				state.lastCaptureTick = currentTick
			}
		}

		return nil
	})
}

// captureEntitySnapshot captures the current entity state
// This delegates to captureSnapshot from entity_parser.go which properly extracts
// hero positions by finding CDOTA_Unit_Hero_* entities
func captureEntitySnapshot(parser *manta.Parser, config *EntityParseConfig, gameStartTime float32, gameStartTick uint32) EntitySnapshot {
	// Calculate game time using centralized conversion
	gameTime := TickToGameTime(parser.Tick, gameStartTick)

	// Use the working captureSnapshot from entity_parser.go
	entityConfig := EntityParseConfig{
		IntervalTicks: config.IntervalTicks,
		MaxSnapshots:  config.MaxSnapshots,
		TargetTicks:   config.TargetTicks,
		TargetHeroes:  config.TargetHeroes,
		EntityClasses: config.EntityClasses,
		IncludeRaw:    config.IncludeRaw,
		IncludeCreeps: config.IncludeCreeps,
	}

	result := captureSnapshot(parser, gameTime, entityConfig)
	if result != nil {
		return *result
	}

	// Fallback empty snapshot
	return EntitySnapshot{
		Tick:   parser.Tick,
		Heroes: make([]HeroSnapshot, 0),
		Teams:  make([]TeamState, 0),
	}
}

// finalizeEntitySnapshots builds the final entity result
func finalizeEntitySnapshots(state *entityCollectorState, totalTicks uint32) *EntityParseResult {
	// Post-process: recalculate game_time for all snapshots now that we know gameStartTick
	// This fixes pre-horn snapshots that were captured before gameStartTick was known
	for i := range state.snapshots {
		state.snapshots[i].GameTime = TickToGameTime(state.snapshots[i].Tick, state.gameStartTick)
	}

	return &EntityParseResult{
		Snapshots:     state.snapshots,
		Success:       true,
		TotalTicks:    totalTicks,
		SnapshotCount: len(state.snapshots),
		GameStartTick: state.gameStartTick,
	}
}

func marshalParseResult(result *ParseResult) *C.char {
	jsonResult, err := json.Marshal(result)
	if err != nil {
		errorResult := &ParseResult{
			Success: false,
			Error:   fmt.Sprintf("Error marshaling result: %v", err),
		}
		jsonResult, _ = json.Marshal(errorResult)
	}
	return C.CString(string(jsonResult))
}
