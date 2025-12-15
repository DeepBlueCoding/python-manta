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

	// Attacks collector (from TE_Projectile)
	Attacks *AttacksConfig `json:"attacks,omitempty"`

	// Entity deaths collector (tracks entity removals)
	EntityDeaths *EntityDeathsConfig `json:"entity_deaths,omitempty"`
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
	Attacks      *AttacksResult      `json:"attacks,omitempty"`
	EntityDeaths *EntityDeathsResult `json:"entity_deaths,omitempty"`
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
	EntityID int    `json:"entity_id"`
	Index    int    `json:"index"` // Deprecated: use entity_id instead
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
	Gold         int `json:"gold"`
	NetWorth     int `json:"net_worth"`
	LastHits     int `json:"last_hits"`
	Denies       int `json:"denies"`
	XP           int `json:"xp"`
	CampsStacked int `json:"camps_stacked"`

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

// AttacksConfig controls attack event parsing from TE_Projectile
type AttacksConfig struct {
	MaxEvents int `json:"max_events"` // Max events (0 = unlimited)
}

// AttackEvent represents a single attack projectile
type AttackEvent struct {
	Tick            int     `json:"tick"`
	SourceIndex     int     `json:"source_index"`      // Entity index of attacker
	TargetIndex     int     `json:"target_index"`      // Entity index of target
	SourceHandle    int64   `json:"source_handle"`     // Raw entity handle
	TargetHandle    int64   `json:"target_handle"`     // Raw entity handle
	ProjectileSpeed int     `json:"projectile_speed"`  // Projectile move speed
	Dodgeable       bool    `json:"dodgeable"`         // Can be dodged/disjointed
	LaunchTick      int     `json:"launch_tick"`       // When projectile was launched
	GameTime        float32 `json:"game_time"`         // Game time in seconds
	GameTimeStr     string  `json:"game_time_str"`     // Formatted game time
}

// AttacksResult contains all attack events from TE_Projectile
type AttacksResult struct {
	Events      []AttackEvent `json:"events"`
	TotalEvents int           `json:"total_events"`
}

// EntityDeathsConfig controls entity death tracking
type EntityDeathsConfig struct {
	MaxEvents     int  `json:"max_events"`      // Max events (0 = unlimited)
	HeroesOnly    bool `json:"heroes_only"`     // Only track hero deaths
	CreepsOnly    bool `json:"creeps_only"`     // Only track creep deaths
	IncludeCreeps bool `json:"include_creeps"`  // Include creeps (default false for performance)
}

// EntityDeath represents an entity being removed from the game
type EntityDeath struct {
	Tick        int     `json:"tick"`
	EntityID    int     `json:"entity_id"`
	ClassName   string  `json:"class_name"`
	Name        string  `json:"name"`          // e.g., "npc_dota_hero_juggernaut" or "npc_dota_creep_goodguys_melee"
	Team        int     `json:"team"`          // 2=Radiant, 3=Dire
	X           float32 `json:"x"`             // Last known position
	Y           float32 `json:"y"`
	Health      int     `json:"health"`        // Health at time of removal (usually 0)
	MaxHealth   int     `json:"max_health"`
	IsHero      bool    `json:"is_hero"`
	IsCreep     bool    `json:"is_creep"`
	IsBuilding  bool    `json:"is_building"`
	IsNeutral   bool    `json:"is_neutral"`    // Neutral creep
	GameTime    float32 `json:"game_time"`
	GameTimeStr string  `json:"game_time_str"`
}

// EntityDeathsResult contains all entity death events
type EntityDeathsResult struct {
	Events      []EntityDeath `json:"events"`
	TotalEvents int           `json:"total_events"`
}
