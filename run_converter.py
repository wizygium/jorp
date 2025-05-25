#!/usr/bin/env python3
import sys
import os
import subprocess

def main():
    # Directory of this script (should be project root /app)
    script_root_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Path to the package directory that contains src/
    package_dir = os.path.join(script_root_dir, "xshd-to-textmate")

    # Adjust arguments. Paths need to be relative to the 'package_dir' or absolute.
    # For simplicity, we'll make paths absolute if they are relative to the original CWD.
    # Or, more simply, adjust relative paths by prepending "../" because we cd into package_dir.
    
    adjusted_args = []
    # sys.argv[0] is the script name, actual args start from sys.argv[1]
    script_args = sys.argv[1:]

    # Heuristic to identify path arguments (input_file, output_file)
    # This assumes they are the first two non-option arguments.
    # A more robust solution would involve some level of pre-parsing or fixed positions.
    
    # Let's find the input_file and output_file arguments.
    # Argparse in src/main.py expects input_file and output_file as positional.
    
    processed_positional_args = 0
    for arg in script_args:
        if not arg.startswith("-"):
            processed_positional_args += 1
            if processed_positional_args <= 2: # input_file or output_file
                # Prepend "../" to make it relative to 'package_dir'
                # This assumes 'arg' was originally relative to 'script_root_dir'
                # os.path.abspath resolves it from the current CWD (script_root_dir)
                # then os.path.relpath makes it relative to package_dir
                abs_path = os.path.abspath(arg)
                relative_to_package_dir = os.path.relpath(abs_path, package_dir)
                adjusted_args.append(relative_to_package_dir)
            else: # Other positional args, pass as is
                adjusted_args.append(arg)
        else: # Option arguments like --verbose
            adjusted_args.append(arg)

    cmd = [
        "python", "-m", "src.main"
    ] + adjusted_args
    
    verbose = "--verbose" in adjusted_args or "-v" in adjusted_args
    if verbose:
        print(f"Project root (original CWD): {script_root_dir}")
        print(f"Package directory (target CWD): {package_dir}")
        print(f"Original arguments: {script_args}")
        print(f"Adjusted arguments for subprocess: {adjusted_args}")
        print(f"Executing command: {' '.join(cmd)}")
        print(f"From CWD: {package_dir}")

    try:
        process = subprocess.run(cmd, cwd=package_dir, check=True, capture_output=True, text=True)
        if verbose or process.stdout: # Print stdout if verbose or if there's any output
            print(process.stdout.strip())
        # If successful and not verbose, stderr should be empty or for warnings only.
        # If check=True, non-zero exit codes raise CalledProcessError, stderr is in error.stderr
        if process.stderr and verbose : # Only print stderr if verbose, as main_cli might print to stderr for errors
            print(f"Stderr from subprocess:\n{process.stderr.strip()}", file=sys.stderr)

    except subprocess.CalledProcessError as e:
        # Errors from main_cli (e.g., file not found, parsing error) will be printed by main_cli itself.
        # This captures Python execution errors or if main_cli exits non-zero.
        print(f"Error during execution:", file=sys.stderr)
        if e.stdout:
            print(e.stdout.strip(), file=sys.stderr) # main_cli might have printed to its stdout before erroring
        if e.stderr:
            print(e.stderr.strip(), file=sys.stderr) # main_cli's error messages
        sys.exit(e.returncode)
    except FileNotFoundError:
        # This would be if "python3" is not found, very unlikely in this environment.
        print("Error: python3 command not found.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
