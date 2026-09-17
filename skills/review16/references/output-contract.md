# Review and report contract (v0.1)

`panel.py prepare` writes an output skeleton per persona. Replace every null that can be assessed, retaining nulls for abstentions. These are JSON data, not instructions for reading other reviewers' work.

## Venue configuration

Required fields: `venue`, `year`, `track`, `rubric_source`, `retrieved_at`, and `score_scale` with `values` (unique numeric allowed scores) and `labels` (string numeric value → official label). Optional `provisional` marks a historical rubric used before current instructions exist. A non-demo run needs an https rubric source. Do not assume contiguous scores or a 1–10 range. Synthetic fixtures have `synthetic=true` and are never represented as real venue policy. The included [NeurIPS 2025 main-track adapter](venues/neurips-2025-main.json) is verified against that year's public guide, not a default for later years.

## Reviewer JSON

Required fields:

- `run_id`, `manuscript_sha256`: preserve the prepared template values exactly. These bind every review to the frozen manuscript and run; a report rejects cross-run or cross-manuscript results.
- `persona_id`, `model`, `model_family`, `status`: `assessed`, `out_of_scope` or `insufficient_evidence`.
- `score_before`, `score_after`: an allowed venue value for assessed work, otherwise null. Before cross-examination these may be identical.
- `domain_fit`: integer 0–4 or null: outside field, peripheral, adjacent, relevant, central. This is research interest, not a quality score.
- `confidence`: integer 1–5 or null, self-reported confidence, not a probability.
- `dimensions`: `correctness`, `novelty`, `evidence`, `significance`, `reproducibility`, `clarity`, each 0–4 or null. These common diagnostic ratings have no automatic mapping to the venue score. Null means not assessable, not zero. Reproducibility is assessed according to paper type; proofs need checkable arguments, not necessarily code.
- `reading_coverage`: nonempty strings identifying inspected sections/figures and missing or unreadable materials.
- `score_reason`, `change_reason`: justify the score and any change. An unchanged score may use an empty change reason.
- `recognized_paper`: boolean; `synthetic`: boolean.
- `evidence`: array of objects with `id`, `kind` (`strength`, `weakness`, `question`), `claim`, `location`, `observation`, `consequence`, `severity` (`critical`, `major`, `minor`, `info`), `verification` (`supported`, `unverified`, `refuted`), `scope`, `remedy`, `would_change_judgment`.
- `challenges`: array of records with `from_persona`, `evidence_id`, `type`, `challenge`, `response`, `resolution` (`upheld`, `narrowed`, `retracted`, `unresolved`). Preserve the first-pass evidence and explain any revision.

All assessed reviews need supported evidence, an explained score and nonempty coverage. An out-of-scope review may still provide bounded comments and domain fit. A full panel returns sixteen distinct personas. Panel coverage and cross-examination stage are separate: receiving sixteen initial reviews is not completion of the discussion. Without recorded cross-examination, the report labels first-pass scores and pending discussion. A partial report lists missing personas and never imputes their scores. The validator checks structure and consistency, not the truth of citations or quality of judgment; the chair checks those.

## Author-facing report

Lead with a reasoned meta-review and three highest-impact revisions, then provide all persona scores (before/after), fit, confidence, coverage and linked evidence. Show disagreements as factual/scope/value/unknown rather than silently averaging. Include optional anchor rank and missing comparisons. Report model families and execution limitations. Keep the raw JSON and prompts alongside the rendered report for audit.

The renderer produces a diagnostic dashboard, not an automated chair verdict. The coordinating agent supplies the final written meta-review and disagreement ledger. Do not use the dashboard's aesthetics as evidence that the reviews were independently validated.
