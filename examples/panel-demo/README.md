# Synthetic panel demo

**Every review, score, challenge and chair statement here is a fixed fictional
fixture. No models or reviewers were run. This is not an accuracy benchmark.**

Open [`../report.html`](../report.html) to explore the sixteen related types, their
before/after scores, interest fit, shared quality diagnostics and evidence records.
The dashboard embeds its data and original character atlas; it uses no CDN.

Re-render the fixture from the repository root, choosing a new output path:

```sh
python3 skills/review16/scripts/panel.py report \
  --run examples/panel-demo --reviews examples/panel-demo/reviews \
  --out /tmp/review16-panel-demo.html --demo
```

To prepare a new run, supply the actual manuscript's absolute path and the exact
official venue/year/track rubric. `prepare` generates sixteen isolated task prompts
and empty JSON skeletons in `templates/`; `reviews/` remains empty. It calls no
model. The host must actually execute tasks and enforce fresh-context isolation.
Preparation copies the manuscript into a read-only `materials/` snapshot. Every
review must preserve its bound `run_id` and `manuscript_sha256`; reporting rejects
changed snapshots and reviews copied from another run.

```sh
python3 skills/review16/scripts/panel.py prepare \
  --manuscript /absolute/path/to/paper.pdf --venue-config /path/to/venue.json \
  --out /tmp/review16-new-run --max-parallel 3
```

The checked-in manifest and task prompts use `/SYNTHETIC_FIXTURE/` paths so they
contain no developer-machine paths. Those prompts are illustrative records, not
tasks to execute verbatim. Generate new prompts for a real local manuscript.
The checked-in manifest resolves `materials/manuscript.md` relative to this folder.

All sixteen fictional role outputs are supplied, but only two unilateral fictional
challenge records exist. The dashboard therefore says **cross-examination partial**,
with **0 / 8 bilateral pair records**. Complete role coverage does not mean the
cross-examination round is complete.

The optional `chair.json` supplies `meta_review`, up to three `priority_actions`,
an optional disagreement ledger, and a required `synthetic` boolean. Without it,
the renderer provides only diagnostics and does not generate a chair verdict.

For a partial-panel example, copy just one review into a new directory and pass
that directory to `--reviews`: the other fifteen remain explicitly missing.
No missing score, confidence or evidence is imputed.
