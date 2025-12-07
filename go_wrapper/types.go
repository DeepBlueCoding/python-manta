package main

// ParseConfig specifies which collectors to enable and their options.
// All fields are optional - omitted collectors won't run.
type ParseConfig struct {
	// Header collector
	Header *HeaderCollectorConfig `json:"header,omitempty"`

	// Game info collector (match info, players, draft)
	GameInfo *GameInfoCollectorConfig `json:"game_info,omitempty"`

	// Combat log collector
	CombatLog *CombatLogConfig `json:"combat_log,omitempty"`

	// Entity snapshot collector
	Entities *EntityParseConfig `json:"entities,omitempty"`

	// Game events collector
	GameEvents *GameEventsConfig `json:"game_events,omitempty"`

	// Modifiers collector
	Modifiers *ModifiersConfig `json:"modifiers,omitempty"`

	// String tables collector
	StringTables *StringTablesConfig `json:"string_tables,omitempty"`

	// Universal message collector
	Messages *UniversalConfig `json:"messages,omitempty"`

	// Parser info collector
	ParserInfo *ParserInfoConfig `json:"parser_info,omitempty"`
}

// HeaderCollectorConfig - header is simple, just enable/disable
type HeaderCollectorConfig struct {
	Enabled bool `json:"enabled"`
}

// GameInfoCollectorConfig - game info is simple, just enable/disable
type GameInfoCollectorConfig struct {
	Enabled bool `json:"enabled"`
}

// UniversalConfig controls universal message parsing
type UniversalConfig struct {
	Filter      string `json:"filter"`       // Message type filter (substring match)
	MaxMessages int    `json:"max_messages"` // Max messages (0 = unlimited)
}

// ParserInfoConfig - parser info is simple, just enable/disable
type ParserInfoConfig struct {
	Enabled bool `json:"enabled"`
}

// ParseResult contains all results from a single parse.
// Only populated fields will be non-nil.
type ParseResult struct {
	Success bool   `json:"success"`
	Error   string `json:"error,omitempty"`

	Header       *HeaderInfo         `json:"header,omitempty"`
	GameInfo     *CDotaGameInfo      `json:"game_info,omitempty"`
	CombatLog    *CombatLogResult    `json:"combat_log,omitempty"`
	Entities     *EntityParseResult  `json:"entities,omitempty"`
	GameEvents   *GameEventsResult   `json:"game_events,omitempty"`
	Modifiers    *ModifiersResult    `json:"modifiers,omitempty"`
	StringTables *StringTablesResult `json:"string_tables,omitempty"`
	Messages     *UniversalResult    `json:"messages,omitempty"`
	ParserInfo   *ParserInfo         `json:"parser_info,omitempty"`
}

// UniversalResult matches the existing universal parse result structure
type UniversalResult struct {
	Messages       []MessageEvent `json:"messages"`
	Success        bool           `json:"success"`
	Error          string         `json:"error,omitempty"`
	TotalMessages  int            `json:"total_messages"`
	FilteredCount  int            `json:"filtered_count"`
	CallbacksUsed  []string       `json:"callbacks_used"`
}

// AbilitySnapshot captures an ability's state (shared between entity_parser and index)
type AbilitySnapshot struct {
	Slot        int     `json:"slot"`
	Name        string  `json:"name"`
	Level       int     `json:"level"`
	Cooldown    float32 `json:"cooldown"`
	MaxCooldown float32 `json:"max_cooldown"`
	ManaCost    int     `json:"mana_cost"`
	Charges     int     `json:"charges"`
	IsUltimate  bool    `json:"is_ultimate"`
}

// TalentChoice captures a talent tier selection
type TalentChoice struct {
	Tier   int    `json:"tier"`
	Slot   int    `json:"slot"`
	IsLeft bool   `json:"is_left"`
	Name   string `json:"name"`
}

// HeroSnapshot captures a hero's complete state (shared between entity_parser and index)
type HeroSnapshot struct {
	// Identity
	Index    int    `json:"index"`
	PlayerID int    `json:"player_id"`
	HeroID   int    `json:"hero_id"`
	HeroName string `json:"hero_name"`
	Team     int    `json:"team"`

	// Position
	X float32 `json:"x"`
	Y float32 `json:"y"`
	Z float32 `json:"z"`

	// Vital stats
	Level     int     `json:"level"`
	Health    int     `json:"health"`
	MaxHealth int     `json:"max_health"`
	Mana      float32 `json:"mana"`
	MaxMana   float32 `json:"max_mana"`
	IsAlive   bool    `json:"is_alive"`

	// Economy (from CDOTA_PlayerResource / CDOTA_Data*)
	Gold     int `json:"gold"`
	NetWorth int `json:"net_worth"`
	LastHits int `json:"last_hits"`
	Denies   int `json:"denies"`
	XP       int `json:"xp"`

	// KDA
	Kills   int `json:"kills"`
	Deaths  int `json:"deaths"`
	Assists int `json:"assists"`

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

	// Abilities and talents
	Abilities     []AbilitySnapshot `json:"abilities,omitempty"`
	Talents       []TalentChoice    `json:"talents,omitempty"`
	AbilityPoints int               `json:"ability_points"`

	// Clone/illusion flags
	IsClone    bool `json:"is_clone,omitempty"`
	IsIllusion bool `json:"is_illusion,omitempty"`
}
