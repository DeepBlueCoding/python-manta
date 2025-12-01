
# Entities Reference

??? info "AI Summary"
    Reference for querying game entities from Dota 2 replays. Entities represent all game objects: heroes, creeps, buildings, items, abilities, and more. Use `query_entities()` to get entity data at a specific tick with optional class filtering. Each entity has an index, serial, class name, and property dictionary. Common properties include health, mana, position, level, gold, and KDA stats.

---

## Entity Data Fields

Every `EntityData` contains:

| Field | Type | Description |
|-------|------|-------------|
| `index` | `int` | Entity index (unique identifier) |
| `serial` | `int` | Entity serial number |
| `class_name` | `str` | Entity class name (e.g., `CDOTA_Unit_Hero_Axe`) |
| `properties` | `Dict[str, Any]` | Entity properties dictionary |

---

## Basic Usage

```python
from python_manta import MantaParser

parser = MantaParser()
result = parser.query_entities("match.dem", class_filter="Hero", max_entities=10)

for entity in result.entities:
    print(f"{entity.class_name} (index={entity.index})")
    print(f"  Health: {entity.properties.get('m_iHealth')}")
    print(f"  Level: {entity.properties.get('m_iCurrentLevel')}")
```

---

## Entity Classes

### Heroes

| Class Pattern | Description |
|---------------|-------------|
| `CDOTA_Unit_Hero_*` | Hero units |
| `CDOTA_Unit_Hero_Axe` | Axe specifically |
| `CDOTA_Unit_Hero_Invoker` | Invoker specifically |

### Creeps

| Class Pattern | Description |
|---------------|-------------|
| `CDOTA_BaseNPC_Creep_*` | Lane creeps |
| `CDOTA_BaseNPC_Creep_Neutral` | Neutral creeps |

### Buildings

| Class Pattern | Description |
|---------------|-------------|
| `CDOTA_BaseNPC_Tower` | Towers |
| `CDOTA_BaseNPC_Barracks` | Barracks |
| `CDOTA_BaseNPC_Building` | Ancient and other buildings |
| `CDOTA_BaseNPC_Fort` | Ancient (throne) |

### Other Units

| Class Pattern | Description |
|---------------|-------------|
| `CDOTA_BaseNPC_Courier` | Couriers |
| `CDOTA_Unit_Roshan` | Roshan |
| `CDOTA_NPC_Observer_Ward` | Observer wards |
| `CDOTA_NPC_Sentry_Ward` | Sentry wards |

### Items

| Class Pattern | Description |
|---------------|-------------|
| `CDOTA_Item_*` | Items |
| `CDOTA_Item_Physical` | Dropped items |

### Abilities

| Class Pattern | Description |
|---------------|-------------|
| `CDOTA_Ability_*` | Ability instances |

---

## Common Hero Properties

### Health & Mana

| Property | Type | Description |
|----------|------|-------------|
| `m_iHealth` | `int` | Current health |
| `m_iMaxHealth` | `int` | Maximum health |
| `m_flMana` | `float` | Current mana |
| `m_flMaxMana` | `float` | Maximum mana |
| `m_flHealthThinkRegen` | `float` | Health regeneration |
| `m_flManaThinkRegen` | `float` | Mana regeneration |

### Position & Movement

| Property | Type | Description |
|----------|------|-------------|
| `m_vecOrigin` | `[x, y, z]` | Position in world coordinates |
| `m_angRotation` | `[pitch, yaw, roll]` | Rotation angles |
| `m_flSpeed` | `float` | Current movement speed |

### Combat Stats

| Property | Type | Description |
|----------|------|-------------|
| `m_iCurrentLevel` | `int` | Hero level |
| `m_iKills` | `int` | Kills |
| `m_iDeaths` | `int` | Deaths |
| `m_iAssists` | `int` | Assists |
| `m_iDamageMin` | `int` | Minimum attack damage |
| `m_iDamageMax` | `int` | Maximum attack damage |
| `m_flPhysicalArmorValue` | `float` | Armor value |
| `m_flMagicalResistanceValue` | `float` | Magic resistance |

### Economy

| Property | Type | Description |
|----------|------|-------------|
| `m_iGold` | `int` | Reliable + unreliable gold |
| `m_iGoldReliable` | `int` | Reliable gold |
| `m_iGoldUnreliable` | `int` | Unreliable gold |
| `m_iTotalEarnedGold` | `int` | Total gold earned |
| `m_iLastHitCount` | `int` | Total last hits |
| `m_iDenyCount` | `int` | Total denies |

### Team & Player

| Property | Type | Description |
|----------|------|-------------|
| `m_iTeamNum` | `int` | Team number (2=Radiant, 3=Dire) |
| `m_iPlayerID` | `int` | Player ID (0-9) |
| `m_hAbilities` | `list` | Ability handles |
| `m_hItems` | `list` | Item handles |

---

## Filtering

### By Class Name

```python
# All heroes
heroes = parser.query_entities("match.dem", class_filter="Hero", max_entities=10)

# All towers
towers = parser.query_entities("match.dem", class_filter="Tower", max_entities=20)

# All couriers
couriers = parser.query_entities("match.dem", class_filter="Courier", max_entities=4)
```

### By Tick

```python
# Get state at specific tick
early_game = parser.query_entities("match.dem", tick=10000, class_filter="Hero")
late_game = parser.query_entities("match.dem", tick=50000, class_filter="Hero")
```

### By Property

```python
# Get all entities, then filter in Python
result = parser.query_entities("match.dem", max_entities=100)

# Find low health heroes
low_health = [
    e for e in result.entities
    if "Hero" in e.class_name
    and e.properties.get("m_iHealth", 0) < 500
]
```

---

## Property Name Patterns

Properties follow Source 2 naming conventions:

| Prefix | Meaning | Example |
|--------|---------|---------|
| `m_i` | Integer | `m_iHealth` |
| `m_fl` | Float | `m_flMana` |
| `m_b` | Boolean | `m_bIsAlive` |
| `m_sz` | String | `m_szName` |
| `m_vec` | Vector | `m_vecOrigin` |
| `m_ang` | Angle | `m_angRotation` |
| `m_h` | Handle | `m_hAbilities` |
| `m_n` | Enum/Int | `m_nGameState` |

---

## Result Metadata

`EntitiesResult` includes:

| Field | Type | Description |
|-------|------|-------------|
| `entities` | `List[EntityData]` | Entity data |
| `total_entities` | `int` | Count of entities returned |
| `tick` | `int` | Tick when captured |
| `net_tick` | `int` | Network tick when captured |
| `success` | `bool` | Parse success flag |
| `error` | `Optional[str]` | Error message if failed |
