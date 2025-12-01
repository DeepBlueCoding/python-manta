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

// ============================================================================
// GAME EVENTS PARSING
// ============================================================================

// GameEventData represents a parsed game event with typed fields
type GameEventData struct {
	Name      string                 `json:"name"`
	Tick      uint32                 `json:"tick"`
	NetTick   uint32                 `json:"net_tick"`
	Fields    map[string]interface{} `json:"fields"`
}

// GameEventsResult holds the result of game events parsing
type GameEventsResult struct {
	Events       []GameEventData `json:"events"`
	EventTypes   []string        `json:"event_types"`
	Success      bool            `json:"success"`
	Error        string          `json:"error,omitempty"`
	TotalEvents  int             `json:"total_events"`
}

// GameEventsConfig controls game event parsing
type GameEventsConfig struct {
	EventFilter  string   `json:"event_filter"`   // Filter by event name (substring match)
	EventNames   []string `json:"event_names"`    // Specific event names to capture (empty = all)
	MaxEvents    int      `json:"max_events"`     // Max events to capture (0 = unlimited)
	CaptureTypes bool     `json:"capture_types"`  // Capture event type definitions
}

//export ParseGameEvents
func ParseGameEvents(filePath *C.char, configJSON *C.char) *C.char {
	goFilePath := C.GoString(filePath)
	goConfigJSON := C.GoString(configJSON)

	config := GameEventsConfig{
		MaxEvents:    0,
		CaptureTypes: true,
	}
	if goConfigJSON != "" {
		json.Unmarshal([]byte(goConfigJSON), &config)
	}

	result, err := RunGameEventsParse(goFilePath, config)
	if err != nil {
		failure := &GameEventsResult{
			Events:  make([]GameEventData, 0),
			Success: false,
			Error:   err.Error(),
		}
		return marshalGameEventsResult(failure)
	}

	return marshalGameEventsResult(result)
}

