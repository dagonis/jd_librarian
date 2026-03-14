import pytest
from pathlib import Path

from jd.core import JohnDecimal, Area, Category, Identifier, JohnnyDecimalFile, LintWarning


# ---------------------------------------------------------------------------
# Fixture: build a small JD library on disk
# ---------------------------------------------------------------------------

@pytest.fixture
def jd_root(tmp_path: Path) -> Path:
    """Create a minimal but realistic JD folder structure and return the root."""
    # Area: 10-19 Management
    area = tmp_path / "10-19 Management"
    area.mkdir()

    # Category: 11 Vendors
    cat_11 = area / "11 Vendors"
    cat_11.mkdir()
    (cat_11 / "01 Acme Corp").mkdir()
    (cat_11 / "02 Globex").mkdir()
    # Put a file inside an identifier
    id_01 = cat_11 / "01 Acme Corp"
    (id_01 / "contract.pdf").touch()
    (id_01 / "notes.md").touch()

    # Category: 12 Intelligence (empty — no identifiers)
    cat_12 = area / "12 Intelligence"
    cat_12.mkdir()

    # Area: 20-29 Projects
    area2 = tmp_path / "20-29 Projects"
    area2.mkdir()

    cat_20 = area2 / "20 Cloud"
    cat_20.mkdir()
    (cat_20 / "01 Cloud Logging").mkdir()

    # Hidden dir and file that should be ignored
    (tmp_path / ".hidden_area").mkdir()
    (cat_11 / ".hidden_id").mkdir()
    (id_01 / ".DS_Store").touch()

    return tmp_path


@pytest.fixture
def jd(jd_root: Path) -> JohnDecimal:
    """Return a JohnDecimal instance built from the test fixture."""
    return JohnDecimal(str(jd_root))


# ---------------------------------------------------------------------------
# Tests: hierarchy construction
# ---------------------------------------------------------------------------

class TestHierarchy:
    def test_areas_loaded(self, jd: JohnDecimal):
        assert len(jd.areas) == 2
        names = [a.area_short_name for a in jd.areas]
        assert names == ["Management", "Projects"]

    def test_categories_loaded(self, jd: JohnDecimal):
        assert len(jd.categories) == 3
        numbers = [c.category_number for c in jd.categories]
        assert "11" in numbers
        assert "12" in numbers
        assert "20" in numbers

    def test_identifiers_loaded(self, jd: JohnDecimal):
        assert len(jd.identifiers) == 3
        short_names = {i.short_name for i in jd.identifiers}
        assert short_names == {"Acme Corp", "Globex", "Cloud Logging"}

    def test_files_loaded(self, jd: JohnDecimal):
        file_names = {f.file_name for f in jd.files}
        assert file_names == {"contract.pdf", "notes.md"}

    def test_hidden_dirs_ignored(self, jd: JohnDecimal):
        all_area_names = [a.area_name for a in jd.areas]
        assert not any(".hidden" in n for n in all_area_names)

    def test_hidden_files_ignored(self, jd: JohnDecimal):
        all_file_names = [f.file_name for f in jd.files]
        assert ".DS_Store" not in all_file_names


# ---------------------------------------------------------------------------
# Tests: dataclass string representations
# ---------------------------------------------------------------------------

class TestStringRepresentations:
    def test_area_str(self, jd: JohnDecimal):
        area = jd.areas[0]
        assert str(area) == "[10-19] Management"

    def test_category_str(self, jd: JohnDecimal):
        cat = next(c for c in jd.categories if c.category_number == "11")
        assert str(cat) == "[11] Vendors"

    def test_identifier_str(self, jd: JohnDecimal):
        ident = next(i for i in jd.identifiers if i.short_name == "Acme Corp")
        assert str(ident) == "[11.01] Acme Corp"

    def test_identifier_fields(self, jd: JohnDecimal):
        ident = next(i for i in jd.identifiers if i.short_name == "Globex")
        assert ident.id_number == "02"
        assert ident.category == "11"


# ---------------------------------------------------------------------------
# Tests: search
# ---------------------------------------------------------------------------

