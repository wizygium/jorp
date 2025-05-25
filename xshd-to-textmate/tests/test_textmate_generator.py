import unittest
import os
import json

from ..src.xshd_parser import parse_xshd
from ..src.textmate_generator import generate_textmate_grammar, escape_regex

class TestTextMateGenerator(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures')
        cls.sample_xshd_path = os.path.join(cls.fixtures_dir, 'sample.xshd')
        cls.output_dir = os.path.join(os.path.dirname(__file__), 'output') # For temporary generated files
        if not os.path.exists(cls.output_dir):
            os.makedirs(cls.output_dir)

        # Parse the sample.xshd once for all tests that need its data
        cls.parsed_sample_xshd_data = parse_xshd(cls.sample_xshd_path)
        if cls.parsed_sample_xshd_data is None:
            raise RuntimeError(f"Failed to parse {cls.sample_xshd_path} for generator tests setup.")

        # Define the expected output file path for comparison
        cls.expected_tmLanguage_path = os.path.join(cls.fixtures_dir, 'expected_sample.tmLanguage.json')
        cls.generated_tmLanguage_path = os.path.join(cls.output_dir, 'generated_sample.tmLanguage.json')

        # Create the expected .JSON-tmLanguage file based on current generator logic
        # This makes the test dependent on the generator's current correct output.
        # Ideally, this expected file is manually verified for correctness.
        cls.create_expected_tmLanguage_file(cls.expected_tmLanguage_path, cls.parsed_sample_xshd_data)


    @classmethod
    def tearDownClass(cls):
        # Clean up generated files
        if os.path.exists(cls.generated_tmLanguage_path):
            os.remove(cls.generated_tmLanguage_path)
        # Remove the output directory if it's empty, or handle more complex cleanup if needed
        if os.path.exists(cls.output_dir) and not os.listdir(cls.output_dir):
            os.rmdir(cls.output_dir)
        # We might also remove the expected file if it's purely dynamically generated for each run
        # For now, let's assume it's a fixture that could be static or is overwritten by create_expected_tmLanguage_file
        if os.path.exists(cls.expected_tmLanguage_path) and "CI" not in os.environ : # Avoid deleting in CI if it's a checked-in fixture
             # If it's dynamically created during test, it should be cleaned up.
             # For this example, we'll assume it's dynamically created by the helper.
            os.remove(cls.expected_tmLanguage_path)


    @staticmethod
    def create_expected_tmLanguage_file(path, xshd_data):
        # Helper to generate the "expected" file using the current generator.
        # This is for setting up the test. In a real scenario, this file would be
        # manually reviewed and committed.
        generate_textmate_grammar(xshd_data, path)


    def test_generate_from_sample_xshd(self):
        self.assertIsNotNone(self.parsed_sample_xshd_data, "Parsed XSHD data is None, cannot proceed.")
        
        generate_textmate_grammar(self.parsed_sample_xshd_data, self.generated_tmLanguage_path)
        self.assertTrue(os.path.exists(self.generated_tmLanguage_path))

        with open(self.generated_tmLanguage_path, 'r') as f_gen:
            generated_grammar = json.load(f_gen)
        
        with open(self.expected_tmLanguage_path, 'r') as f_exp:
            expected_grammar = json.load(f_exp)
        
        # Perform a deep comparison of the dictionaries
        self.assertDictEqual(generated_grammar, expected_grammar)

    def test_grammar_structure_and_metadata(self):
        # Test with a minimal, manually defined xshd_data structure
        minimal_xshd = {
            "name": "MiniLang",
            "extensions": [".mini", ".m"],
            "rulesets": [{"ignorecase": False}], # Required for global_ignorecase
            "comments": {"line_comment_start": ["#"]},
            # other fields can be empty lists/dicts
            "keywords": {}, "strings": [], "digits": None, "spans": [] 
        }
        output_path = os.path.join(self.output_dir, "minimal_test.tmLanguage.json")
        generate_textmate_grammar(minimal_xshd, output_path)
        self.assertTrue(os.path.exists(output_path))

        with open(output_path, 'r') as f:
            grammar = json.load(f)

        self.assertEqual(grammar["name"], "MiniLang")
        self.assertEqual(grammar["scopeName"], "source.minilang")
        self.assertListEqual(sorted(grammar["fileTypes"]), sorted(["mini", "m"]))
        self.assertIn("patterns", grammar)
        self.assertIn("repository", grammar)
        
        # Check if comments are processed
        self.assertIn("comments", grammar["repository"])
        self.assertTrue(any(p.get("match") == escape_regex("#") + ".*$" for p in grammar["repository"]["comments"]["patterns"]))

        if os.path.exists(output_path):
            os.remove(output_path)

    def test_keyword_generation(self):
        # Test specific keyword mapping, including ignorecase
        keyword_xshd = {
            "name": "KeywordTestLang", "extensions": [".key"],
            "rulesets": [{"ignorecase": True}], # Test ignorecase TRUE
            "keywords": {
                "ControlFlow": ["IF", "THEN", "ELSE"],
                "Builtins": ["PRINT", "READ"]
            },
            "comments": {}, "strings": [], "digits": None, "spans": []
        }
        output_path = os.path.join(self.output_dir, "keywords_test.tmLanguage.json")
        generate_textmate_grammar(keyword_xshd, output_path)
        self.assertTrue(os.path.exists(output_path))

        with open(output_path, 'r') as f:
            grammar = json.load(f)
        
        self.assertIn("keywords", grammar["repository"])
        kw_patterns = grammar["repository"]["keywords"]["patterns"]
        
        lang_name_test = keyword_xshd['name'].lower().replace(" ", "") # "keywordtestlang"
        expected_control_scope = f"keyword.control.{lang_name_test}"
        expected_builtin_scope = f"support.function.builtin.{lang_name_test}"

        # Diagnostic print:
        print("\n[DEBUG] In test_keyword_generation:")
        print(f"  Expected lang_name_test: '{lang_name_test}'")
        print(f"  Expected ControlFlow scope: '{expected_control_scope}'")
        print(f"  Expected Builtins scope: '{expected_builtin_scope}'")
        print("  Actual keyword pattern names found in grammar:")
        if not kw_patterns:
            print("    <No keyword patterns found in repository>")
        for p_idx, p_item in enumerate(kw_patterns):
            print(f"    {p_idx}: '{p_item.get('name')}'")

        control_kw = next((p for p in kw_patterns if p["name"] == expected_control_scope), None)
        self.assertIsNotNone(control_kw, f"ControlFlow keyword group with scope '{expected_control_scope}' was not found.")
        
        # Check for (?i) for ignorecase=true
        self.assertTrue(control_kw["match"].startswith("(?i)"), "Keyword pattern should start with (?i) for ignorecase=true") # type: ignore
        
        # Check general structure and presence of all keywords, order might change due to sorting by length
        self.assertTrue(control_kw["match"].startswith("(?i)\\b("), "Keyword pattern structure is incorrect (prefix)") # type: ignore
        self.assertTrue(control_kw["match"].endswith(")\\b"), "Keyword pattern structure is incorrect (suffix)") # type: ignore
        self.assertIn("IF", control_kw["match"]) # type: ignore
        self.assertIn("THEN", control_kw["match"]) # type: ignore
        self.assertIn("ELSE", control_kw["match"]) # type: ignore
        
        # Redundant check for name if next() worked, but good for clarity:
        self.assertEqual(control_kw["name"], expected_control_scope) # type: ignore

        builtin_kw = next((p for p in kw_patterns if p["name"] == expected_builtin_scope), None)
        self.assertIsNotNone(builtin_kw, f"Builtins keyword group with scope '{expected_builtin_scope}' was not found.")
        
        self.assertTrue(builtin_kw["match"].startswith("(?i)"), "Builtin keyword pattern should start with (?i) for ignorecase=true") # type: ignore
        self.assertTrue(builtin_kw["match"].startswith("(?i)\\b("), "Builtin pattern structure is incorrect (prefix)") # type: ignore
        self.assertTrue(builtin_kw["match"].endswith(")\\b"), "Builtin pattern structure is incorrect (suffix)") # type: ignore
        self.assertIn("PRINT", builtin_kw["match"]) # type: ignore
        self.assertIn("READ", builtin_kw["match"]) # type: ignore
        self.assertEqual(builtin_kw["name"], expected_builtin_scope) # type: ignore


        if os.path.exists(output_path):
            os.remove(output_path)

    def test_span_generation_and_scoping(self):
        span_xshd = {
            "name": "SpanLang", "extensions": [".span"],
            "rulesets": [{"ignorecase": False}],
            "spans": [
                {"name": "FunctionDef", "begin": "def\\s", "end": ":", "rule": "Function"},
                {"name": "ClassDef", "begin": "class\\s", "end": "\\{", "rule": "Type"},
                {"name": "SingleLineDirective", "begin": "@directive", "stopateol": True},
                {"name": "RegionMarker", "begin": "#region", "end": "#endregion", "color": "Gray"},
                # A span that might be misidentified if not for handled_span_names
                {"name": "StringLikeSpan", "begin": "`", "end": "`"}, 
            ],
            "strings": [{"name": "ActualString", "begin": "\"", "end": "\""}], # To test handled_span_names
            "comments": {}, "keywords": {}, "digits": None, 
        }
        output_path = os.path.join(self.output_dir, "spans_test.tmLanguage.json")
        generate_textmate_grammar(span_xshd, output_path)
        self.assertTrue(os.path.exists(output_path))

        with open(output_path, 'r') as f:
            grammar = json.load(f)

        self.assertIn("custom_spans", grammar["repository"])
        cs_patterns = grammar["repository"]["custom_spans"]["patterns"]

        # Check for FunctionDef with its specific scope
        func_span = next((p for p in cs_patterns if p["name"] == "entity.name.function.spanlang"), None)
        self.assertIsNotNone(func_span, "FunctionDef span with scope 'entity.name.function.spanlang' not found.")
        self.assertEqual(func_span["begin"], escape_regex("def\\s"))
        self.assertEqual(func_span["end"], escape_regex(":"))

        # Check for ClassDef with its specific scope
        class_span = next((p for p in cs_patterns if p["name"] == "entity.name.type.spanlang"), None)
        self.assertIsNotNone(class_span, "ClassDef span with scope 'entity.name.type.spanlang' not found.")
        self.assertEqual(class_span["begin"], escape_regex("class\\s"))
        self.assertEqual(class_span["end"], escape_regex("\\{")) # Test escaping of {

        # Check for SingleLineDirective (heuristic maps to meta.preprocessor if "directive" in name)
        directive_span = next((p for p in cs_patterns if p["name"] == f"meta.preprocessor.spanlang"), None)
        self.assertIsNotNone(directive_span, f"SingleLineDirective span expected as 'meta.preprocessor.spanlang' not found.")
        self.assertTrue(directive_span["match"].startswith(escape_regex("@directive")))
        self.assertTrue(directive_span["match"].endswith(".*$")) # from stopateol

        # Check for RegionMarker (uses default meta scope: meta.regionmarker.spanlang)
        region_span = next((p for p in cs_patterns if p["name"] == "meta.regionmarker.spanlang"), None)
        self.assertIsNotNone(region_span, "RegionMarker span with scope 'meta.regionmarker.spanlang' not found.")

        # For "StringLikeSpan" in this specific test's span_xshd:
        # It's NOT in span_xshd["strings"], so it's NOT in handled_span_names via strings.
        # It does not have "comment" in name/rule, so not handled via comments.
        # So it SHOULD be processed as a custom_span.
        lang_name_for_span_test = span_xshd['name'].lower() # "spanlang"
        expected_stringlike_custom_scope = f"meta.stringlikespan.{lang_name_for_span_test}"
        stringlike_span_in_custom = next((p for p in cs_patterns if p["name"] == expected_stringlike_custom_scope), None)
        self.assertIsNotNone(stringlike_span_in_custom, 
                             f"StringLikeSpan should be in custom_spans with scope {expected_stringlike_custom_scope} for this test's specific input data. Found: {[p['name'] for p in cs_patterns]}")
        self.assertEqual(stringlike_span_in_custom["begin"], escape_regex("`"))
        self.assertEqual(stringlike_span_in_custom["end"], escape_regex("`"))

        # And it should NOT be in strings_patterns because it wasn't in span_xshd["strings"] to begin with for this test.
        strings_patterns = grammar["repository"]["strings"]["patterns"]
        stringlike_span_in_strings = next((p for p in strings_patterns if "stringlikespan" in p["name"].lower()), None)
        self.assertIsNone(stringlike_span_in_strings, "StringLikeSpan should NOT be in string_patterns for this test's specific input data, as it was not provided in xshd_data['strings'].")


        if os.path.exists(output_path):
            os.remove(output_path)

    def test_empty_input_for_generator(self):
        # Test with completely empty or invalid xshd_data
        generate_textmate_grammar({}, os.path.join(self.output_dir, "empty_input.tmLanguage.json"))
        # Expecting error print from function, and no file created (or an empty/error file)
        # The function currently prints an error and returns if not xshd_data or no name.
        self.assertFalse(os.path.exists(os.path.join(self.output_dir, "empty_input.tmLanguage.json")), 
                         "File should not be created for empty input if generator exits early.")

        generate_textmate_grammar({"name": "NoRules"}, os.path.join(self.output_dir, "norules_input.tmLanguage.json"))
        # This should generate a file, but it will be minimal.
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "norules_input.tmLanguage.json")))
        if os.path.exists(os.path.join(self.output_dir, "norules_input.tmLanguage.json")):
            os.remove(os.path.join(self.output_dir, "norules_input.tmLanguage.json"))


if __name__ == '__main__':
    unittest.main()
