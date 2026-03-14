from dataclasses import dataclass
from itertools import chain
from pathlib import Path

from .models import (
    Area, Category, Identifier, JohnnyDecimalFile, LintWarning,
    _visible_dirs,
)
from . import lint as _lint
from . import scaffold as _scaffold
from . import stats as _stats


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

    # -- Stats (delegates to jd.stats) --

    def stats(self) -> dict:
        return _stats.stats(self)

    def stats_cli(self) -> str:
        return _stats.stats_cli(self)

    # -- Lint (delegates to jd.lint) --

    def lint(self) -> list[LintWarning]:
        return _lint.lint(self)

    @staticmethod
    def lint_from_path(path: str) -> list[LintWarning]:
        return _lint.lint_from_path(path)

    # -- Scaffold (delegates to jd.scaffold) --

    @staticmethod
    def scaffold(target: str, mode: str = "blank", template_path: str | None = None, dry_run: bool = False) -> list[str]:
        return _scaffold.scaffold(target, mode, template_path, dry_run)

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
