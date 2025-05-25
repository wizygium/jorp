import argparse
import sys
import os

# Add the parent directory of 'src' to sys.path to allow sibling imports
# when running this script directly for testing, though not strictly necessary if run as a module/package.
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# These relative imports are standard for execution as part of a package
# e.g., when running `python -m xshd_to_textmate.src.main ...`
from .xshd_parser import parse_xshd
from .textmate_generator import generate_textmate_grammar


def main_cli():
    """
    Command-line interface for the XSHD to TextMate converter.
    """
    parser = argparse.ArgumentParser(description="Convert .xshd syntax highlighting files to TextMate .JSON-tmLanguage grammar.")
    parser.add_argument("input_file", help="Path to the input .xshd file.")
    parser.add_argument("output_file", help="Path for the generated TextMate grammar JSON file (e.g., mylang.tmLanguage.json).")
    parser.add_argument(
        "-v", "--verbose", 
        action="store_true", 
        help="Enable verbose output."
    )

    args = parser.parse_args()

    if args.verbose:
        print(f"Starting conversion...")
        print(f"Input XSHD file: {args.input_file}")
        print(f"Output TextMate file: {args.output_file}")

    # Validate input file existence
    if not os.path.exists(args.input_file):
        print(f"Error: Input file not found: {args.input_file}")
        sys.exit(1)
    
    # Validate output file extension (optional, but good practice)
    if not args.output_file.endswith((".JSON-tmLanguage", ".tmLanguage.json", ".tmLanguage")):
        print(f"Warning: Output file '{args.output_file}' does not have a standard TextMate grammar extension (e.g., .tmLanguage.json).")


    if args.verbose:
        print("Parsing XSHD file...")
    
    xshd_data = parse_xshd(args.input_file)

    if not xshd_data:
        print(f"Failed to parse XSHD file: {args.input_file}")
        sys.exit(1)

    if args.verbose:
        print("XSHD parsing successful.")
        # Could print a summary of parsed_data if very verbose
        # print(f"Parsed language: {xshd_data.get('name')}")

    if args.verbose:
        print("Generating TextMate grammar...")

    generate_textmate_grammar(xshd_data, args.output_file)
    # generate_textmate_grammar already prints success/error, so no need to duplicate unless we want more CLI-specific messages.
    # We can assume if it returns without error, it was successful.
    # The generate_textmate_grammar function has its own print statements for success or failure.

    if args.verbose:
        print("Conversion process completed.")
    # A final success message from the CLI itself might be good.
    # print(f"TextMate grammar generated successfully at {args.output_file}") -> This is already in generate_textmate_grammar

if __name__ == "__main__":
    main_cli()
