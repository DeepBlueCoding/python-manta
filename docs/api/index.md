
# API Reference

??? info "AI Summary"
    Complete API documentation for Python Manta. The main class is `MantaParser` which provides all parsing methods. Data is returned as Pydantic models (`HeaderInfo`, `CDotaGameInfo`, `GameEventsResult`, etc.) for type safety and easy serialization. Key methods: `parse_header()`, `parse_draft()`, `parse_universal()`, `parse_game_events()`, `parse_combat_log()`, `parse_modifiers()`, `query_entities()`, `get_string_tables()`, `get_parser_info()`.

---

## Overview

Python Manta provides a single main class and several data models:

### Main Class

| Class | Description |
|-------|-------------|
| [`MantaParser`](manta-parser) | Main parser class with all parsing methods |

### Data Models

| Model | Description |
|-------|-------------|
| [`HeaderInfo`](models#headerinfo) | Demo file header metadata |
| [`CDotaGameInfo`](models#cdotagameinfo) | Draft information |
| [`CHeroSelectEvent`](models#cheroselectevent) | Single pick/ban event |
| [`UniversalParseResult`](models#universalparseresult) | Universal parsing results |
| [`MessageEvent`](models#messageevent) | Single message from replay |
| [`GameEventsResult`](models#gameeventsresult) | Game events parsing results |
| [`GameEventData`](models#gameeventdata) | Single game event |
| [`ModifiersResult`](models#modifiersresult) | Modifier parsing results |
| [`ModifierEntry`](models#modifierentry) | Single modifier/buff entry |
| [`EntitiesResult`](models#entitiesresult) | Entity query results |
| [`EntityData`](models#entitydata) | Single entity data |
| [`CombatLogResult`](models#combatlogresult) | Combat log parsing results |
| [`CombatLogEntry`](models#combatlogentry) | Single combat log entry |
| [`StringTablesResult`](models#stringtablesresult) | String table results |
| [`ParserInfo`](models#parserinfo) | Parser state information |

### Convenience Functions

```python
from python_manta import (
    parse_demo_header,    # Quick header parsing
    parse_demo_draft,     # Quick draft parsing
    parse_demo_universal, # Quick message parsing
    parse_demo_entities,  # Quick entity parsing
)
```

---

## Quick Reference

```python
from python_manta import MantaParser

parser = MantaParser()

# Basic parsing
header = parser.parse_header("match.dem")
draft = parser.parse_draft("match.dem")
messages = parser.parse_universal("match.dem", "CDOTAUserMsg_ChatMessage", 100)

# Advanced parsing
events = parser.parse_game_events("match.dem", event_filter="dota", max_events=100)
combat = parser.parse_combat_log("match.dem", heroes_only=True, max_entries=500)
modifiers = parser.parse_modifiers("match.dem", max_modifiers=100)
entities = parser.query_entities("match.dem", class_filter="Hero", max_entities=10)
tables = parser.get_string_tables("match.dem", table_names=["userinfo"])
info = parser.get_parser_info("match.dem")
```
