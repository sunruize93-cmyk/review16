#!/usr/bin/env python3
"""Fetch one public OpenReview API2 forum without credentials or PDF downloads.

Official API reference, checked 2026-09-17:
https://docs.openreview.net/reference/api-v2/openapi-definition

Usage: python fetch_openreview.py --forum AC5n7xHuR1 --out /tmp/review16-forum
This is a source-audit input, NOT a ready-to-use blinded calibration packet.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin, urlparse
from urllib.request import Request, urlopen

API_BASE = "https://api2.openreview.net"
PAGE_SIZE = 100
MAX_PAGES = 3
MAX_RESPONSE_BYTES = 8 * 1024 * 1024
TIMEOUT_SECONDS = 20
SCORE_TERMS = {
    "rating", "score", "confidence", "recommendation", "soundness",
    "originality", "novelty", "significance", "presentation", "contribution",
    "quality", "reproducibility", "clarity", "correctness",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def content_value(field: Any) -> Any:
    """Unwrap API2 value containers; preserve type and nonstandard payloads."""
    if isinstance(field, dict) and "value" in field:
        return field["value"]
    return field


def score_fields(note: dict[str, Any]) -> list[dict[str, Any]]:
    """Collect candidate fields by name, without interpreting their scale."""
    result = []
    content = note.get("content", {})
    if not isinstance(content, dict):
        return result
    for name, raw in content.items():
        tokens = set(re.findall(r"[a-z]+", name.lower()))
        if tokens & SCORE_TERMS:
            result.append({
                "field_name": name,
                "raw_field": raw,
                "value": content_value(raw),
                "classification": "candidate_score_field_by_name",
                "scale": None,
                "phase": None,
                "phase_status": "not_inferred_source_audit_required",
            })
    return result


def note_metadata(note: dict[str, Any]) -> dict[str, Any]:
    return {
        "note_id": note.get("id"),
        "forum": note.get("forum"),
        "replyto": note.get("replyto"),
        "invitations": note.get("invitations", note.get("invitation", [])),
        "timestamps": {key: note[key] for key in
                       ("cdate", "tcdate", "mdate", "tmdate", "pdate", "odate")
                       if key in note},
        "score_fields": score_fields(note),
    }


def pdf_candidates(submission: dict[str, Any],
                   edits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep observed PDF fields with their exact provenance; never fetch them."""
    candidates = []
    sources = [("current_submission", None, submission)]
    sources.extend(("submission_edit", edit.get("id"), edit.get("note", {}))
                   for edit in edits)
    for source, edit_id, note in sources:
        if not isinstance(note, dict) or not isinstance(note.get("content"), dict):
            continue
        for name, raw in note["content"].items():
            if name.lower().strip("_") != "pdf":
                continue
            value = content_value(raw)
            url = None
            if isinstance(value, str):
                parsed = urlparse(value)
                if parsed.scheme in ("http", "https") and parsed.netloc:
                    url = value
                elif value.startswith("/") and not value.startswith("//"):
                    url = urljoin("https://openreview.net", value)
            candidates.append({
                "source": source,
                "note_id": note.get("id", submission.get("id")),
                "edit_id": edit_id,
                "field_name": name,
                "raw_field": raw,
                "value": value,
                "url": url,
                "downloaded": False,
                "submission_version_verified": False,
            })
    return candidates


def fetch_json(path: str, params: dict[str, Any]) -> dict[str, Any]:
    """One bounded, anonymous GET. No retries, cookies, keys, or full-text fetches."""
    url = API_BASE + path + "?" + urlencode(params)
    record: dict[str, Any] = {"url": url, "retrieved_at": utc_now()}
    request = Request(url, headers={
        "Accept": "application/json",
        "User-Agent": "Review16-public-metadata/0.1",
    }, method="GET")
    try:
        with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            record["http_status"] = response.status
            raw = response.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                raise ValueError("response_exceeds_byte_limit")
            record["response_sha256"] = hashlib.sha256(raw).hexdigest()
            payload = json.loads(raw)
            if not isinstance(payload, dict):
                raise ValueError("expected_json_object")
            record["response"] = payload
            record["ok"] = True
    except HTTPError as exc:
        record.update(ok=False, http_status=exc.code, error=f"HTTP {exc.code}")
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        record.update(ok=False, error=f"{type(exc).__name__}: {exc}")
    return record


def fetch_collection(path: str, params: dict[str, Any], key: str,
                     getter=fetch_json) -> dict[str, Any]:
    """Retrieve at most three 100-item pages; expose truncation and failures."""
    pages = []
    items = []
    complete = False
    failure = None
    for page in range(MAX_PAGES):
        offset = page * PAGE_SIZE
        record = getter(path, {**params, "limit": PAGE_SIZE, "offset": offset})
        pages.append(record)
        if not record.get("ok"):
            failure = record.get("error", "request_failed")
            break
        response = record["response"]
        batch = response.get(key)
        if not isinstance(batch, list) or any(not isinstance(x, dict) for x in batch):
            failure = f"invalid_{key}_response"
            break
        items.extend(batch)
        count = response.get("count")
        if len(batch) < PAGE_SIZE or (
            isinstance(count, int) and not isinstance(count, bool)
            and offset + len(batch) >= count
        ):
            complete = True
            break
    return {
        "items": items,
        "pages": pages,
        "complete": complete,
        "failure": failure,
        "bounded_truncation": not complete and failure is None,
    }


