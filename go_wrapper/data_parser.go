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
func ParseGameEvents(filePath *C.char, configJSON *C.char) (cResult *C.char) {
	goFilePath := C.GoString(filePath)
	goConfigJSON := C.GoString(configJSON)

	// Recover from any panics in manta library
	defer func() {
		if r := recover(); r != nil {
			failure := &GameEventsResult{
				Events:  make([]GameEventData, 0),
				Success: false,
				Error:   fmt.Sprintf("panic during parsing: %v", r),
			}
			cResult = marshalGameEventsResult(failure)
		}
	}()

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
func ParseModifiers(filePath *C.char, configJSON *C.char) (cResult *C.char) {
	goFilePath := C.GoString(filePath)
	goConfigJSON := C.GoString(configJSON)

	// Recover from any panics in manta library
	defer func() {
		if r := recover(); r != nil {
			failure := &ModifiersResult{
				Modifiers: make([]ModifierEntry, 0),
				Success:   false,
				Error:     fmt.Sprintf("panic during parsing: %v", r),
			}
			cResult = marshalModifiersResult(failure)
		}
	}()

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
func QueryEntities(filePath *C.char, configJSON *C.char) (cResult *C.char) {
	goFilePath := C.GoString(filePath)
	goConfigJSON := C.GoString(configJSON)

	// Recover from any panics in manta library
	defer func() {
		if r := recover(); r != nil {
			failure := &EntitiesResult{
				Entities: make([]EntityData, 0),
				Success:  false,
				Error:    fmt.Sprintf("panic during parsing: %v", r),
			}
			cResult = marshalEntitiesResult(failure)
		}
	}()

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
func GetStringTables(filePath *C.char, configJSON *C.char) (cResult *C.char) {
	goFilePath := C.GoString(filePath)
	goConfigJSON := C.GoString(configJSON)

	// Recover from any panics in manta library
	defer func() {
		if r := recover(); r != nil {
			failure := &StringTablesResult{
				Tables:  make(map[string][]StringTableData),
				Success: false,
				Error:   fmt.Sprintf("panic during parsing: %v", r),
			}
			cResult = marshalStringTablesResult(failure)
		}
	}()

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

// CombatLogEntry represents a structured combat log entry with ALL available fields
type CombatLogEntry struct {
	Tick               uint32  `json:"tick"`
	NetTick            uint32  `json:"net_tick"`
	Type               int32   `json:"type"`
	TypeName           string  `json:"type_name"`
	TargetName         string  `json:"target_name"`
	TargetSourceName   string  `json:"target_source_name"`
	AttackerName       string  `json:"attacker_name"`
	DamageSourceName   string  `json:"damage_source_name"`
	InflictorName      string  `json:"inflictor_name"`
	IsAttackerIllusion bool    `json:"is_attacker_illusion"`
	IsAttackerHero     bool    `json:"is_attacker_hero"`
	IsTargetIllusion   bool    `json:"is_target_illusion"`
	IsTargetHero       bool    `json:"is_target_hero"`
	IsVisibleRadiant   bool    `json:"is_visible_radiant"`
	IsVisibleDire      bool    `json:"is_visible_dire"`
	Value              int32   `json:"value"`
	ValueName          string  `json:"value_name"`
	Health             int32   `json:"health"`
	GameTime           float32 `json:"game_time"`
	StunDuration       float32 `json:"stun_duration"`
	SlowDuration       float32 `json:"slow_duration"`
	IsAbilityToggleOn  bool    `json:"is_ability_toggle_on"`
	IsAbilityToggleOff bool    `json:"is_ability_toggle_off"`
	AbilityLevel       int32   `json:"ability_level"`
	XP                 int32   `json:"xp"`
	Gold               int32   `json:"gold"`
	LastHits           int32   `json:"last_hits"`
	AttackerTeam       int32   `json:"attacker_team"`
	TargetTeam         int32   `json:"target_team"`
	// Location data
	LocationX float32 `json:"location_x"`
	LocationY float32 `json:"location_y"`
	// Assist tracking
	AssistPlayer0  int32   `json:"assist_player0"`
	AssistPlayer1  int32   `json:"assist_player1"`
	AssistPlayer2  int32   `json:"assist_player2"`
	AssistPlayer3  int32   `json:"assist_player3"`
	AssistPlayers  []int32 `json:"assist_players"`
	// Damage classification
	DamageType     int32 `json:"damage_type"`
	DamageCategory int32 `json:"damage_category"`
	// Additional combat info
	IsTargetBuilding     bool    `json:"is_target_building"`
	IsUltimateAbility    bool    `json:"is_ultimate_ability"`
	IsHealSave           bool    `json:"is_heal_save"`
	TargetIsSelf         bool    `json:"target_is_self"`
	ModifierDuration     float32 `json:"modifier_duration"`
	StackCount           int32   `json:"stack_count"`
	HiddenModifier       bool    `json:"hidden_modifier"`
	InvisibilityModifier bool    `json:"invisibility_modifier"`
	// Hero levels
	AttackerHeroLevel int32 `json:"attacker_hero_level"`
	TargetHeroLevel   int32 `json:"target_hero_level"`
	// Economy stats
	XPM           int32 `json:"xpm"`
	GPM           int32 `json:"gpm"`
	EventLocation int32 `json:"event_location"`
	Networth      int32 `json:"networth"`
	// Ward/rune/camp info
	ObsWardsPlaced  int32 `json:"obs_wards_placed"`
	NeutralCampType int32 `json:"neutral_camp_type"`
	NeutralCampTeam int32 `json:"neutral_camp_team"`
	RuneType        int32 `json:"rune_type"`
	// Building info
	BuildingType int32 `json:"building_type"`
	// Modifier details
	ModifierElapsedDuration float32 `json:"modifier_elapsed_duration"`
	SilenceModifier         bool    `json:"silence_modifier"`
	HealFromLifesteal       bool    `json:"heal_from_lifesteal"`
	ModifierPurged              bool    `json:"modifier_purged"`
	ModifierPurgeAbility        int32   `json:"modifier_purge_ability"`
	ModifierPurgeAbilityName    string  `json:"modifier_purge_ability_name"`
	ModifierPurgeNpc            int32   `json:"modifier_purge_npc"`
	ModifierPurgeNpcName        string  `json:"modifier_purge_npc_name"`
	RootModifier                bool    `json:"root_modifier"`
	AuraModifier                bool    `json:"aura_modifier"`
	ArmorDebuffModifier         bool    `json:"armor_debuff_modifier"`
	NoPhysicalDamageModifier    bool    `json:"no_physical_damage_modifier"`
	ModifierAbility             int32   `json:"modifier_ability"`
	ModifierAbilityName         string  `json:"modifier_ability_name"`
	ModifierHidden              bool    `json:"modifier_hidden"`
	MotionControllerModifier bool   `json:"motion_controller_modifier"`
	// Kill/death info
	SpellEvaded         bool  `json:"spell_evaded"`
	LongRangeKill       bool  `json:"long_range_kill"`
	TotalUnitDeathCount int32 `json:"total_unit_death_count"`
	WillReincarnate     bool  `json:"will_reincarnate"`
	// Ability info
	InflictorIsStolenAbility bool  `json:"inflictor_is_stolen_ability"`
	SpellGeneratedAttack     bool  `json:"spell_generated_attack"`
	UsesCharges              bool  `json:"uses_charges"`
	// Game state
	AtNightTime        bool    `json:"at_night_time"`
	AttackerHasScepter bool    `json:"attacker_has_scepter"`
	RegeneratedHealth  float32 `json:"regenerated_health"`
	// Tracking/events
	KillEaterEvent  int32 `json:"kill_eater_event"`
	UnitStatusLabel int32 `json:"unit_status_label"`
	TrackedStatId   int32 `json:"tracked_stat_id"`
}

// CombatLogResult holds combat log parsing results
type CombatLogResult struct {
	Entries       []CombatLogEntry `json:"entries"`
	Success       bool             `json:"success"`
	Error         string           `json:"error,omitempty"`
	TotalEntries  int              `json:"total_entries"`
	GameStartTime float32          `json:"game_start_time"` // Timestamp when game clock hits 00:00
	GameStartTick uint32           `json:"game_start_tick"` // Tick when horn sounds (game_time = 0)
}

// CombatLogConfig controls combat log parsing
type CombatLogConfig struct {
	Types      []int32 `json:"types"`       // Filter by combat log type (empty = all)
	MaxEntries int     `json:"max_entries"` // Max entries (0 = unlimited)
	HeroesOnly bool    `json:"heroes_only"` // Only hero-related entries
}

//export ParseCombatLog
func ParseCombatLog(filePath *C.char, configJSON *C.char) (cResult *C.char) {
	goFilePath := C.GoString(filePath)
	goConfigJSON := C.GoString(configJSON)

	// Recover from any panics in manta library
	defer func() {
		if r := recover(); r != nil {
			failure := &CombatLogResult{
				Entries: make([]CombatLogEntry, 0),
				Success: false,
				Error:   fmt.Sprintf("panic during parsing: %v", r),
			}
			cResult = marshalCombatLogResult(failure)
		}
	}()

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

	// Store raw combat log entries with indices for later name resolution
	type rawEntry struct {
		tick               uint32
		netTick            uint32
		msg                *dota.CMsgDOTACombatLogEntry
	}
	rawEntries := make([]rawEntry, 0)

	// Track game start time and tick (when GAME_IN_PROGRESS state begins)
	var gameStartTime float32 = 0
	var gameStartTick uint32 = 0

	// Parse combat log entries - store raw data
	parser.Callbacks.OnCMsgDOTACombatLogEntry(func(m *dota.CMsgDOTACombatLogEntry) error {
		// Detect game start: GAME_STATE event with value=5 (GAME_IN_PROGRESS)
		if m.GetType() == dota.DOTA_COMBATLOG_TYPES_DOTA_COMBATLOG_GAME_STATE {
			if m.GetValue() == 5 { // DOTA_GAMERULES_STATE_GAME_IN_PROGRESS
				gameStartTime = m.GetTimestamp()
				gameStartTick = parser.Tick
			}
		}

		if config.MaxEntries > 0 && len(rawEntries) >= config.MaxEntries {
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

		// NOTE: heroes_only filter is applied after name resolution
		// This allows checking both boolean flags AND name strings for hero detection

		// Store raw entry for later processing
		rawEntries = append(rawEntries, rawEntry{
			tick:    parser.Tick,
			netTick: parser.NetTick,
			msg:     m,
		})

		return nil
	})

	// Parse the file first to populate string tables
	if err := parser.Start(); err != nil {
		return nil, fmt.Errorf("error parsing file: %w", err)
	}

	// Now resolve names using fully populated string tables
	getName := func(idx uint32) string {
		if name, ok := parser.LookupStringByIndex("CombatLogNames", int32(idx)); ok {
			return name
		}
		return fmt.Sprintf("unknown_%d", idx)
	}

	// Convert raw entries to final entries with resolved names
	for _, raw := range rawEntries {
		m := raw.msg
		entryType := m.GetType()

		// Convert assist_players slice
		assistPlayers := make([]int32, len(m.GetAssistPlayers()))
		for i, ap := range m.GetAssistPlayers() {
			assistPlayers[i] = ap
		}

		// Resolve value name - for PURCHASE events, value is an index into CombatLogNames
		valueName := ""
		if name, ok := parser.LookupStringByIndex("CombatLogNames", int32(m.GetValue())); ok {
			valueName = name
		}

		// Resolve modifier-related name fields - these are also CombatLogNames indices
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
			Tick:               raw.tick,
			NetTick:            raw.netTick,
			Type:               int32(entryType),
			TypeName:           dota.DOTA_COMBATLOG_TYPES_name[int32(entryType)],
			TargetName:         getName(m.GetTargetName()),
			TargetSourceName:   getName(m.GetTargetSourceName()),
			AttackerName:       getName(m.GetAttackerName()),
			DamageSourceName:   getName(m.GetDamageSourceName()),
			InflictorName:      getName(m.GetInflictorName()),
			IsAttackerIllusion: m.GetIsAttackerIllusion(),
			IsAttackerHero:     m.GetIsAttackerHero(),
			IsTargetIllusion:   m.GetIsTargetIllusion(),
			IsTargetHero:       m.GetIsTargetHero(),
			IsVisibleRadiant:   m.GetIsVisibleRadiant(),
			IsVisibleDire:      m.GetIsVisibleDire(),
			Value:              int32(m.GetValue()),
			ValueName:          valueName,
			Health:             m.GetHealth(),
			GameTime:           TickToGameTime(raw.tick, gameStartTick),
			StunDuration:       m.GetStunDuration(),
			SlowDuration:       m.GetSlowDuration(),
			IsAbilityToggleOn:  m.GetIsAbilityToggleOn(),
			IsAbilityToggleOff: m.GetIsAbilityToggleOff(),
			AbilityLevel:       int32(m.GetAbilityLevel()),
			XP:                 int32(m.GetXpReason()),
			Gold:               int32(m.GetGoldReason()),
			LastHits:           int32(m.GetLastHits()),
			AttackerTeam:       int32(m.GetAttackerTeam()),
			TargetTeam:         int32(m.GetTargetTeam()),
			// Location data
			LocationX: m.GetLocationX(),
			LocationY: m.GetLocationY(),
			// Assist tracking
			AssistPlayer0: int32(m.GetAssistPlayer0()),
			AssistPlayer1: int32(m.GetAssistPlayer1()),
			AssistPlayer2: int32(m.GetAssistPlayer2()),
			AssistPlayer3: int32(m.GetAssistPlayer3()),
			AssistPlayers: assistPlayers,
			// Damage classification
			DamageType:     int32(m.GetDamageType()),
			DamageCategory: int32(m.GetDamageCategory()),
			// Additional combat info
			IsTargetBuilding:     m.GetIsTargetBuilding(),
			IsUltimateAbility:    m.GetIsUltimateAbility(),
			IsHealSave:           m.GetIsHealSave(),
			TargetIsSelf:         m.GetTargetIsSelf(),
			ModifierDuration:     m.GetModifierDuration(),
			StackCount:           int32(m.GetStackCount()),
			HiddenModifier:       m.GetHiddenModifier(),
			InvisibilityModifier: m.GetInvisibilityModifier(),
			// Hero levels
			AttackerHeroLevel: int32(m.GetAttackerHeroLevel()),
			TargetHeroLevel:   int32(m.GetTargetHeroLevel()),
			// Economy stats
			XPM:           int32(m.GetXpm()),
			GPM:           int32(m.GetGpm()),
			EventLocation: int32(m.GetEventLocation()),
			Networth:      int32(m.GetNetworth()),
			// Ward/rune/camp info
			ObsWardsPlaced:  int32(m.GetObsWardsPlaced()),
			NeutralCampType: int32(m.GetNeutralCampType()),
			NeutralCampTeam: int32(m.GetNeutralCampTeam()),
			RuneType:        int32(m.GetRuneType()),
			// Building info
			BuildingType: int32(m.GetBuildingType()),
			// Modifier details
			ModifierElapsedDuration:  m.GetModifierElapsedDuration(),
			SilenceModifier:          m.GetSilenceModifier(),
			HealFromLifesteal:        m.GetHealFromLifesteal(),
			ModifierPurged:              m.GetModifierPurged(),
			ModifierPurgeAbility:        int32(m.GetModifierPurgeAbility()),
			ModifierPurgeAbilityName:    modifierPurgeAbilityName,
			ModifierPurgeNpc:            int32(m.GetModifierPurgeNpc()),
			ModifierPurgeNpcName:        modifierPurgeNpcName,
			RootModifier:                m.GetRootModifier(),
			AuraModifier:                m.GetAuraModifier(),
			ArmorDebuffModifier:         m.GetArmorDebuffModifier(),
			NoPhysicalDamageModifier:    m.GetNoPhysicalDamageModifier(),
			ModifierAbility:             int32(m.GetModifierAbility()),
			ModifierAbilityName:         modifierAbilityName,
			ModifierHidden:              m.GetModifierHidden(),
			MotionControllerModifier: m.GetMotionControllerModifier(),
			// Kill/death info
			SpellEvaded:         m.GetSpellEvaded(),
			LongRangeKill:       m.GetLongRangeKill(),
			TotalUnitDeathCount: int32(m.GetTotalUnitDeathCount()),
			WillReincarnate:     m.GetWillReincarnate(),
			// Ability info
			InflictorIsStolenAbility: m.GetInflictorIsStolenAbility(),
			SpellGeneratedAttack:     m.GetSpellGeneratedAttack(),
			UsesCharges:              m.GetUsesCharges(),
			// Game state
			AtNightTime:        m.GetAtNightTime(),
			AttackerHasScepter: m.GetAttackerHasScepter(),
			RegeneratedHealth:  m.GetRegeneratedHealth(),
			// Tracking/events
			KillEaterEvent:  int32(m.GetKillEaterEvent()),
			UnitStatusLabel: int32(m.GetUnitStatusLabel()),
			TrackedStatId:   int32(m.GetTrackedStatId()),
		}

		// Apply heroes_only filter (checks both boolean flags AND name strings)
		if config.HeroesOnly {
			isHeroRelated := entry.IsAttackerHero || entry.IsTargetHero ||
				strings.Contains(entry.AttackerName, "npc_dota_hero_") ||
				strings.Contains(entry.TargetName, "npc_dota_hero_")
			if !isHeroRelated {
				continue
			}
		}

		result.Entries = append(result.Entries, entry)
	}

	result.Success = true
	result.TotalEntries = len(result.Entries)
	result.GameStartTime = gameStartTime
	result.GameStartTick = gameStartTick
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
func GetParserInfo(filePath *C.char) (cResult *C.char) {
	goFilePath := C.GoString(filePath)

	// Recover from any panics in manta library
	defer func() {
		if r := recover(); r != nil {
			failure := &ParserInfo{
				Success: false,
				Error:   fmt.Sprintf("panic during parsing: %v", r),
			}
			cResult = marshalParserInfo(failure)
		}
	}()

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

// ============================================================================
// ATTACKS PARSING (from TE_Projectile)
// ============================================================================

//export ParseAttacks
func ParseAttacks(filePath *C.char, configJSON *C.char) (cResult *C.char) {
	goFilePath := C.GoString(filePath)
	goConfigJSON := C.GoString(configJSON)

	// Recover from any panics in manta library
	defer func() {
		if r := recover(); r != nil {
			failure := &AttacksResult{
				Events:  make([]AttackEvent, 0),
				Success: false,
				Error:   fmt.Sprintf("panic during parsing: %v", r),
			}
			cResult = marshalAttacksResult(failure)
		}
	}()

	config := AttacksConfig{
		MaxEvents: 0,
	}
	if goConfigJSON != "" {
		json.Unmarshal([]byte(goConfigJSON), &config)
	}

	result, err := RunAttacksParse(goFilePath, config)
	if err != nil {
		failure := &AttacksResult{
			Events: make([]AttackEvent, 0),
		}
		return marshalAttacksResult(failure)
	}

	return marshalAttacksResult(result)
}

// RunAttacksParse executes attack event parsing from TE_Projectile
func RunAttacksParse(filePath string, config AttacksConfig) (*AttacksResult, error) {
	result := &AttacksResult{
		Events: make([]AttackEvent, 0),
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

	// Track game start tick for game time calculation
	var gameStartTick uint32 = 0

	// Detect game start from combat log
	parser.Callbacks.OnCMsgDOTACombatLogEntry(func(m *dota.CMsgDOTACombatLogEntry) error {
		if gameStartTick == 0 && m.GetType() == dota.DOTA_COMBATLOG_TYPES_DOTA_COMBATLOG_GAME_STATE {
			if m.GetValue() == 5 { // DOTA_GAMERULES_STATE_GAME_IN_PROGRESS
				gameStartTick = parser.Tick
			}
		}
		return nil
	})

	// Register TE_Projectile handler for attack events
	parser.Callbacks.OnCDOTAUserMsg_TE_Projectile(func(m *dota.CDOTAUserMsg_TE_Projectile) error {
		// Only capture attack projectiles
		if !m.GetIsAttack() {
			return nil
		}

		if config.MaxEvents > 0 && len(result.Events) >= config.MaxEvents {
			return nil
		}

		sourceHandle := int64(m.GetSource())
		targetHandle := int64(m.GetTarget())

		// Convert handles to entity indices (lower 14 bits)
		sourceIndex := int(sourceHandle & 0x3FFF)
		targetIndex := int(targetHandle & 0x3FFF)

		event := AttackEvent{
			Tick:            int(parser.Tick),
			SourceIndex:     sourceIndex,
			TargetIndex:     targetIndex,
			SourceHandle:    sourceHandle,
			TargetHandle:    targetHandle,
			ProjectileSpeed: int(m.GetMoveSpeed()),
			Dodgeable:       m.GetDodgeable(),
			LaunchTick:      int(m.GetLaunchTick()),
		}

		result.Events = append(result.Events, event)
		return nil
	})

	if err := parser.Start(); err != nil {
		return nil, fmt.Errorf("error parsing file: %w", err)
	}

	// Post-process: add game time to events
	for i := range result.Events {
		result.Events[i].GameTime = TickToGameTime(uint32(result.Events[i].Tick), gameStartTick)
		result.Events[i].GameTimeStr = FormatGameTime(result.Events[i].GameTime)
	}

	result.TotalEvents = len(result.Events)
	return result, nil
}

func marshalAttacksResult(result *AttacksResult) *C.char {
	jsonResult, err := json.Marshal(result)
	if err != nil {
		errorResult := &AttacksResult{
			Events: make([]AttackEvent, 0),
		}
		jsonResult, _ = json.Marshal(errorResult)
	}
	return C.CString(string(jsonResult))
}
