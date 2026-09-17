#!/usr/bin/env python3
"""Fetch one public ICLR 2017 paper from the pinned AllenAI PeerRead archive.

Raw human reviews are coordinator-only. This is a retrieval fallback, not proof
that a PDF matches a particular review round. Uses Python 3.9+ stdlib only.
"""
import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

COMMIT = "9bb37751781a900cee9e74ec3105997732c8e8e5"
BASE = "https://raw.githubusercontent.com/allenai/PeerRead/" + COMMIT
MAX_BYTES = 40 * 1024 * 1024


def recommendations(payload):
    """Keep source recommendation entries; never use annotated aspect scores.

    Entries are not deduplicated or interpreted as initial/final ratings.
    Exclude committee decisions, comments without scores and meta-reviews.
    """
    result = []
    for index, review in enumerate(payload.get("reviews", [])):
        identity = review.get("OTHER_KEYS", "")
        value = review.get("RECOMMENDATION")
        if (review.get("is_meta_review") or review.get("IS_META_REVIEW")
                or not isinstance(identity, str)
                or not re.fullmatch(r"ICLR 2017 conference AnonReviewer\d+", identity)
                or isinstance(value, bool) or not isinstance(value, (int, float))
                or value not in range(1, 11)):
            continue
        result.append({"source_review_index": index, "source_reviewer": identity,
                       "score": value, "source_date": review.get("DATE"),
                       "review_phase": None})
    return result


def fetch(url, pdf=False):
    request = Request(url, headers={"User-Agent": "Review16-PeerRead/0.1"})
    with urlopen(request, timeout=30) as response:
        data = response.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("response exceeds 40 MiB limit")
    if pdf and not data.startswith(b"%PDF-"):
        raise ValueError("response is not a PDF")
    if not pdf:
        payload = json.loads(data)
        if not isinstance(payload, dict) or not isinstance(payload.get("reviews"), list):
            raise ValueError("invalid PeerRead review payload")
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper-id", required=True)
    parser.add_argument("--split", choices=["train", "dev", "test"], required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--download-pdf", action="store_true")
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9]+", args.paper_id):
        parser.error("paper-id must be numeric")
    if args.out.exists():
        parser.error("output directory must be new")
    args.out.mkdir(parents=True, mode=0o700)
    prefix = BASE + "/data/iclr_2017/" + args.split
    metadata = {
        "schema": "review16.peerread-source-audit.v1", "source_commit": COMMIT,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "paper_id": args.paper_id, "split": args.split,
        "source_repository": "https://github.com/allenai/PeerRead",
        "submission_version_verified": False, "review_phase": None,
        "anchor_eligible": False,
        "limitations": ["Archive presence does not establish manuscript/review-round alignment.",
                        "Dates alone do not distinguish initial and revised recommendations.",
                        "Raw reviews and metadata contain outcomes: keep out of reviewer contexts.",
                        "Third-party papers/reviews retain their own rights; not covered by Review16 MIT."],
        "files": [], "ok": False,
    }
    try:
        paths = [("reviews_raw/" + args.paper_id + ".json", "reviews.private.json", False)]
        if args.download_pdf:
            paths.append(("pdfs/" + args.paper_id + ".pdf", "paper.pdf", True))
        for remote, local, is_pdf in paths:
            url = prefix + "/" + remote
            raw = fetch(url, pdf=is_pdf)
            path = args.out / local
            path.write_bytes(raw)
            path.chmod(0o600)
            metadata["files"].append({"path": local, "url": url,
                                      "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)})
            if not is_pdf:
                payload = json.loads(raw)
                metadata["title"] = payload.get("title")
                metadata["recommendation_entries"] = recommendations(payload)
        metadata["ok"] = True
    except Exception as exc:
        metadata["error"] = type(exc).__name__ + ": " + str(exc)
    path = args.out / "metadata.private.json"
    path.write_text(json.dumps(metadata, indent=2) + "\n")
    path.chmod(0o600)
    print(json.dumps({"ok": metadata["ok"], "metadata": str(path), "anchor_eligible": False}))
    return 0 if metadata["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
