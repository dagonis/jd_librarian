import argparse
import os
import sys
from pathlib import Path

from . import __version__
from .core import JohnDecimal
from .report import generate_report


def _validate_jd_root(path: str) -> None:
    """Exit with a helpful message if the JD root doesn't exist."""
    resolved = Path(path).expanduser()
    if not resolved.exists():
        print(f"Error: JD root does not exist: {resolved}", file=sys.stderr)
        print("Set JD_ROOT or pass --jd_root to a valid directory.", file=sys.stderr)
        sys.exit(1)
    if not resolved.is_dir():
        print(f"Error: JD root is not a directory: {resolved}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    # Top level argument parser
    parser = argparse.ArgumentParser(description="JD Librarian - A command line tool for managing Johnny Decimal libraries!")
    parser.add_argument("--version", "-V", action="version", version=f"jd-librarian {__version__}")
    parser.add_argument("--jd_root", 
                        help="The root of the Johnny Decimal library. This is can also be set with the environment variable JD_ROOT", 
                        default=os.getenv("JD_ROOT", "~/jd"))
    parser.add_argument("--dry_run", help="Don't actually do anything, just print what would happen", action="store_true")
    parser.add_argument("--stats", "-s", help="Print some stats about the Johnny Decimal library", action="store_true")
    parser.add_argument("--files", help="Include files when printing the tree", action="store_true")
    # Lets --dry_run also be passed after the subcommand (e.g. `jd add_id 11 Foo --dry_run`)
    dry_run_parent = argparse.ArgumentParser(add_help=False)
    dry_run_parent.add_argument("--dry_run", help="Don't actually do anything, just print what would happen",
                                action="store_true", default=argparse.SUPPRESS)
    subparsers = parser.add_subparsers(help="Johnny Decimal command help", dest="command")
    # Subparser for searching JD
    search_parser = subparsers.add_parser("search", help="Search Johnny Decimal")
    search_parser.add_argument("search_term", help="The search term to use")
    search_parser.add_argument("--include_category", "-c", help="Include the category in the search results", action="store_true")
    search_parser.add_argument("--include_files", "-f", help="Include the files in the search results", action="store_true")
    # Subparser for Showing a specific category
    show_category_parser = subparsers.add_parser("show", help="Show a specific Johnny Decimal category")
    show_category_parser.add_argument("category_id", help="The category ID to show")
    # Subparser for printing the folder path of a category or identifier
    path_parser = subparsers.add_parser("path", help="Print the folder path of a category or identifier (e.g. cd \"$(jd path 11.01)\")")
    path_parser.add_argument("jd_id", help="The category (11) or identifier (11.01) ID")
    # Subparser for adding JD Categories
    add_category_parser = subparsers.add_parser("add_category", parents=[dry_run_parent], help="Add a new Johnny Decimal category")
    add_category_parser.add_argument("area_id", help="The area ID to add the category to")
    add_category_parser.add_argument("new_category_name", help="The name of the new category to add")
    # Subparser for adding JD Identifiers
    add_identifier_parser = subparsers.add_parser("add_id", parents=[dry_run_parent], help="Add a new Johnny Decimal identifier")
    add_identifier_parser.add_argument("category_id", help="The category ID to add the identifier to")
    add_identifier_parser.add_argument("new_identifier_name", help="The name of the new identifier to add")
    add_identifier_parser.add_argument("--add_placeholder", "-p", help="Add a placeholder file for the new identifier. This is useful if you are using tools like Obsidian where you may want to link to this ID.", action="store_true")
    # Subparser for linting the JD library
    subparsers.add_parser("lint", help="Check the Johnny Decimal library for structural problems")
    # Subparser for scaffolding a new JD library
    scaffold_parser = subparsers.add_parser("scaffold", parents=[dry_run_parent], help="Create a new Johnny Decimal library from scratch")
    scaffold_parser.add_argument("target", help="Directory to create the new JD library in")
    scaffold_parser.add_argument("--mode", choices=["blank", "opinionated", "template"], default="blank",
                                 help="Scaffold mode: blank (default), opinionated, or template")
    scaffold_parser.add_argument("--template", dest="template_path", help="Path to template file (required for template mode)")
    # Subparser for stats
    subparsers.add_parser("stats", help="Show usage statistics for the Johnny Decimal library")
    # Subparser for HTML report
    report_parser = subparsers.add_parser("report", help="Generate an HTML report of the library")
    report_parser.add_argument("-o", "--output", default="jd_report.html", help="Output file path (default: jd_report.html)")
    # On to the rest of the script
    args = parser.parse_args()
    if args.command == "scaffold":
        created = JohnDecimal.scaffold(args.target, args.mode, args.template_path, args.dry_run)
        for path in created:
            print(f"{'Would create' if args.dry_run else 'Created'}: {path}")
        return
    _validate_jd_root(args.jd_root)
    if args.command == "lint":
        warnings = JohnDecimal.lint_from_path(args.jd_root)
        if warnings:
            for w in warnings:
                print(w)
        else:
            print("No issues found!")
        return
    jd = JohnDecimal(args.jd_root)
    if args.command == "stats":
        print(jd.stats_cli())
    elif args.command == "report":
        out = generate_report(jd, JohnDecimal.lint_from_path(args.jd_root), args.output)
        print(f"Report written to {out}")
    elif args.command == "search":
        print(jd.search_johnny_decimal(args.search_term, args.include_category, args.include_files))
    elif args.command == "add_category":
        if not jd.add_johnny_decimal_category(args.area_id, args.new_category_name, args.dry_run) and not args.dry_run:
            sys.exit(1)
    elif args.command == "add_id":
        if not jd.add_johnny_decimal_identifier(args.category_id, args.new_identifier_name, args.add_placeholder, args.dry_run) and not args.dry_run:
            sys.exit(1)
    elif args.command == "show":
        if "." in args.category_id:
            print(jd.get_johnny_decimal_identifier(args.category_id))
        else:
            print(jd.get_johnny_decimal_category(args.category_id))
    elif args.command == "path":
        path = jd.get_johnny_decimal_path(args.jd_id)
        if path is None:
            print(f"Error: nothing found for {args.jd_id}", file=sys.stderr)
            sys.exit(1)
        print(path)
    else:
        print(jd.print_johnny_decimal_tree(print_files=args.files, stats=args.stats))


if __name__ == "__main__":
    main()
