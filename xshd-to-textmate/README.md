# XSHD to TextMate Grammar Converter

## Description

This tool converts `.xshd` (XML Syntax Highlighting Definition) files, commonly used by text editors like Kate or a C# IDE (SharpDevelop/MonoDevelop), into TextMate `.JSON-tmLanguage` grammar files. These generated grammar files are compatible with a wide range of modern editors that support TextMate grammars, such as Visual Studio Code, Sublime Text, and others.

## Features

-   **Parses .xshd files**: Extracts syntax highlighting rules from the XML structure of `.xshd` files.
-   **Generates TextMate JSON grammars**: Outputs grammar definitions in the standard JSON format used by TextMate.
-   **Handles common syntax elements**:
    -   Keywords (grouped by categories defined in XSHD)
    -   Comments (both line and block comments)
    -   String literals (double-quoted, single-quoted)
    -   Numbers/Digits (basic recognition)
-   **Basic XSHD span support**: Translates other XSHD `Span` elements into TextMate `begin`/`end` patterns or `match` patterns, with heuristically determined scopes.
-   **Command-Line Interface**: Provides a CLI for easy conversion of files.

## Requirements

-   Python 3.x (specifically, 3.6 or newer due to f-string usage and dictionary iteration order). Standard libraries `xml.etree.ElementTree`, `json`, `argparse`, `os`, `sys`, `re`, `subprocess` are used.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository_url>
    cd xshd-to-textmate-converter # Or your chosen directory name
    ```
    (Replace `<repository_url>` with the actual URL of the repository).

2.  **Make the main script executable** (optional, for convenience):
    The primary script for running the converter is `run_converter.py` located in the project root.
    ```bash
    chmod +x run_converter.py
    ```

No external Python packages are required beyond the standard library.

## Usage

The converter is run using the `run_converter.py` script from the root directory of the project.

### Command Syntax:

```bash
./run_converter.py <input_file.xshd> <output_file.JSON-tmLanguage> [options]
```

Or, if you haven't made it executable:
```bash
python3 run_converter.py <input_file.xshd> <output_file.JSON-tmLanguage> [options]
```

### Arguments:

-   `input_file`: (Required) Path to the input `.xshd` file.
-   `output_file`: (Required) Path for the generated TextMate grammar JSON file (e.g., `mylanguage.tmLanguage.json`). It's good practice to use extensions like `.JSON-tmLanguage` or `.tmLanguage.json`.
-   `-v`, `--verbose`: (Optional) Enable verbose output, showing more details about the conversion process.

### Example Command:

```bash
./run_converter.py xshd-to-textmate/examples/dummy.xshd python-from-xshd.JSON-tmLanguage --verbose
```
This command would convert `xshd-to-textmate/examples/dummy.xshd` and save the resulting TextMate grammar to `python-from-xshd.JSON-tmLanguage` in the project root, with verbose output.

## Example

Sample `.xshd` files can be found in the `xshd-to-textmate/examples/` directory within this project. These can be used to test the converter. For instance, `dummy.xshd` provides a basic syntax definition for Python-like features.

## How it Works

The conversion process involves two main steps:

1.  **Parsing**: The `.xshd` file (which is an XML file) is parsed using Python's `xml.etree.ElementTree`. The script extracts information about the language name, file extensions, keywords, comment styles, string delimiters, digit highlighting rules, and other custom span-based syntax rules. This information is structured into an intermediate Python dictionary.
    (See `xshd-to-textmate/src/xshd_parser.py`)

2.  **Generation**: The intermediate dictionary is then transformed into a TextMate grammar structure. This involves mapping XSHD constructs to TextMate concepts:
    -   XSHD keywords become lists of keywords in `match` patterns, often scoped as `keyword.control`, `keyword.other`, `support.function.builtin`, etc.
    -   XSHD comment definitions are translated into `comment.line` or `comment.block` patterns.
    -   XSHD string definitions become `string.quoted` patterns.
    -   Other XSHD `Span` elements are converted into `begin`/`end` patterns or `match` patterns with heuristically determined scopes (e.g., `entity.name.function`, `meta.preprocessor`).
    The final grammar is written as a JSON file.
    (See `xshd-to-textmate/src/textmate_generator.py`)

The main CLI logic is in `xshd-to-textmate/src/main.py`, and `run_converter.py` is the top-level script that executes it.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

When contributing, please ensure that your changes are well-tested. If adding new features or fixing bugs in the parser or generator, consider adding or updating unit tests in the `xshd-to-textmate/tests/` directory.

## License

This project is licensed under the MIT License. (A formal `LICENSE` file can be added if desired).
