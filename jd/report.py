"""Generate a self-contained HTML report for a Johnny Decimal library."""

from __future__ import annotations

import html
from datetime import datetime, timezone
from pathlib import Path

from .core import JohnDecimal
from .models import LintWarning


def generate_report(jd: JohnDecimal, warnings: list[LintWarning], output_path: str) -> str:
    """Build and write a cyberpunk-themed HTML report. Returns the output path."""
    stats = jd.stats()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    area_rows = ""
    for a in stats["areas"]:
        pct = a["category_capacity"]
        area_rows += _row(a["name"], pct, f'{a["categories"]} cats, {a["identifiers"]} ids, {a["files"]} files')

    cat_rows = ""
    for c in stats["categories"]:
        pct = c["identifier_capacity"]
        cat_rows += _row(c["name"], pct, f'{c["identifiers"]} ids, {c["files"]} files')

    lint_rows = ""
    if warnings:
        for w in warnings:
            severity = _severity_class(w.rule)
            lint_rows += f'<tr><td class="{severity}">{_esc(w.rule)}</td><td>{_esc(w.message)}</td></tr>\n'
    else:
        lint_rows = '<tr><td colspan="2" class="ok">✓ No issues found</td></tr>'

    lint_class = "clean" if not warnings else ("error" if len(warnings) > 5 else "warn")

    report = _TEMPLATE.format(
        timestamp=now,
        total_areas=stats["total_areas"],
        active_areas=stats["active_areas"],
        total_categories=stats["total_categories"],
        max_categories=stats["total_areas"] * 10,
        category_pct=stats["category_capacity"],
        total_identifiers=stats["total_identifiers"],
        identifier_pct=stats["identifier_capacity"],
        total_files=stats["total_files"],
        busiest_area=_esc(stats["busiest_area"]),
        deepest_category=_esc(stats["deepest_category"]),
        lint_count=len(warnings),
        lint_class=lint_class,
        area_rows=area_rows,
        category_rows=cat_rows,
        lint_rows=lint_rows,
        overall_bar=_html_bar(stats["category_capacity"]),
        id_bar=_html_bar(stats["identifier_capacity"]),
    )

    out = Path(output_path)
    out.write_text(report)
    return str(out.resolve())


def _esc(text: str) -> str:
    return html.escape(str(text))


def _severity_class(rule: str) -> str:
    high = {"bad_naming", "duplicate_category", "duplicate_id", "category_out_of_range"}
    medium = {"empty_category", "empty_identifier", "id_gap"}
    if rule in high:
        return "severity-high"
    if rule in medium:
        return "severity-medium"
    return "severity-low"


def _html_bar(pct: float) -> str:
    clamped = min(pct, 100)
    color = "#0ff" if clamped < 60 else "#ff0" if clamped < 85 else "#f0a"
    return f'<div class="bar"><div class="bar-fill" style="width:{clamped}%;background:{color}"></div><span class="bar-label">{pct:.1f}%</span></div>'


def _row(name: str, pct: float, detail: str) -> str:
    clamped = min(pct, 100)
    color = "#0ff" if clamped < 60 else "#ff0" if clamped < 85 else "#f0a"
    return (
        f'<tr><td class="name">{_esc(name)}</td>'
        f'<td><div class="bar"><div class="bar-fill" style="width:{clamped}%;background:{color}"></div>'
        f'<span class="bar-label">{pct:.1f}%</span></div></td>'
        f'<td class="detail">{_esc(detail)}</td></tr>\n'
    )


