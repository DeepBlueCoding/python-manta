---
name: write-docs
description: Authors and updates the python-manta mkdocs documentation site (guides, API reference, reference pages) consistent with the mkdocs.yml nav, mike versioning, llms.txt generation, and the project's time-formatting and data-extraction-only content rules. Use whenever the user wants to write or update docs, add a guide, document a new feature/collector in the docs site, update the API reference, add a reference page, edit mkdocs, or work on the GitHub Pages / llms.txt site. Use this even when the user just says "document this" or "add it to the docs".
---

# Writing python-manta docs

Stack: mkdocs-material (slate / deep purple) + the `mike` versioning plugin, deployed to GitHub
Pages. Docs live under `docs/`. Read `CLAUDE.md` first for the content philosophy; this skill adds
the mkdocs/nav/llms mechanics it omits.

## Layout — where content goes

```
docs/
├── guides/      # task/how-to guides (Overview, MCP Use Cases, Unit Orders, Combat Log, ...)
├── api/         # API Reference: index.md, parser.md, models.md
├── reference/   # one page per collector: callbacks, game-events, combat-log, attacks,
│                #   wards, modifiers, entities, string-tables (+ index.md, Overview)
└── design/      # design notes
```

New collector → add `docs/reference/<name>.md`. New how-to → `docs/guides/<name>.md`. API surface
change → edit `docs/api/parser.md` or `docs/api/models.md`. Use existing pages as templates
(`docs/reference/wards.md`, `docs/api/parser.md`).

## A page is invisible until it is in the nav

Register every new page under the `nav:` tree in `mkdocs.yml` (~line 58). It will not ship, and will
NOT appear in `llms.txt`, otherwise. Example addition under Reference:

```yaml
  - Reference:
    - Overview: reference/index.md
    - Wards: reference/wards.md
    - Foo: reference/foo.md        # <- new
```

`scripts/generate_llms_txt.py` parses the nav from `mkdocs.yml` (PyYAML with a hand-rolled fallback
parser) to build `llms.txt` (index) and `llms-full.txt` (concatenated). Keep nav indentation clean
(2-space steps) or the fallback parser mis-reads it.

## Available Material/markdown features

From `mkdocs.yml` `markdown_extensions`: `admonition`, `pymdownx.details`,
`pymdownx.superfences`, `pymdownx.highlight` + `inlinehilite`, `pymdownx.snippets`,
`pymdownx.tabbed` (alternate_style), `tables`, `attr_list`, `md_in_html`, `toc` (permalink). Use
admonitions (`!!! note`), tabbed code blocks, and fenced code with language hints. `mike` makes docs
versioned — write version-agnostic prose (no "in the next release").

## Content rules (project-specific)

- Time: NEVER show decimal minutes ("77.9 minutes"). Durations use `H:MM:SS`; game clock uses signed
  `MM:SS` where negative = pre-horn (CLAUDE.md "Time Formatting" has the exact format helpers).
- Enums: document with `.display_name` for human text and `from_*_name()` for resolution; show
  canonical members (e.g. `Hero.SHADOW_FIEND`), not raw replay strings.
- Scope: docs describe RAW data extraction and simple helper properties only — never analysis,
  aggregation, or stat computation. Reference pages mirror collectors one-to-one.
- README.md and CLAUDE.md already hold the API quick reference; link to / mirror them, don't fork a
  divergent version.

## Build / preview / deploy

```bash
cd /home/juanma/projects/python-manta
uv run python scripts/generate_llms_txt.py   # regenerate llms.txt + llms-full.txt after nav changes
uv run mkdocs serve                          # local preview at http://127.0.0.1:8000
uv run mkdocs build                          # static build check (errors out on broken nav refs)
```

Deploy is automatic via `.github/workflows/docs.yml` — do NOT run `mike deploy` by hand. It fires
only on push to `master` OR on 4-part non-dev release tags `v[0-9]+.[0-9]+.[0-9]+.[0-9]+`, and only
when `docs/**`, `mkdocs.yml`, `scripts/generate_llms_txt.py`, or the workflow changed. It installs
`mkdocs-material mike pyyaml`, runs `generate_llms_txt.py`, then
`mike deploy --push --update-aliases <version> latest` (tags) or `mike deploy --push master`.
