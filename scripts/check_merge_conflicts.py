#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

CONFLICT_MARKERS = ("<<<<<<< ", "=======", ">>>>>>> ")
SKIP_PARTS = {".git", ".venv", "venv", "env", "__pycache__", ".pytest_cache", "data/output"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Check the repository for unresolved merge conflict markers.")
    parser.add_argument("--base-ref", help="Optional target branch/ref to test with git merge-tree, such as origin/main")
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    marker_hits = find_conflict_markers(repo)
    if marker_hits:
        for path, line_number, marker in marker_hits:
            print(f"{path}:{line_number}: unresolved conflict marker {marker!r}")
        return 1

    if args.base_ref:
        return check_merge_tree(repo, args.base_ref)

    print("No unresolved conflict markers found in working tree files.")
    return 0


def find_conflict_markers(repo: Path) -> list[tuple[str, int, str]]:
    hits: list[tuple[str, int, str]] = []
    for path in repo.rglob("*"):
        relative = path.relative_to(repo)
        if path.is_dir() or any(part in SKIP_PARTS for part in relative.parts):
            continue
        if not is_tracked(repo, relative):
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for line_number, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith(CONFLICT_MARKERS):
                hits.append((str(relative), line_number, stripped))
    return hits


def is_tracked(repo: Path, relative: Path) -> bool:
    result = subprocess.run(["git", "ls-files", "--error-unmatch", str(relative)], cwd=repo, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return result.returncode == 0


def check_merge_tree(repo: Path, base_ref: str) -> int:
    merge_base = subprocess.check_output(["git", "merge-base", "HEAD", base_ref], cwd=repo, text=True).strip()
    result = subprocess.run(["git", "merge-tree", merge_base, base_ref, "HEAD"], cwd=repo, text=True, capture_output=True)
    if result.returncode != 0:
        print(result.stderr or result.stdout, file=sys.stderr)
        return result.returncode
    if "<<<<<<<" in result.stdout:
        print(f"Potential textual conflicts detected when merging HEAD into {base_ref}.")
        return 1
    print(f"No textual conflicts detected by git merge-tree against {base_ref}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
