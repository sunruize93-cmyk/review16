#!/usr/bin/env python3
"""Re-render the recorded real-paper reviews; does not run models again.

Downloads the original PDF from the pinned source and verifies its digest.
Third-party material stays in the user-selected output directory.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from urllib.request import urlopen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    out = args.out.expanduser().resolve()
    if out.exists():
        parser.error("--out must be a new directory")
    here = Path(__file__).resolve().parent
    provenance = json.loads((here / "provenance.json").read_text())
    source = next(x for x in provenance["files"] if x["path"] == "paper.pdf")
    with urlopen(source["url"], timeout=30) as response:
        pdf = response.read(40 * 1024 * 1024 + 1)
    if hashlib.sha256(pdf).hexdigest() != source["sha256"]:
        raise ValueError("Source PDF digest differs from the reviewed manuscript")
    out.mkdir(parents=True)
    (out / "materials").mkdir()
    (out / "materials/manuscript.pdf").write_bytes(pdf)
    (out / "materials/manuscript.pdf").chmod(0o444)
    shutil.copytree(here / "reviews", out / "reviews")
    for name in ("manifest.json", "chair.json"):
        shutil.copy2(here / name, out / name)
    script = here.parents[1] / "skills/review16/scripts/panel.py"
    subprocess.run([sys.executable, str(script), "report", "--run", str(out),
                    "--reviews", str(out / "reviews"), "--out", str(out / "report.html")], check=True)
    print("Recorded judgments re-rendered; no new model evaluation was performed.")


if __name__ == "__main__":
    main()
