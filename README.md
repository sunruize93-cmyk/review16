# Review16

**One paper. Sixteen connected reviewer perspectives. Evidence you can check.**

[简体中文](README.zh-CN.md) · [Real-paper test](examples/real-paper/README.md) · [Technical guide](docs/guide.md) · [MIT](LICENSE)

Review16 is a pre-submission review skill for **AI/ML papers**. Your agent runs 16 independent reviewers, pairs them for one round of evidence-based challenges, and gives you an illustrated report with every score and the most useful revisions.

![The sixteen Review16 types](skills/review16/assets/reviewer-atlas.png)

## Get started

**1. Install into Codex** (Python 3.9+):

```bash
git clone https://github.com/sunruize93-cmyk/review16.git
cd review16
python3 install.py
```

The installer keeps existing installations safe. Start a new Codex session after installation. Use a host with subagent support; reviewers can run in batches of three.

**2. Attach your paper and ask:**

> Use $review16 to review this paper for [conference, year, track]. Run all 16 reviewers and one cross-examination round. Show individual scores, disagreements, and the three most useful revisions. Add blinded historical comparisons if suitable data are available.

**3. Open the HTML report** your agent creates. Click a reviewer to inspect its evidence, score and related types. You do not need to launch 16 agents yourself.

## What you get

- **16 individual reviews:** scores before/after discussion, evidence and confidence.
- **An explanation of disagreements:** mistaken readings, scope differences and research preferences.
- **Three priority revisions:** a reasoned assessment, without mechanically averaging scores.
- **Optional historical positioning:** an interval within a disclosed reference set, when paper versions and public scores can be verified.

## Why these sixteen?

Four paired preferences create **2 × 2 × 2 × 2 = 16** types:

| Axis | Two preferences |
|---|---|
| Evidence | **D**eductive ↔ **E**mpirical |
| Contribution | **I**nsight ↔ **U**tility |
| Scope | **G**eneral ↔ **C**ontextual |
| Research risk | **N**ovelty ↔ **R**eliability |

Each type has **four one-axis neighbors** and **one four-axis opposite**. DIGN and DIGR differ only in novelty/reliability; DIGN and EUCR cross-examine each other. All share the same domain and correctness standards. [Explore the type relationships →](skills/review16/references/types.md)

## Try it and know its limits

See the [real-paper test and all scores](examples/real-paper/README.md), or download [the synthetic interface demo](examples/report.html) and open it locally.

This is an experimental author tool. Sixteen roles are not sixteen independent human experts; different scores alone do not prove better reviews. It does **not predict acceptance probability**. Historical ranking requires auditable data; missing data are reported rather than invented. [Validation](docs/validation.md) · [Benchmark plan](docs/benchmark-plan.md)

## More

[CLI and other hosts](docs/guide.md) · [Historical-data protocol](skills/review16/references/anchors.md) · [Contributing](CONTRIBUTING.md) · [Related projects](docs/landscape.zh-CN.md)

Inspired by structured type systems; not affiliated with MBTI or 16Personalities. [Original illustration provenance](assets/illustration-provenance.md). MIT covers this project's code and original materials; third-party papers and reviews retain their own terms.
