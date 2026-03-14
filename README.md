# JD Librarian

A command line tool for managing [Johnny Decimal](https://johnnydecimal.com/) libraries.

The Johnny Decimal system organizes information using a simple numerical hierarchy: **Areas** (10 max) contain **Categories** (10 per area) which contain **Identifiers** (99 per category). JD Librarian lets you search, manage, lint, scaffold, and report on your library from the terminal.

## Features

- **Search** — find categories, identifiers, and files by keyword
- **Show** — display a specific category or identifier and its contents
- **Add** — create new categories and identifiers with automatic numbering
- **Lint** — check your library for structural problems (10 rules covering naming, duplicates, capacity, orphan files, and more)
- **Scaffold** — create a new JD library from scratch (blank, opinionated, or from a template file)
- **Stats** — view usage statistics with capacity bars per area and category
- **Report** — generate a self-contained cyberpunk-themed HTML report with stats, lint findings, and capacity visualizations
- **Dry Run** — preview any change before it happens with `--dry_run`
- **Template Support** — scaffold from plain-text or YAML template files

## Installation

Requires **Python 3.10+**.

```bash
git clone https://github.com/dagonis/jd_librarian.git
cd jd_librarian
pip install -e ".[dev]"
```

This installs the `jd` command globally. Set your library root:

```bash
export JD_ROOT=~/path/to/your/jd/library
```

Or pass it per-command with `--jd_root /path/to/library`.

## Commands

### Search

```bash
jd search "vendors"
jd search "acme" --include_category --include_files
```

### Show

```bash
jd show 11          # show category 11 and its identifiers
jd show 11.01       # show identifier 11.01 and its files
```

### Add Category

```bash
jd add_category 10 "New Category"
jd --dry_run add_category 10 "New Category"
```

### Add Identifier

```bash
jd add_id 11 "New Vendor"
jd add_id 11 "New Vendor" --add_placeholder    # creates a .md file inside
```

### Tree View

```bash
jd                  # print the full tree
jd -s               # include stats summary
```

### Lint

Check your library for structural issues:

```bash
jd lint
```

**Rules checked:**
| Priority | Rule | Description |
|----------|------|-------------|
| High | `bad_naming` | Folders don't match `NN-NN Name` / `NN Name` format |
| High | `duplicate_category` | Multiple categories with the same number in an area |
| High | `duplicate_id` | Multiple identifiers with the same number in a category |
| High | `category_out_of_range` | Category number outside its parent area's range |
| Medium | `empty_category` | Category with no identifiers |
| Medium | `empty_identifier` | Identifier with no files |
| Medium | `id_gap` | Gaps in identifier numbering within a category |
| Low | `category_capacity` | Category approaching the 99-identifier limit |
| Low | `area_capacity` | Area approaching the 10-category limit |
| Low | `orphan_file` | File at the wrong level (root, area, or category) |

### Scaffold

Create a new JD library from scratch:

```bash
jd scaffold ~/new_library                              # blank — 10 unused areas
jd scaffold ~/new_library --mode opinionated           # 00-09 Admin, 90-99 Testing
jd scaffold ~/new_library --mode template --template template.txt
jd scaffold ~/new_library --mode template --template template.yaml
```

**Plain-text template format:**
```
00-09 Admin
  00 Index
  01 Homepage
10-19 Projects
  10 Active
20-29 People
```

**YAML template format:**
```yaml
00-09 Admin:
  - 00 Index
  - 01 Homepage
10-19 Projects:
  - 10 Active
20-29 People:
```

Areas at column 0, categories indented. Any area not listed defaults to "Unused". See [examples/](examples/) for sample templates.

### Stats

```bash
jd stats
```

Shows capacity bars per area and category:

```
═══ JD Library Stats ═══

  Areas:        7/10 active
  Categories:   46/100 slots (46.0%)
  Identifiers:  216
  Files:        910

── Per Area ──
  [00-09] Admin                  ████████████████░░░░  80.0%  (8 cats, 15 ids, 402 files)
  [10-19] Management             ██████████████░░░░░░  70.0%  (7 cats, 50 ids, 172 files)
  ...
```

### Report

Generate a self-contained HTML report:

```bash
jd report                          # writes jd_report.html
jd report -o ~/reports/latest.html # custom output path
```

The report includes stats cards, per-area/category capacity bars, the full lint report, and a link back to this repo — all in a dark cyberpunk theme.

## Development

Run the test suite (112 tests):

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## License

MIT — see [LICENSE](LICENSE) for details.