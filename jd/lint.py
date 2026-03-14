"""Lint checks for Johnny Decimal libraries."""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from .models import Category, Identifier, LintWarning, _visible_dirs, _visible_files

if TYPE_CHECKING:
    from .core import JohnDecimal


def lint(jd: JohnDecimal) -> list[LintWarning]:
    """Check the library for structural problems. Returns a list of warnings."""
    warnings: list[LintWarning] = []
    _lint_duplicate_categories(jd, warnings)
    _lint_category_out_of_range(jd, warnings)
    _lint_duplicate_identifiers(jd, warnings)
    _lint_empty_categories(jd, warnings)
    _lint_empty_identifiers(jd, warnings)
    _lint_id_gaps(jd, warnings)
    _lint_category_capacity(jd, warnings)
    _lint_area_capacity(jd, warnings)
    _lint_orphan_files(jd, warnings)
    return warnings


def lint_from_path(path: str) -> list[LintWarning]:
    """Run all lint checks, starting with bad naming (which can prevent normal init)."""
    from .core import JohnDecimal

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

    if warnings:
        return warnings

    jd = JohnDecimal(path)
    warnings.extend(lint(jd))
    return warnings


def _lint_duplicate_categories(jd: JohnDecimal, warnings: list[LintWarning]) -> None:
    for area in jd.areas:
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


def _lint_category_out_of_range(jd: JohnDecimal, warnings: list[LintWarning]) -> None:
    for area in jd.areas:
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


def _lint_duplicate_identifiers(jd: JohnDecimal, warnings: list[LintWarning]) -> None:
    for category in jd.categories:
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


def _lint_empty_categories(jd: JohnDecimal, warnings: list[LintWarning]) -> None:
    for category in jd.categories:
        if not category.identifiers:
            warnings.append(LintWarning(
                "empty_category",
                f"Category {category} has no identifiers",
                category.file_system_location,
            ))


def _lint_empty_identifiers(jd: JohnDecimal, warnings: list[LintWarning]) -> None:
    for identifier in jd.identifiers:
        if not identifier.files:
            warnings.append(LintWarning(
                "empty_identifier",
                f"Identifier {identifier} has no files",
                identifier.file_system_location,
            ))


def _lint_id_gaps(jd: JohnDecimal, warnings: list[LintWarning]) -> None:
    for category in jd.categories:
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


def _lint_category_capacity(jd: JohnDecimal, warnings: list[LintWarning], threshold: int = 80) -> None:
    for category in jd.categories:
        count = len(category.identifiers)
        if count >= threshold:
            warnings.append(LintWarning(
                "category_capacity",
                f"Category {category} has {count}/99 identifiers",
                category.file_system_location,
            ))


def _lint_area_capacity(jd: JohnDecimal, warnings: list[LintWarning], threshold: int = 8) -> None:
    for area in jd.areas:
        count = len(area.categories)
        if count >= threshold:
            warnings.append(LintWarning(
                "area_capacity",
                f"Area {area} has {count}/10 categories",
                area.file_system_location,
            ))


def _lint_orphan_files(jd: JohnDecimal, warnings: list[LintWarning]) -> None:
    root = Path(jd.file_system_location)
    for f in _visible_files(root):
        warnings.append(LintWarning("orphan_file", f"File at root level: {f.name}", f))
    for area in jd.areas:
        for f in _visible_files(area.file_system_location):
            warnings.append(LintWarning("orphan_file", f"File in area {area}: {f.name}", f))
    for category in jd.categories:
        for f in _visible_files(category.file_system_location):
            warnings.append(LintWarning(
                "orphan_file",
                f"File in category {category} (should be inside an identifier): {f.name}",
                f,
            ))
