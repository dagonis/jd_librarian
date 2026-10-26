# Changelog

All notable changes to JD Librarian will be documented in this file.

## [Unreleased]

### Added
- **Path** — `jd path 11.01` prints the folder path for a category or identifier, for use with `cd`, `open`, etc.
- `--files` flag to include files in the tree view
- `--dry_run` can now be passed after the subcommand (e.g. `jd add_id 11 Foo --dry_run`)
- Python 3.14 in CI

### Fixed
- `python -m jd` crashed with `NameError` (`_validate_jd_root` was defined after `main()` ran)
- `~` in `--jd_root` / `JD_ROOT` (including the `~/jd` default) wasn't expanded
- `add_category 1 ...` matched area `10-19` by prefix and created an out-of-range `01` category
- `show 1.01` substring-matched `11.01`; identifier lookup is now exact
- `add_category` / `add_id` failed silently (exit 0, no output) for a missing or full area/category
- Any non-conforming folder (e.g. `Inbox`) crashed tree, search, stats, and report; such folders are now skipped
- `lint` stopped after `bad_naming` findings; it now reports all issues in one pass, and `report` includes naming issues

### Changed
- Version is defined once in `jd/__init__.py`
- CLI tests run via `python -m jd` with the current interpreter rather than whatever `jd` is on `PATH`

## [1.0.0] - 2026-03-13

### Added
- **Scaffold** — create new JD libraries from scratch (`jd scaffold`)
  - Three modes: `blank`, `opinionated`, and `template`
  - Template support for both plain-text and YAML formats
- **Lint** — check library for structural problems (`jd lint`)
  - 10 rules: bad naming, duplicate categories/identifiers, out-of-range categories, empty categories/identifiers, ID gaps, capacity warnings, orphan files
- **Stats** — view usage statistics with capacity bars (`jd stats`)
- **Report** — generate a self-contained cyberpunk-themed HTML report (`jd report`)
  - Includes stats, lint findings, and capacity visualizations
- **`--version` / `-V` flag** to display the current version
- **Error handling** for invalid `JD_ROOT` paths
- **GitHub Actions CI** running tests on Python 3.10–3.13
- **py.typed marker** for PEP 561 type checking support
- Example template files (plain-text and YAML superhero themes)

### Changed
- Modernized codebase: `pathlib` throughout, dataclasses, type hints
- Refactored into focused modules: `core`, `models`, `lint`, `scaffold`, `stats`, `report`
- Migrated to `pyproject.toml` with `pip install -e .` entry point
- Comprehensive test suite (112+ tests)

### Removed
- Legacy `os.path` usage replaced with `pathlib`
- Direct script invocation — now installed as `jd` console entry point
