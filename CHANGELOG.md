# Changelog

All notable changes to JD Librarian will be documented in this file.

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
