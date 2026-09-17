# Anchor calibration: schemas and protocol

`scripts/anchor_rank.py` uses Python 3.9+ and the standard library. It performs no downloads or model calls. It creates a randomized comparison package, freezes a balanced comparison plan, and calculates conservative **sample-anchor ranks** from locked pair judgments.

This tool does **not** estimate acceptance probability. Every `acceptance_probability` field is `null`. It does not convert 16 roles into 16 independent observations, compute confidence intervals across those roles, or infer a complete ranking from a sparse comparison graph.

## 1. Assemble a homogeneous, inspectable corpus

Use one venue, year, track, review phase, and numeric score scale per corpus. A single top-level context applies to every paper. Context overrides on individual papers are rejected. Do not merge initial scores with post-rebuttal scores, journal recommendations with conference ratings, or different track scales.

Select the manuscript version actually available to the human reviewers at the declared phase. Published camera-ready papers paired with initial scores are not a valid substitute. Verify the version yourself before setting `submission_version_verified: true`. Human ratings must come from the declared phase; preserve their provenance in your local audit records. The script checks declarations and arithmetic, not source authenticity.

Each paper needs a local UTF-8 **full text** with comparable access to its methods, evaluation, and limitations. Preserve section/table locators and the evidence needed for review. Inspect and remove identity/outcome cues such as author names, affiliations, original paper titles where identifying, source URLs, acceptance badges, review text, score annotations, and revealing filenames before declaring `blinding_checked: true`. Avoid removing technical content needed to assess the paper. Exact and whitespace-normalized duplicates are rejected; near-duplicate versions still require manual detection.

Blinding cannot guarantee that a model has forgotten a famous paper or its reception. Report this contamination risk. The script only verifies that the operator supplied `blinding_checked: true`; it does not perform or certify semantic de-identification.

```json
{
  "schema": "review16.anchor-corpus.v1",
  "venue": "Exact venue name",
  "year": 2026,
  "track": "Exact track name",
  "review_phase": "initial-review",
  "score_scale": {
    "name": "Exact official score scale name",
    "min": 1,
    "max": 10,
    "higher_is_better": true,
    "values": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
  },
  "bands": [
    {"id": "1-to-below-4", "lower": 1, "upper": 4},
    {"id": "4-to-below-7", "lower": 4, "upper": 7},
    {"id": "7-to-10", "lower": 7, "upper": 10}
  ],
  "papers": [
    {
      "id": "private-source-id",
      "blinded_text_path": "texts/privately-named-file.txt",
      "blinding_checked": true,
      "submission_version_verified": true,
      "material_level": "fulltext",
      "human_scores": [5, 6, 7],
      "provenance": "Private source reference and version/phase verification notes"
    }
  ]
}
```

This is a shape example, not real conference data. Do not copy its scale or cut points without checking the chosen venue. Optional corpus `synthetic` is a boolean and defaults to false; `provenance` is an optional string. Other unknown keys are rejected. Human scores must be a nonempty array of finite in-range numbers; booleans are not numbers. Duplicate JSON keys, `NaN`, infinities, and overflowed float literals are rejected.

For discrete venue scales, provide optional `score_scale.values`: a nonempty array of unique finite numeric ratings inside the scale bounds. When supplied, **each individual human rating must belong to this exact allowed set**, even if a disallowed number lies inside `min`/`max`. For example, with values `[1, 3, 5]`, a human rating of `2` is invalid, while ratings `[1, 3]` validly average to `2` for band assignment. Means may be fractional and need not themselves be allowed individual ratings. When `values` is absent, only numeric range validation is possible; do not silently treat that as validation of a venue's discrete choices.

The arithmetic mean of `human_scores` assigns each paper to a band. Bands must be contiguous, non-overlapping, and cover the declared scale. Lower endpoints are inclusive; upper endpoints are exclusive, except the scale maximum is included in the last band. Thus a mean exactly equal to an interior boundary belongs to the upper band. Band IDs must be unique. Lower-is-better scales are supported as metadata; the tool does not reinterpret them as acceptance labels.

If your venue does not expose low-score submissions, those bands remain empty. Do not fill them with another venue, camera-ready versions, abstracts, synthetic scores, or papers selected on prestige. Top-level coverage reports list the number available, requested, selected, and missing in every band. This is a deliberately score-stratified sample, not a representative estimate of the venue submission population.

## 2. Prepare the target and blinded package

Target JSON:

```json
{
  "schema": "review16.target.v1",
  "id": "private-target-id",
  "blinded_text_path": "texts/target-fulltext.txt",
  "blinding_checked": true,
  "material_level": "fulltext"
}
```

