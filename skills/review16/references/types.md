# A connected type system

The system uses four declared binary preferences, giving exactly 2⁴ = 16 combinations. This is a designed taxonomy for review, inspired by the memorability and combinatorial structure of personality types. It is not MBTI, an affiliation with MBTI or 16Personalities, or a validated psychometric test. The empirical independence of these axes remains untested.

| Position | Pole A | Pole B | What varies |
|---|---|---|---|
| 1 | D · Deductive · 演绎 | E · Empirical · 实证 | Preferred form of supporting evidence |
| 2 | I · Insight · 解释 | U · Utility · 效用 | What makes the contribution valuable |
| 3 | G · General · 通用 | C · Contextual · 情境 | Preferred scope of the contribution |
| 4 | N · Novelty-seeking · 探索 | R · Reliability-seeking · 稳健 | How promising novelty versus mature validation is valued |

All poles demand correctness and honest evidence. D does not mean every empirical paper needs a theorem. E does not mean a theorem requires a new benchmark. I can value useful methods, U can value explanatory discoveries, C is not low ambition, and N never licenses unsupported claims. R does not reject novelty automatically. These are priorities within an applicable venue rubric, not mutually exclusive capabilities or preset leniency.

## The sixteen types

Rows fix the first two preferences, columns fix the last two. This makes the connections visible instead of scattering disciplines arbitrarily.

| | G + N | G + R | C + N | C + R |
|---|---|---|---|---|
| **D + I** | DIGN Architect · 范式架构师 | DIGR Guardian · 公理守门人 | DICN Detective · 机制探案者 | DICR Auditor · 证明审计师 |
| **D + U** | DUGN Inventor · 算法发明家 | DUGR Engineer · 优化工程师 | DUCN Strategist · 设计策略师 | DUCR Verifier · 验证工程师 |
| **E + I** | EIGN Explorer · 规律探索者 | EIGR Curator · 证据策展人 | EICN Hunter · 现象猎手 | EICR Experimenter · 实验侦探 |
| **E + U** | EUGN Pioneer · 前沿开拓者 | EUGR Builder · 基准工程师 | EUCN Designer · 交互先锋 | EUCR Steward · 部署守护者 |

## Relations determine the review protocol

Represent a type by its four choices. Hamming distance is the number of choices that differ. Each type has exactly four distance-one neighbors and one distance-four opposite. For example:

- DIGN → EIGN changes only the preferred form of evidence.
- DIGN → DUGN changes only insight versus utility.
- DIGN → DICN changes only general versus contextual scope.
- DIGN → DIGR changes only novelty versus reliability emphasis.
- DIGN ↔ EUCR differs on all four axes and forms a cross-examination pair.

The graph is the four-dimensional hypercube: 16 vertices, 32 undirected neighbor edges, 8 opposite pairs. `build_personas.py` generates the exact codebook and graph. These counts are properties of the design, not evidence of psychological validity.

Use opposite pairs to challenge assumptions broadly. Use existing neighbor reviews to explain a specific source of disagreement. Neither relation compels different scores. If evidence is decisive, all types may agree; deliberately spreading scores is a failure.

## Fields remain many-to-many

A field is not a personality. Optimization work may benefit from DUGN and DUGR, but also EUGR when compute and actual performance dominate the claim. A mechanistic-interpretability paper may interest DICN, EICN and EICR. A foundation-model paper can appeal to EUGN, EIGN and EUCR for different reasons. These mappings are editable routing hypotheses, not measured real-world preferences.

For clean type comparisons, hold the target domain and venue rubric constant across all sixteen agents. The same ML expert is asked to apply sixteen distinct preferences. Use the card's suggested domains only to interpret possible research-community affinity; do not give a theory-only paper sixteen unrelated disciplinary grading standards.

To make a stronger cross-field preference claim, run an additional controlled domain-routing study: hold type/model/materials fixed, vary the actual domain rubric, and compare against public papers from that domain. A first-release author report can give **hypotheses about receptive communities**, but cannot claim measured venue preference from role names alone. Record when domain expertise is inadequate and abstain.

## Validation

On matched cases, change one axis while fixing the other three, model, rubric and budget. Check whether it changes the intended priority without increasing factual errors or merely shifting all scores upward. Test D/E, I/U, G/C and N/R interactions instead of assuming orthogonality. Compare against equal-budget homogeneous reviewers. The benchmark plan also tests irrelevant polish, valid fixes, position reversal and false consensus.
