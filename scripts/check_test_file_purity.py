"""Fail when test modules define non-test functions or classes.

Policy:
- Test modules should contain test functions only.
- Shared setup/helpers/mocks should live in conftest.py or tests/support/.
"""

from __future__ import annotations

import ast
from pathlib import Path


TESTS_ROOT = Path("tests")


def should_skip(path: Path) -> bool:
    name = path.name
    if name == "conftest.py" or name == "__init__.py":
        return True
    parts = set(path.parts)
    return "support" in parts or "data" in parts


def find_violations(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    violations: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            violations.append(f"{path}:{node.lineno} top-level class '{node.name}' is not allowed in test modules")
            continue
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("test_"):
            violations.append(
                f"{path}:{node.lineno} top-level function '{node.name}' is not allowed in test modules"
            )
    return violations


def iter_test_modules() -> list[Path]:
    modules = []
    for path in TESTS_ROOT.rglob("test_*.py"):
        if should_skip(path):
            continue
        modules.append(path)
    return sorted(modules)


def main() -> int:
    violations: list[str] = []
    for path in iter_test_modules():
        violations.extend(find_violations(path))

    if not violations:
        print("check_test_file_purity: ok")
        return 0

    print("check_test_file_purity: violations found")
    for violation in violations:
        print(f"- {violation}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
