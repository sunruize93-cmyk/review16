# Validation record — 2026-09-17

This records local v0.1 engineering checks, a bounded synthetic smoke test, and a real-paper workflow test. The latter uses one convenience-selected historical manuscript; it is not a held-out performance benchmark or evidence of superiority.

## Local checks

- Python 3.9 standard-library test suite: **59 tests passed** (26 anchor, 8 OpenReview parser, 3 PeerRead parser, 22 panel/report tests).
- Skill Creator frontmatter and scaffold validator: passed.
- Type graph: all 16 Cartesian-product types, 32 distance-one edges, and 8 distance-four opposite pairs checked.
- Full CLI smoke: `prepare → plan-pairs → summarize`, then panel `prepare → report`. With zero judgments, the three-paper reference example returned rank 1–3; no probability or fabricated judgment was emitted. The empty panel retained all sixteen missing reviewers.
- Fresh code audit identified two concrete faults: results could be attached to a different manuscript/run, and initial reviews could be labelled post-cross-examination. Both were fixed and independently rechecked. Reviews now bind run ID and manuscript digest; preparation writes a read-only snapshot and rendering verifies its content. Review coverage and discussion stage are separate.
- Desktop browser inspection: portrait atlas, type-neighborhood diagram, dashboard layout, type-card selection, neighbor/opposite relations and corrected partial-discussion label inspected. The report is self-contained and declares its synthetic data visibly. Mobile rendering was not separately verified.
- Markdown local-link checks, portable example paths and staged whitespace checks passed.

## Behavioral smoke

A fresh evaluator used only DICR and EUGN on a synthetic manuscript containing a false universal claim and an embedded request for a high score. Both roles identified the same valid counterexample and assigned 2 — Reject before and after one exchange. Different revision priorities remained; score disagreement was not forced. Fourteen unrun types were not filled in.

Because worker slots were occupied, the evaluator disclosed that it executed the two roles sequentially in the same context. This **does not validate independent multi-agent performance**. It is one easy constructed case, with no historical anchors. The [manuscript and original review text](../examples/forward-smoke/README.md) are retained. The illustrative sixteen-card dashboard is separately authored fictional data and is not this model-generated smoke test.

## Real-paper execution

The [public case study](../examples/real-paper/README.md) preserves actual first-pass reviews, opposite-pair challenge/response records, provenance and a downloadable report. It uses fresh reviewer contexts and the original ICLR 2017 rubric. PDF, extracted text and page renders were available to each reviewer. Third-party source material is referenced by pinned URL and digest rather than redistributed under MIT.

All 16 first passes and 8 bilateral pairs completed: 32 responses, 24 upheld and 8 narrowed checks, with 14 scores of 5 and two of 6 before and after discussion. The immutable initial evidence and exact incoming challenge text were checked against final records. The public reproduction command downloaded the pinned PDF, verified its digest and successfully rebuilt the complete report. These are workflow checks, not accuracy metrics.

Final report inspection found two presentation issues: narrow windows hid manuscript identity, and an unchanged score was introduced as a score change. Both labels/layouts were corrected and checked in the rendered report.

The installer was exercised in a fresh temporary directory and correctly refused to overwrite it on a second invocation. The PeerRead network success path was exercised on paper 673 from the development split.

## Outstanding empirical work

- The live OpenReview single-forum request returned HTTP 403 in this environment. Offline parsing and failure handling were tested; online success and submission-version recovery were not established.
- The pinned AllenAI PeerRead fallback successfully retrieved a real ICLR 2017 PDF and original recommendation records. A source-checked historical rubric was recovered from official OpenReview scripts. Manuscript/review-phase alignment remains unverified, so historical anchor calibration was not run.
- No held-out real-paper comparison against a single reviewer, homogeneous ensemble, PaperJury or other system has been run.
- Four-axis behavioral separability, community affinities, review accuracy, cost effectiveness and acceptance prediction remain unverified.
- Execution identity, full reading and challenge authenticity remain host declarations. Structural checks cannot prove their semantic truth. The report explicitly keeps semantic execution unverified.

The next scientific milestone is the [predeclared benchmark](benchmark-plan.md), beginning with a small source-audited cohort rather than a stronger marketing claim.
