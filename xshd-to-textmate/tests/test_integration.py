import unittest
import json
import tempfile
import subprocess
import os
import sys

# Define the base path for the project if needed, assuming tests are run from project root
# Or calculate paths relative to this test file.
# For simplicity, assuming 'Examples' is directly accessible relative to where tests are run
# or using absolute paths based on this file's location.

class TestConversionIntegration(unittest.TestCase):

    def test_xshd_to_textmate_conversion(self):
        # Define paths
        # Assuming the script is run from the root of the repository,
        # so 'Examples/' and 'xshd-to-textmate/' are subdirectories.
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        input_xshd_path = os.path.join(base_dir, 'Examples', 'Syntax.xshd')
        reference_tmLanguage_path = os.path.join(base_dir, 'Examples', 'pcsp.JSON-tmLanguage')

        # Create a temporary file for the output
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.JSON-tmLanguage') as tmp_output_file:
            output_tmLanguage_path = tmp_output_file.name
        
        try:
            # Construct the command
            # Ensure we use the same Python interpreter that's running the tests
            python_executable = sys.executable
            command = [
                python_executable,
                '-m',
                'xshd-to-textmate.src.main',
                input_xshd_path,
                output_tmLanguage_path
            ]

            # Execute the conversion process
            # We need to run this from the base_dir so that the module can be found
            process = subprocess.run(command, capture_output=True, text=True, cwd=base_dir)

            # Check if the process ran successfully
            self.assertEqual(process.returncode, 0, f"Conversion script failed with error: {process.stderr}")
            if "successfully generated" not in process.stdout.lower():
                 print(f"Warning: 'successfully generated' message not found in stdout: {process.stdout}")


            # Read and parse the generated temporary JSON file
            with open(output_tmLanguage_path, 'r') as f:
                generated_json_content = f.read()
            # Handle potential empty file if conversion failed silently before process.returncode check
            if not generated_json_content.strip():
                self.fail(f"Generated output file is empty. Stderr: {process.stderr}, Stdout: {process.stdout}")
            generated_dict = json.loads(generated_json_content)

            # Read and parse the reference JSON file
            with open(reference_tmLanguage_path, 'r') as f:
                reference_dict = json.load(f)

            # Assert that the two dictionaries are equal
            self.assertEqual(generated_dict, reference_dict)

        finally:
            # Clean up the temporary file
            if os.path.exists(output_tmLanguage_path):
                os.remove(output_tmLanguage_path)

if __name__ == '__main__':
    unittest.main()
