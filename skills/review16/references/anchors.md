# Historical anchor protocol

## Eligibility before sampling

An anchor set is scoped to one venue, year, track, paper type and review phase. Match topic and contribution type before reading scores to choose examples. Freeze eligibility and band boundaries, record counts before and after exclusions, and sample without replacement. Human ratings are noisy observations, not objective quality labels.

Possible modes: `scored_full`, `scored_selected`, `accepted_only`, `no_anchors`. Scored-selected data may have author opt-in and availability bias. Accepted-only papers can be descriptive neighbors but cannot populate low-score bands or yield a conference-wide quality estimate. The numeric v0.1 ranking CLI requires genuine scored anchors; otherwise use a clearly labelled qualitative comparison.

Verify the submission-time version corresponding to ratings. Current OpenReview PDFs can be later revisions. Record the review phase and original rating scale and preserve per-review values; an average is a declared aggregation choice, not the original review. Never call a decision or best-paper award a numeric review score. Do not mix ARR assessment scores with conference decisions.

The single-forum OpenReview helper saves raw public metadata and current note edits where accessible. A human/agent data audit still resolves which revision and which ratings belong together. `submission_version_verified=false` is deliberate until that audit finishes. Network failure must not produce a plausible-looking empty corpus.

If OpenReview is unavailable, try a legitimate public archive before stopping.
The included `scripts/fetch_peerread.py --paper-id 673 --split dev --download-pdf --out NEW_DIR`
retrieves an ICLR 2017 PDF and original recommendation entries from a pinned
AllenAI PeerRead commit. Use `reviews_raw`, not manually annotated aspect labels
as overall recommendations. The helper leaves version/phase alignment unverified.
It enables real manuscript review even when calibrated historical ranking cannot
be justified. Keep its `*.private.json` files out of reviewer contexts. Do not
substitute another venue/year's archive for the author's chosen target silently.

## Blinding and data separation

Create normalized full-text packets for target and anchors using the same process. Remove authors, affiliations, publication/award marks, public review comments, outcome-bearing file names, and identifiable metadata. Preserve scientific evidence, formulas, captions, citations and necessary figures. Do not asymmetrically redact citations from one paper. Record redactions and recognition risk privately. Reviewers may still recognize well-known work from training; collect `recognized_paper` and perform a sensitivity analysis excluding recognized comparisons.

`prepare` creates `public/` and `private/`. **Filesystem separation is not an access-control sandbox.** Give comparator agents only public packets in an isolated workspace, or restrict their tool/file access. If the host cannot enforce this, disclose the procedural nature of blinding. Do not grant the private-map path through full-history forks, shared task metadata, a parent summary or the grader prompt. Copy public materials out before dispatch when necessary.

The anonymous plan must treat every manuscript symmetrically. A star graph with one recurring center discloses the target. Comparing every paper against every other one prevents this but is expensive; the provided sparse connected regular graph is the default. Its interval may remain wide. Do not narrow it using untested transitivity assumptions. Decide the plan before seeing results; target-specific adaptive comparisons can compromise masking.

AB and BA judgments must be fresh and separately generated. They are correlated checks on order bias, not independent statistical samples. Keep ties and abstentions. If an anchor comparison is unresolved, unobserved, recognized or unstable, it contributes uncertainty rather than a forced win. Comparisons for correctness, novelty and overall scientific merit need separate predeclared criteria and result sets.

## What the number means

The conservative target rank comes from direct target–anchor relations, with rank 1 best. Unresolved relationships can land on either side. Ties allow shared or adjacent positions as specified by the deterministic tool. This is an identification range conditional on these comparisons, **not a statistical confidence interval**. A sparse graph can produce a large range; show its coverage prominently.

Equal counts per score band overrepresent rare bands. The sample-anchor rank is not a population percentile. Population weighting would require known eligible-population counts and defensible sampling/availability assumptions, and is not implemented in v0.1. Venue acceptance probability would additionally require a separate held-out calibrated outcome model. Always set `acceptance_probability=null`.

Historical human scores may be revealed by the coordinator only after blind judgments are locked. Report anchor IDs with source links in the final audit appendix, low-band coverage, score-phase/version checks, rejected-paper availability, comparison completion and recognition/order sensitivity. Do not infer awards from review scores or guarantee that top-ranked papers win awards.

## Cost

For N anonymous papers, k ring neighbors yield roughly N×k unordered pairs, each with two orderings. All-pairs requires N(N−1) ordered comparisons for a single criterion and one judging configuration. Multiple models, criteria or repetitions multiply that cost. The sixteen-persona manuscript panel is separate. Publish planned calls and token estimates before dispatch, and honor a cap. v0.1 has no paid-model runner.
