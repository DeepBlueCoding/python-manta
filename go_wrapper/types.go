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

// ItemSnapshot captures an item's state in inventory
type ItemSnapshot struct {
	Slot        int     `json:"slot"`         // Inventory slot (0-5: main, 6-8: backpack, 9: TP, 10-15: stash, 16: neutral)
	Name        string  `json:"name"`         // Item class name (e.g., "item_blink", "item_power_treads")
	Charges     int     `json:"charges"`      // Current charges (for items like Magic Stick, Bottle)
	Cooldown    float32 `json:"cooldown"`     // Remaining cooldown
	MaxCooldown float32 `json:"max_cooldown"` // Max cooldown duration
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

	// Inventory (slots 0-5: main, 6-8: backpack, 9: TP, 10-15: stash, 16: neutral)
	Inventory []ItemSnapshot `json:"inventory,omitempty"`

	// Clone/illusion flags
	IsClone    bool `json:"is_clone,omitempty"`
	IsIllusion bool `json:"is_illusion,omitempty"`
}

// AttacksConfig controls attack event parsing
type AttacksConfig struct {
	MaxEvents int `json:"max_events"` // Max events (0 = unlimited)
}

// AttackEvent represents a single attack (ranged projectile or melee)
type AttackEvent struct {
	Tick            int     `json:"tick"`
	SourceIndex     int     `json:"source_index"`      // Entity index of attacker (0 for melee without entity)
	TargetIndex     int     `json:"target_index"`      // Entity index of target (0 for melee without entity)
	SourceHandle    int64   `json:"source_handle"`     // Raw entity handle (0 for melee)
	TargetHandle    int64   `json:"target_handle"`     // Raw entity handle (0 for melee)
	ProjectileSpeed int     `json:"projectile_speed"`  // Projectile move speed (0 for melee)
	Dodgeable       bool    `json:"dodgeable"`         // Can be dodged/disjointed
	LaunchTick      int     `json:"launch_tick"`       // When projectile was launched
	GameTime        float32 `json:"game_time"`         // Game time in seconds
	GameTimeStr     string  `json:"game_time_str"`     // Formatted game time
	// Common fields (populated for both ranged and melee)
	IsMelee      bool    `json:"is_melee"`       // True if melee attack (from combat log)
	AttackerName string  `json:"attacker_name"`  // Attacker name
	TargetName   string  `json:"target_name"`    // Target name
	LocationX    float32 `json:"location_x"`     // Attack location X
	LocationY    float32 `json:"location_y"`     // Attack location Y
	// Melee attack fields (from combat log DAMAGE events)
	Damage             int   `json:"damage"`               // Damage dealt (melee only, 0 for ranged)
	TargetHealth       int   `json:"target_health"`        // Target health AFTER attack (melee only)
	AttackerTeam       int   `json:"attacker_team"`        // Attacker team: 2=Radiant, 3=Dire (melee only)
	TargetTeam         int   `json:"target_team"`          // Target team: 2=Radiant, 3=Dire (melee only)
	IsAttackerHero     bool  `json:"is_attacker_hero"`     // Attacker is a hero (melee only)
	IsTargetHero       bool  `json:"is_target_hero"`       // Target is a hero (melee only)
	IsAttackerIllusion bool  `json:"is_attacker_illusion"` // Attacker is an illusion (melee only)
	IsTargetIllusion   bool  `json:"is_target_illusion"`   // Target is an illusion (melee only)
	IsTargetBuilding   bool  `json:"is_target_building"`   // Target is a building (melee only)
	DamageType         int   `json:"damage_type"`          // 1=physical, 2=magical, 4=pure (melee only)
}

// AttacksResult contains all attack events
type AttacksResult struct {
	Events      []AttackEvent `json:"events"`
	TotalEvents int           `json:"total_events"`
	Success     bool          `json:"success"`
	Error       string        `json:"error,omitempty"`
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
