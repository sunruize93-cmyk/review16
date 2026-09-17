#!/usr/bin/env python3
"""Build blinded anchor comparisons and report conservative, sample-only ranks.

Standard library only. No LLM calls, downloads, or acceptance-probability model.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import itertools
import json
import math
from pathlib import Path
import random
import re
import secrets
import shutil
import sys
import tempfile


class ValidationError(ValueError):
    pass


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def read_json(path):
    def invalid(value):
        raise ValidationError(f"non-finite JSON number: {value}")
    def finite_float(value):
        parsed = float(value)
        if not math.isfinite(parsed):
            invalid(value)
        return parsed
    with Path(path).open(encoding="utf-8") as stream:
        return json.load(stream, object_pairs_hook=_object, parse_constant=invalid, parse_float=finite_float)


def keys(value, required, optional=(), where="object"):
    if not isinstance(value, dict):
        raise ValidationError(f"{where} must be an object")
    missing = set(required) - value.keys()
    extra = value.keys() - set(required) - set(optional)
    if missing or extra:
        raise ValidationError(f"{where}: missing keys {sorted(missing)}; unknown keys {sorted(extra)}")


def string(value, where):
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{where} must be a nonempty string")
    return value


def number(value, where):
    try:
        finite = math.isfinite(value) if type(value) in (int, float) else False
    except OverflowError:
        finite = False
    if not finite:
        raise ValidationError(f"{where} must be a finite number")
    return value


def integer(value, where, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValidationError(f"{where} must be an integer >= {minimum}")
    return value


def schema(value, expected):
    if value != expected:
        raise ValidationError(f"schema must be {expected!r}")


def unique_strings(values, where, minimum=1):
    if not isinstance(values, list) or len(values) < minimum:
        raise ValidationError(f"{where} must be an array with at least {minimum} entries")
    for value in values:
        string(value, where)
    if len(values) != len(set(values)):
        raise ValidationError(f"duplicate entries in {where}")
    return values


def write_new(path, value):
    path = Path(path)
    # Exclusive creation also refuses existing files and symlinks.
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def text_material(item, base, where):
    string(item["id"], f"{where}.id")
    if item["blinding_checked"] is not True:
        raise ValidationError(f"{where}: blinding_checked must be true; human inspection required")
    if item["material_level"] != "fulltext":
        raise ValidationError(f"{where}: comparable fulltext required; abstracts alone require abstention")
    raw_path = string(item["blinded_text_path"], f"{where}.blinded_text_path")
    path = (base / raw_path).resolve()
    if not path.is_file():
        raise ValidationError(f"{where}: local text file missing: {path}")
    text = path.read_text(encoding="utf-8")
    if not text.strip() or "\x00" in text:
        raise ValidationError(f"{where}: expected nonempty UTF-8 plain text")
    # Whitespace-normalized duplicates are rejected, including target/anchor duplicates.
    fingerprint = hashlib.sha256(" ".join(text.split()).encode()).hexdigest()
    return text, fingerprint, str(path)


def load_corpus(path):
    path = Path(path).resolve()
    corpus = read_json(path)
    keys(corpus, ["schema", "venue", "year", "track", "review_phase", "score_scale", "bands", "papers"],
         ["synthetic"], "corpus")
    schema(corpus["schema"], "review16.anchor-corpus.v1")
    for field in ("venue", "track", "review_phase"):
        string(corpus[field], f"corpus.{field}")
    integer(corpus["year"], "corpus.year", 1900)
    if "synthetic" in corpus and type(corpus["synthetic"]) is not bool:
        raise ValidationError("corpus.synthetic must be a boolean")
    scale = corpus["score_scale"]
    keys(scale, ["name", "min", "max", "higher_is_better"], ["values"], where="score_scale")
    string(scale["name"], "score_scale.name")
    low, high = number(scale["min"], "score_scale.min"), number(scale["max"], "score_scale.max")
    if low >= high or type(scale["higher_is_better"]) is not bool:
        raise ValidationError("score_scale requires min < max and boolean higher_is_better")
    allowed_values = scale.get("values")
    if "values" in scale:
        if not isinstance(allowed_values, list) or not allowed_values:
            raise ValidationError("score_scale.values must be a nonempty array of allowed numeric ratings")
        for value in allowed_values:
            if not low <= number(value, "score_scale.values entry") <= high:
                raise ValidationError("score_scale.values entry outside scale bounds")
        if len(set(allowed_values)) != len(allowed_values):
            raise ValidationError("score_scale.values contains duplicate numeric ratings")
    bands = corpus["bands"]
    if not isinstance(bands, list) or not bands:
        raise ValidationError("bands must be a nonempty array")
    seen = set()
    for band in bands:
        keys(band, ["id", "lower", "upper"], where="band")
        band_id = string(band["id"], "band.id")
        if band_id in seen:
            raise ValidationError("duplicate band id")
        seen.add(band_id)
        a, b = number(band["lower"], "band.lower"), number(band["upper"], "band.upper")
        if not low <= a < b <= high:
            raise ValidationError("band bounds must satisfy scale.min <= lower < upper <= scale.max")
    bands = sorted(bands, key=lambda band: band["lower"])
    if bands[0]["lower"] != low or bands[-1]["upper"] != high:
        raise ValidationError("bands must cover the complete score scale")
    for left, right in zip(bands, bands[1:]):
        if left["upper"] != right["lower"]:
            raise ValidationError("bands must be contiguous and non-overlapping")
    if not isinstance(corpus["papers"], list):
        raise ValidationError("papers must be an array")
    papers, ids, hashes = [], set(), set()
    for index, raw in enumerate(corpus["papers"]):
        where = f"papers[{index}]"
        keys(raw, ["id", "blinded_text_path", "blinding_checked", "material_level",
                   "submission_version_verified", "human_scores"], ["provenance"], where)
        if raw["submission_version_verified"] is not True:
            raise ValidationError(f"{where}: submission_version_verified must be true")
        if "provenance" in raw:
            string(raw["provenance"], f"{where}.provenance")
        scores = raw["human_scores"]
        if not isinstance(scores, list) or not scores:
            raise ValidationError(f"{where}: human_scores must be a nonempty array")
        for score in scores:
            if not low <= number(score, "human score") <= high:
                raise ValidationError(f"{where}: human score outside scale")
            if allowed_values is not None and score not in allowed_values:
                raise ValidationError(f"{where}: human score is not in score_scale.values")
        text, digest, source = text_material(raw, path.parent, where)
        if raw["id"] in ids or digest in hashes:
            raise ValidationError(f"{where}: duplicate paper id or normalized text")
        ids.add(raw["id"])
        hashes.add(digest)
        mean = math.fsum(score / len(scores) for score in scores)
        band_id = next(b["id"] for b in bands if b["lower"] <= mean < b["upper"]
                       or (mean == high and b["upper"] == high))
        papers.append({**raw, "text": text, "fingerprint": digest, "source_path": source,
                       "human_score_mean": mean, "band_id": band_id})
    return corpus, bands, papers


def random_id(rng, used, prefix):
    while True:
        result = prefix + f"{rng.getrandbits(64):016x}"
        if result not in used:
            used.add(result)
            return result


def prepare(corpus_path, target_path, out, per_band=10, seed=None):
    integer(per_band, "per_band", 1)
    if seed is not None:
        integer(seed, "seed")
    out = Path(out)
    if out.exists() or out.is_symlink():
        raise ValidationError(f"refusing to overwrite existing output: {out}")
    corpus, bands, papers = load_corpus(corpus_path)
    target_path = Path(target_path).resolve()
    target = read_json(target_path)
    keys(target, ["schema", "id", "blinded_text_path", "blinding_checked", "material_level"], ["synthetic"], "target")
    schema(target["schema"], "review16.target.v1")
    if "synthetic" in target and type(target["synthetic"]) is not bool:
        raise ValidationError("target.synthetic must be a boolean")
    text, digest, source = text_material(target, target_path.parent, "target")
    if any(p["id"] == target["id"] or p["fingerprint"] == digest for p in papers):
        raise ValidationError("target duplicates a corpus paper id or normalized text")
    target = {**target, "text": text, "fingerprint": digest, "source_path": source}
    seed = secrets.randbits(128) if seed is None else seed
    rng = random.Random(seed)
    selected, coverage = [], []
    for band in bands:
        pool = [p for p in papers if p["band_id"] == band["id"]]
        chosen = rng.sample(pool, min(per_band, len(pool)))
        selected.extend(chosen)
        coverage.append({"band_id": band["id"], "available": len(pool), "requested": per_band,
                         "selected": len(chosen), "shortfall": max(0, per_band-len(pool))})
    selected.append(target)
    rng.shuffle(selected)
    used, public_papers, private_papers = set(), [], []
    out.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{out.name}-", dir=out.parent))
    try:
        (staging / "public" / "texts").mkdir(parents=True)
        (staging / "private").mkdir(mode=0o700)
        for paper in selected:
            anonymous_id = random_id(rng, used, "P")
            relative = f"texts/{anonymous_id}.txt"
            (staging / "public" / relative).write_text(paper["text"], encoding="utf-8")
            public_papers.append({"anonymous_id": anonymous_id, "text_path": relative, "material_level": "fulltext"})
            private_papers.append({k: v for k, v in paper.items() if k != "text"} | {
                "anonymous_id": anonymous_id, "is_target": paper is target})
        manifest = {"schema": "review16.blind-package.v1", "papers": public_papers}
        mapping = {"schema": "review16.private-mapping.v1", "seed": seed,
                   "context": {k: corpus[k] for k in ("venue", "year", "track", "review_phase", "score_scale")},
                   "synthetic": bool(corpus.get("synthetic") or target.get("synthetic")),
                   "bands": bands, "coverage": coverage,
                   "blinding_status": "Operator declarations checked; model-memory decontamination NOT established.",
                   "papers": private_papers}
        write_new(staging / "public" / "manifest.json", manifest)
        write_new(staging / "private" / "mapping.json", mapping)
        (staging / "private" / "mapping.json").chmod(0o600)
        # mkdir is exclusive: unlike rename, it cannot replace an existing empty directory.
        out.mkdir()
        for child in staging.iterdir():
            shutil.move(str(child), str(out / child.name))
        staging.rmdir()
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return {"output": str(out.resolve()), "sampled_anchors": len(selected)-1, "coverage": coverage,
            "synthetic": mapping["synthetic"], "acceptance_probability": None,
            "warning": "Only give reviewers public/. Keep private/ and this coverage report hidden until reviews lock."}


def load_public(path):
    base = Path(path).resolve().parent
    manifest = read_json(path)
    keys(manifest, ["schema", "papers"], where="public manifest")
    schema(manifest["schema"], "review16.blind-package.v1")
    if not isinstance(manifest["papers"], list):
        raise ValidationError("manifest papers must be an array")
    ids, paths = [], set()
    for paper in manifest["papers"]:
        keys(paper, ["anonymous_id", "text_path", "material_level"], where="public paper")
        relative = Path(string(paper["text_path"], "text_path"))
        source = (base / relative).resolve()
        if relative.is_absolute() or ".." in relative.parts or base not in source.parents:
            raise ValidationError("public text_path must stay inside the public package")
        if source in paths or not source.is_file() or not source.read_text(encoding="utf-8").strip():
            raise ValidationError("public text must be present, nonempty, and unique")
        paths.add(source)
        if paper["material_level"] != "fulltext":
            raise ValidationError("only comparable fulltext packages can be planned")
        ids.append(paper["anonymous_id"])
    unique_strings(ids, "anonymous IDs", 2)
    if any(re.fullmatch(r"P[0-9a-f]{16}", item) is None for item in ids):
        raise ValidationError("anonymous paper IDs must be generated P + 16 lowercase hex digits")
    return ids


def plan_pairs(public_path, out, neighbors=2, all_pairs=False, seed=None):
    integer(neighbors, "neighbors", 1)
    if seed is not None:
        integer(seed, "seed")
    ids = load_public(public_path)
    rng = random.Random(secrets.randbits(128) if seed is None else seed)
    ring = ids[:]
    rng.shuffle(ring)
    if all_pairs:
        pairs = list(itertools.combinations(sorted(ids), 2))
    else:
        pairs = sorted({tuple(sorted((ring[i], ring[(i+step) % len(ring)])))
                        for i in range(len(ring)) for step in range(1, min(neighbors, len(ring)//2)+1)})
    comparisons, used = [], set()
    for first, second in pairs:
        for left, right in ((first, second), (second, first)):
            comparisons.append({"comparison_id": random_id(rng, used, "C"), "left": left, "right": right})
    rng.shuffle(comparisons)
    plan = {"schema": "review16.pair-plan.v1", "anonymous_ids": ids,
            "protocol": "all-pairs" if all_pairs else "balanced-connected-ring",
            "comparisons": comparisons}
    write_new(out, plan)
    return {"papers": len(ids), "unordered_pairs": len(pairs), "comparisons": len(comparisons),
            "note": "Freeze this plan before judging; show each comparison separately. AB/BA reversals are not independent samples."}


def load_plan(path):
    plan = read_json(path)
    keys(plan, ["schema", "anonymous_ids", "protocol", "comparisons"], where="plan")
    schema(plan["schema"], "review16.pair-plan.v1")
    ids = unique_strings(plan["anonymous_ids"], "plan anonymous_ids", 2)
    if any(re.fullmatch(r"P[0-9a-f]{16}", item) is None for item in ids):
        raise ValidationError("invalid anonymous paper ID format")
    if plan["protocol"] not in ("all-pairs", "balanced-connected-ring"):
        raise ValidationError("unknown plan protocol")
    if not isinstance(plan["comparisons"], list) or not plan["comparisons"]:
        raise ValidationError("comparisons must be a nonempty array")
    by_id, directed, graph = {}, set(), defaultdict(set)
    for row in plan["comparisons"]:
        keys(row, ["comparison_id", "left", "right"], where="comparison")
        cid = string(row["comparison_id"], "comparison_id")
        left, right = row["left"], row["right"]
        if not isinstance(left, str) or not isinstance(right, str) or left not in ids or right not in ids or left == right:
            raise ValidationError("comparison must have two distinct known anonymous IDs")
        if cid in by_id or (left, right) in directed:
            raise ValidationError("duplicate comparison ID or directed pair")
        by_id[cid] = row
        directed.add((left, right))
        graph[left].add(right)
        graph[right].add(left)
    if any((b, a) not in directed for a, b in directed):
        raise ValidationError("every comparison must have its AB/BA reverse")
    visited, pending = set(), [ids[0]]
    while pending:
        item = pending.pop()
        if item not in visited:
            visited.add(item)
            pending.extend(graph[item]-visited)
    if visited != set(ids):
        raise ValidationError("comparison graph must be connected")
    degrees = [len(graph[item]) for item in ids]
    if max(degrees) != min(degrees):
        raise ValidationError("comparison graph must have equal paper degree")
    if plan["protocol"] == "all-pairs" and len(directed) != len(ids)*(len(ids)-1):
        raise ValidationError("all-pairs plan is incomplete")
    return plan, by_id


def load_decisions(path, by_id):
    data = read_json(path)
    keys(data, ["schema", "decisions"], where="decisions file")
    schema(data["schema"], "review16.pair-decisions.v1")
    if not isinstance(data["decisions"], list):
        raise ValidationError("decisions must be an array")
    rows, families = {}, {}
    for row in data["decisions"]:
        keys(row, ["comparison_id", "reviewer_id", "model_family", "decision", "evidence", "recognized_paper"], where="decision")
        for field in ("comparison_id", "reviewer_id", "model_family", "evidence"):
            string(row[field], field)
        if row["comparison_id"] not in by_id:
            raise ValidationError("decision comparison_id is not in the preregistered plan")
        if row["decision"] not in ("left", "right", "tie", "abstain"):
            raise ValidationError("decision must be left, right, tie, or abstain")
        if type(row["recognized_paper"]) is not bool:
            raise ValidationError("recognized_paper must be an explicit boolean")
        reviewer = row["reviewer_id"]
        key = reviewer, row["comparison_id"]
        if key in rows:
            raise ValidationError("duplicate decision for one reviewer and comparison")
        if reviewer in families and families[reviewer] != row["model_family"]:
            raise ValidationError("reviewer model_family changed within run")
        families[reviewer] = row["model_family"]
        rows[key] = row
    return rows, families


def _canonical(row, comparison):
    if row["decision"] in ("tie", "abstain"):
        return row["decision"]
    return comparison[row["decision"]]


def _rank(relations, plan_complete=True):
    counts = Counter(relations.values())
    counts = {key: counts[key] for key in ("win", "tie", "loss", "uncertain")}
    return {"sample_anchor_rank": {"best": 1+counts["loss"] if plan_complete else 1,
                                   "worst": 1+counts["loss"]+counts["tie"]+counts["uncertain"] if plan_complete else len(relations)+1,
                                   "total_papers": len(relations)+1,
                                   "sampled_anchors": len(relations)},
            "observed_comparison": counts, "anchor_relations": relations,
            "rank_status": "direct-comparison-bound" if plan_complete else "incomplete-plan-unconstrained",
            "acceptance_probability": None}


def _consensus(values):
    return values[0] if values and len(set(values)) == 1 else "uncertain"


def summarize(plan_path, decisions_path, private_path, out):
    plan, by_id = load_plan(plan_path)
    rows, families = load_decisions(decisions_path, by_id)
    mapping = read_json(private_path)
    keys(mapping, ["schema", "seed", "context", "synthetic", "bands", "coverage", "blinding_status", "papers"], where="private mapping")
    schema(mapping["schema"], "review16.private-mapping.v1")
    if not isinstance(mapping["papers"], list):
        raise ValidationError("private mapping papers must be an array")
    mapped = {}
    for paper in mapping["papers"]:
        if not isinstance(paper, dict) or "anonymous_id" not in paper or "is_target" not in paper:
            raise ValidationError("invalid private mapping paper")
        anonymous_id = string(paper["anonymous_id"], "mapping anonymous_id")
        if anonymous_id in mapped or type(paper["is_target"]) is not bool:
            raise ValidationError("duplicate private mapping ID or invalid is_target")
        mapped[anonymous_id] = paper
    if set(mapped) != set(plan["anonymous_ids"]):
        raise ValidationError("private mapping and plan anonymous IDs differ")
    targets = [p["anonymous_id"] for p in mapped.values() if p["is_target"]]
    if len(targets) != 1:
        raise ValidationError("private mapping must contain exactly one target")
    target = targets[0]
    anchors = sorted(set(mapped)-{target})
    pair_rows = defaultdict(list)
    for cid, comp in by_id.items():
        pair_rows[tuple(sorted((comp["left"], comp["right"])))].append(cid)
    diagnostics = []
    reviewers = {}
    for reviewer, family in sorted(families.items()):
        relations = {anchor: "uncertain" for anchor in anchors}
        counts = Counter()
        for pair, cids in sorted(pair_rows.items()):
            present = [rows.get((reviewer, cid)) for cid in cids]
            outcomes = [_canonical(row, by_id[cid]) if row else "missing" for row, cid in zip(present, cids)]
            if any(row and row["recognized_paper"] for row in present):
                status = "recognized"
            elif "missing" in outcomes:
                status = "incomplete"
            elif "abstain" in outcomes:
                status = "abstain"
            elif outcomes[0] != outcomes[1]:
                status = "reversal_conflict"
            else:
                status = "consistent"
            counts[status] += 1
            if status != "consistent":
                diagnostics.append({"reviewer_id": reviewer, "model_family": family, "pair": list(pair),
                                    "status": status, "comparison_ids": cids, "outcomes": outcomes})
            if target in pair and status == "consistent":
                other = pair[0] if pair[1] == target else pair[1]
                relations[other] = "tie" if outcomes[0] == "tie" else "win" if outcomes[0] == target else "loss"
        received = sum(r == reviewer for r, _ in rows)
        complete = received == len(by_id)
        reviewers[reviewer] = {"model_family": family, **_rank(relations, plan_complete=complete),
                               "plan_complete": complete, "comparisons_received": received,
                               "comparisons_expected": len(by_id), "missing_comparison_count": len(by_id)-received,
                               "pair_diagnostics": dict(counts)}
    family_results = {}
    for family in sorted(set(families.values())):
        members = [r for r, f in families.items() if f == family]
        relation = {a: _consensus([reviewers[r]["anchor_relations"][a] if reviewers[r]["plan_complete"]
                                  else "uncertain" for r in members]) for a in anchors}
        family_results[family] = {"reviewer_ids": sorted(members), **_rank(relation)}
    pooled = {a: _consensus([data["anchor_relations"][a] for data in family_results.values()]) for a in anchors}
    direct_pairs = sum(target in pair for pair in pair_rows)
    report = {"schema": "review16.rank-report.v1", "synthetic": mapping["synthetic"],
              "context": mapping["context"], "coverage": mapping["coverage"],
              "target_anonymous_id": target, "aggregate": _rank(pooled),
              "per_reviewer": reviewers, "per_model_family": family_results,
              "model_family_count": len(family_results), "reviewer_count": len(reviewers),
              "run_complete_for_observed_configurations": bool(reviewers) and all(r["plan_complete"] for r in reviewers.values()),
              "target_direct_anchor_pairs_planned": direct_pairs,
              "decisions_received": len(rows), "decisions_expected_for_observed_reviewers": len(by_id)*len(reviewers),
              "reversal_diagnostics": diagnostics, "acceptance_probability": None,
              "interpretation": [
                  "Ranks are positions only within this stratified sample of anchors, conditional on the recorded judgments.",
                  "No venue acceptance probability or population percentile is estimated; score-stratified anchors are not a representative submission sample.",
                  "Only direct target-versus-anchor comparisons constrain rank; transitive or sparse Borda rankings are not inferred.",
                  "A tie spans its possible ordering positions; missing, unplanned, abstained, recognized, and reversal-conflicting comparisons remain uncertain.",
                  "Each reviewer_id is one preregistered judging configuration reused across fresh contexts. Partial-plan configurations retain direct observations but have unconstrained robust ranks and cannot narrow family/aggregate ranks.",
                  "Within-family and across-family aggregation requires unanimous agreement; 16 personas from one model are not 16 independent samples.",
                  "AB/BA reversal is a robustness check, not an independent observation. No confidence interval is computed.",
                  "Blinding is an operator declaration; model memory and outcome contamination remain unmeasured.",
                  "Evidence strings are retained in the decisions source; this program validates format, not the truth or sufficiency of evidence."
              ]}
    write_new(out, report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prep = commands.add_parser("prepare", help="sample anchors and isolate public/private materials")
    prep.add_argument("--corpus", required=True)
    prep.add_argument("--target", required=True)
    prep.add_argument("--out", required=True)
    prep.add_argument("--per-band", type=int, default=10)
    prep.add_argument("--seed", type=int)
    pairs = commands.add_parser("plan-pairs", help="freeze balanced connected paired comparisons")
    pairs.add_argument("--public", required=True, dest="public_path")
    pairs.add_argument("--out", required=True)
    pairs.add_argument("--neighbors", type=int, default=2)
    pairs.add_argument("--all-pairs", action="store_true")
    pairs.add_argument("--seed", type=int)
    summary = commands.add_parser("summarize", help="unblind locked decisions and report conservative ranks")
    summary.add_argument("--plan", required=True)
    summary.add_argument("--decisions", required=True)
    summary.add_argument("--private", required=True, dest="private_path")
    summary.add_argument("--out", required=True)
    args = vars(parser.parse_args(argv))
    command = args.pop("command")
    try:
        if command == "prepare":
            result = prepare(args.pop("corpus"), args.pop("target"), **args)
        elif command == "plan-pairs":
            result = plan_pairs(**args)
        else:
            result = summarize(args.pop("plan"), args.pop("decisions"), **args)
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    except (ValidationError, OSError, json.JSONDecodeError, UnicodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
