from dataclasses import dataclass
from pathlib import Path


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
