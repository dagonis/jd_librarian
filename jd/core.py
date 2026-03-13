from dataclasses import dataclass
from itertools import chain
from pathlib import Path


def _visible_dirs(path: Path) -> list[Path]:
    """Return sorted visible (non-hidden) subdirectories of path."""
    return sorted(p for p in path.iterdir() if p.is_dir() and not p.name.startswith("."))


def _visible_files(path: Path) -> list[Path]:
    """Return visible (non-hidden) files in path."""
    return [p for p in path.iterdir() if p.is_file() and not p.name.startswith(".")]


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
