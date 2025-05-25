import unittest
import os
import xml.etree.ElementTree as ET

import xml.etree.ElementTree as ET

# Relative import assuming 'tests' is a package and 'src' is a sibling package
# This requires running unittest in a way that recognizes 'xshd_to_textmate' as the top-level package
# e.g. from /app, running `python -m unittest discover xshd_to_textmate.tests` or similar.
from ..src.xshd_parser import parse_xshd

class TestXSHDParser(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures')
        cls.sample_xshd_path = os.path.join(cls.fixtures_dir, 'sample.xshd')
        cls.empty_xshd_path = os.path.join(cls.fixtures_dir, 'empty.xshd')
        cls.minimal_xshd_path = os.path.join(cls.fixtures_dir, 'minimal.xshd')
        cls.malformed_xshd_path = os.path.join(cls.fixtures_dir, 'malformed.xshd')
        cls.no_attributes_xshd_path = os.path.join(cls.fixtures_dir, 'no_attributes.xshd')


        # Create an empty .xshd file for testing
        with open(cls.empty_xshd_path, 'w') as f:
            f.write("<?xml version=\"1.0\"?><SyntaxDefinition name=\"Empty\"></SyntaxDefinition>") # Must be valid XML

        # Create a minimal .xshd file
        with open(cls.minimal_xshd_path, 'w') as f:
            f.write("<?xml version=\"1.0\"?><SyntaxDefinition name=\"Minimal\" extensions=\".min\"></SyntaxDefinition>")

        # Create a malformed .xshd file
        with open(cls.malformed_xshd_path, 'w') as f:
            f.write("<?xml version=\"1.0\"?><SyntaxDefinition name=\"Malformed\" extensions=\".mal\"") # Missing closing tag

        # Create an XSHD file with some missing optional attributes
        with open(cls.no_attributes_xshd_path, 'w') as f:
            f.write("""<?xml version="1.0"?>
<SyntaxDefinition name="NoAttribs">
    <RuleSet>
        <KeyWords name="OnlyName">
            <Key word="test"/>
        </KeyWords>
        <Span name="OnlyNameSpan">
            <Begin>BEGIN</Begin>
        </Span>
    </RuleSet>
</SyntaxDefinition>""")


    @classmethod
    def tearDownClass(cls):
        # Clean up created fixture files
        os.remove(cls.empty_xshd_path)
        os.remove(cls.minimal_xshd_path)
        os.remove(cls.malformed_xshd_path)
        os.remove(cls.no_attributes_xshd_path)

    def test_parse_sample_xshd(self):
        data = parse_xshd(self.sample_xshd_path)
        self.assertIsNotNone(data)
        self.assertEqual(data["name"], "SampleLang")
        self.assertEqual(data["extensions"], [".spl"])

        # Digits
        self.assertIsNotNone(data["digits"])
        self.assertEqual(data["digits"]["name"], "Numbers")
        self.assertEqual(data["digits"]["color"], "Blue")
        self.assertEqual(data["digits"]["bold"], "true")

        # Comments
        self.assertIn("//", data["comments"]["line_comment_start"])
        self.assertIn("/*", data["comments"]["block_comment_start"])
        self.assertIn("*/", data["comments"]["block_comment_end"])
        self.assertIn("/**", data["comments"]["block_comment_start"]) # DocComment
        self.assertIn("*/", data["comments"]["block_comment_end"])   # DocComment end

        # Strings
        self.assertTrue(any(s["begin"] == '"' and s["end"] == '"' for s in data["strings"]))
        self.assertTrue(any(s["begin"] == "'" and s["end"] == "'" and s["stopateol"] for s in data["strings"]))

        # Keywords
        self.assertIn("Keywords", data["keywords"])
        self.assertIn("if", data["keywords"]["Keywords"])
        self.assertIn("Types", data["keywords"])
        self.assertIn("int", data["keywords"]["Types"])
        self.assertIn("Constants", data["keywords"])
        self.assertIn("TRUE", data["keywords"]["Constants"])
        
        # Check ignorecase from the first ruleset
        self.assertTrue(data["rulesets"][0]["ignorecase"])

        # Spans (check a few distinctive ones)
        self.assertTrue(any(s["name"] == "LineComment" and s["begin"] == "//" for s in data["spans"]))
        self.assertTrue(any(s["name"] == "BlockComment" and s["begin"] == "/*" and s["end"] == "*/" for s in data["spans"]))
        self.assertTrue(any(s["name"] == "DocComment" and s["begin"] == "/**" and s["italic"] == "true" for s in data["spans"]))
        self.assertTrue(any(s["name"] == "Preprocessor" and s["begin"] == "#" and s["rule"] == "Preprocessor" for s in data["spans"]))
        self.assertTrue(any(s["name"] == "Region" and s["begin"] == "#region" and s["end"] == "#endregion" for s in data["spans"]))

        # Check second ruleset
        self.assertEqual(len(data["rulesets"]), 2)
        self.assertEqual(data["rulesets"][1].get("ignorecase"), True) # From sample.xshd
        self.assertIn("InactiveKeywords", data["rulesets"][1]["keywords"])
        self.assertIn("todo", data["rulesets"][1]["keywords"]["InactiveKeywords"])
        # Also ensure these keywords are reflected in the global keywords list
        self.assertIn("InactiveKeywords", data["keywords"])
        self.assertIn("todo", data["keywords"]["InactiveKeywords"])


    def test_parse_non_existent_file(self):
        data = parse_xshd("non_existent_file.xshd")
        self.assertIsNone(data) # Expecting None and an error message printed by the function

    def test_parse_malformed_xml(self):
        data = parse_xshd(self.malformed_xshd_path)
        self.assertIsNone(data) # Expecting None and an error message

    def test_parse_empty_xshd(self):
        # "Empty" here means a valid XML with SyntaxDefinition but no other rules.
        data = parse_xshd(self.empty_xshd_path)
        self.assertIsNotNone(data)
        self.assertEqual(data["name"], "Empty")
        self.assertEqual(data["extensions"], []) # No extensions specified
        self.assertEqual(data["keywords"], {})
        self.assertEqual(data["comments"]["line_comment_start"], [])
        self.assertEqual(data["strings"], [])
        self.assertIsNone(data["digits"])

    def test_parse_minimal_xshd(self):
        data = parse_xshd(self.minimal_xshd_path)
        self.assertIsNotNone(data)
        self.assertEqual(data["name"], "Minimal")
        self.assertEqual(data["extensions"], [".min"])
        self.assertEqual(data["keywords"], {})

    def test_parse_no_attributes_xshd(self):
        # Test a file where optional attributes on KeyWords and Span are missing
        data = parse_xshd(self.no_attributes_xshd_path)
        self.assertIsNotNone(data)
        self.assertEqual(data["name"], "NoAttribs")
        self.assertIn("OnlyName", data["keywords"])
        self.assertEqual(data["keywords"]["OnlyName"], ["test"])
        
        span_found = False
        for span in data["spans"]:
            if span["name"] == "OnlyNameSpan":
                span_found = True
                self.assertEqual(span["begin"], "BEGIN")
                self.assertIsNone(span["end"]) # No End tag
                self.assertIsNone(span["rule"]) # No rule attribute
                self.assertIsNone(span["color"])# No color attribute
                self.assertFalse(span["stopateol"]) # Default
                self.assertFalse(span["multiline"]) # Default
                break
        self.assertTrue(span_found, "Span 'OnlyNameSpan' not found in parsed data")

if __name__ == '__main__':
    unittest.main()
