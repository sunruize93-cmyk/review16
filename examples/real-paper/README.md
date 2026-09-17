# Real-paper test: Hierarchical Memory Networks

**Executed on 2026-09-17. Real manuscript, real model outputs, one complete cross-examination round.**

中文摘要：本轮使用真实 ICLR 2017 稿件，运行了 16 个独立上下文和 8 组双向质询。初审为 14 个 5 分、2 个 6 分；本轮结果不代表准确率评测，历史分数也没有被当作已校准的质量标签。

[Download the HTML report](https://github.com/sunruize93-cmyk/review16/releases/download/v0.1.0/review16-real-paper-report.html) · [Report source](report.html) · [Execution record](execution.json) · [Source audit](provenance.json)

## Individual scores

Original ICLR 2017 scale: **5 = marginally below acceptance threshold; 6 = marginally above**. The full official 1–10 labels are in the [source-checked adapter](../../skills/review16/references/venues/iclr-2017-conference.json).

| Reviewer | Initial | After discussion | Research fit | Self-reported confidence |
|---|---:|---:|---:|---:|
| [DIGN](reviews/dign.json) · Architect | 5 | 5 | 3/4 | 4/5 |
| [DIGR](reviews/digr.json) · Guardian | 5 | 5 | 3/4 | 4/5 |
| [DICN](reviews/dicn.json) · Detective | 5 | 5 | 3/4 | 4/5 |
| [DICR](reviews/dicr.json) · Auditor | 5 | 5 | 3/4 | 4/5 |
| [DUGN](reviews/dugn.json) · Inventor | 5 | 5 | 4/4 | 4/5 |
| [DUGR](reviews/dugr.json) · Engineer | 5 | 5 | 4/4 | 4/5 |
| [DUCN](reviews/ducn.json) · Strategist | 5 | 5 | 3/4 | 4/5 |
| [DUCR](reviews/ducr.json) · Verifier | 5 | 5 | 3/4 | 4/5 |
| [EIGN](reviews/eign.json) · Explorer | 6 | 6 | 4/4 | 3/5 |
| [EIGR](reviews/eigr.json) · Curator | 5 | 5 | 4/4 | 4/5 |
| [EICN](reviews/eicn.json) · Hunter | 6 | 6 | 4/4 | 3/5 |
| [EICR](reviews/eicr.json) · Experimenter | 5 | 5 | 4/4 | 4/5 |
| [EUGN](reviews/eugn.json) · Pioneer | 5 | 5 | 4/4 | 4/5 |
| [EUGR](reviews/eugr.json) · Builder | 5 | 5 | 4/4 | 4/5 |
| [EUCN](reviews/eucn.json) · Designer | 5 | 5 | 4/4 | 4/5 |
| [EUCR](reviews/eucr.json) · Steward | 5 | 5 | 4/4 | 4/5 |

Fit is interest/relevance, not quality. Confidence is not a probability. The scores are correlated judgments from one model family; no average is used as a chair verdict.

## What happened

The shared finding was that restricting the training candidates is a coherent approach, with an informative reported accuracy improvement. The main objection was that candidate-count reduction does not establish the claimed end-to-end acceleration. The discussion qualified both: the positive result concerns the full supervised training recipe; the negative establishes missing runtime evidence, not proof that acceleration is impossible.

EIGN and EICN valued the preliminary empirical phenomenon enough for a marginal positive judgment. Other types placed more weight on the missing practical evidence. This illustrates a value disagreement in this run; it does not demonstrate that a particular axis caused the difference.

Every reviewer kept its original score after discussion. This was not a forced consensus: the 5/6 disagreement remains. The [chair assessment](chair.json) prioritizes complete timing/accuracy comparisons, separating proposed mechanisms from observations, and reproducible configuration details. All original evidence was preserved.

The result demonstrates that this workflow can return below-threshold judgments. It **does not establish that Review16 has solved score compression, recognizes excellent papers reliably, or improves review accuracy**. There was no matched-budget baseline, human adjudication, repeated run, second model family or held-out cohort.

## Sources and limits

- Manuscript: [Hierarchical Memory Networks, original forum](https://openreview.net/forum?id=BJ0Ee8cxx), retrieved from [AllenAI PeerRead's pinned archive](https://github.com/allenai/PeerRead/blob/9bb37751781a900cee9e74ec3105997732c8e8e5/data/iclr_2017/dev/pdfs/673.pdf). Ten pages; PDF SHA-256: `688418c90285c0d245ae00e4a2feb161da67be95c220da4ff1ec6ea35b2822db`.
- OpenReview API2 and the selected paper's API1 endpoints returned HTTP 403. The public PeerRead fallback succeeded. The web search index could expose the paper, but did not supply auditable revision/rating histories.
- The archive's three original recommendation entries are **5, 5, 4**. They were withheld from reviewer prompts. The coordinator had inspected them during convenience selection and was not blinded. These are descriptive archive entries, not verified same-phase ground truth for accuracy scoring. Manually annotated PeerRead aspect labels were not used as recommendations.
- All 16 reviewer contexts started fresh. Each received its own persona, the same venue rubric, full manuscript text and page renders. Reviewers reported full reading and no recognition. The manuscript retained title/authors; these self-reports do not rule out memorization or prestige effects. Filesystem access was restricted by instructions, not OS isolation. See [execution context](execution-context.md).
- The paper was judged retrospectively against its 2017 contribution, without requiring modern baselines. Reviewers did not browse external novelty claims or rerun experiments. The source file is fixed, but the archive does not establish which revision each historical reviewer assessed.
- **Historical calibration was not run.** No ten-per-band corpus was sampled, no blind anchor rank was produced, and no acceptance probability was estimated. The version/phase audit required for that feature remains incomplete. The alternative source solved manuscript retrieval, not calibrated ranking.

Third-party papers and human review text are not bundled. MIT applies to Review16 code and original outputs; source materials retain their own rights. Human recommendation numbers are recorded with provenance, without republishing the reviews.

## Inspect or reproduce

- [Frozen initial reviews](round0/) and [their digest lock](round0-lock.json).
- [Outgoing challenge packages](challenges-out/), [final reviews with responses](reviews/), and [chair assessment](chair.json).
- [Prepared prompts](tasks/), [challenge prompts](cross-tasks/), [response prompts](response-tasks/) and [manifest](manifest.json). Machine-specific prompt paths were made portable; original local prompt digests are retained separately.

From the repository root, this downloads and verifies the source PDF, then re-renders the **recorded judgments**. It does not call models or reproduce model stochasticity:

```bash
python3 examples/real-paper/reproduce.py --out /tmp/review16-reproduced
```

To run a new review, install the skill and supply the manuscript and the historical ICLR 2017 adapter. Keep human scores out of the reviewer contexts. See [the evaluation plan](../../docs/benchmark-plan.md) for the broader tests needed before claiming better accuracy.
