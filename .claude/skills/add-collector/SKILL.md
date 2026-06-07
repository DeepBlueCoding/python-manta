---
name: add-collector
description: Adds a new single-pass data collector to python-manta end-to-end (Go CGO layer, Python Pydantic models, parse() kwarg, fixture, scenario test, docs) so it becomes reachable as parser.parse(<name>={...}). Use whenever the user wants to add a new collector, track or capture a new kind of event/entity during parsing (wards-style, attacks-style), expose new dotabuff/manta data through parse(), add a parse() collector kwarg, or create a new *Result/*Config result type. Use this even if the user only describes the data they want surfaced (e.g. "track every tower attack", "capture courier deaths") without saying the word "collector".
---

# Adding a single-pass collector

A collector is one config object passed to `parser.parse(<name>={...})` that captures a class of
events/entities in the single parsing pass and returns a `*Result`. Wards is the canonical
template — grep `ward` / `Wards` across `go_wrapper/` and `src/python_manta/manta_python.py` and
copy its shape.

This crosses the CGO boundary by JSON: Python sends `config.model_dump_json(exclude_none=True)`,
Go fills a `*Result` struct, Python rebuilds it as `ParseResult(**json.loads(...))`. **JSON field
names must match exactly** between Go struct `json:"..."` tags and Pydantic field names, or the
field silently arrives empty/defaulted. Use ONE name (`snake_case`) for the collector everywhere.

Read `CLAUDE.md` first — this file adds the task-specific touchpoints it does not spell out.

## Touchpoint checklist (all required for one collector named `foo`)

Go side (`go_wrapper/`):
- [ ] `types.go`: add `FooConfig` struct + `FooResult` struct (mirror `WardsConfig`/`WardsResult`).
- [ ] `types.go`: add `Foo *FooConfig `json:"foo,omitempty"`` field on `ParseConfig`.
- [ ] `types.go`: add `Foo *FooResult `json:"foo,omitempty"`` field on `ParseResult`.
- [ ] `parser.go`: add an `if config.Foo != nil { ... }` collector block (wards block is ~line 790).
- [ ] `parser.go`: if `FooResult` carries `game_time`, add a post-pass tick→game_time loop (see below).

Python side (`src/python_manta/manta_python.py`):
- [ ] add `FooConfig(BaseModel)` and `FooResult(BaseModel)` (config classes cluster ~line 2765, result classes ~line 2580; e.g. `WardsResult` ~2578, `WardsConfig` ~2765).
- [ ] add `foo: Optional[FooConfig] = None` on `ParseConfig` (~line 2770).
- [ ] add `foo: Optional[FooResult] = None` on `ParseResult` (~line 2796).
- [ ] add `foo: Optional[Dict[str, Any]] = None` kwarg to `Parser.parse()` (~line 3297).
- [ ] add `if foo is not None: config.foo = FooConfig(**foo)` in `parse()` (~line 3360).

Wiring + tests + docs:
- [ ] `src/python_manta/__init__.py`: re-export `FooConfig`, `FooResult`, and any event model.
- [ ] `tests/conftest.py`: add a `scope="module"` fixture `def foo_result(parser): ...` (see test skill).
- [ ] `tests/scenarios/test_foo.py`: integration test with golden values (see test skill).
- [ ] `docs/reference/foo.md` + register it under `nav: Reference` in `mkdocs.yml`.

## game_time gotcha (do NOT skip)

Collector callbacks only know `parser.Tick`. `game_time` is filled AFTER parsing, in a post-pass
loop in `parser.go`, because `gameStartTick` may not be known when an early event fires. Pattern
(the wards post-pass `// Post-process: add game time` loop is ~line 1062; other collectors do the
same, e.g. attacks ~line 991, entity_deaths ~line 1002):

```go
if fooResult != nil {
    for i := range fooResult.Events {
        fooResult.Events[i].GameTime = TickToGameTime(uint32(fooResult.Events[i].Tick), gameStartTick)
    }
}
```

`gameStartTick` is detected always-on from the `CDOTAGamerulesProxy` entity field
`m_pGameRules.m_flGameStartTime` (parser.go ~line 104) and refined by the combat-log GAME_STATE
`value==5` detector when `combat_log` is enabled (parser.go ~line 219). `TicksPerSecond` is 30
(`time_utils.go`). Game time is signed: negative = pre-horn.

## Entity-based vs callback-based collectors

- Entity-based (like wards): register `OnEntity` inside the guard, filter by `className`
  (wards check `className == "CDOTA_NPC_Observer_Ward"` / `"CDOTA_NPC_Observer_Ward_TrueSight"`),
  read fields off the entity, and track create/delete (wards map entity index → event index).
- Callback-based: register the specific manta callback inside the guard.
- Always respect `MaxEvents` from the config (0 = unlimited, matching wards).

## Scope rule

python-manta is data-extraction-only (CLAUDE.md). Expose raw fields and canonical enums
(`Hero`, `Item`, etc.). Do NOT add aggregation/counting/analysis — that is the consumer's job.
The `*Result` may carry trivial helper properties (e.g. `total_events`), nothing more.

## Rebuild + verify (static-safe)

After ANY Go edit the `.so` must be rebuilt:

```bash
cd /home/juanma/projects/python-manta && ./build.sh
```

`build.sh` runs `tools/prepare_manta.sh` (syncs `go_wrapper/manta` to `.manta-version`), then
`go build -buildmode=c-shared -o libmanta_wrapper.so .`, then copies `.so`/`.h` into
`src/python_manta/`. Pure-Python edits still need the rebuilt `.so` if you also touched Go.

HARD CONSTRAINT: a full test suite may be running on this machine. Do NOT launch the full suite.
To smoke-verify a collector, run only its scenario file with coverage off:

```bash
uv run pytest tests/scenarios/test_foo.py --no-cov
```