_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>JD Librarian // System Report</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Orbitron:wght@400;700&display=swap');

  :root {{
    --bg: #0a0a0f;
    --surface: #12121a;
    --border: #1a1a2e;
    --cyan: #0ff;
    --magenta: #f0a;
    --yellow: #ff0;
    --text: #c8c8d0;
    --dim: #8888a0;
  }}

  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  body {{
    background: var(--bg);
    color: var(--text);
    font-family: 'Share Tech Mono', monospace;
    line-height: 1.6;
    min-height: 100vh;
  }}

  /* scanline overlay */
  body::after {{
    content: '';
    position: fixed;
    inset: 0;
    background: repeating-linear-gradient(
      0deg,
      transparent,
      transparent 2px,
      rgba(0, 255, 255, 0.015) 2px,
      rgba(0, 255, 255, 0.015) 4px
    );
    pointer-events: none;
    z-index: 999;
  }}

  .container {{
    max-width: 1100px;
    margin: 0 auto;
    padding: 2rem 1.5rem;
  }}

  header {{
    text-align: center;
    margin-bottom: 3rem;
    position: relative;
  }}

  header h1 {{
    font-family: 'Orbitron', sans-serif;
    font-size: 2.2rem;
    color: var(--cyan);
    text-shadow: 0 0 20px rgba(0, 255, 255, 0.5), 0 0 40px rgba(0, 255, 255, 0.2);
    letter-spacing: 0.1em;
  }}

  header .subtitle {{
    color: var(--dim);
    font-size: 0.85rem;
    margin-top: 0.5rem;
  }}

  header .timestamp {{
    color: var(--magenta);
    font-size: 0.75rem;
    margin-top: 0.3rem;
  }}

  .grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    margin-bottom: 2rem;
  }}

  .card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 1.2rem;
    position: relative;
    overflow: hidden;
  }}

  .card::before {{
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--cyan), var(--magenta));
  }}

  .card .label {{
    font-size: 0.7rem;
    color: var(--dim);
    text-transform: uppercase;
    letter-spacing: 0.15em;
  }}

  .card .value {{
    font-family: 'Orbitron', sans-serif;
    font-size: 1.8rem;
    color: var(--cyan);
    text-shadow: 0 0 10px rgba(0, 255, 255, 0.3);
    margin-top: 0.3rem;
  }}

  .card .meta {{
    font-size: 0.75rem;
    color: var(--dim);
    margin-top: 0.2rem;
  }}

  section {{
    margin-bottom: 2.5rem;
  }}

  section h2 {{
    font-family: 'Orbitron', sans-serif;
    font-size: 1.1rem;
    color: var(--magenta);
    text-shadow: 0 0 10px rgba(255, 0, 170, 0.3);
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.5rem;
    margin-bottom: 1rem;
    letter-spacing: 0.08em;
  }}

  table {{
    width: 100%;
    border-collapse: collapse;
  }}

  th {{
    text-align: left;
    font-size: 0.7rem;
    color: var(--dim);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    padding: 0.5rem 0.8rem;
    border-bottom: 1px solid var(--border);
  }}

  td {{
    padding: 0.5rem 0.8rem;
    border-bottom: 1px solid rgba(26, 26, 46, 0.5);
    font-size: 0.85rem;
  }}

  tr:hover td {{
    background: rgba(0, 255, 255, 0.03);
  }}

  .name {{ color: var(--cyan); white-space: nowrap; }}
  .detail {{ color: var(--dim); font-size: 0.8rem; }}

  .bar {{
    position: relative;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 2px;
    height: 22px;
    min-width: 150px;
    overflow: hidden;
  }}

  .bar-fill {{
    height: 100%;
    border-radius: 2px;
    transition: width 0.5s ease;
    box-shadow: 0 0 8px currentColor;
  }}

  .bar-label {{
    position: absolute;
    right: 6px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 0.7rem;
    color: var(--text);
    text-shadow: 0 0 4px var(--bg);
  }}

  /* Lint severity */
  .severity-high {{ color: #f44; font-weight: bold; }}
  .severity-medium {{ color: var(--yellow); }}
  .severity-low {{ color: var(--dim); }}
  .ok {{ color: var(--cyan); text-align: center; padding: 1rem; }}

  .lint-count {{
    display: inline-block;
    padding: 0.15rem 0.6rem;
    border-radius: 3px;
    font-size: 0.8rem;
    margin-left: 0.5rem;
  }}

  .lint-count.clean {{ background: rgba(0,255,255,0.15); color: var(--cyan); }}
  .lint-count.warn {{ background: rgba(255,255,0,0.15); color: var(--yellow); }}
  .lint-count.error {{ background: rgba(255,0,170,0.15); color: var(--magenta); }}

  footer {{
    text-align: center;
    padding: 2rem 0 1rem;
    border-top: 1px solid var(--border);
    font-size: 0.75rem;
    color: var(--dim);
  }}

  footer a {{
    color: var(--cyan);
    text-decoration: none;
  }}

  footer a:hover {{
    text-shadow: 0 0 8px var(--cyan);
  }}

  /* Glow pulse on header */
  @keyframes pulse {{
    0%, 100% {{ opacity: 1; }}
    50% {{ opacity: 0.7; }}
  }}

  header h1 {{
    animation: pulse 4s ease-in-out infinite;
  }}
</style>
</head>
<body>
<div class="container">

<header>
  <h1>JD LIBRARIAN</h1>
  <div class="subtitle">// SYSTEM REPORT</div>
  <div class="timestamp">Generated {timestamp}</div>
</header>

<div class="grid">
  <div class="card">
    <div class="label">Areas</div>
    <div class="value">{active_areas}/{total_areas}</div>
    <div class="meta">active</div>
  </div>
  <div class="card">
    <div class="label">Categories</div>
    <div class="value">{total_categories}</div>
    <div class="meta">{category_pct}% of {max_categories} slots</div>
  </div>
  <div class="card">
    <div class="label">Identifiers</div>
    <div class="value">{total_identifiers}</div>
    <div class="meta">{identifier_pct}% avg capacity</div>
  </div>
  <div class="card">
    <div class="label">Files</div>
    <div class="value">{total_files}</div>
    <div class="meta">total tracked</div>
  </div>
</div>

<div class="grid">
  <div class="card">
    <div class="label">Category Capacity</div>
    {overall_bar}
  </div>
  <div class="card">
    <div class="label">Identifier Capacity</div>
    {id_bar}
  </div>
  <div class="card">
    <div class="label">Busiest Area</div>
    <div class="meta" style="color:var(--cyan);margin-top:0.5rem;font-size:0.9rem">{busiest_area}</div>
  </div>
  <div class="card">
    <div class="label">Fullest Category</div>
    <div class="meta" style="color:var(--cyan);margin-top:0.5rem;font-size:0.9rem">{deepest_category}</div>
  </div>
</div>

<section>
  <h2>▸ Area Breakdown</h2>
  <table>
    <tr><th>Area</th><th>Capacity</th><th>Detail</th></tr>
    {area_rows}
  </table>
</section>

<section>
  <h2>▸ Category Breakdown</h2>
  <table>
    <tr><th>Category</th><th>Capacity</th><th>Detail</th></tr>
    {category_rows}
  </table>
</section>

<section>
  <h2>▸ Linter Report <span class="lint-count {lint_class}">{lint_count} findings</span></h2>
  <table>
    <tr><th>Rule</th><th>Message</th></tr>
    {lint_rows}
  </table>
</section>

</div>

<footer>
  <a href="https://github.com/dagonis/jd_librarian" target="_blank">⟁ github.com/dagonis/jd_librarian</a>
  &nbsp;&nbsp;•&nbsp;&nbsp; Powered by JD Librarian
</footer>

</body>
</html>
"""
