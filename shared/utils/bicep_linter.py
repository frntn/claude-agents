"""
Utility helpers for linting and auto-fixing Bicep templates.

These helpers provide lightweight static analysis that focuses on the two
warning classes we routinely see when running `bicep build` / `az deployment`:

1. `no-unused-params` – parameters declared but never referenced.
2. `no-unnecessary-dependson` – explicit dependsOn entries that the compiler
   can infer automatically.

The goal is to keep generated infrastructure templates warning-free without
relying on the Bicep CLI being available in the execution environment.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Iterable, List


@dataclass
class BicepLintResult:
    """Result for a single Bicep file lint operation."""

    file: Path
    removed_parameters: List[str] = field(default_factory=list)
    removed_dependson: List[str] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return bool(self.removed_parameters or self.removed_dependson)


def lint_bicep_targets(targets: Iterable[Path]) -> List[BicepLintResult]:
    """
    Lint and auto-fix a collection of Bicep files/directories.

    Args:
        targets: Iterable of file system paths (files or directories).

    Returns:
        List of lint results ordered by path.
    """
    files: List[Path] = []
    for target in targets:
        if target.is_file() and target.suffix == ".bicep":
            files.append(target)
        elif target.is_dir():
            files.extend(sorted(target.rglob("*.bicep")))

    results: List[BicepLintResult] = []
    for file_path in sorted(set(files)):
        results.append(_lint_single_file(file_path))

    return results


def format_lint_report(results: List[BicepLintResult]) -> str:
    """
    Create a human-friendly report from lint results.
    """
    if not results:
        return "✅ No Bicep files found to lint."

    changed_files = [r for r in results if r.changed]
    if not changed_files:
        return "✅ Bicep lint completed – no changes required."

    report_lines: List[str] = [
        "🛠️  Bicep Linter Auto-Fixes Applied:",
        "",
    ]

    for result in changed_files:
        report_lines.append(f"- {result.file}")
        if result.removed_parameters:
            removed = ", ".join(result.removed_parameters)
            report_lines.append(f"  • Removed unused parameters: {removed}")
        if result.removed_dependson:
            removed = ", ".join(result.removed_dependson)
            report_lines.append(f"  • Removed redundant dependsOn entries: {removed}")
    return "\n".join(report_lines)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_PARAM_PATTERN = re.compile(r"^\s*param\s+([a-zA-Z_][\w]*)\b.*$", re.MULTILINE)


def _lint_single_file(path: Path) -> BicepLintResult:
    """Lint and auto-fix a single Bicep file."""
    original_text = path.read_text(encoding="utf-8")
    updated_text = original_text

    removed_params: List[str]
    updated_text, removed_params = _remove_unused_parameters(updated_text)

    removed_depends: List[str]
    updated_text, removed_depends = _remove_redundant_dependson(updated_text)

    if updated_text != original_text:
        path.write_text(updated_text, encoding="utf-8")

    return BicepLintResult(
        file=path,
        removed_parameters=removed_params,
        removed_dependson=removed_depends,
    )


def _remove_unused_parameters(content: str) -> tuple[str, List[str]]:
    """
    Remove parameter declarations that are never referenced elsewhere.
    """
    removed: List[str] = []
    if not content:
        return content, removed

    # Count occurrences once using the original content.
    occurrences = {}
    for match in _PARAM_PATTERN.finditer(content):
        name = match.group(1)
        occurrences[name] = len(re.findall(rf"\b{name}\b", content))

    if not occurrences:
        return content, removed

    lines = content.splitlines()
    filtered_lines: List[str] = []
    for line in lines:
        match = _PARAM_PATTERN.match(line)
        if match:
            name = match.group(1)
            if occurrences.get(name, 0) <= 1:
                removed.append(name)
                continue  # Drop the entire line
        filtered_lines.append(line)

    updated = "\n".join(filtered_lines)
    if content.endswith("\n"):
        updated += "\n"
    updated = re.sub(r"\n{3,}", "\n\n", updated)
    return updated, removed


def _remove_redundant_dependson(content: str) -> tuple[str, List[str]]:
    """
    Remove dependsOn blocks when every entry points to a locally declared
    module/resource. Bicep will infer those dependencies automatically.
    """
    removed: List[str] = []
    if not content:
        return content, removed

    lines = content.splitlines()
    updated_lines: List[str] = []
    i = 0
    length = len(lines)

    while i < length:
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith("dependsOn:"):
            block_lines = [line]
            i += 1
            while i < length:
                block_lines.append(lines[i])
                if lines[i].strip().endswith("]"):
                    i += 1
                    break
                i += 1
            else:
                # Unterminated block; keep as-is
                updated_lines.extend(block_lines)
                break

            block_text = "\n".join(block_lines)
            entries = _extract_dependson_entries(block_text)

            if entries and _all_entries_are_local_symbols(entries, content):
                removed.extend(entries)
                continue  # Drop the entire dependsOn block

            updated_lines.extend(block_lines)
        else:
            updated_lines.append(line)
            i += 1

    updated = "\n".join(updated_lines)
    if content.endswith("\n"):
        updated += "\n"
    updated = re.sub(r"\n{3,}", "\n\n", updated)
    return updated, removed


def _extract_dependson_entries(block_text: str) -> List[str]:
    """
    Extract identifier entries from a dependsOn block.
    """
    entries = []
    for token in re.split(r"[,\\n]", block_text):
        token = token.strip()
        if not token or token.startswith("dependsOn"):
            continue
        # Remove trailing comments
        token = token.split("//", maxsplit=1)[0].strip()
        if re.match(r"^[a-zA-Z_][\w]*$", token):
            entries.append(token)
    return entries


def _all_entries_are_local_symbols(entries: List[str], content: str) -> bool:
    """
    Check if every dependsOn entry corresponds to a module/resource declared in
    the same file. We assume these dependencies can be inferred automatically.
    """
    for entry in entries:
        pattern = rf"\b(module|resource)\s+{entry}\b"
        if not re.search(pattern, content):
            return False
    return True
