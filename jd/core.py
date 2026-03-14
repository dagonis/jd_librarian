from dataclasses import dataclass, field
from itertools import chain
from pathlib import Path
import re


# -- Area range constants --

_AREA_RANGES = [
    ("00-09", 0), ("10-19", 10), ("20-29", 20), ("30-39", 30), ("40-49", 40),
    ("50-59", 50), ("60-69", 60), ("70-79", 70), ("80-89", 80), ("90-99", 90),
]


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

    Any area range not listed defaults to 'Unused'.
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
    """Parse a YAML template file.

    Expected format:
        00-09 Admin:
          - 00 Index
          - 01 Homepage
        10-19 Projects:
          - 10 Active
    """
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


def _visible_dirs(path: Path) -> list[Path]:
    """Return sorted visible (non-hidden) subdirectories of path."""
    return sorted(p for p in path.iterdir() if p.is_dir() and not p.name.startswith("."))


def _visible_files(path: Path) -> list[Path]:
    """Return visible (non-hidden) files in path."""
    return [p for p in path.iterdir() if p.is_file() and not p.name.startswith(".")]


@dataclass
class LintWarning:
    """A single lint finding from a JD library check."""
    rule: str
    message: str
    path: Path

    def __str__(self) -> str:
        return f"[{self.rule}] {self.message}"


