#!/usr/bin/env python3
"""Install Review16 locally, without overwriting an existing skill."""
import argparse
import os
from pathlib import Path
import shutil


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skills-dir", type=Path, default=Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "skills")
    args = parser.parse_args()
    source = Path(__file__).resolve().parent / "skills" / "review16"
    destination = args.skills_dir.expanduser().resolve() / "review16"
    if destination.exists() or destination.is_symlink():
        parser.error(f"Existing installation preserved: {destination}. Back it up or choose --skills-dir.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"))
    print(f"Installed Review16: {destination}\nStart a new Codex session and ask: Use $review16 to review this paper.")


if __name__ == "__main__":
    main()