An optional `synthetic` boolean marks test data. Text paths resolve relative to the JSON file, or may be absolute local paths. The target must have a distinct source ID and normalized text from **every** paper in the corpus, including anchors not selected in this run. All source IDs and source text paths stay private.

From the repository root:

```sh
python3 skills/review16/scripts/anchor_rank.py prepare \
  --corpus corpus.json --target target.json --out run --seed 42
```

The default is 10 papers per band sampled without replacement. Use `--per-band N` to preregister another positive count. Short bands use all available papers and record the shortfall; no paper is resampled. An empty corpus can produce an explicit all-missing coverage report, but pair planning requires at least one anchor. Rejecting an abstract-only input is intentional: obtain equivalent full text or abstain from calibration.

`--seed` is optional. Without it, the tool generates a random private seed. A fixed seed reproduces selection, anonymous IDs, and order for the same inputs. Do not show the seed, corpus order, or private mapping to reviewers.

Output:

```text
run/
  public/
    manifest.json
    texts/P<random-hex>.txt
  private/
    mapping.json
```

The public manifest contains only a schema ID and randomly ordered papers with `anonymous_id`, relative `text_path`, and `material_level: "fulltext"`. It contains no target flag, original ID, human score, URL, venue, decision, or seed. Anonymous file names are generated uniformly for all papers, including the target. The original text contents are copied as supplied; the operator is responsible for blinding those contents.

The private mapping stores the source data, human means/bands, target flag, context, coverage, and seed. The tool requests `0700` for the private directory and `0600` for its mapping file. **These permissions do not isolate agents running under the same operating-system account.** The orchestrator must provision reviewers with only the public files in an isolated directory/context and deny access to private data. Do not share the entire `run/` directory or the preparation command's coverage output with reviewers. Only the coordinator uses private data after judgments lock.

Output paths must not already exist. Files and symlinks are never overwritten. A failed filesystem operation can leave an incomplete output directory; inspect it and choose a new output path. Do not rename incomplete output as a successful run.

## 3. Freeze a balanced comparison plan

```sh
python3 skills/review16/scripts/anchor_rank.py plan-pairs \
  --public run/public/manifest.json --out run/public/plan.json \
  --neighbors 2 --seed 43
```

The sparse plan randomly orders all anonymous papers around a ring and compares each to its `k` nearest neighbors in each direction, capped at a complete graph. Every paper has the same number of partners and the graph is connected. `--neighbors 2` is the default; `--neighbors 1` gives a cycle. A sparse plan can leave a wide target-rank interval. This is expected, not grounds to conceal the interval or add target-only comparisons.

Use `--all-pairs` for all unordered pairs. Every pair is evaluated in both AB and BA orientation, with unique randomized `comparison_id` values and randomized trial order. The all-pairs mode contains `n(n-1)` comparisons; this is twice the unordered-pair count. The plan uses no private mapping and does not identify or oversample the target.

Freeze the plan **before reading any judgments**. Keep a copy/hash in the run record. The tool enforces membership and structural balance when summarizing; it cannot prove that the coordinator preregistered it at an earlier time. No post-hoc adaptive target-only plan is supported. A material change needs a new, clearly labeled run.

Give a reviewer one comparison at a time, including both anonymous full texts and the review rubric. Evaluate AB and BA in **fresh contexts**, without exposing the previous answer, while retaining the same preregistered judging-configuration `reviewer_id` so the two orientations can be paired. If a platform cannot provide fresh contexts, the run deviates from this protocol; record that limitation and do not describe the reversal check as context-isolated. If either text is unreadable, incomplete, outside the reviewer's competence, or lacks comparable evidence for the requested criterion, return `abstain` with a specific reason. Do not force a winner.

## 4. Record independent judgments before discussion

Decisions file:

```json
{
  "schema": "review16.pair-decisions.v1",
  "decisions": [
    {
      "comparison_id": "C0123456789abcdef",
      "reviewer_id": "theory-specialist",
      "model_family": "actual-model-family",
      "decision": "left",
      "recognized_paper": false,
      "evidence": "Left P... §3 proves the stated claim under explicit assumptions; right P... §3 omits the required boundary case."
    }
  ]
}
```

Use IDs actually produced by the plan; the IDs above are placeholders. `decision` is exactly `left`, `right`, `tie`, or `abstain`. Required `recognized_paper` must be an explicit JSON boolean: `true` if the judging context recognizes either manuscript or recalls its identity, publication outcome, or reputation; otherwise `false`. Do not omit the field when false. Either orientation reporting recognition makes the pair uncertain with diagnostic status `recognized`, regardless of an otherwise consistent winner. This records self-reported recognition, not proof that unrecognized papers are uncontaminated. `evidence` is a nonempty string that should cite manuscript section/page/table locations and explain the comparison. The program validates the string's presence, not whether it is truthful or sufficiently grounded. The coordinator must audit it.