class TestSearch:
    def test_search_finds_identifier(self, jd: JohnDecimal):
        result = jd.search_johnny_decimal("acme")
        assert "Acme Corp" in result

    def test_search_finds_category(self, jd: JohnDecimal):
        result = jd.search_johnny_decimal("vendors")
        assert "[11] Vendors" in result

    def test_search_case_insensitive(self, jd: JohnDecimal):
        result = jd.search_johnny_decimal("GLOBEX")
        assert "Globex" in result

    def test_search_no_results(self, jd: JohnDecimal):
        result = jd.search_johnny_decimal("nonexistent")
        assert "No results found" in result

    def test_search_include_files(self, jd: JohnDecimal):
        result = jd.search_johnny_decimal("contract", include_files=True)
        assert "contract.pdf" in result

    def test_search_without_category(self, jd: JohnDecimal):
        result = jd.search_johnny_decimal("acme", include_category=False)
        assert "->" not in result
        assert "Acme Corp" in result

    def test_search_with_category(self, jd: JohnDecimal):
        result = jd.search_johnny_decimal("acme", include_category=True)
        assert "->" in result


# ---------------------------------------------------------------------------
# Tests: tree printing
# ---------------------------------------------------------------------------

class TestTree:
    def test_tree_contains_all_levels(self, jd: JohnDecimal):
        tree = jd.print_johnny_decimal_tree()
        assert "[10-19] Management" in tree
        assert "[11] Vendors" in tree
        assert "[11.01] Acme Corp" in tree

    def test_tree_with_stats(self, jd: JohnDecimal):
        tree = jd.print_johnny_decimal_tree(stats=True)
        assert "Areas: 2" in tree
        assert "Categories: 3" in tree
        assert "Identifiers: 3" in tree

    def test_tree_with_files(self, jd: JohnDecimal):
        tree = jd.print_johnny_decimal_tree(print_files=True)
        assert "contract.pdf" in tree
        assert "notes.md" in tree

    def test_tree_without_files(self, jd: JohnDecimal):
        tree = jd.print_johnny_decimal_tree(print_files=False)
        assert "contract.pdf" not in tree

    def test_tree_tabs(self, jd: JohnDecimal):
        tree = jd.print_johnny_decimal_tree(tabs=True)
        assert "\t[11] Vendors" in tree


# ---------------------------------------------------------------------------
# Tests: show category / identifier
# ---------------------------------------------------------------------------

class TestShow:
    def test_get_category(self, jd: JohnDecimal):
        result = jd.get_johnny_decimal_category("11")
        assert "[11] Vendors" in result
        assert "[11.01] Acme Corp" in result
        assert "[11.02] Globex" in result

    def test_get_category_not_found(self, jd: JohnDecimal):
        result = jd.get_johnny_decimal_category("99")
        assert "No category found" in result

    def test_get_identifier(self, jd: JohnDecimal):
        result = jd.get_johnny_decimal_identifier("11.01")
        assert "Acme Corp" in result
        assert "contract.pdf" in result
        assert "notes.md" in result

    def test_get_identifier_not_found(self, jd: JohnDecimal):
        result = jd.get_johnny_decimal_identifier("99.99")
        assert "No identifier found" in result


# ---------------------------------------------------------------------------
# Tests: add category
# ---------------------------------------------------------------------------

class TestAddCategory:
    def test_add_category(self, jd: JohnDecimal, jd_root: Path):
        result = jd.add_johnny_decimal_category("10", "New Category")
        assert result is True
        # 11 and 12 exist, 10 is open so it gets the first available slot
        new_dir = jd_root / "10-19 Management" / "10 New Category"
        assert new_dir.is_dir()

    def test_add_category_dry_run(self, jd: JohnDecimal, jd_root: Path):
        result = jd.add_johnny_decimal_category("10", "Dry Run Cat", dry_run=True)
        assert result is False
        # Nothing should have been created
        dirs = list((jd_root / "10-19 Management").iterdir())
        dir_names = [d.name for d in dirs]
        assert "13 Dry Run Cat" not in dir_names

    def test_add_category_bad_area(self, jd: JohnDecimal):
        result = jd.add_johnny_decimal_category("90", "Won't Work")
        assert result is False


