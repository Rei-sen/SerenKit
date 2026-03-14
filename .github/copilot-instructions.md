# Copilot / AI Agent Instructions for SerenKit

Purpose: short, up-to-date guidance for AI agents working on this Blender add-on.

Overview
- SerenKit is a Blender add-on that provides export pipelines and modpack tooling for Final Fantasy XIV.
- Key directories:
  - `operators/`: Blender-facing operators and UI hooks (entrypoints called from the add-on).
  - `properties/`: Blender `PropertyGroup` definitions used for per-collection and per-object settings.
  - `shared/`: Pure-Python business logic and helpers; this is where unit-testable code should live.
  - `xivpy/`: Vendored third-party game format utils — do not change unless fixing a confirmed bug.

Active export flow
- The supported export pipeline is the session-based implementation in `shared/export/new_export_session.py`.
- The Blender operator `operators/ffxiv_exporter.py` is the primary entrypoint that constructs `ExportSettings` and then drives the session exporter.

Shape keys & conversion
- Shape key logic and helpers live in `shared/export/shapekey_utils.py`. Use these helpers when applying or collecting shape keys for variants.
- MDL conversion is handled via `shared/export/textools_adapter.py` and requires a configured Textools executable and `game_path` (set in collection/add-on preferences).

Developer workflows
- Use a local virtualenv at the repo root named `.venv`.
  - Activate (PowerShell): & .\\.venv\\Scripts\\Activate.ps1
  - Install dev deps: `python -m pip install -r requirements-dev.txt`
- Run tests: `python -m pytest -q` (tests live in `tests/` and use a `bpy` shim provided by `tests/conftest.py`).
- Manual Blender testing: install the add-on via Blender Preferences → Add-ons → Install..., enable it, and configure Textools path in add-on prefs when testing MDL conversion.

Testing and editing guidance
- Tests mock `bpy` via the `tests/conftest.py` shim — avoid importing the real `bpy` in unit tests.
- Prefer adding pure-Python helpers to `shared/` so they are unit-testable.
- Keep type hints and `pathlib.Path` usage consistent with existing code.

Important files (quick links)
- `shared/export/new_export_session.py`: active export session loop and Textools usage.
- `operators/ffxiv_exporter.py`: Blender operator and entrypoint for exports.
- `shared/export/shapekey_utils.py`: authoritative shape key helpers.
- `shared/export_context.py`: `CollectionExportInfo` and readiness checks.
- `tests/conftest.py`: `bpy` shim used by unit tests.

Integration notes
- Textools: external executable required for MDL conversion; path is configured in add-on prefs and collection properties.
- Game path: many exporters require the game installation path; check collection properties and readiness logic in `shared/export_context.py`.

Safety and maintenance
- Do not modify `xivpy/` unless addressing a clear bug — it's vendored code.
- When making changes that touch Blender APIs, isolate pure-Python logic into `shared/` and keep Blender-specific code in `operators/` and `properties/` so tests can run without Blender.

Getting started suggestions for contributors
- Extract small helpers from `operators/` into `shared/` to increase test coverage.
- Add unit tests for `shared/export/shapekey_utils.py` and `shared/export/new_export_session.py` behavior using the existing `bpy` shim.

If anything here is unclear or you'd like me to expand a specific area (e.g., detailed notes on `profile`/`variants` logic or the Textools adapter), tell me which files to inspect and I'll iterate.
