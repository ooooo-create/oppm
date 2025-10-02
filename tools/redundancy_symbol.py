from pathlib import Path
from typing import TypedDict

# pyrefly: ignore  # import-error
import regex

PATTERN = r"^\s*(?:success|error|warning|info|step|debug).*?\p{So}"

# text = "success(📦This is a sample text with success, error, warning, info, step, and debug symbols."
# print(regex.findall(PATTERN, text))
src_path = Path(__file__).parent.parent / "src" / "oppm"


class ErrorLine(TypedDict):
    file: str
    line_number: int
    message: str


error_lines: list[ErrorLine] = []

for file in src_path.rglob("*.py"):
    with file.open("r", encoding="utf-8") as f:
        content = f.readlines()
        for i, line in enumerate(content):
            find_res = regex.findall(PATTERN, line)
            if find_res:
                error_lines.append(ErrorLine(file=str(file), line_number=i + 1, message=line.strip()))
if len(error_lines) > 0:
    print("❌  Found redundancy symbols:")
    for error_line in error_lines:
        print(f"{error_line['file']}:{error_line['line_number']}: {error_line['message']}")
    exit(1)
else:
    print("✅  No redundancy symbols found.")
    exit(0)