# ---------------------------------------------------------------------------
# Tests: add identifier
# ---------------------------------------------------------------------------

class TestAddIdentifier:
    def test_add_identifier(self, jd: JohnDecimal, jd_root: Path):
        result = jd.add_johnny_decimal_identifier("11", "New Vendor")
        assert result is True
        new_dir = jd_root / "10-19 Management" / "11 Vendors" / "03 New Vendor"
        assert new_dir.is_dir()

    def test_add_identifier_with_placeholder(self, jd: JohnDecimal, jd_root: Path):
        result = jd.add_johnny_decimal_identifier("11", "Placeholder Vendor", placeholder=True)
        assert result is True
        new_dir = jd_root / "10-19 Management" / "11 Vendors" / "03 Placeholder Vendor"
        assert new_dir.is_dir()
        assert (new_dir / "Placeholder Vendor.md").is_file()

    def test_add_identifier_dry_run(self, jd: JohnDecimal, jd_root: Path):
        result = jd.add_johnny_decimal_identifier("11", "Dry Run ID", dry_run=True)
        assert result is False
        new_dir = jd_root / "10-19 Management" / "11 Vendors" / "03 Dry Run ID"
        assert not new_dir.exists()

    def test_add_identifier_bad_category(self, jd: JohnDecimal):
        result = jd.add_johnny_decimal_identifier("99", "Won't Work")
        assert result is False

    def test_add_identifier_to_empty_category(self, jd: JohnDecimal, jd_root: Path):
        result = jd.add_johnny_decimal_identifier("12", "First Item")
        assert result is True
        new_dir = jd_root / "10-19 Management" / "12 Intelligence" / "01 First Item"
        assert new_dir.is_dir()


# ---------------------------------------------------------------------------
# Tests: CLI (end-to-end via subprocess)
# ---------------------------------------------------------------------------