@dataclass
class JohnDecimal:
    """
    Represents a complete Johnny Decimal library rooted at a filesystem location.
    Builds the full Area > Category > Identifier > File hierarchy on init.

    The implied format of a JD ID is AC.ID where AC is area/category and ID is the identifier.
    """
    file_system_location: str

    def __post_init__(self) -> None:
        root = Path(self.file_system_location)
        self.areas = sorted([Area(p) for p in _visible_dirs(root)], key=lambda a: a.area_name)
        self.categories = list(chain.from_iterable(a.categories for a in self.areas))
        self.identifiers = list(chain.from_iterable(c.identifiers for c in self.categories))
        self.files = list(chain.from_iterable(i.files for i in self.identifiers))

    # -- Read operations --

    def search_johnny_decimal(self, search_term: str, include_category: bool = True, include_files: bool = False) -> str:
        results = []
        term = search_term.lower()
        for category in self.categories:
            if term in category.category_name.lower():
                results.append(str(category))
            for identifier in category.identifiers:
                if term in identifier.full_name.lower():
                    if include_category:
                        results.append(f"{category} -> {identifier}")
                    else:
                        results.append(str(identifier))
                if include_files:
                    for jdfile in identifier.files:
                        if term in jdfile.file_name.lower():
                            results.append(str(jdfile))
        if not results:
            return f"No results found for {search_term}"
        return "\n".join(results)

    def print_johnny_decimal_tree(self, space_len: int = 4, tabs: bool = False, print_files: bool = False, stats: bool = False) -> str:
        lines = []
        indent = "\t" if tabs else " " * space_len
        for area in self.areas:
            lines.append(str(area))
            for category in area.categories:
                lines.append(f"{indent}{category}")
                for identifier in category.identifiers:
                    lines.append(f"{indent}{indent}{identifier}")
                    if print_files:
                        for jdfile in identifier.files:
                            lines.append(f"{indent}{indent}{indent}{jdfile}")
        if stats:
            lines.append(f"\n\nAreas: {len(self.areas)}, Categories: {len(self.categories)}, Identifiers: {len(self.identifiers)}")
        return "\n".join(lines)

    def get_johnny_decimal_category(self, category_id: str) -> str:
        for category in self.categories:
            if category.category_number == category_id:
                lines = [str(category)]
                lines.extend(f"    {identifier}" for identifier in category.identifiers)
                return "\n".join(lines)
        return f"No category found for {category_id}"

    def get_johnny_decimal_identifier(self, identifier_id: str) -> str:
        for identifier in self.identifiers:
            if identifier_id in str(identifier):
                lines = [str(identifier)]
                lines.extend(f"    {jdfile.file_name}" for jdfile in identifier.files)
                return "\n".join(lines)
        return f"No identifier found for {identifier_id}"

    def __str__(self) -> str:
        return str(self.identifiers)

    # -- Lint operations --

    def lint(self) -> list[LintWarning]:
        """Check the library for structural problems. Returns a list of warnings."""
        warnings: list[LintWarning] = []
        self._lint_bad_naming(warnings)
        self._lint_duplicate_categories(warnings)
        self._lint_category_out_of_range(warnings)
        self._lint_duplicate_identifiers(warnings)
        self._lint_empty_categories(warnings)
        self._lint_empty_identifiers(warnings)
        self._lint_id_gaps(warnings)
        self._lint_category_capacity(warnings)
        self._lint_area_capacity(warnings)
        self._lint_orphan_files(warnings)
        return warnings

    @staticmethod
    def lint_from_path(path: str) -> list[LintWarning]:
        """Run all lint checks, starting with bad naming (which can prevent normal init)."""
        warnings: list[LintWarning] = []
        root = Path(path)
        area_pattern = re.compile(r"^\d{2}-\d{2} .+$")
        category_pattern = re.compile(r"^\d{2} .+$")
        identifier_pattern = re.compile(r"^\d{2} .+$")

        for d in _visible_dirs(root):
            if not area_pattern.match(d.name):
                warnings.append(LintWarning("bad_naming", f"Area folder doesn't match 'NN-NN Name' format: {d.name}", d))
            else:
                for cd in _visible_dirs(d):
                    if not category_pattern.match(cd.name):
                        warnings.append(LintWarning("bad_naming", f"Category folder doesn't match 'NN Name' format: {cd.name}", cd))
                    else:
                        for idd in _visible_dirs(cd):
                            if not identifier_pattern.match(idd.name):
                                warnings.append(LintWarning("bad_naming", f"Identifier folder doesn't match 'NN Name' format: {idd.name}", idd))

        # If there are bad naming issues, the tree can't be fully parsed, so return early
        if warnings:
            return warnings

        jd = JohnDecimal(path)
        warnings.extend(jd.lint())
        return warnings

    def _lint_bad_naming(self, warnings: list[LintWarning]) -> None:
        """Flag folders that don't follow the expected JD naming conventions.
        Only checks folders that were successfully parsed (already well-formed)."""
        pass  # Handled by lint_from_path before init

    def _lint_duplicate_categories(self, warnings: list[LintWarning]) -> None:
        """Flag areas that contain multiple categories with the same number."""
        for area in self.areas:
            seen: dict[str, Category] = {}
            for category in area.categories:
                if category.category_number in seen:
                    warnings.append(LintWarning(
                        "duplicate_category",
                        f"Duplicate category number {category.category_number} in {area}: "
                        f"'{seen[category.category_number].category_name}' and '{category.category_name}'",
                        category.file_system_location,
                    ))
                else:
                    seen[category.category_number] = category

    def _lint_category_out_of_range(self, warnings: list[LintWarning]) -> None:
        """Flag categories whose number falls outside the parent area's range."""
        for area in self.areas:
            try:
                start, end = area.area_number_range.split("-")
                range_start, range_end = int(start), int(end)
            except ValueError:
                continue
            for category in area.categories:
                try:
                    cat_num = int(category.category_number)
                except ValueError:
                    continue
                if not (range_start <= cat_num <= range_end):
                    warnings.append(LintWarning(
                        "category_out_of_range",
                        f"Category {category.category_number} ({category.category_short_name}) "
                        f"is outside area range {area.area_number_range}",
                        category.file_system_location,
                    ))

    def _lint_duplicate_identifiers(self, warnings: list[LintWarning]) -> None:
        """Flag categories that contain multiple identifiers with the same number."""
        for category in self.categories:
            seen: dict[str, Identifier] = {}
            for identifier in category.identifiers:
                if identifier.id_number in seen:
                    warnings.append(LintWarning(
                        "duplicate_id",
                        f"Duplicate identifier {category.category_number}.{identifier.id_number} in {category}: "
                        f"'{seen[identifier.id_number].short_name}' and '{identifier.short_name}'",
                        identifier.file_system_location,
                    ))
                else:
                    seen[identifier.id_number] = identifier

    def _lint_empty_categories(self, warnings: list[LintWarning]) -> None:
        """Flag categories that have no identifiers."""
        for category in self.categories:
            if not category.identifiers:
                warnings.append(LintWarning(
                    "empty_category",
                    f"Category {category} has no identifiers",
                    category.file_system_location,
                ))

    def _lint_empty_identifiers(self, warnings: list[LintWarning]) -> None:
        """Flag identifiers that have no files inside."""
        for identifier in self.identifiers:
            if not identifier.files:
                warnings.append(LintWarning(
                    "empty_identifier",
                    f"Identifier {identifier} has no files",
                    identifier.file_system_location,
                ))

    def _lint_id_gaps(self, warnings: list[LintWarning]) -> None:
        """Flag categories where identifier numbers have gaps."""
        for category in self.categories:
            if len(category.identifiers) < 2:
                continue
            numbers = sorted(int(i.id_number) for i in category.identifiers)
            missing = []
            for i in range(numbers[0], numbers[-1] + 1):
                if i not in numbers:
                    missing.append(str(i).zfill(2))
            if missing:
                warnings.append(LintWarning(
                    "id_gap",
                    f"Category {category} has gaps in identifier numbers: {', '.join(missing)}",
                    category.file_system_location,
                ))

    def _lint_category_capacity(self, warnings: list[LintWarning], threshold: int = 80) -> None:
        """Warn when a category is approaching the 99 identifier limit."""
        for category in self.categories:
            count = len(category.identifiers)
            if count >= threshold:
                warnings.append(LintWarning(
                    "category_capacity",
                    f"Category {category} has {count}/99 identifiers",
                    category.file_system_location,
                ))

    def _lint_area_capacity(self, warnings: list[LintWarning], threshold: int = 8) -> None:
        """Warn when an area is approaching the 10 category limit."""
        for area in self.areas:
            count = len(area.categories)
            if count >= threshold:
                warnings.append(LintWarning(
                    "area_capacity",
                    f"Area {area} has {count}/10 categories",
                    area.file_system_location,
                ))

    def _lint_orphan_files(self, warnings: list[LintWarning]) -> None:
        """Flag files sitting at the wrong level (root, area, or category level)."""
        root = Path(self.file_system_location)
        # Files in the root
        for f in _visible_files(root):
            warnings.append(LintWarning(
                "orphan_file",
                f"File at root level: {f.name}",
                f,
            ))
        # Files in area folders
        for area in self.areas:
            for f in _visible_files(area.file_system_location):
                warnings.append(LintWarning(
                    "orphan_file",
                    f"File in area {area}: {f.name}",
                    f,
                ))
        # Files in category folders
        for category in self.categories:
            for f in _visible_files(category.file_system_location):
                warnings.append(LintWarning(
                    "orphan_file",
                    f"File in category {category} (should be inside an identifier): {f.name}",
                    f,
                ))

    # -- Scaffold operations --

    @staticmethod
    def scaffold(target: str, mode: str = "blank", template_path: str | None = None, dry_run: bool = False) -> list[str]:
        """Create a new JD library folder structure.

        Modes:
            blank       — 10 areas all named 'Unused'
            opinionated — 00-09 Admin, 90-99 Testing, rest Unused
            template    — read from a plain-text template file

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

    # -- Create operations --

    def add_johnny_decimal_category(self, area_id: str, new_category_name: str, dry_run: bool = False) -> bool:
        for area in self.areas:
            if area.area_number_range.startswith(area_id):
                existing = {c.category_number for c in area.categories}
                for i in range(int(area_id), int(area_id) + 10):
                    number = str(i).zfill(2)
                    if number not in existing:
                        new_category_path = area.file_system_location / f"{number} {new_category_name}"
                        if not dry_run:
                            new_category_path.mkdir()
                            print(f"Created - {new_category_path}")
                            return True
                        print(f"Would have created - {new_category_path}")
                        return False
        return False

    def add_johnny_decimal_identifier(self, category_id: str, identifier_name: str, placeholder: bool = False, dry_run: bool = False) -> bool:
        for category in self.categories:
            if category.category_number == category_id:
                existing = {ident.id_number for ident in category.identifiers}
                for i in range(1, 100):
                    number = str(i).zfill(2)
                    if number not in existing:
                        new_path = category.file_system_location / f"{number} {identifier_name}"
                        if not dry_run:
                            new_path.mkdir()
                            if placeholder:
                                (new_path / f"{identifier_name}.md").touch()
                            print(f"Created - {category.category_number}.{number} {identifier_name} - {new_path}")
                            return True
                        print(f"Would have created - {new_path}")
                        return False
        return False


@dataclass
class Area:
    """
    Represents a Johnny Decimal area (e.g. '00-09 Admin', '80-89 Unused').
    """
    file_system_location: Path

    def __post_init__(self) -> None:
        self.area_name = self.file_system_location.name
        self.area_number_range, self.area_short_name = self.area_name.split(" ", maxsplit=1)
        self.categories = sorted(
            [Category(p, self.area_name) for p in _visible_dirs(self.file_system_location)],
            key=lambda c: c.category_name,
        )

    def __str__(self) -> str:
        return f"[{self.area_number_range}] {self.area_short_name}"


@dataclass
class Category:
    """
    Represents a Johnny Decimal category (e.g. '11 Vendors').
    Full ID format: Category.Identifier, e.g. 11.01
    """
    file_system_location: Path
    area: str

    def __post_init__(self) -> None:
        self.category_name = self.file_system_location.name
        self.category_number, self.category_short_name = self.category_name.split(" ", maxsplit=1)
        self.identifiers = sorted(
            [Identifier(p, self.area, self.category_number) for p in _visible_dirs(self.file_system_location)],
            key=lambda i: i.full_name,
        )

    def __str__(self) -> str:
        return f"[{self.category_number}] {self.category_short_name}"


@dataclass
class Identifier:
    """
    Represents a Johnny Decimal identifier (e.g. '01 Homepage').
    Full ID format: Category.Identifier, e.g. 11.01
    """
    file_system_location: Path
    area: str
    category: str

    def __post_init__(self) -> None:
        self.full_name = self.file_system_location.name
        self.id_number, self.short_name = self.full_name.split(" ", maxsplit=1)
        self.files = [JohnnyDecimalFile(p, self.area, self.category, self.id_number) for p in _visible_files(self.file_system_location)]

    def __str__(self) -> str:
        return f"[{self.category}.{self.id_number}] {self.short_name}"


@dataclass
class JohnnyDecimalFile:
    """
    Represents a file inside a Johnny Decimal identifier folder.
    """
    file_system_location: Path
    area: str
    category: str
    identifier: str

    def __post_init__(self) -> None:
        self.file_name = self.file_system_location.name

    def __str__(self) -> str:
        return f"[{self.category}.{self.identifier}] {self.file_name}"
