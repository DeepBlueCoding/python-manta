---
name: add-or-fix-enum-model
description: Adds or modifies the Pydantic models and game-data enums in python-manta's manta_python.py (heroes, items, neutral items, rune/entity/combat-log/damage types) following the project's strict canonical-enum-plus-alias philosophy. Use whenever the user wants to add a new hero/item/enum, add an alias for an internal replay name, add or change a Pydantic model field, add a display_name, resolve npc_dota_hero_* / item_* names, or update enums for a new Dota patch. Use this even when the user just says "map this name", "add this hero", or "the enum is missing X".
---

# Adding / fixing enums and models

Everything lives in `src/python_manta/manta_python.py` (~3600 lines, the entire public surface).
Read `CLAUDE.md` ("Enum Design Philosophy", "Library Philosophy") first — this skill adds the exact
locations and the test/export mechanics.

## Enum philosophy (enforced, do not violate)

`str, Enum` with CANONICAL members only. NEVER add `_ALT` or duplicate members for aliases.
Internal/replay names resolve to canonical members through module-level alias dicts:

- `_HERO_ALIASES` — manta_python.py ~line 566
- `_ITEM_ALIASES` — ~line 1109
- `_NEUTRAL_ITEM_ALIASES` — ~line 1585

Each aliased enum exposes a classmethod `from_*_name(cls, name)` (does
`canonical = _X_ALIASES.get(name, name)` then enum lookup) and an instance `@property display_name`
returning human text.

```python
Hero.from_hero_name("npc_dota_hero_nevermore")   # -> Hero.SHADOW_FIEND
Item.from_item_name("item_famango")              # -> Item.ENCHANTED_MANGO
Hero.SHADOW_FIEND.display_name                    # -> "Shadow Fiend"
```

`from_hero_name` is at ~line 721, `Item.from_item_name` ~line 1373, `NeutralItem.from_item_name`
~line 1770; `display_name` properties recur throughout.

## Adding a new canonical member

1. Add the member to the enum body (canonical name → its canonical replay value).
2. If the replay/internal name differs from the canonical value, add `internal_name: "MEMBER_NAME"`
   to the matching `_*_ALIASES` dict. Do NOT add a second enum member.
3. Ensure `display_name` produces correct human text (extend its mapping if it is table-driven).
4. Export it (see below) and add a real-value unit test (see below).

## Adding / changing a Pydantic model field

Pydantic v2 (`pydantic>=2.0.0`). Models cross the CGO boundary by name: a new field MUST match the
`json:"..."` tag of the corresponding Go struct field in `go_wrapper/types.go`, or it silently
arrives missing/defaulted. If you add a field that comes from the parser, also add it on the Go side
and rebuild the `.so` with `./build.sh` (see the add-collector skill).

## Export it

Add every new public enum/model to `src/python_manta/__init__.py` — import it AND add it to the
`__all__` list (~74 names, ~line 116) or it cannot be imported as `from python_manta import X`.

## Scope guard

Only add things that MAP or TYPE game data: enums, IDs, and simple helper properties (e.g.
`is_pro_match`). Do NOT add analysis or statistics. Ask "is this raw data access or analysis?" —
only raw access belongs here.

## Tests (real values, not type checks)

Unit tests go in `tests/python_manta/enums/test_enums.py` or `tests/python_manta/models/test_models.py`,
marked `-m unit`. Assert REAL expected values — e.g. that a known replay name resolves to a specific
enum member and that `display_name` equals the exact string. Do NOT write `isinstance`/`len >= 0`
checks. Run just the file with coverage off (the 90% gate only passes on the full suite, which may
already be running on this machine):

```bash
cd /home/juanma/projects/python-manta
uv run pytest tests/python_manta/enums/test_enums.py --no-cov
```
