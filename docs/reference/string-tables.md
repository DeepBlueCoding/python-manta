
# String Tables Reference

??? info "AI Summary"
    Reference for string tables in Dota 2 replays. String tables store key-value mappings for names, abilities, items, models, and other game data. Use `get_string_tables()` to retrieve all tables or filter by name. Common tables include `userinfo` (player info), `ActiveModifiers` (buff names), `CombatLogNames` (unit names), and `EntityNames`.

---

## String Table Structure

Every `StringTableData` entry contains:

| Field | Type | Description |
|-------|------|-------------|
| `table_name` | `str` | Name of the table |
| `index` | `int` | Entry index in table |
| `key` | `str` | Entry key |
| `value` | `Optional[str]` | Entry value (may be binary/base64) |

---

## Basic Usage

```python
from python_manta import MantaParser

parser = MantaParser()
result = parser.get_string_tables("match.dem")

print(f"Tables found: {result.table_names}")
print(f"Total entries: {result.total_entries}")

for table_name, entries in result.tables.items():
    print(f"\n{table_name}: {len(entries)} entries")
    for entry in entries[:5]:  # First 5 entries
        print(f"  [{entry.index}] {entry.key}")
```

---

## Common Tables

### userinfo

Player information including Steam IDs and names.

```python
result = parser.get_string_tables("match.dem", table_filter="userinfo")

for entry in result.tables.get("userinfo", []):
    print(f"Player {entry.index}: {entry.key}")
```

### CombatLogNames

Names used in combat log entries (heroes, abilities, items).

```python
result = parser.get_string_tables("match.dem", table_filter="CombatLogNames")

for entry in result.tables.get("CombatLogNames", []):
    print(f"[{entry.index}] {entry.key}")
```

### ActiveModifiers

Active modifier/buff names in the game.

```python
result = parser.get_string_tables("match.dem", table_filter="ActiveModifiers")

for entry in result.tables.get("ActiveModifiers", []):
    print(f"Modifier: {entry.key}")
```

### EntityNames

Entity names used in the replay.

```python
result = parser.get_string_tables("match.dem", table_filter="EntityNames")

for entry in result.tables.get("EntityNames", []):
    print(f"Entity: {entry.key}")
```

---

## All Table Names

Common string tables found in Dota 2 replays:

| Table Name | Description |
|------------|-------------|
| `userinfo` | Player information |
| `server_query_info` | Server query data |
| `instancebaseline` | Entity baselines |
| `lightstyles` | Light styles |
| `CombatLogNames` | Names for combat log |
| `ActiveModifiers` | Active modifier names |
| `EntityNames` | Entity name mappings |
| `soundprecache` | Sound precache |
| `decalprecache` | Decal precache |
| `genericprecache` | Generic precache |

---

## Filtering

```python
# Get specific table
result = parser.get_string_tables("match.dem", table_filter="userinfo")

# Get multiple tables (run multiple calls)
tables_needed = ["userinfo", "CombatLogNames", "EntityNames"]
all_data = {}

for table in tables_needed:
    result = parser.get_string_tables("match.dem", table_filter=table)
    all_data[table] = result.tables.get(table, [])
```

---

## Binary Values

Some string table values contain binary data encoded as base64. These typically appear in:

- `instancebaseline` - Entity baseline data
- Some precache tables

```python
import base64

for entry in result.tables.get("somtable", []):
    if entry.value:
        try:
            decoded = base64.b64decode(entry.value)
            # Process binary data
        except:
            # Plain string value
            pass
```

---

## Use Cases

### Player Name Resolution

```python
# Get player names
result = parser.get_string_tables("match.dem", table_filter="userinfo")

player_names = {}
for entry in result.tables.get("userinfo", []):
    player_names[entry.index] = entry.key

# Use with other parsed data
for entity in entities:
    player_id = entity.properties.get("m_iPlayerID")
    if player_id in player_names:
        print(f"Hero owned by {player_names[player_id]}")
```

### Combat Log Name Resolution

```python
# Get name mappings
result = parser.get_string_tables("match.dem", table_filter="CombatLogNames")

name_lookup = {entry.index: entry.key for entry in result.tables.get("CombatLogNames", [])}

# Resolve combat log names
for log_entry in combat_log:
    attacker = name_lookup.get(log_entry.attacker_id, "Unknown")
    target = name_lookup.get(log_entry.target_id, "Unknown")
```

---

## Result Metadata

`StringTablesResult` includes:

| Field | Type | Description |
|-------|------|-------------|
| `tables` | `Dict[str, List[StringTableData]]` | Table name -> entries |
| `table_names` | `List[str]` | List of all table names |
| `total_entries` | `int` | Total entries across all tables |
| `success` | `bool` | Parse success flag |
| `error` | `Optional[str]` | Error message if failed |