def build_metadata(forum: str, submission: dict[str, Any],
                   replies: list[dict[str, Any]], edits: list[dict[str, Any]],
                   retrieval: dict[str, Any]) -> dict[str, Any]:
    content = submission.get("content", {})
    if not isinstance(content, dict):
        content = {}
    venue = {name: {"raw_field": content[name], "value": content_value(content[name])}
             for name in ("venue", "venueid") if name in content}
    return {
        "schema_version": "review16.openreview-public-metadata.v1",
        "forum": forum,
        "forum_url": "https://openreview.net/forum?" + urlencode({"id": forum}),
        "retrieved_at": utc_now(),
        "api_base": API_BASE,
        "authentication": "anonymous_public_get_only",
        "title": content_value(content.get("title")),
        "venue": venue,
        "submission": note_metadata(submission),
        "reply_records": [note_metadata(note) for note in replies],
        "submission_edit_ids": [edit.get("id") for edit in edits],
        "pdf_candidates": pdf_candidates(submission, edits),
        "submission_version_verified": False,
        "submission_version_status": "requires_source_audit",
        "score_phase": None,
        "score_scale": None,
        "review_score_history_fetched": False,
        "retrieval": retrieval,
        "audit_requirements": [
            "This contains identity, decision, and rating information: never pass it to blinded reviewers.",
            "Candidate score fields are name-based; verify the venue-year invitation rubric.",
            "Current scores may be updated scores; initial versus final review phase is not inferred.",
            "Only submission edits are requested; reviewer-note edit histories are not fetched.",
            "Edit payloads may be partial changes, not complete historical note versions.",
            "PDF candidates have not been downloaded or matched to a submission deadline.",
            "Public visibility and a PDF URL do not establish redistribution rights.",
            "A missing item can reflect restricted visibility, absent data, or bounded retrieval.",
        ],
    }


def write_json(path: Path, value: Any) -> None:
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--forum", required=True, help="A single public forum ID, not a URL")
    parser.add_argument("--out", type=Path, required=True, help="New output directory")
    args = parser.parse_args(argv)
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", args.forum):
        parser.error("--forum must be a single alphanumeric OpenReview ID")
    try:
        args.out.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        parser.error("--out already exists; choose a new directory to preserve prior snapshots")

    record = fetch_json("/notes", {"id": args.forum})
    write_json(args.out / "raw_submission.json", record)
    notes = record.get("response", {}).get("notes", [])
    submission = next((note for note in notes if isinstance(note, dict)
                       and note.get("id") == args.forum), None) if isinstance(notes, list) else None
    if submission is None or submission.get("replyto") is not None or (
        submission.get("forum") not in (None, args.forum)
    ):
        error = record.get("error", "public_top_level_submission_not_found")
        metadata = build_metadata(args.forum, {}, [], [], {
            "status": "unavailable", "error": error, "raw_submission": "raw_submission.json",
        })
        write_json(args.out / "metadata.json", metadata)
        print(f"No public forum snapshot obtained: {error}. See {args.out / 'metadata.json'}", file=sys.stderr)
        return 2

    forum_data = fetch_collection("/notes", {"forum": args.forum}, "notes")
    edit_data = fetch_collection("/notes/edits", {"note.id": args.forum}, "edits")
    write_json(args.out / "raw_forum_notes.json", forum_data)
    write_json(args.out / "raw_submission_edits.json", edit_data)
    replies = [note for note in forum_data["items"]
               if note.get("id") != args.forum and note.get("forum") == args.forum]
    retrieval = {
        "status": "complete_public_snapshot" if forum_data["complete"] and edit_data["complete"] else "partial",
        "scope": "one_forum_current_notes_and_public_submission_edits",
        "page_size": PAGE_SIZE,
        "max_pages_per_collection": MAX_PAGES,
        "max_requests": 1 + 2 * MAX_PAGES,
        "max_response_bytes": MAX_RESPONSE_BYTES,
        "timeout_seconds_per_request": TIMEOUT_SECONDS,
        "raw_files": ["raw_submission.json", "raw_forum_notes.json", "raw_submission_edits.json"],
        "collections": {
            label: {key: data[key] for key in ("complete", "failure", "bounded_truncation")}
            for label, data in (("forum_notes", forum_data), ("submission_edits", edit_data))
        },
    }
    metadata = build_metadata(args.forum, submission, replies, edit_data["items"], retrieval)
    write_json(args.out / "metadata.json", metadata)
    print(json.dumps({"status": retrieval["status"], "forum": args.forum,
                      "replies": len(replies), "submission_edits": len(edit_data["items"]),
                      "submission_version_verified": False, "out": str(args.out)}, ensure_ascii=False))
    return 0 if retrieval["status"] == "complete_public_snapshot" else 1


if __name__ == "__main__":
    raise SystemExit(main())
