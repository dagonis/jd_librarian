import argparse
import os

from .core import JohnDecimal

def main() -> None:
    # Top level argument parser
    parser = argparse.ArgumentParser(description="JD Librarian - A command line tool for managing Johnny Decimal libraries!")
    parser.add_argument("--jd_root", 
                        help="The root of the Johnny Decimal library. This is can also be set with the environment variable JD_ROOT", 
                        default=os.getenv("JD_ROOT", "~/jd"))
    parser.add_argument("--dry_run", help="Don't actually do anything, just print what would happen", action="store_true")
    parser.add_argument("--stats", "-s", help="Print some stats about the Johnny Decimal library", action="store_true")
    subparsers = parser.add_subparsers(help="Johnny Decimal command help", dest="command")
    # Subparser for searching JD
    search_parser = subparsers.add_parser("search", help="Search Johnny Decimal")
    search_parser.add_argument("search_term", help="The search term to use")
    search_parser.add_argument("--include_category", "-c", help="Include the category in the search results", action="store_true")
    search_parser.add_argument("--include_files", "-f", help="Include the files in the search results", action="store_true")
    # Subparser for Showing a specific category
    show_category_parser = subparsers.add_parser("show", help="Show a specific Johnny Decimal category")
    show_category_parser.add_argument("category_id", help="The category ID to show")
    # Subparser for adding JD Categories
    add_category_parser = subparsers.add_parser("add_category", help="Add a new Johnny Decimal category")
    add_category_parser.add_argument("area_id", help="The area ID to add the category to")
    add_category_parser.add_argument("new_category_name", help="The name of the new category to add")
    # Subparser for adding JD Identifiers
    add_identifier_parser = subparsers.add_parser("add_id", help="Add a new Johnny Decimal identifier")
    add_identifier_parser.add_argument("category_id", help="The category ID to add the identifier to")
    add_identifier_parser.add_argument("new_identifier_name", help="The name of the new identifier to add")
    add_identifier_parser.add_argument("--add_placeholder", "-p", help="Add a placeholder file for the new identifier. This is useful if you are using tools like Obsidian where you may want to link to this ID.", action="store_true")
    # Subparser for linting the JD library
    subparsers.add_parser("lint", help="Check the Johnny Decimal library for structural problems")
    # On to the rest of the script
    args = parser.parse_args()
    if args.command == "lint":
        warnings = JohnDecimal.lint_from_path(args.jd_root)
        if warnings:
            for w in warnings:
                print(w)
        else:
            print("No issues found!")
        return
    jd = JohnDecimal(args.jd_root)
    if hasattr(args, 'search_term'):
        print(jd.search_johnny_decimal(args.search_term, args.include_category, args.include_files))
    elif hasattr(args, 'new_category_name'):
        jd.add_johnny_decimal_category(args.area_id, args.new_category_name, args.dry_run)
    elif hasattr(args, 'new_identifier_name'):
        jd.add_johnny_decimal_identifier(args.category_id, args.new_identifier_name, args.add_placeholder, args.dry_run)
    elif hasattr(args, 'category_id'):
        if "." not in args.category_id:
            print(jd.get_johnny_decimal_category(args.category_id))
        elif "." in args.category_id:
            print(jd.get_johnny_decimal_identifier(args.category_id))
    else:
        print(jd.print_johnny_decimal_tree(stats=args.stats))


if __name__ == '__main__':
    main()