class TestCLI:
    def test_cli_tree(self, jd_root: Path):
        import subprocess
        result = subprocess.run(
            ["jd", "--jd_root", str(jd_root)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "[10-19] Management" in result.stdout

    def test_cli_search(self, jd_root: Path):
        import subprocess
        result = subprocess.run(
            ["jd", "--jd_root", str(jd_root), "search", "acme"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "Acme Corp" in result.stdout

    def test_cli_show_category(self, jd_root: Path):
        import subprocess
        result = subprocess.run(
            ["jd", "--jd_root", str(jd_root), "show", "11"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "[11] Vendors" in result.stdout

    def test_cli_show_identifier(self, jd_root: Path):
        import subprocess
        result = subprocess.run(
            ["jd", "--jd_root", str(jd_root), "show", "11.01"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "Acme Corp" in result.stdout

    def test_cli_add_id(self, jd_root: Path):
        import subprocess
        result = subprocess.run(
            ["jd", "--jd_root", str(jd_root), "add_id", "20", "New Project"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert (jd_root / "20-29 Projects" / "20 Cloud" / "02 New Project").is_dir()

    def test_cli_add_id_dry_run(self, jd_root: Path):
        import subprocess
        result = subprocess.run(
            ["jd", "--jd_root", str(jd_root), "--dry_run", "add_id", "20", "Dry"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "Would have created" in result.stdout


# ---------------------------------------------------------------------------
# Tests: lint
# ---------------------------------------------------------------------------

class TestLint:
    def test_clean_library_has_no_high_severity_warnings(self, jd: JohnDecimal):
        warnings = jd.lint()
        high_severity = [w for w in warnings if w.rule in ("duplicate_category", "duplicate_id", "category_out_of_range", "bad_naming")]
        assert high_severity == []

    def test_duplicate_category_number(self, tmp_path: Path):
        area = tmp_path / "10-19 Management"
        area.mkdir()
        (area / "11 Vendors").mkdir()
        (area / "11 Also Vendors").mkdir()
        jd = JohnDecimal(str(tmp_path))
        warnings = jd.lint()
        rules = [w.rule for w in warnings]
        assert "duplicate_category" in rules

    def test_duplicate_identifier_number(self, tmp_path: Path):
        area = tmp_path / "10-19 Management"
        area.mkdir()
        cat = area / "11 Vendors"
        cat.mkdir()
        (cat / "01 Acme").mkdir()
        (cat / "01 Also Acme").mkdir()
        jd = JohnDecimal(str(tmp_path))
        warnings = jd.lint()
        rules = [w.rule for w in warnings]
        assert "duplicate_id" in rules

    def test_category_out_of_range(self, tmp_path: Path):
        area = tmp_path / "10-19 Management"
        area.mkdir()
        (area / "25 Wrong Place").mkdir()
        jd = JohnDecimal(str(tmp_path))
        warnings = jd.lint()
        rules = [w.rule for w in warnings]
        assert "category_out_of_range" in rules

    def test_bad_area_naming(self, tmp_path: Path):
        (tmp_path / "Management").mkdir()
        warnings = JohnDecimal.lint_from_path(str(tmp_path))
        rules = [w.rule for w in warnings]
        assert "bad_naming" in rules

    def test_bad_category_naming(self, tmp_path: Path):
        area = tmp_path / "10-19 Management"
        area.mkdir()
        (area / "Vendors").mkdir()
        warnings = JohnDecimal.lint_from_path(str(tmp_path))
        rules = [w.rule for w in warnings]
        assert "bad_naming" in rules

    def test_bad_identifier_naming(self, tmp_path: Path):
        area = tmp_path / "10-19 Management"
        area.mkdir()
        cat = area / "11 Vendors"
        cat.mkdir()
        (cat / "Acme Corp").mkdir()
        warnings = JohnDecimal.lint_from_path(str(tmp_path))
        rules = [w.rule for w in warnings]
        assert "bad_naming" in rules

    def test_lint_warning_str(self):
        w = LintWarning("duplicate_id", "test message", Path("/tmp"))
        assert str(w) == "[duplicate_id] test message"

    def test_multiple_issues(self, tmp_path: Path):
        area = tmp_path / "10-19 Management"
        area.mkdir()
        (area / "11 Vendors").mkdir()
        (area / "11 Also Vendors").mkdir()
        (area / "25 Out of Range").mkdir()
        jd = JohnDecimal(str(tmp_path))
        warnings = jd.lint()
        rules = {w.rule for w in warnings}
        assert "duplicate_category" in rules
        assert "category_out_of_range" in rules

    def test_empty_category(self, tmp_path: Path):
        area = tmp_path / "10-19 Management"
        area.mkdir()
        (area / "11 Vendors").mkdir()  # no identifiers inside
        jd = JohnDecimal(str(tmp_path))
        warnings = jd.lint()
        rules = [w.rule for w in warnings]
        assert "empty_category" in rules

    def test_empty_category_not_flagged_when_has_ids(self, jd: JohnDecimal):
        warnings = jd.lint()
        # The fixture's "12 Intelligence" is empty, so it should be flagged
        empty_cats = [w for w in warnings if w.rule == "empty_category"]
        cat_names = [w.message for w in empty_cats]
        assert any("Intelligence" in m for m in cat_names)
        # But "11 Vendors" should NOT be flagged
        assert not any("Vendors" in m for m in cat_names)

    def test_empty_identifier(self, tmp_path: Path):
        area = tmp_path / "10-19 Management"
        area.mkdir()
        cat = area / "11 Vendors"
        cat.mkdir()
        (cat / "01 Acme").mkdir()  # no files inside
        jd = JohnDecimal(str(tmp_path))
        warnings = jd.lint()
        rules = [w.rule for w in warnings]
        assert "empty_identifier" in rules

    def test_empty_identifier_not_flagged_when_has_files(self, jd: JohnDecimal):
        warnings = jd.lint()
        empty_ids = [w for w in warnings if w.rule == "empty_identifier"]
        # Acme Corp has files, so it should NOT be flagged
        assert not any("Acme Corp" in w.message for w in empty_ids)

    def test_id_gaps(self, tmp_path: Path):
        area = tmp_path / "10-19 Management"
        area.mkdir()
        cat = area / "11 Vendors"
        cat.mkdir()
        (cat / "01 Acme").mkdir()
        (cat / "03 Globex").mkdir()  # gap at 02
        jd = JohnDecimal(str(tmp_path))
        warnings = jd.lint()
        gap_warnings = [w for w in warnings if w.rule == "id_gap"]
        assert len(gap_warnings) == 1
        assert "02" in gap_warnings[0].message

    def test_no_id_gaps_when_contiguous(self, tmp_path: Path):
        area = tmp_path / "10-19 Management"
        area.mkdir()
        cat = area / "11 Vendors"
        cat.mkdir()
        (cat / "01 Acme").mkdir()
        (cat / "02 Globex").mkdir()
        jd = JohnDecimal(str(tmp_path))
        warnings = jd.lint()
        gap_warnings = [w for w in warnings if w.rule == "id_gap"]
        assert len(gap_warnings) == 0

    def test_category_capacity_warning(self, tmp_path: Path):
        area = tmp_path / "10-19 Management"
        area.mkdir()
        cat = area / "11 Vendors"
        cat.mkdir()
        # Create 80 identifiers to hit the threshold
        for i in range(1, 81):
            (cat / f"{str(i).zfill(2)} Vendor{i}").mkdir()
        jd = JohnDecimal(str(tmp_path))
        warnings = jd.lint()
        rules = [w.rule for w in warnings]
        assert "category_capacity" in rules

    def test_category_capacity_no_warning_below_threshold(self, tmp_path: Path):
        area = tmp_path / "10-19 Management"
        area.mkdir()
        cat = area / "11 Vendors"
        cat.mkdir()
        for i in range(1, 5):
            (cat / f"{str(i).zfill(2)} Vendor{i}").mkdir()
        jd = JohnDecimal(str(tmp_path))
        warnings = jd.lint()
        cap_warnings = [w for w in warnings if w.rule == "category_capacity"]
        assert len(cap_warnings) == 0

    def test_area_capacity_warning(self, tmp_path: Path):
        area = tmp_path / "10-19 Management"
        area.mkdir()
        # Create 8 categories to hit the threshold
        for i in range(10, 18):
            (area / f"{i} Category{i}").mkdir()
        jd = JohnDecimal(str(tmp_path))
        warnings = jd.lint()
        rules = [w.rule for w in warnings]
        assert "area_capacity" in rules

    def test_area_capacity_no_warning_below_threshold(self, tmp_path: Path):
        area = tmp_path / "10-19 Management"
        area.mkdir()
        (area / "11 Vendors").mkdir()
        (area / "12 Intel").mkdir()
        jd = JohnDecimal(str(tmp_path))
        warnings = jd.lint()
        cap_warnings = [w for w in warnings if w.rule == "area_capacity"]
        assert len(cap_warnings) == 0

    def test_orphan_file_at_root(self, tmp_path: Path):
        area = tmp_path / "10-19 Management"
        area.mkdir()
        (tmp_path / "stray_file.txt").touch()
        jd = JohnDecimal(str(tmp_path))
        warnings = jd.lint()
        orphan_warnings = [w for w in warnings if w.rule == "orphan_file"]
        assert any("stray_file.txt" in w.message for w in orphan_warnings)

    def test_orphan_file_in_area(self, tmp_path: Path):
        area = tmp_path / "10-19 Management"
        area.mkdir()
        (area / "notes.txt").touch()
        jd = JohnDecimal(str(tmp_path))
        warnings = jd.lint()
        orphan_warnings = [w for w in warnings if w.rule == "orphan_file"]
        assert any("notes.txt" in w.message for w in orphan_warnings)

    def test_orphan_file_in_category(self, tmp_path: Path):
        area = tmp_path / "10-19 Management"
        area.mkdir()
        cat = area / "11 Vendors"
        cat.mkdir()
        (cat / "README.md").touch()
        jd = JohnDecimal(str(tmp_path))
        warnings = jd.lint()
        orphan_warnings = [w for w in warnings if w.rule == "orphan_file"]
        assert any("README.md" in w.message for w in orphan_warnings)
        assert "should be inside an identifier" in orphan_warnings[0].message

    def test_no_orphan_files_in_clean_library(self, jd: JohnDecimal):
        warnings = jd.lint()
        orphan_warnings = [w for w in warnings if w.rule == "orphan_file"]
        assert len(orphan_warnings) == 0


class TestLintCLI:
    def test_cli_lint_runs(self, jd_root: Path):
        import subprocess
        result = subprocess.run(
            ["jd", "--jd_root", str(jd_root), "lint"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0

    def test_cli_lint_with_issues(self, tmp_path: Path):
        import subprocess
        area = tmp_path / "10-19 Management"
        area.mkdir()
        (area / "11 Vendors").mkdir()
        (area / "11 Also Vendors").mkdir()
        result = subprocess.run(
            ["jd", "--jd_root", str(tmp_path), "lint"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "duplicate_category" in result.stdout


# ---------------------------------------------------------------------------
# Scaffold tests
# ---------------------------------------------------------------------------

_ALL_AREA_LABELS = [
    "00-09", "10-19", "20-29", "30-39", "40-49",
    "50-59", "60-69", "70-79", "80-89", "90-99",
]


class TestScaffoldBlank:
    def test_creates_ten_unused_areas(self, tmp_path: Path):
        target = tmp_path / "my_jd"
        created = JohnDecimal.scaffold(str(target), mode="blank")
        dirs = sorted(p.name for p in target.iterdir())
        assert len(dirs) == 10
        assert all("Unused" in d for d in dirs)

    def test_area_labels_are_correct(self, tmp_path: Path):
        target = tmp_path / "my_jd"
        JohnDecimal.scaffold(str(target), mode="blank")
        dirs = sorted(p.name for p in target.iterdir())
        for label, dirname in zip(_ALL_AREA_LABELS, dirs):
            assert dirname.startswith(label)

    def test_no_categories_created(self, tmp_path: Path):
        target = tmp_path / "my_jd"
        JohnDecimal.scaffold(str(target), mode="blank")
        for area_dir in target.iterdir():
            assert list(area_dir.iterdir()) == []

    def test_returns_created_paths(self, tmp_path: Path):
        target = tmp_path / "my_jd"
        created = JohnDecimal.scaffold(str(target), mode="blank")
        assert len(created) == 10
        assert all(Path(p).exists() for p in created)

    def test_resulting_library_is_valid(self, tmp_path: Path):
        target = tmp_path / "my_jd"
        JohnDecimal.scaffold(str(target), mode="blank")
        jd = JohnDecimal(str(target))
        assert len(jd.areas) == 10
        assert len(jd.categories) == 0


class TestScaffoldOpinionated:
    def test_creates_ten_areas(self, tmp_path: Path):
        target = tmp_path / "my_jd"
        JohnDecimal.scaffold(str(target), mode="opinionated")
        dirs = sorted(p.name for p in target.iterdir())
        assert len(dirs) == 10

    def test_admin_and_testing_named(self, tmp_path: Path):
        target = tmp_path / "my_jd"
        JohnDecimal.scaffold(str(target), mode="opinionated")
        names = {p.name for p in target.iterdir()}
        assert "00-09 Admin" in names
        assert "90-99 Testing" in names

    def test_remaining_areas_unused(self, tmp_path: Path):
        target = tmp_path / "my_jd"
        JohnDecimal.scaffold(str(target), mode="opinionated")
        for p in target.iterdir():
            if not p.name.startswith("00-09") and not p.name.startswith("90-99"):
                assert "Unused" in p.name

    def test_resulting_library_is_valid(self, tmp_path: Path):
        target = tmp_path / "my_jd"
        JohnDecimal.scaffold(str(target), mode="opinionated")
        jd = JohnDecimal(str(target))
        assert len(jd.areas) == 10


class TestScaffoldTemplate:
    TEMPLATE = (
        "00-09 Admin\n"
        "  00 Index\n"
        "  01 Homepage\n"
        "10-19 Projects\n"
        "  10 Active\n"
        "20-29 People\n"
    )

    def _write_template(self, tmp_path: Path) -> Path:
        tpl = tmp_path / "template.txt"
        tpl.write_text(self.TEMPLATE)
        return tpl

    def test_creates_areas_from_template(self, tmp_path: Path):
        tpl = self._write_template(tmp_path)
        target = tmp_path / "my_jd"
        JohnDecimal.scaffold(str(target), mode="template", template_path=str(tpl))
        names = {p.name for p in target.iterdir()}
        assert "00-09 Admin" in names
        assert "10-19 Projects" in names
        assert "20-29 People" in names

    def test_fills_missing_areas_as_unused(self, tmp_path: Path):
        tpl = self._write_template(tmp_path)
        target = tmp_path / "my_jd"
        JohnDecimal.scaffold(str(target), mode="template", template_path=str(tpl))
        dirs = sorted(p.name for p in target.iterdir())
        assert len(dirs) == 10
        assert "30-39 Unused" in {p.name for p in target.iterdir()}

    def test_creates_categories(self, tmp_path: Path):
        tpl = self._write_template(tmp_path)
        target = tmp_path / "my_jd"
        JohnDecimal.scaffold(str(target), mode="template", template_path=str(tpl))
        admin = target / "00-09 Admin"
        cats = sorted(p.name for p in admin.iterdir())
        assert cats == ["00 Index", "01 Homepage"]

    def test_returns_area_and_category_paths(self, tmp_path: Path):
        tpl = self._write_template(tmp_path)
        target = tmp_path / "my_jd"
        created = JohnDecimal.scaffold(str(target), mode="template", template_path=str(tpl))
        # 10 areas + 3 categories (00 Index, 01 Homepage, 10 Active)
        assert len(created) == 13
        assert all(Path(p).exists() for p in created)

    def test_resulting_library_is_valid(self, tmp_path: Path):
        tpl = self._write_template(tmp_path)
        target = tmp_path / "my_jd"
        JohnDecimal.scaffold(str(target), mode="template", template_path=str(tpl))
        jd = JohnDecimal(str(target))
        assert len(jd.areas) == 10
        assert len(jd.categories) == 3

    def test_template_mode_requires_path(self, tmp_path: Path):
        target = tmp_path / "my_jd"
        with pytest.raises(ValueError, match="template mode requires"):
            JohnDecimal.scaffold(str(target), mode="template")

    def test_empty_lines_ignored(self, tmp_path: Path):
        tpl = tmp_path / "template.txt"
        tpl.write_text("00-09 Admin\n\n  00 Index\n\n10-19 Projects\n")
        target = tmp_path / "my_jd"
        JohnDecimal.scaffold(str(target), mode="template", template_path=str(tpl))
        jd = JohnDecimal(str(target))
        assert len(jd.categories) == 1  # Just "00 Index"


class TestScaffoldDryRun:
    def test_dry_run_returns_paths_but_creates_nothing(self, tmp_path: Path):
        target = tmp_path / "my_jd"
        created = JohnDecimal.scaffold(str(target), mode="blank", dry_run=True)
        assert len(created) == 10
        assert not target.exists()

    def test_dry_run_template_returns_categories(self, tmp_path: Path):
        tpl = tmp_path / "template.txt"
        tpl.write_text("00-09 Admin\n  00 Index\n")
        target = tmp_path / "my_jd"
        created = JohnDecimal.scaffold(str(target), mode="template", template_path=str(tpl), dry_run=True)
        assert len(created) == 11  # 10 areas + 1 category
        assert not target.exists()


class TestScaffoldCLI:
    def test_cli_scaffold_blank(self, tmp_path: Path):
        import subprocess
        target = tmp_path / "my_jd"
        result = subprocess.run(
            ["jd", "scaffold", str(target)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "Created:" in result.stdout
        assert target.exists()
        assert len(list(target.iterdir())) == 10

    def test_cli_scaffold_opinionated(self, tmp_path: Path):
        import subprocess
        target = tmp_path / "my_jd"
        result = subprocess.run(
            ["jd", "scaffold", str(target), "--mode", "opinionated"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "Admin" in result.stdout

    def test_cli_scaffold_template(self, tmp_path: Path):
        import subprocess
        tpl = tmp_path / "template.txt"
        tpl.write_text("00-09 Admin\n  00 Index\n")
        target = tmp_path / "my_jd"
        result = subprocess.run(
            ["jd", "scaffold", str(target), "--mode", "template", "--template", str(tpl)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert (target / "00-09 Admin" / "00 Index").exists()

    def test_cli_scaffold_dry_run(self, tmp_path: Path):
        import subprocess
        target = tmp_path / "my_jd"
        result = subprocess.run(
            ["jd", "--dry_run", "scaffold", str(target)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "Would create:" in result.stdout
        assert not target.exists()


class TestScaffoldYAMLTemplate:
    YAML_TEMPLATE = (
        "00-09 Admin:\n"
        "  - 00 Index\n"
        "  - 01 Homepage\n"
        "10-19 Projects:\n"
        "  - 10 Active\n"
        "20-29 People:\n"
    )

    def _write_template(self, tmp_path: Path, ext: str = ".yaml") -> Path:
        tpl = tmp_path / f"template{ext}"
        tpl.write_text(self.YAML_TEMPLATE)
        return tpl

    def test_creates_areas_from_yaml(self, tmp_path: Path):
        tpl = self._write_template(tmp_path)
        target = tmp_path / "my_jd"
        JohnDecimal.scaffold(str(target), mode="template", template_path=str(tpl))
        names = {p.name for p in target.iterdir()}
        assert "00-09 Admin" in names
        assert "10-19 Projects" in names
        assert "20-29 People" in names

    def test_creates_categories_from_yaml(self, tmp_path: Path):
        tpl = self._write_template(tmp_path)
        target = tmp_path / "my_jd"
        JohnDecimal.scaffold(str(target), mode="template", template_path=str(tpl))
        admin = target / "00-09 Admin"
        cats = sorted(p.name for p in admin.iterdir())
        assert cats == ["00 Index", "01 Homepage"]

    def test_fills_missing_areas_as_unused(self, tmp_path: Path):
        tpl = self._write_template(tmp_path)
        target = tmp_path / "my_jd"
        JohnDecimal.scaffold(str(target), mode="template", template_path=str(tpl))
        dirs = sorted(p.name for p in target.iterdir())
        assert len(dirs) == 10
        assert "30-39 Unused" in {p.name for p in target.iterdir()}

    def test_yml_extension_works(self, tmp_path: Path):
        tpl = self._write_template(tmp_path, ext=".yml")
        target = tmp_path / "my_jd"
        JohnDecimal.scaffold(str(target), mode="template", template_path=str(tpl))
        assert (target / "00-09 Admin" / "00 Index").exists()

    def test_area_with_no_categories(self, tmp_path: Path):
        tpl = tmp_path / "template.yaml"
        tpl.write_text("00-09 Admin:\n20-29 People:\n")
        target = tmp_path / "my_jd"
        JohnDecimal.scaffold(str(target), mode="template", template_path=str(tpl))
        assert (target / "00-09 Admin").exists()
        assert list((target / "00-09 Admin").iterdir()) == []

    def test_resulting_library_is_valid(self, tmp_path: Path):
        tpl = self._write_template(tmp_path)
        target = tmp_path / "my_jd"
        JohnDecimal.scaffold(str(target), mode="template", template_path=str(tpl))
        jd = JohnDecimal(str(target))
        assert len(jd.areas) == 10
        assert len(jd.categories) == 3

    def test_invalid_yaml_raises(self, tmp_path: Path):
        tpl = tmp_path / "bad.yaml"
        tpl.write_text("- just a list\n- not a mapping\n")
        target = tmp_path / "my_jd"
        with pytest.raises(ValueError, match="must be a mapping"):
            JohnDecimal.scaffold(str(target), mode="template", template_path=str(tpl))

    def test_cli_scaffold_yaml_template(self, tmp_path: Path):
        import subprocess
        tpl = self._write_template(tmp_path)
        target = tmp_path / "my_jd"
        result = subprocess.run(
            ["jd", "scaffold", str(target), "--mode", "template", "--template", str(tpl)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert (target / "00-09 Admin" / "00 Index").exists()
