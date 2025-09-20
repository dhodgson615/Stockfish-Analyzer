import os
from typing import List


def find_python_files(root_dir: str) -> List[str]:
    """Find all .py files in the repository recursively."""
    python_files = []

    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith(".py"):
                full_path = os.path.join(dirpath, filename)
                python_files.append(full_path)

    return python_files


def check_docstring_length(file_path: str, max_length: int = 72) -> List[int]:
    """Find docstring lines that exceed the maximum length."""
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    long_lines = []
    in_docstring = False
    docstring_delimiter = None

    for i, line in enumerate(lines):
        line_no = i + 1  # 1-based line numbering
        line = line.rstrip("\n")
        stripped = line.strip()

        # Skip empty lines
        if not stripped:
            continue

        # Check for docstring start
        if not in_docstring:
            if stripped.startswith('"""') or stripped.startswith("'''"):
                docstring_delimiter = (
                    '"""' if stripped.startswith('"""') else "'''"
                )

                in_docstring = True

                # Check if docstring ends on the same line
                if (
                    stripped.endswith(docstring_delimiter)
                    and len(stripped) > 6
                ):
                    in_docstring = False

                # Check line length
                if len(line) > max_length:
                    long_lines.append(line_no)

                continue

        # Check for docstring end if we're in a docstring
        elif in_docstring:
            if docstring_delimiter is not None and docstring_delimiter in line:
                in_docstring = False

            # Check line length for all lines in a docstring
            if len(line) > max_length:
                long_lines.append(line_no)

    return long_lines


def check_indentation(file_path: str) -> List[int]:
    """Find lines where indentation decreases without a blank line
    above.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    problematic_lines = []

    for i in range(1, len(lines)):
        # Get current and previous line
        prev_line = lines[i - 1].rstrip("\n")
        curr_line = lines[i].rstrip("\n")

        # Skip if current line is blank
        if not curr_line.strip():
            continue

        # Skip if previous line is blank
        if not prev_line.strip():
            continue

        # Calculate indentation levels
        prev_indent = len(prev_line) - len(prev_line.lstrip())
        curr_indent = len(curr_line) - len(curr_line.lstrip())

        # Check for decrease in indentation
        if curr_indent < prev_indent:
            stripped_content = curr_line.strip()

            # Skip if line starts with brackets/braces/parentheses
            if not stripped_content or stripped_content[0] not in "(){}[]":
                problematic_lines.append(i + 1)  # 1-based line numbers

    return problematic_lines


def main() -> None:
    repo_root = os.path.dirname(os.path.abspath(__file__))

    if not repo_root:
        repo_root = os.getcwd()

    python_files = find_python_files(repo_root)

    for file_path in python_files:
        relative_path = os.path.relpath(file_path, repo_root)
        long_docstrings = check_docstring_length(file_path)
        problematic_indents = check_indentation(file_path)

        if long_docstrings or problematic_indents:
            print(f"\nFile: {relative_path}")

            if long_docstrings:
                print("        Docstring lines exceeding 72 characters:")

                for line_num in sorted(long_docstrings):
                    print(f"            Line {line_num}")

            if problematic_indents:
                print("        Lines with problematic indentation:")

                for line_num in sorted(problematic_indents):
                    print(f"            Line {line_num}")


if __name__ == "__main__":
    main()