// RunGameEventsParse executes game events parsing
func RunGameEventsParse(filePath string, config GameEventsConfig) (*GameEventsResult, error) {
	result := &GameEventsResult{
		Events:     make([]GameEventData, 0),
		EventTypes: make([]string, 0),
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

	// Store event type definitions for lookup
	eventTypeNames := make(map[int32]string)
	eventTypeFields := make(map[string][]string)

	// Capture event type definitions
	parser.Callbacks.OnCMsgSource1LegacyGameEventList(func(m *dota.CMsgSource1LegacyGameEventList) error {
		for _, d := range m.GetDescriptors() {
			eventTypeNames[d.GetEventid()] = d.GetName()
			if config.CaptureTypes {
				result.EventTypes = append(result.EventTypes, d.GetName())
			}
			// Store field names for this event type
			fieldNames := make([]string, len(d.GetKeys()))
			for i, k := range d.GetKeys() {
				fieldNames[i] = k.GetName()
			}
			eventTypeFields[d.GetName()] = fieldNames
		}
		return nil
	})

	// Register handlers for specific events or all events
	if len(config.EventNames) > 0 {
		// Register handlers for specific event names
		for _, eventName := range config.EventNames {
			name := eventName // Capture for closure
			parser.OnGameEvent(name, func(e *manta.GameEvent) error {
				if config.MaxEvents > 0 && len(result.Events) >= config.MaxEvents {
					return nil
				}
				event := extractGameEventData(e, name, parser.Tick, parser.NetTick, eventTypeFields[name])
				result.Events = append(result.Events, event)
				return nil
			})
		}
	} else {
		// Use raw message handler to capture all game events
		parser.Callbacks.OnCMsgSource1LegacyGameEvent(func(m *dota.CMsgSource1LegacyGameEvent) error {
			if config.MaxEvents > 0 && len(result.Events) >= config.MaxEvents {
				return nil
			}

			eventName, ok := eventTypeNames[m.GetEventid()]
			if !ok {
				return nil
			}

			// Apply filter if specified
			if config.EventFilter != "" && !strings.Contains(eventName, config.EventFilter) {
				return nil
			}

			// Extract fields
			fields := make(map[string]interface{})
			fieldNames := eventTypeFields[eventName]
			keys := m.GetKeys()

			for i, key := range keys {
				fieldName := fmt.Sprintf("field_%d", i)
				if i < len(fieldNames) {
					fieldName = fieldNames[i]
				}

				switch key.GetType() {
				case 1: // string
					fields[fieldName] = key.GetValString()
				case 2: // float
					fields[fieldName] = key.GetValFloat()
				case 3: // long
					fields[fieldName] = key.GetValLong()
				case 4: // short
					fields[fieldName] = key.GetValShort()
				case 5: // byte
					fields[fieldName] = key.GetValByte()
				case 6: // bool
					fields[fieldName] = key.GetValBool()
				case 7: // uint64
					fields[fieldName] = key.GetValUint64()
				}
			}

			result.Events = append(result.Events, GameEventData{
				Name:    eventName,
				Tick:    parser.Tick,
				NetTick: parser.NetTick,
				Fields:  fields,
			})

			return nil
		})
	}

	if err := parser.Start(); err != nil {
		return nil, fmt.Errorf("error parsing file: %w", err)
	}

	result.Success = true
	result.TotalEvents = len(result.Events)
	return result, nil
}

// extractGameEventData extracts data from a GameEvent using typed accessors
func extractGameEventData(e *manta.GameEvent, name string, tick, netTick uint32, fieldNames []string) GameEventData {
	fields := make(map[string]interface{})

	// Try to extract each field by name
	for _, fieldName := range fieldNames {
		if val, err := e.GetString(fieldName); err == nil {
			fields[fieldName] = val
		} else if val, err := e.GetFloat32(fieldName); err == nil {
			fields[fieldName] = val
		} else if val, err := e.GetInt32(fieldName); err == nil {
			fields[fieldName] = val
		} else if val, err := e.GetBool(fieldName); err == nil {
			fields[fieldName] = val
		} else if val, err := e.GetUint64(fieldName); err == nil {
			fields[fieldName] = val
		}
	}

	return GameEventData{
		Name:    name,
		Tick:    tick,
		NetTick: netTick,
		Fields:  fields,
	}
}

func marshalGameEventsResult(result *GameEventsResult) *C.char {
	jsonResult, err := json.Marshal(result)
	if err != nil {
		errorResult := &GameEventsResult{
			Success: false,
			Error:   fmt.Sprintf("Error marshaling result: %v", err),
		}
		jsonResult, _ = json.Marshal(errorResult)
	}
	return C.CString(string(jsonResult))
}

// ============================================================================
// MODIFIER/BUFF TRACKING
// ============================================================================

// ModifierEntry represents a buff/debuff entry
type ModifierEntry struct {
	Tick          uint32  `json:"tick"`
	NetTick       uint32  `json:"net_tick"`
	Parent        uint32  `json:"parent"`         // Entity handle of unit with modifier
	Caster        uint32  `json:"caster"`         // Entity handle of caster
	Ability       uint32  `json:"ability"`        // Ability that created modifier
	ModifierClass int32   `json:"modifier_class"` // Modifier class ID
	SerialNum     int32   `json:"serial_num"`     // Serial number
	Index         int32   `json:"index"`          // Modifier index
	CreationTime  float32 `json:"creation_time"`  // When modifier was created
	Duration      float32 `json:"duration"`       // Modifier duration (-1 = permanent)
	StackCount    int32   `json:"stack_count"`    // Number of stacks
	IsAura        bool    `json:"is_aura"`        // Whether it's an aura
	IsDebuff      bool    `json:"is_debuff"`      // Whether it's a debuff
}

// ModifiersResult holds modifier parsing results
type ModifiersResult struct {
	Modifiers     []ModifierEntry `json:"modifiers"`
	Success       bool            `json:"success"`
	Error         string          `json:"error,omitempty"`
	TotalModifiers int            `json:"total_modifiers"`
}

// ModifiersConfig controls modifier parsing
type ModifiersConfig struct {
	MaxModifiers int  `json:"max_modifiers"` // Max modifiers to capture (0 = unlimited)
	DebuffsOnly  bool `json:"debuffs_only"`  // Only capture debuffs
	AurasOnly    bool `json:"auras_only"`    // Only capture auras
}

//export ParseModifiers
func ParseModifiers(filePath *C.char, configJSON *C.char) *C.char {
	goFilePath := C.GoString(filePath)
	goConfigJSON := C.GoString(configJSON)

	config := ModifiersConfig{
		MaxModifiers: 0,
	}
	if goConfigJSON != "" {
		json.Unmarshal([]byte(goConfigJSON), &config)
	}

	result, err := RunModifiersParse(goFilePath, config)
	if err != nil {
		failure := &ModifiersResult{
			Modifiers: make([]ModifierEntry, 0),
			Success:   false,
			Error:     err.Error(),
		}
		return marshalModifiersResult(failure)
	}

	return marshalModifiersResult(result)
}

// RunModifiersParse executes modifier parsing
func RunModifiersParse(filePath string, config ModifiersConfig) (*ModifiersResult, error) {
	result := &ModifiersResult{
		Modifiers: make([]ModifierEntry, 0),
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

	// Register modifier handler
	parser.OnModifierTableEntry(func(m *dota.CDOTAModifierBuffTableEntry) error {
		if config.MaxModifiers > 0 && len(result.Modifiers) >= config.MaxModifiers {
			return nil
		}

		isAura := m.GetAura()

		// Apply filters
		if config.AurasOnly && !isAura {
			return nil
		}
		// Note: isDebuff not directly available in protobuf, skip debuffs_only filter

		entry := ModifierEntry{
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
			IsDebuff:      false, // Not directly available
		}

		result.Modifiers = append(result.Modifiers, entry)
		return nil
	})

	if err := parser.Start(); err != nil {
		return nil, fmt.Errorf("error parsing file: %w", err)
	}

	result.Success = true
	result.TotalModifiers = len(result.Modifiers)
	return result, nil
}

func marshalModifiersResult(result *ModifiersResult) *C.char {
	jsonResult, err := json.Marshal(result)
	if err != nil {
		errorResult := &ModifiersResult{
			Success: false,
			Error:   fmt.Sprintf("Error marshaling result: %v", err),
		}
		jsonResult, _ = json.Marshal(errorResult)
	}
	return C.CString(string(jsonResult))
}

// ============================================================================
// FULL ENTITY QUERY API
// ============================================================================

// EntityData represents an entity's full state
type EntityData struct {
	Index      int32                  `json:"index"`
	Serial     int32                  `json:"serial"`
	ClassName  string                 `json:"class_name"`
	Properties map[string]interface{} `json:"properties"`
}

// EntitiesResult holds entity query results
type EntitiesResult struct {
	Entities      []EntityData `json:"entities"`
	Success       bool         `json:"success"`
	Error         string       `json:"error,omitempty"`
	TotalEntities int          `json:"total_entities"`
	Tick          uint32       `json:"tick"`
	NetTick       uint32       `json:"net_tick"`
}

// EntitiesConfig controls entity querying
type EntitiesConfig struct {
	ClassFilter    string   `json:"class_filter"`     // Filter by class name (substring)
	ClassNames     []string `json:"class_names"`      // Specific class names to capture
	PropertyFilter []string `json:"property_filter"`  // Only include these properties (empty = all)
	AtTick         uint32   `json:"at_tick"`          // Capture entities at this tick (0 = end of file)
	MaxEntities    int      `json:"max_entities"`     // Max entities to return (0 = unlimited)
}

//export QueryEntities
func QueryEntities(filePath *C.char, configJSON *C.char) *C.char {
	goFilePath := C.GoString(filePath)
	goConfigJSON := C.GoString(configJSON)

	config := EntitiesConfig{
		AtTick:      0,
		MaxEntities: 0,
	}
	if goConfigJSON != "" {
		json.Unmarshal([]byte(goConfigJSON), &config)
	}

	result, err := RunEntitiesQuery(goFilePath, config)
	if err != nil {
		failure := &EntitiesResult{
			Entities: make([]EntityData, 0),
			Success:  false,
			Error:    err.Error(),
		}
		return marshalEntitiesResult(failure)
	}

	return marshalEntitiesResult(result)
}

// RunEntitiesQuery executes entity querying
func RunEntitiesQuery(filePath string, config EntitiesConfig) (*EntitiesResult, error) {
	result := &EntitiesResult{
		Entities: make([]EntityData, 0),
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

	captured := false

	// If targeting a specific tick, wait for it
	if config.AtTick > 0 {
		parser.OnEntity(func(e *manta.Entity, op manta.EntityOp) error {
			if captured {
				return nil
			}

			if parser.Tick >= config.AtTick {
				captureAllEntities(parser, config, result)
				captured = true
				parser.Stop()
			}
			return nil
		})
	}

	if err := parser.Start(); err != nil && !captured {
		return nil, fmt.Errorf("error parsing file: %w", err)
	}

	// If no specific tick, capture at end of parsing
	if !captured {
		captureAllEntities(parser, config, result)
	}

	result.Success = true
	result.TotalEntities = len(result.Entities)
	result.Tick = parser.Tick
	result.NetTick = parser.NetTick
	return result, nil
}

// captureAllEntities captures entities matching the config filters
func captureAllEntities(parser *manta.Parser, config EntitiesConfig, result *EntitiesResult) {
	// Build filter function
	filter := func(e *manta.Entity) bool {
		if e == nil {
			return false
		}
		className := e.GetClassName()

		// Check class filter
		if config.ClassFilter != "" && !strings.Contains(className, config.ClassFilter) {
			return false
		}

		// Check specific class names
		if len(config.ClassNames) > 0 {
			found := false
			for _, cn := range config.ClassNames {
				if strings.Contains(className, cn) {
					found = true
					break
				}
			}
			if !found {
				return false
			}
		}

		return true
	}

	entities := parser.FilterEntity(filter)

	for _, e := range entities {
		if e == nil {
			continue
		}

		if config.MaxEntities > 0 && len(result.Entities) >= config.MaxEntities {
			break
		}

		// Get properties
		allProps := e.Map()
		props := make(map[string]interface{})

		if len(config.PropertyFilter) > 0 {
			// Only include specified properties
			for _, propName := range config.PropertyFilter {
				if val, ok := allProps[propName]; ok {
					props[propName] = val
				}
			}
		} else {
			props = allProps
		}

		result.Entities = append(result.Entities, EntityData{
			Index:      e.GetIndex(),
			Serial:     e.GetSerial(),
			ClassName:  e.GetClassName(),
			Properties: props,
		})
	}
}

func marshalEntitiesResult(result *EntitiesResult) *C.char {
	jsonResult, err := json.Marshal(result)
	if err != nil {
		errorResult := &EntitiesResult{
			Success: false,
			Error:   fmt.Sprintf("Error marshaling result: %v", err),
		}
		jsonResult, _ = json.Marshal(errorResult)
	}
	return C.CString(string(jsonResult))
}

// ============================================================================
// STRING TABLE ACCESS
// ============================================================================

// StringTableData represents a string table entry
type StringTableData struct {
	TableName string `json:"table_name"`
	Index     int32  `json:"index"`
	Key       string `json:"key"`
	Value     string `json:"value,omitempty"` // Base64 encoded if binary
}

// StringTablesResult holds string table lookup results
type StringTablesResult struct {
	Tables       map[string][]StringTableData `json:"tables"`
	TableNames   []string                     `json:"table_names"`
	Success      bool                         `json:"success"`
	Error        string                       `json:"error,omitempty"`
	TotalEntries int                          `json:"total_entries"`
}

// StringTablesConfig controls string table extraction
type StringTablesConfig struct {
	TableNames    []string `json:"table_names"`    // Tables to extract (empty = all)
	IncludeValues bool     `json:"include_values"` // Include value data (can be large)
	MaxEntries    int      `json:"max_entries"`    // Max entries per table (0 = unlimited)
}

//export GetStringTables
func GetStringTables(filePath *C.char, configJSON *C.char) *C.char {
	goFilePath := C.GoString(filePath)
	goConfigJSON := C.GoString(configJSON)

	config := StringTablesConfig{
		IncludeValues: false,
		MaxEntries:    100,
	}
	if goConfigJSON != "" {
		json.Unmarshal([]byte(goConfigJSON), &config)
	}

	result, err := RunStringTablesExtract(goFilePath, config)
	if err != nil {
		failure := &StringTablesResult{
			Tables:  make(map[string][]StringTableData),
			Success: false,
			Error:   err.Error(),
		}
		return marshalStringTablesResult(failure)
	}

	return marshalStringTablesResult(result)
}

// RunStringTablesExtract extracts string table data
func RunStringTablesExtract(filePath string, config StringTablesConfig) (*StringTablesResult, error) {
	result := &StringTablesResult{
		Tables:     make(map[string][]StringTableData),
		TableNames: make([]string, 0),
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

	// Capture string table creation
	parser.Callbacks.OnCSVCMsg_CreateStringTable(func(m *dota.CSVCMsg_CreateStringTable) error {
		tableName := m.GetName()

		// Check if we should capture this table
		if len(config.TableNames) > 0 {
			found := false
			for _, tn := range config.TableNames {
				if tn == tableName {
					found = true
					break
				}
			}
			if !found {
				return nil
			}
		}

		result.TableNames = append(result.TableNames, tableName)
		result.Tables[tableName] = make([]StringTableData, 0)

		return nil
	})

	// Capture string table entries from demo string tables
	parser.Callbacks.OnCDemoStringTables(func(m *dota.CDemoStringTables) error {
		for _, table := range m.GetTables() {
			tableName := table.GetTableName()

			// Check if we should capture this table
			if len(config.TableNames) > 0 {
				found := false
				for _, tn := range config.TableNames {
					if tn == tableName {
						found = true
						break
					}
				}
				if !found {
					continue
				}
			}

			if result.Tables[tableName] == nil {
				result.Tables[tableName] = make([]StringTableData, 0)
				result.TableNames = append(result.TableNames, tableName)
			}

			for i, item := range table.GetItems() {
				if config.MaxEntries > 0 && i >= config.MaxEntries {
					break
				}

				entry := StringTableData{
					TableName: tableName,
					Index:     int32(i),
					Key:       item.GetStr(),
				}

				result.Tables[tableName] = append(result.Tables[tableName], entry)
				result.TotalEntries++
			}
		}
		return nil
	})

	if err := parser.Start(); err != nil {
		return nil, fmt.Errorf("error parsing file: %w", err)
	}

	result.Success = true
	return result, nil
}

func marshalStringTablesResult(result *StringTablesResult) *C.char {
	jsonResult, err := json.Marshal(result)
	if err != nil {
		errorResult := &StringTablesResult{
			Success: false,
			Error:   fmt.Sprintf("Error marshaling result: %v", err),
		}
		jsonResult, _ = json.Marshal(errorResult)
	}
	return C.CString(string(jsonResult))
}

// ============================================================================
// COMBAT LOG PARSING (Structured)
// ============================================================================

// CombatLogEntry represents a structured combat log entry
type CombatLogEntry struct {
	Tick           uint32  `json:"tick"`
	NetTick        uint32  `json:"net_tick"`
	Type           int32   `json:"type"`
	TypeName       string  `json:"type_name"`
	TargetName     string  `json:"target_name"`
	TargetSourceName string `json:"target_source_name"`
	AttackerName   string  `json:"attacker_name"`
	DamageSourceName string `json:"damage_source_name"`
	InflictorName  string  `json:"inflictor_name"`
	IsAttackerIllusion bool `json:"is_attacker_illusion"`
	IsAttackerHero bool    `json:"is_attacker_hero"`
	IsTargetIllusion bool  `json:"is_target_illusion"`
	IsTargetHero   bool    `json:"is_target_hero"`
	IsVisibleRadiant bool  `json:"is_visible_radiant"`
	IsVisibleDire  bool    `json:"is_visible_dire"`
	Value          int32   `json:"value"`
	Health         int32   `json:"health"`
	Timestamp      float32 `json:"timestamp"`
	StunDuration   float32 `json:"stun_duration"`
	SlowDuration   float32 `json:"slow_duration"`
	IsAbilityToggleOn bool `json:"is_ability_toggle_on"`
	IsAbilityToggleOff bool `json:"is_ability_toggle_off"`
	AbilityLevel   int32   `json:"ability_level"`
	XP             int32   `json:"xp"`
	Gold           int32   `json:"gold"`
	LastHits       int32   `json:"last_hits"`
	AttackerTeam   int32   `json:"attacker_team"`
	TargetTeam     int32   `json:"target_team"`
}

// CombatLogResult holds combat log parsing results
type CombatLogResult struct {
	Entries      []CombatLogEntry `json:"entries"`
	Success      bool             `json:"success"`
	Error        string           `json:"error,omitempty"`
	TotalEntries int              `json:"total_entries"`
}

// CombatLogConfig controls combat log parsing
type CombatLogConfig struct {
	Types      []int32 `json:"types"`       // Filter by combat log type (empty = all)
	MaxEntries int     `json:"max_entries"` // Max entries (0 = unlimited)
	HeroesOnly bool    `json:"heroes_only"` // Only hero-related entries
}

//export ParseCombatLog
func ParseCombatLog(filePath *C.char, configJSON *C.char) *C.char {
	goFilePath := C.GoString(filePath)
	goConfigJSON := C.GoString(configJSON)

	config := CombatLogConfig{
		MaxEntries: 0,
	}
	if goConfigJSON != "" {
		json.Unmarshal([]byte(goConfigJSON), &config)
	}

	result, err := RunCombatLogParse(goFilePath, config)
	if err != nil {
		failure := &CombatLogResult{
			Entries: make([]CombatLogEntry, 0),
			Success: false,
			Error:   err.Error(),
		}
		return marshalCombatLogResult(failure)
	}

	return marshalCombatLogResult(result)
}

// RunCombatLogParse executes combat log parsing
func RunCombatLogParse(filePath string, config CombatLogConfig) (*CombatLogResult, error) {
	result := &CombatLogResult{
		Entries: make([]CombatLogEntry, 0),
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

	// Build name lookup from string tables
	stringLookup := make(map[int32]string)

	parser.Callbacks.OnCDemoStringTables(func(m *dota.CDemoStringTables) error {
		for _, table := range m.GetTables() {
			if table.GetTableName() == "CombatLogNames" {
				for i, item := range table.GetItems() {
					stringLookup[int32(i)] = item.GetStr()
				}
			}
		}
		return nil
	})

	// Parse combat log entries
	parser.Callbacks.OnCMsgDOTACombatLogEntry(func(m *dota.CMsgDOTACombatLogEntry) error {
		if config.MaxEntries > 0 && len(result.Entries) >= config.MaxEntries {
			return nil
		}

		entryType := m.GetType()

		// Apply type filter
		if len(config.Types) > 0 {
			found := false
			for _, t := range config.Types {
				if t == int32(entryType) {
					found = true
					break
				}
			}
			if !found {
				return nil
			}
		}

		// Apply heroes only filter
		if config.HeroesOnly {
			if !m.GetIsAttackerHero() && !m.GetIsTargetHero() {
				return nil
			}
		}

		// Look up names
		getName := func(idx uint32) string {
			if name, ok := stringLookup[int32(idx)]; ok {
				return name
			}
			return fmt.Sprintf("unknown_%d", idx)
		}

		entry := CombatLogEntry{
			Tick:              parser.Tick,
			NetTick:          parser.NetTick,
			Type:             int32(entryType),
			TypeName:         dota.DOTA_COMBATLOG_TYPES_name[int32(entryType)],
			TargetName:       getName(m.GetTargetName()),
			TargetSourceName: getName(m.GetTargetSourceName()),
			AttackerName:     getName(m.GetAttackerName()),
			DamageSourceName: getName(m.GetDamageSourceName()),
			InflictorName:    getName(m.GetInflictorName()),
			IsAttackerIllusion: m.GetIsAttackerIllusion(),
			IsAttackerHero:   m.GetIsAttackerHero(),
			IsTargetIllusion: m.GetIsTargetIllusion(),
			IsTargetHero:     m.GetIsTargetHero(),
			IsVisibleRadiant: m.GetIsVisibleRadiant(),
			IsVisibleDire:    m.GetIsVisibleDire(),
			Value:            int32(m.GetValue()),
			Health:           m.GetHealth(),
			Timestamp:        m.GetTimestamp(),
			StunDuration:     m.GetStunDuration(),
			SlowDuration:     m.GetSlowDuration(),
			IsAbilityToggleOn: m.GetIsAbilityToggleOn(),
			IsAbilityToggleOff: m.GetIsAbilityToggleOff(),
			AbilityLevel:     int32(m.GetAbilityLevel()),
			XP:               int32(m.GetXpReason()),       // XP reason available
			Gold:             int32(m.GetGoldReason()),     // Gold reason available
			LastHits:         int32(m.GetLastHits()),
			AttackerTeam:     int32(m.GetAttackerTeam()),
			TargetTeam:       int32(m.GetTargetTeam()),
		}

		result.Entries = append(result.Entries, entry)
		return nil
	})

	if err := parser.Start(); err != nil {
		return nil, fmt.Errorf("error parsing file: %w", err)
	}

	result.Success = true
	result.TotalEntries = len(result.Entries)
	return result, nil
}

func marshalCombatLogResult(result *CombatLogResult) *C.char {
	jsonResult, err := json.Marshal(result)
	if err != nil {
		errorResult := &CombatLogResult{
			Success: false,
			Error:   fmt.Sprintf("Error marshaling result: %v", err),
		}
		jsonResult, _ = json.Marshal(errorResult)
	}
	return C.CString(string(jsonResult))
}

// ============================================================================
// PARSER INFO (State Access)
// ============================================================================

// ParserInfo holds parser state information
type ParserInfo struct {
	GameBuild      int32    `json:"game_build"`
	Tick           uint32   `json:"tick"`
	NetTick        uint32   `json:"net_tick"`
	StringTables   []string `json:"string_tables"`
	EntityCount    int      `json:"entity_count"`
	Success        bool     `json:"success"`
	Error          string   `json:"error,omitempty"`
}

//export GetParserInfo
func GetParserInfo(filePath *C.char) *C.char {
	goFilePath := C.GoString(filePath)

	result, err := RunGetParserInfo(goFilePath)
	if err != nil {
		failure := &ParserInfo{
			Success: false,
			Error:   err.Error(),
		}
		return marshalParserInfo(failure)
	}

	return marshalParserInfo(result)
}

// RunGetParserInfo extracts parser state info
func RunGetParserInfo(filePath string) (*ParserInfo, error) {
	result := &ParserInfo{
		StringTables: make([]string, 0),
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

	// Capture string table names
	parser.Callbacks.OnCSVCMsg_CreateStringTable(func(m *dota.CSVCMsg_CreateStringTable) error {
		result.StringTables = append(result.StringTables, m.GetName())
		return nil
	})

	// Capture game build from server info
	parser.Callbacks.OnCSVCMsg_ServerInfo(func(m *dota.CSVCMsg_ServerInfo) error {
		result.GameBuild = m.GetProtocol() // Use protocol as closest available
		return nil
	})

	if err := parser.Start(); err != nil {
		return nil, fmt.Errorf("error parsing file: %w", err)
	}

	result.Tick = parser.Tick
	result.NetTick = parser.NetTick

	// Count entities
	entities := parser.FilterEntity(func(e *manta.Entity) bool {
		return e != nil
	})
	result.EntityCount = len(entities)

	result.Success = true
	return result, nil
}

func marshalParserInfo(result *ParserInfo) *C.char {
	jsonResult, err := json.Marshal(result)
	if err != nil {
		errorResult := &ParserInfo{
			Success: false,
			Error:   fmt.Sprintf("Error marshaling result: %v", err),
		}
		jsonResult, _ = json.Marshal(errorResult)
	}
	return C.CString(string(jsonResult))
}
