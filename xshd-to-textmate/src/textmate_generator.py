import json
import re

# Reference for TextMate grammar: https://macromates.com/manual/en/language_grammars

def escape_regex(string: str) -> str:
    """Escapes special characters in a string for use in a TextMate regex."""
    if not string:
        return ""
    # This is a basic list, more might be needed depending on XSHD syntax
    return re.sub(r'([.?*+^$[\]\\(){}|-])', r'\\\1', string)

def generate_textmate_grammar(xshd_data: dict, output_path: str):
    """
    Generates a TextMate grammar JSON file from parsed XSHD data.

    Args:
        xshd_data: A dictionary containing syntax information parsed from an .xshd file.
        output_path: The path to write the generated .tmLanguage.json file.
    """
    if not xshd_data or not xshd_data.get("name"):
        print("Error: Invalid or missing XSHD data. Cannot generate grammar.")
        return

    lang_name = xshd_data.get("name", "untitled").lower().replace(" ", "")
    scope_name = f"source.{lang_name}"
    file_types = xshd_data.get("extensions", [])
    # Remove leading dots from extensions if present, TextMate doesn't use them here
    file_types = [ft.lstrip('.') for ft in file_types]


    patterns = []
    repository = {} # Initialize repository
    main_patterns = [] # Main patterns for the grammar

    # Determine global ignorecase setting (e.g., from the first ruleset)
    # A more sophisticated approach might be needed if ignorecase varies significantly between rulesets
    global_ignorecase = False
    if xshd_data.get("rulesets"):
        global_ignorecase = xshd_data["rulesets"][0].get("ignorecase", False)

    # Helper to add ignorecase flag to regex if needed
    def possibly_case_insensitive(regex_str: str, ignore_case_flag: bool) -> str:
        return f"(?i){regex_str}" if ignore_case_flag else regex_str

    # 1. Comments
    comments_repo = []
    comment_scope_base = f"comment.{lang_name}"
    
    # Line Comments
    line_comment_starts = xshd_data.get("comments", {}).get("line_comment_start", [])
    for lc_start in line_comment_starts:
        if not lc_start: continue
        comments_repo.append({
            "name": f"comment.line.{escape_regex(lc_start).replace(' ', '_')}.{lang_name}",
            "match": f"{escape_regex(lc_start)}.*$"
        })

    # Block Comments
    block_comment_starts = xshd_data.get("comments", {}).get("block_comment_start", [])
    block_comment_ends = xshd_data.get("comments", {}).get("block_comment_end", [])
    # Assuming starts and ends are paired if multiple exist (common in XSHD for same type)
    # For simplicity, we'll take the first one if multiple distinct ones exist, or handle pairs if possible.
    # A more robust solution would handle multiple, distinct block comment types.
    if block_comment_starts and block_comment_ends:
        # Simple case: use the first pair
        # TODO: Handle multiple distinct block comment styles if needed
        for i in range(min(len(block_comment_starts), len(block_comment_ends))):
            bc_start = block_comment_starts[i]
            bc_end = block_comment_ends[i]
            if not bc_start or not bc_end: continue
            comments_repo.append({
                "name": f"comment.block.{lang_name}",
                "begin": escape_regex(bc_start),
                "end": escape_regex(bc_end),
                "patterns": [{"include": "#self"}] # Allow nesting of language elements
            })
    
    if comments_repo:
        repository["comments"] = {"patterns": comments_repo}
        main_patterns.append({"include": "#comments"})

    # 2. Strings
    strings_repo = []
    string_scope_base = f"string.quoted.{lang_name}"
    xshd_strings = xshd_data.get("strings", [])
    for i, s_def in enumerate(xshd_strings):
        begin_delim = s_def.get("begin")
        end_delim = s_def.get("end")
        str_name = s_def.get("name", f"unnamed_string_{i}").lower().replace(" ", "_")
        
        if not begin_delim or not end_delim:
            continue

        # Basic escape for TextMate: only \ and the delimiter itself
        # More complex XSHD escape sequences would need specific rules inside the string content
        # For now, we assume simple backslash escapes for common chars like the delimiter itself or \
        string_content_patterns = [
            {"match": r"\\.", "name": f"constant.character.escape.{lang_name}"}
        ]
        
        # Heuristic for string type (double, single, other)
        string_type = "double"
        if '"' in begin_delim:
            string_type = "double"
        elif "'" in begin_delim:
            string_type = "single"
        else:
            string_type = "other"
            
        scope_name_str = f"string.quoted.{string_type}.{str_name}.{lang_name}"
        if s_def.get("stopateol", False):
             scope_name_str += ".no-multiline"


        strings_repo.append({
            "name": scope_name_str,
            "begin": escape_regex(begin_delim),
            "end": escape_regex(end_delim),
            "patterns": string_content_patterns
        })

    if strings_repo:
        repository["strings"] = {"patterns": strings_repo}
        main_patterns.append({"include": "#strings"})

    # 3. Keywords
    # Keywords are grouped by their XSHD 'name' (category)
    keywords_repo = []
    xshd_keywords_map = xshd_data.get("keywords", {})
    for kw_category, kw_list in xshd_keywords_map.items():
        if not kw_list:
            continue
        
        # Determine TextMate scope based on common keyword categories
        category_lower = kw_category.lower()
        final_scope = f"keyword.other.{lang_name}" # Default scope

        if "constant" in category_lower: # e.g. True, False, None
            final_scope = f"constant.language.{lang_name}"
        elif "builtin" in category_lower or "predefined" in category_lower or category_lower == "builtins":
            # Heuristic: if 'function', 'type', 'class' also in name, refine scope
            if "function" in category_lower or category_lower == "builtins": # "builtins" often refers to functions
                final_scope = f"support.function.builtin.{lang_name}"
            elif "type" in category_lower:
                final_scope = f"support.type.{lang_name}"
            elif "class" in category_lower:
                final_scope = f"support.class.builtin.{lang_name}"
            else: # Default for other builtins if not more specific
                final_scope = f"keyword.language.{lang_name}"
        elif "keyword" in category_lower or "control" in category_lower: # Catches "Keywords", "UserKeywords", "ControlFlow" etc.
            if "user" in category_lower: # Typically less critical, more like variables or custom
                final_scope = f"keyword.other.{lang_name}"
            elif "operator" in category_lower:
                final_scope = f"keyword.operator.{lang_name}"
            # Add other specific "keyword" sub-types here if needed
            else: # Default for primary "Keywords"
                final_scope = f"keyword.control.{lang_name}"
        # else: it remains keyword.other.lang_name (the default initially set)
        # This could be a place for even more specific user-defined categories if necessary:
        # elif kw_category == "MySpecialCategory":
        #     final_scope = f"customscope.{kw_category.lower()}.{lang_name}"

        # Sort keywords by length, longest first, to help with matching if some are prefixes of others
        sorted_kw_list = sorted(kw_list, key=len, reverse=True)
        
        # Escape keywords for regex, as some might contain special characters (though unusual for keywords)
        escaped_kw_list = [escape_regex(kw) for kw in sorted_kw_list]

        keyword_pattern = r"\b(" + "|".join(escaped_kw_list) + r")\b"
        keyword_pattern = possibly_case_insensitive(keyword_pattern, global_ignorecase)

        keywords_repo.append({
            "name": final_scope,
            "match": keyword_pattern
        })
    
    if keywords_repo:
        repository["keywords"] = {"patterns": keywords_repo}
        main_patterns.append({"include": "#keywords"})

    # 4. Numbers/Digits
    # XSHD "Digits" usually just styles them, doesn't define a pattern.
    # We'll add a generic number pattern if "Digits" is mentioned.
    if xshd_data.get("digits") is not None:
        # A very basic number pattern. More complex patterns could be added.
        # Handles integers and simple decimals. Does not handle hex, octal, scientific notation.
        number_pattern = r"\b\d+(\.\d+)?\b" 
        # XSHD Digits doesn't specify ignorecase, but numbers are typically case-sensitive in their form.
        # No need for possibly_case_insensitive here unless specific non-standard number formats are used.
        repository["numbers"] = {
            "patterns": [{
                "name": f"constant.numeric.{lang_name}",
                "match": number_pattern
            }]
        }
        main_patterns.append({"include": "#numbers"})

    # 5. Other Spans from XSHD (those not already handled as comments/strings)
    # These are more complex and require careful mapping.
    # This is a simplified initial approach.
    other_spans_repo = []
    xshd_spans = xshd_data.get("spans", [])
    handled_span_names = set() # To avoid double-processing spans used for comments/strings

    # Collect names of spans already processed as comments or strings
    for s_def in xshd_strings:
        if s_def.get("name"):
            handled_span_names.add(s_def["name"])
    for span_element in xshd_spans: # Iterate through original spans to find comment names
        name_lower = (span_element.get("name") or "").lower()
        rule_lower = (span_element.get("rule") or "").lower()
        if "comment" in name_lower or "comment" in rule_lower:
            if span_element.get("name"):
                 handled_span_names.add(span_element["name"])


    for span_def in xshd_spans:
        span_name = span_def.get("name")
        if not span_name or span_name in handled_span_names:
            continue # Skip if no name or already handled

        begin_pattern = span_def.get("begin")
        end_pattern = span_def.get("end")
        span_rule = span_def.get("rule", "").lower() # e.g., "Function", "Preprocessor"
        
        # Determine TextMate scope based on XSHD span name or rule
        # This is highly heuristic.
        tm_scope = f"meta.{span_name.lower().replace(' ', '_')}.{lang_name}" # Default scope
        if "function" in span_name.lower() or "function" in span_rule:
            tm_scope = f"entity.name.function.{lang_name}"
        elif "class" in span_name.lower() or "type" in span_rule or "struct" in span_name.lower():
            tm_scope = f"entity.name.type.{lang_name}"
        elif "preprocessor" in span_name.lower() or "preprocessor" in span_rule or "directive" in span_name.lower():
            tm_scope = f"meta.preprocessor.{lang_name}"
            if begin_pattern and not end_pattern: # Often preproc directives are single lines
                 other_spans_repo.append({
                    "name": tm_scope,
                    "match": f"{escape_regex(begin_pattern)}.*$"
                })
                 continue # Move to next span
        elif "variable" in span_name.lower() or "identifier" in span_name.lower():
            tm_scope = f"variable.other.{lang_name}"
        elif "namespace" in span_name.lower():
            tm_scope = f"entity.name.namespace.{lang_name}"
        
        # Only create a rule if we have a begin pattern
        if begin_pattern:
            escaped_begin = escape_regex(begin_pattern)
            # If it's a begin/end span
            if end_pattern:
                escaped_end = escape_regex(end_pattern)
                other_spans_repo.append({
                    "name": tm_scope,
                    "begin": possibly_case_insensitive(escaped_begin, global_ignorecase),
                    "end": possibly_case_insensitive(escaped_end, global_ignorecase),
                    "patterns": [{"include": "#self"}] # Allow nesting
                })
            # If it's a match-only span (e.g. stopateol=true without explicit end)
            elif span_def.get("stopateol"):
                other_spans_repo.append({
                    "name": tm_scope,
                    "match": possibly_case_insensitive(escaped_begin, global_ignorecase) 
                           + (r".*$" if span_def.get("stopateol") else "") 
                })
            # else: it's a begin without an end and not stopateol, harder to map directly.
            # We could make it a match rule if appropriate, or ignore if too ambiguous.
            # For now, we require an end or stopateol for non-block spans.

    if other_spans_repo:
        repository["custom_spans"] = {"patterns": other_spans_repo}
        main_patterns.append({"include": "#custom_spans"})


    grammar = {
        "scopeName": scope_name,
        "fileTypes": file_types,
        "name": xshd_data.get("name"),
        "patterns": main_patterns,
        "repository": repository,
    }

    try:
        with open(output_path, 'w') as f:
            json.dump(grammar, f, indent=2)
        print(f"TextMate grammar successfully generated at {output_path}")
    except IOError:
        print(f"Error: Could not write to output path {output_path}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == '__main__':
    # Example usage with dummy xshd_data (similar to what xshd_parser would produce)
    dummy_xshd_data_for_tm = {
        "name": "Python",
        "extensions": [".py", ".pyw"],
        "keywords": {
            "Keywords": ["def", "class", "if", "else", "elif", "return", "for", "while", "try", "except", "finally", "with", "import", "from", "as", "pass", "break", "continue", "global", "nonlocal", "lambda", "yield", "del", "in", "is", "not", "and", "or"],
            "UserKeywords": ["self", "True", "False", "None"],
            "Builtins": ["print", "len", "range", "open", "str", "int", "list", "dict", "set", "tuple"]
        },
        "comments": {
            "line_comment_start": ["#"],
            "block_comment_start": ["\"\"\""],
            "block_comment_end": ["\"\"\""],
        },
        "strings": [
            {"begin": "\"", "end": "\"", "name": "String", "stopateol": True},
            {"begin": "'", "end": "'", "name": "Char", "stopateol": True},
            {"begin": "r\"", "end": "\"", "name": "RawString", "stopateol": False},
            {"begin": "f\"", "end": "\"", "name": "FormattedString", "stopateol": False}
        ],
        "digits": {"name": "Digits", "color": "DarkBlue"}, # Example, might translate to a numeric rule
        "rulesets": [ # Simplified for this example
            {
                "ignorecase": False,
                "delimiters": "&()[]{}<>%:;.,=", 
            }
        ],
        "spans": [ # Includes comments and strings which are handled separately, but other spans might exist
            {"name": "LineComment", "rule": "Comment", "begin": "#", "stopateol": True},
            {"name": "BlockComment", "rule": "Comment", "begin": "\"\"\"", "end": "\"\"\"", "multiline": True},
            {"name": "String", "rule": "String", "begin": "\"", "end": "\"", "stopateol": True},
            {"name": "Char", "rule": "Char", "begin": "'", "end": "'", "stopateol": True},
            {"name": "FunctionDef", "rule": "Function", "begin": "def\\s+[A-Za-z_][A-Za-z0-9_]*", "end": ":"} 
        ]
    }

    generate_textmate_grammar(dummy_xshd_data_for_tm, "dummy_python.tmLanguage.json")

    # Test with minimal data
    minimal_data = {
        "name": "MiniLang",
        "extensions": [".mini"],
        "keywords": {"Control": ["IF", "THEN", "ENDIF"]},
        "comments": {"line_comment_start": ["//"]},
        "strings": [{"begin": "`", "end": "`", "name": "BacktickString", "stopateol": False}],
        "digits": None,
        "rulesets": [{"ignorecase": True}],
        "spans": []
    }
    generate_textmate_grammar(minimal_data, "minimal_lang.tmLanguage.json")

    # Test with missing name
    generate_textmate_grammar({"extensions": [".noname"]}, "noname_lang.tmLanguage.json")
    
    # Test with empty data
    generate_textmate_grammar({}, "empty_lang.tmLanguage.json")
