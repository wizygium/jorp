import xml.etree.ElementTree as ET

def parse_xshd(file_path: str):
    """
    Parses an .xshd file and extracts language syntax information.

    Args:
        file_path: The path to the .xshd file.

    Returns:
        A dictionary containing the extracted syntax information.
        Returns None if parsing fails.
    """
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Initialize structured data
        syntax_info = {
            "name": None,
            "extensions": [],
            "keywords": {}, # Store keywords in a dict, categorized by type
            "comments": {
                "line_comment_start": [],
                "block_comment_start": [],
                "block_comment_end": [],
            },
            "strings": [], # List of string delimiter pairs
            "digits": None,
            "rulesets": [], # Information about rulesets
            "spans": [], # Detailed span information
        }

        # Extract language name and extensions
        syntax_info["name"] = root.get("name")
        extensions_str = root.get("extensions")
        if extensions_str:
            syntax_info["extensions"] = [ext.strip() for ext in extensions_str.split(';') if ext.strip()]

        # Find Digits element
        digits_element = root.find("Digits")
        if digits_element is not None:
            syntax_info["digits"] = {
                "name": digits_element.get("name"),
                "color": digits_element.get("color"),
                "bold": digits_element.get("bold"),
                "italic": digits_element.get("italic"),
            }
        
        # Process RuleSet elements (assuming one main RuleSet for now, can be extended)
        # XSHD can have nested RuleSets, but we'll start with the top-level ones.
        for ruleset_element in root.findall("RuleSet"):
            rs_info = {
                "ignorecase": ruleset_element.get("ignorecase", "false").lower() == "true",
                "delimiters": None,
                "keywords": {}, # Keywords specific to this ruleset
                "spans": [], # Spans specific to this ruleset
            }
            
            delimiters_element = ruleset_element.find("Delimiters")
            if delimiters_element is not None and delimiters_element.text:
                rs_info["delimiters"] = delimiters_element.text

            # Extract Keywords
            for keywords_element in ruleset_element.findall("KeyWords"):
                kw_category = keywords_element.get("name", "default")
                kw_list = []
                for key_element in keywords_element.findall("Key"):
                    word = key_element.get("word")
                    if word:
                        kw_list.append(word)
                if kw_list:
                    # Add to both ruleset-specific and global keywords
                    rs_info["keywords"].setdefault(kw_category, []).extend(kw_list)
                    syntax_info["keywords"].setdefault(kw_category, []).extend(kw_list)
            
            # Extract Spans (includes comments, strings, etc.)
            for span_element in ruleset_element.findall("Span"):
                span_info = {
                    "name": span_element.get("name"),
                    "rule": span_element.get("rule"),
                    "color": span_element.get("color"),
                    "bold": span_element.get("bold"),
                    "italic": span_element.get("italic"),
                    "stopateol": span_element.get("stopateol", "false").lower() == "true",
                    "multiline": span_element.get("multiline", "false").lower() == "true",
                    "begin": None,
                    "end": None,
                }
                begin_element = span_element.find("Begin")
                if begin_element is not None and begin_element.text:
                    span_info["begin"] = begin_element.text.strip()
                
                end_element = span_element.find("End")
                if end_element is not None and end_element.text:
                    span_info["end"] = end_element.text.strip()

                rs_info["spans"].append(span_info)
                syntax_info["spans"].append(span_info) # Also add to global spans list

                # Categorize comments and strings based on span properties
                name_lower = (span_info["name"] or "").lower()
                rule_lower = (span_info["rule"] or "").lower()

                if "comment" in name_lower or "comment" in rule_lower:
                    if span_info["stopateol"] and span_info["begin"]: # Line comment
                        syntax_info["comments"]["line_comment_start"].append(span_info["begin"])
                    elif span_info["multiline"] and span_info["begin"] and span_info["end"]: # Block comment
                        syntax_info["comments"]["block_comment_start"].append(span_info["begin"])
                        syntax_info["comments"]["block_comment_end"].append(span_info["end"])
                
                if "string" in name_lower or "char" in name_lower or "string" in rule_lower or "char" in rule_lower:
                     if span_info["begin"] and span_info["end"]:
                        syntax_info["strings"].append({
                            "begin": span_info["begin"],
                            "end": span_info["end"],
                            "name": span_info["name"],
                            "stopateol": span_info["stopateol"],
                        })
            
            syntax_info["rulesets"].append(rs_info)

        # Remove duplicates from keyword lists if any category was processed multiple times
        for category in syntax_info["keywords"]:
            syntax_info["keywords"][category] = sorted(list(set(syntax_info["keywords"][category])))
        
        for key in ["line_comment_start", "block_comment_start", "block_comment_end"]:
            syntax_info["comments"][key] = sorted(list(set(syntax_info["comments"][key])))

        return syntax_info
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return None
    except ET.ParseError:
        print(f"Error: Invalid XML in file {file_path}")
        return None

if __name__ == '__main__':
    # Example usage (for testing purposes)
    # Create a dummy .xshd file for testing
    dummy_xshd_content = """<?xml version="1.0"?>
    <SyntaxDefinition name="Python" extensions=".py;.pyw">
        <Digits name="Digits" color="DarkBlue"/>
        <RuleSet ignorecase="false">
            <Delimiters>&amp;()[]{}&lt;&gt;%:;.,=</Delimiters>
            <Span name="LineComment" rule="Comment" color="Green" stopateol="true">
                <Begin>#</Begin>
            </Span>
            <Span name="BlockComment" rule="Comment" color="Green" multiline="true">
                <Begin>\"\"\"</Begin>
                <End>\"\"\"</End>
            </Span>
            <Span name="String" rule="String" color="Sienna" stopateol="true">
                <Begin>"</Begin>
                <End>"</End>
            </Span>
            <Span name="Char" rule="Char" color="Sienna" stopateol="true">
                <Begin>'</Begin>
                <End>'</End>
            </Span>
            <KeyWords name="Keywords" bold="true" italic="false" color="Blue">
                <Key word="def"/>
                <Key word="class"/>
                <Key word="if"/>
                <Key word="else"/>
                <Key word="elif"/>
                <Key word="return"/>
            </KeyWords>
            <KeyWords name="UserKeywords" bold="true" italic="false" color="DarkMagenta">
                <Key word="self"/>
                <Key word="True"/>
                <Key word="False"/>
                <Key word="None"/>
            </KeyWords>
        </RuleSet>
    </SyntaxDefinition>
    """
    with open("dummy.xshd", "w") as f:
        f.write(dummy_xshd_content)
    
    parsed_data = parse_xshd("dummy.xshd")
    if parsed_data:
        print("Successfully parsed dummy.xshd:")
        import json
        print(json.dumps(parsed_data, indent=2))
    
    # Test with a non-existent file
    print("\nTesting with a non-existent file:")
    parse_xshd("non_existent.xshd")

    # Test with an invalid XML file
    with open("invalid.xshd", "w") as f:
        f.write("<root><open></root>") # Intentionally invalid XML
    print("\nTesting with an invalid XML file:")
    parse_xshd("invalid.xshd")
