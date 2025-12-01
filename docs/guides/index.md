
# Guides

??? info "AI Summary"
    In-depth guides for using Python Manta's features. Covers game events parsing (364 event types like kills, damage, abilities), combat log analysis (structured damage/heal/death data), entity queries (hero stats, positions, items), and modifier tracking (buffs, debuffs, auras). Each guide includes practical examples and common use cases.

---

## Available Guides

| Guide | Description |
|-------|-------------|
| [Game Events](game-events) | Parse 364 Source 1 game event types |
| [Combat Log](combat-log) | Analyze damage, heals, deaths, and kills |
| [Entity Queries](entities) | Query hero/unit state and properties |
| [Modifiers](modifiers) | Track buffs, debuffs, and auras |
| [Universal Messages](universal) | Parse any of 272 message callbacks |

---

## Choosing the Right API

| What You Need | API | Guide |
|---------------|-----|-------|
| Match metadata | `parse_header()` | [Getting Started](../getting-started) |
| Draft picks/bans | `parse_draft()` | [Getting Started](../getting-started) |
| Chat messages | `parse_universal("CDOTAUserMsg_ChatMessage")` | [Universal](universal) |
| Item purchases | `parse_universal("CDOTAUserMsg_ItemPurchased")` | [Universal](universal) |
| Map pings | `parse_universal("CDOTAUserMsg_LocationPing")` | [Universal](universal) |
| Damage dealt | `parse_combat_log(types=[0])` | [Combat Log](combat-log) |
| Deaths/kills | `parse_combat_log(types=[4])` | [Combat Log](combat-log) |
| Hero positions | `query_entities(class_filter="Hero")` | [Entities](entities) |
| Buff tracking | `parse_modifiers()` | [Modifiers](modifiers) |
| Kill events | `parse_game_events(event_filter="dota_player_kill")` | [Game Events](game-events) |
| Rune pickups | `parse_game_events(event_filter="dota_rune")` | [Game Events](game-events) |
| Player info | `get_string_tables(table_names=["userinfo"])` | [API Reference](../api/manta-parser#string-tables) |
