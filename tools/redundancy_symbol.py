from pathlib import Path

import regex

PATTERN = r"^\s*(?:success|error|warning|info|step|debug).*?\p{So}"

# text = "success(📦This is a sample text with success, error, warning, info, step, and debug symbols."
# print(regex.findall(PATTERN, text))
src_path = Path(__file__).parent.parent / "src" / "oppm"

for file in src_path.rglob("*.py"):
    with file.open("r", encoding="utf-8") as f:
        content = f.readlines()
        for i, line in enumerate(content):
            find_res = regex.findall(PATTERN, line)
            if find_res:
                print(f"{file}:{i + 1}: {line.strip()}")
