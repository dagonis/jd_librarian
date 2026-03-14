"""Usage statistics for Johnny Decimal libraries."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .core import JohnDecimal


def _bar(percent: float, width: int = 20) -> str:
    """Return a unicode bar chart segment for CLI display."""
    filled = round(width * min(percent, 100) / 100)
    return "█" * filled + "░" * (width - filled)


def stats(jd: JohnDecimal) -> dict:
    """Compute usage statistics for the library.

    Returns a dict with overall, per-area, and per-category stats.
    """
    total_areas = len(jd.areas)
    active_areas = sum(1 for a in jd.areas if a.categories)
    total_categories = len(jd.categories)
    total_identifiers = len(jd.identifiers)
    total_files = len(jd.files)

    max_categories = total_areas * 10
    max_identifiers = total_categories * 99 if total_categories else 0

    area_stats = []
    for area in jd.areas:
        cat_count = len(area.categories)
        id_count = sum(len(c.identifiers) for c in area.categories)
        file_count = sum(len(i.files) for c in area.categories for i in c.identifiers)
        area_stats.append({
            "name": str(area),
            "categories": cat_count,
            "category_capacity": round(cat_count / 10 * 100, 1),
            "identifiers": id_count,
            "files": file_count,
        })

    category_stats = []
    for category in jd.categories:
        id_count = len(category.identifiers)
        file_count = sum(len(i.files) for i in category.identifiers)
        category_stats.append({
            "name": str(category),
            "area": category.area,
            "identifiers": id_count,
            "identifier_capacity": round(id_count / 99 * 100, 1),
            "files": file_count,
        })

    deepest_category = max(jd.categories, key=lambda c: len(c.identifiers)).category_name if jd.categories else "N/A"
    busiest_area = max(jd.areas, key=lambda a: sum(len(c.identifiers) for c in a.categories)).area_name if jd.areas else "N/A"

    return {
        "total_areas": total_areas,
        "active_areas": active_areas,
        "total_categories": total_categories,
        "category_capacity": round(total_categories / max_categories * 100, 1) if max_categories else 0,
        "total_identifiers": total_identifiers,
        "identifier_capacity": round(total_identifiers / max_identifiers * 100, 1) if max_identifiers else 0,
        "total_files": total_files,
        "busiest_area": busiest_area,
        "deepest_category": deepest_category,
        "areas": area_stats,
        "categories": category_stats,
    }


def stats_cli(jd: JohnDecimal) -> str:
    """Return a formatted CLI string of library statistics."""
    s = stats(jd)
    lines = [
        "═══ JD Library Stats ═══",
        "",
        f"  Areas:        {s['active_areas']}/{s['total_areas']} active",
        f"  Categories:   {s['total_categories']}/{s['total_areas'] * 10} slots ({s['category_capacity']}%)",
        f"  Identifiers:  {s['total_identifiers']}",
        f"  Files:        {s['total_files']}",
        "",
        f"  Busiest area:     {s['busiest_area']}",
        f"  Fullest category: {s['deepest_category']}",
        "",
        "── Per Area ──",
    ]
    for a in s["areas"]:
        bar = _bar(a["category_capacity"])
        lines.append(f"  {a['name']:<30} {bar} {a['category_capacity']:5.1f}%  ({a['categories']} cats, {a['identifiers']} ids, {a['files']} files)")
    lines.append("")
    lines.append("── Per Category ──")
    for c in s["categories"]:
        bar = _bar(c["identifier_capacity"])
        lines.append(f"  {c['name']:<30} {bar} {c['identifier_capacity']:5.1f}%  ({c['identifiers']} ids, {c['files']} files)")
    return "\n".join(lines)