`reviewer_id` identifies one **preregistered judging configuration**, including its fixed model/checkpoint, rubric, role/prompt version, and settings. It is **not** a fresh-context instance ID. All fresh contexts executing that configuration, including both AB/BA orientations, reuse the same reviewer ID. Give a materially different configuration a different preregistered ID. Each configuration can submit at most one decision per comparison and must keep the same `model_family` throughout the run. Persona names, separate sessions, AB/BA reversals, and repeated samples do not create new model families. Record the configuration-to-model/prompt mapping and context policy in the surrounding experiment record. This file deliberately does not allow numerical ratings or identities that could contaminate the pair decision.

Every configuration observed by this v1 tool is expected to judge the **entire same frozen plan**, using `abstain` when necessary. Undeclared heterogeneous subset assignments are not supported. If several judges divide a plan among themselves, each will appear incomplete; do not use new context instance IDs to represent those workers. Use the shared preregistered configuration ID only when the model, role, prompt, and settings truly match. Distinct judging configurations remain distinct even if that creates incomplete coverage.

Preserve the pre-discussion file. Cross-examination can produce a separately versioned post-discussion file with its own report; do not overwrite the original to make reviewers appear more consistent.

## 5. Unblind and summarize

```sh
python3 skills/review16/scripts/anchor_rank.py summarize \
  --plan run/public/plan.json --decisions decisions.json \
  --private run/private/mapping.json --out rank-report.json
```

Both orientations must be present, unrecognized, and agree after translating left/right choices back to paper IDs. Recognition in either orientation is `recognized`; otherwise a missing reverse is `incomplete`, any abstention is `abstain`, and contradictory winners or tie/winner combinations are `reversal_conflict`. Each appears in `reversal_diagnostics` and contributes an uncertain relation, not a half-win or fabricated tie.

Reports preserve per-configuration direct observations and aggregate eligible results by model family. Each configuration reports `plan_complete`, `comparisons_received`, `comparisons_expected`, and `missing_comparison_count`. An incomplete configuration retains its observed direct win/tie/loss/uncertain counts for diagnosis, but its robust rank spans the entire sample with `rank_status: "incomplete-plan-unconstrained"`; it cannot narrow a family or aggregate rank. This prevents undeclared subset assignments or target-only judging from producing a misleadingly precise final interval. Complete configurations still receive conservative bounds from direct target-anchor comparisons; planned abstentions count as completed trials but leave their relations uncertain.

Within one family, a direct target-anchor result must be unanimous across every configuration appearing in the file; disagreement, incompleteness, or missing evidence leaves it uncertain. Across families, the aggregate again requires unanimity. Empty decisions are valid and produce a fully uncertain range. `run_complete_for_observed_configurations` is true only if at least one configuration appears and each observed configuration completes the plan. Configurations wholly absent from the file cannot be counted: compare `reviewer_count` and IDs against the preregistered roster before accepting the run as complete. The tool cannot infer that roster from absent records.

For `A` sampled anchors, let `L` be directly supported target losses and `W` directly supported target wins. The conservative positional bounds are:

```text
best position  = 1 + L
worst position = 1 + A - W
```

These formulas apply to complete judging configurations and their eligible consensus results. Ties span their possible order positions. Abstentions, recognition, missing judgments, reversal conflicts, disagreements, and anchors with no direct target comparison remain uncertain. Incomplete configurations instead receive the deliberately unconstrained range described above. These are **bounds conditional on recorded pair judgments**, not confidence bounds for an objective ground-truth rank. No indirect transitivity, sparse Borda score, or ordinary confidence interval over 16 personas is substituted for evidence.

`aggregate`, `per_reviewer`, and `per_model_family` expose `sample_anchor_rank`, `observed_comparison` (`win/tie/loss/uncertain`), and anonymous `anchor_relations`. The report also records coverage, family count, expected decisions for the reviewers actually observed, and planned direct-target coverage. Its target identity and context make it a **post-unblinding author report**; never feed it back into the initial blind reviews.

Interpretation example: with six anchors, two supported wins, and four unexamined target comparisons, the result is position **1–5 of 7**, not first place. Display the sample size, missing score bands, and model-family dependence beside that interval. Do not label it a venue percentile or acceptance chance.

## Verification and demo boundary

```sh
python3 -m unittest discover -s tests -p 'test_anchor_rank.py' -v
```

The checked-in `examples/anchors/` dataset is conspicuously synthetic, has a deliberately missing middle band, and tests plumbing only. It is not a validation benchmark for AI reviewing, a collection of real human scores, or evidence of predictive calibration.
