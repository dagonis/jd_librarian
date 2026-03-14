"""Scaffold new Johnny Decimal libraries."""

from pathlib import Path


_AREA_RANGES = [
    ("00-09", 0), ("10-19", 10), ("20-29", 20), ("30-39", 30), ("40-49", 40),
    ("50-59", 50), ("60-69", 60), ("70-79", 70), ("80-89", 80), ("90-99", 90),
]


def scaffold(target: str, mode: str = "blank", template_path: str | None = None, dry_run: bool = False) -> list[str]:
    """Create a new JD library folder structure.

    Modes:
        blank       — 10 areas all named 'Unused'
        opinionated — 00-09 Admin, 90-99 Testing, rest Unused
        template    — read from a plain-text or YAML template file

    Returns a list of directory paths that were (or would be) created.
    """
    root = Path(target)
    if mode == "template":
        if not template_path:
            raise ValueError("template mode requires a template file path")
        structure = _parse_template(template_path)
    elif mode == "opinionated":
        structure = _opinionated_structure()
    else:
        structure = _blank_structure()

    created: list[str] = []
    for area_name, categories in structure:
        area_path = root / area_name
        if not dry_run:
            area_path.mkdir(parents=True, exist_ok=True)
        created.append(str(area_path))
        for cat_name in categories:
            cat_path = area_path / cat_name
            if not dry_run:
                cat_path.mkdir(exist_ok=True)
            created.append(str(cat_path))
    return created


def _blank_structure() -> list[tuple[str, list[str]]]:
    """Return the folder structure for a blank JD library (all areas Unused)."""
    return [(f"{label} Unused", []) for label, _ in _AREA_RANGES]


def _opinionated_structure() -> list[tuple[str, list[str]]]:
    """Return the folder structure for an opinionated JD library."""
    names = {"00-09": "Admin", "90-99": "Testing"}
    return [(f"{label} {names.get(label, 'Unused')}", []) for label, _ in _AREA_RANGES]


def _parse_template(template_path: str) -> list[tuple[str, list[str]]]:
    """Parse a template file into a JD folder structure.

    Auto-detects format by file extension:
      .yaml / .yml  — YAML mapping of area names to category lists
      anything else  — plain-text (areas at column 0, categories indented)
    """
    path = Path(template_path)
    if path.suffix in (".yaml", ".yml"):
        return _parse_yaml_template(path)
    return _parse_text_template(path)


def _parse_text_template(path: Path) -> list[tuple[str, list[str]]]:
    """Parse a plain-text template file."""
    text = path.read_text()
    defined: dict[str, tuple[str, list[str]]] = {}
    current_label: str | None = None

    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        if raw_line[0] != " " and raw_line[0] != "\t":
            current_label = stripped.split(" ", maxsplit=1)[0]
            defined[current_label] = (stripped, [])
        else:
            if current_label is not None:
                defined[current_label][1].append(stripped)

    return _fill_missing_areas(defined)


def _parse_yaml_template(path: Path) -> list[tuple[str, list[str]]]:
    """Parse a YAML template file."""
    import yaml
    data = yaml.safe_load(path.read_text())
    if not isinstance(data, dict):
        raise ValueError("YAML template must be a mapping of area names to category lists")

    defined: dict[str, tuple[str, list[str]]] = {}
    for area_name, categories in data.items():
        label = str(area_name).split(" ", maxsplit=1)[0]
        if categories is None or categories == []:
            cats: list[str] = []
        else:
            if not isinstance(categories, (list, tuple)):
                raise ValueError(
                    f"Categories for area '{area_name}' must be a list or tuple, "
                    f"got {type(categories).__name__}"
                )
            cats = [str(c) for c in categories]
        defined[label] = (str(area_name), cats)

    return _fill_missing_areas(defined)


def _fill_missing_areas(defined: dict[str, tuple[str, list[str]]]) -> list[tuple[str, list[str]]]:
    """Fill in any missing area ranges as 'Unused'."""
    result: list[tuple[str, list[str]]] = []
    for label, _ in _AREA_RANGES:
        if label in defined:
            result.append(defined[label])
        else:
            result.append((f"{label} Unused", []))
    return result
