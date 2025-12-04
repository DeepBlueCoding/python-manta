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
