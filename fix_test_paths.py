#!/usr/bin/env python3
"""
Script to fix hardcoded test file paths in test files.
Converts patterns like:
    self.test_data_file = "filename.json"
    ...
    self.file_manager.create_test_file(self.test_data_file, data)

To:
    self.test_data_file = self.file_manager.create_test_file("filename.json", data)
"""

import re
import glob
from pathlib import Path


def fix_test_file(filepath):
    """Fix hardcoded paths in a test file."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original_content = content

    # Pattern: assignment of filename, then later creation with that variable
    # We need to consolidate these into one line

    # Find all test file assignments
    assignments = list(
        re.finditer(r'(\s+)self\.(test_(?:data|settings)_file) = "([^"]+)"', content)
    )

    changes_made = False

    for match in reversed(assignments):  # Process from end to avoid offset issues
        indent, var_name, filename = match.group(1), match.group(2), match.group(3)

        # Look for the corresponding create_test_file call
        create_pattern = (
            rf"self\.file_manager\.create_test_file\(self\.{re.escape(var_name)},"
        )

        # Search for this pattern after the assignment
        search_start = match.end()
        create_match = re.search(create_pattern, content[search_start:])

        if create_match:
            # Find the complete create_test_file call
            create_start = search_start + create_match.start()

            # Find the end of the create_test_file call (matching parentheses)
            paren_count = 0
            i = create_start + len("self.file_manager.create_test_file(")
            while i < len(content):
                if content[i] == "(":
                    paren_count += 1
                elif content[i] == ")":
                    if paren_count == 0:
                        break
                    paren_count -= 1
                i += 1

            create_end = i + 1

            # Extract the data parameter (second argument)
            call_content = content[create_start:create_end]
            # Extract second parameter after first comma
            params_start = call_content.find("(") + 1
            params = call_content[params_start:-1]

            # Split by comma, handling nested structures
            first_comma = find_first_comma(params)
            if first_comma > 0:
                data_param = params[first_comma + 1 :].strip()

                # Create the new assignment
                new_assignment = f'{indent}self.{var_name} = self.file_manager.create_test_file("{filename}", {data_param})'

                # Replace the assignment
                content = (
                    content[: match.start()]
                    + new_assignment
                    + content[match.end() : create_start]
                    + content[create_end:]
                )
                changes_made = True

    if changes_made and content != original_content:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    return False


def find_first_comma(s):
    """Find first comma not inside parentheses, brackets, or braces."""
    depth = 0
    for i, char in enumerate(s):
        if char in "({[":
            depth += 1
        elif char in ")}]":
            depth -= 1
        elif char == "," and depth == 0:
            return i
    return -1


def main():
    """Fix all test files."""
    test_patterns = [
        "tests/test_completion*.py",
        "tests/test_button*.py",
        "tests/test_analysis*.py",
        "tests/test_csv_export.py",
    ]

    files_updated = []

    for pattern in test_patterns:
        for filepath in glob.glob(pattern):
            if fix_test_file(filepath):
                files_updated.append(filepath)
                print(f"Updated: {filepath}")

    if files_updated:
        print(f"\nTotal files updated: {len(files_updated)}")
    else:
        print("No files needed updating")


if __name__ == "__main__":
    main()
