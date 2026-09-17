#!/usr/bin/env python3
"""Build the transparent 2^4 type system; no learned psychometric claims."""
import itertools
import json
from pathlib import Path

AXES = [
    {"id": "evidence", "name": "Evidence preference", "zh": "证据偏好", "poles": {
        "D": {"name": "Deductive", "zh": "演绎", "question": "Which explicit assumptions and valid derivations support the central claim?"},
        "E": {"name": "Empirical", "zh": "实证", "question": "Which observations, controls and uncertainty estimates support the central claim?"}}},
    {"id": "contribution", "name": "Contribution preference", "zh": "贡献目标", "poles": {
        "I": {"name": "Insight", "zh": "解释", "question": "What does this change about our understanding of the mechanism?"},
        "U": {"name": "Utility", "zh": "效用", "question": "What meaningful problem does this solve, compared with realistic alternatives?"}}},
    {"id": "scope", "name": "Scope preference", "zh": "适用范围", "poles": {
        "G": {"name": "General", "zh": "通用", "question": "Which stated conditions support transfer across settings, and where does it stop?"},
        "C": {"name": "Contextual", "zh": "情境", "question": "How well does the claim hold in the specific setting, including its constraints?"}}},
    {"id": "risk", "name": "Research-risk preference", "zh": "研究风险偏好", "poles": {
        "N": {"name": "Novelty-seeking", "zh": "探索", "question": "What new research possibility is established, beyond a fashionable narrative?"},
        "R": {"name": "Reliability-seeking", "zh": "稳健", "question": "Which stress tests, checks or replications establish that the stated result is dependable?"}}},
]

# Domain affinities are explicit starting hypotheses, not exclusive assignments.
CARDS = {
    "DIGN": ("Architect", "范式架构师", ["learning theory", "causal ML"], "A new formal abstraction that explains a broad class of learning problems.", "Mistaking elegant notation for a new explanation."),
    "DIGR": ("Guardian", "公理守门人", ["learning theory", "statistical learning"], "A reusable explanatory result whose assumptions and boundaries are defensible.", "Unstated regularity assumptions or an unjustified transfer of a theorem."),
    "DICN": ("Detective", "机制探案者", ["mechanistic interpretability", "causal ML", "AI for science"], "A new, precisely delimited explanation of an important phenomenon.", "Claiming identification where only an illustrative mechanism was proved."),
    "DICR": ("Auditor", "证明审计师", ["theory", "formal methods for ML"], "An exact argument for the actual conditions in the manuscript.", "Boundary cases, quantifier errors and claims stronger than the derivation."),
    "DUGN": ("Inventor", "算法发明家", ["optimization", "algorithms for ML"], "A new algorithmic principle with general, demonstrated problem-solving value.", "A renamed classical algorithm without a consequential difference."),
    "DUGR": ("Engineer", "优化工程师", ["optimization", "efficient ML"], "A useful general method with sound complexity and convergence guarantees.", "Guarantees that ignore the cost or feasibility of their assumptions."),
    "DUCN": ("Strategist", "设计策略师", ["model-based RL", "decision-focused learning", "AI for science"], "A carefully reasoned new design for a consequential constrained problem.", "A clever construction whose assumptions cannot hold in the target setting."),
    "DUCR": ("Verifier", "验证工程师", ["safe RL", "formal verification", "robust control"], "A practical decision rule whose guarantee matches the operating conditions.", "A safety or feasibility claim that holds only for a different system."),
    "EIGN": ("Explorer", "规律探索者", ["representation learning", "scaling laws"], "A surprising empirical regularity that changes a general understanding.", "Cherry-picked regularities or speculation presented as an established law."),
    "EIGR": ("Curator", "证据策展人", ["evaluation methodology", "empirical ML"], "A replicable body of evidence that establishes a broadly useful explanation.", "A pooled trend masking task-level failures or a data-dependent analysis."),
    "EICN": ("Hunter", "现象猎手", ["NLP", "vision", "mechanistic interpretability"], "A new, well-observed phenomenon within a clearly defined model or task.", "Anecdotes generalized beyond the measured regime."),
    "EICR": ("Experimenter", "实验侦探", ["causal evaluation", "NLP", "vision"], "Controlled experiments that isolate the explanation in the claimed setting.", "Confounded ablations, leakage and comparisons with mismatched conditions."),
    "EUGN": ("Pioneer", "前沿开拓者", ["foundation models", "generative AI", "agents"], "A new capability with credible usefulness across meaningful tasks.", "An impressive selected demo with no adequate capability evaluation."),
    "EUGR": ("Builder", "基准工程师", ["ML systems", "benchmarks", "efficient ML"], "Dependable practical gains under fair, reproducible multi-setting evaluation.", "Unmatched compute, hidden costs, stale baselines or evaluation leakage."),
    "EUCN": ("Designer", "交互先锋", ["human-centered AI", "robotics", "AI for science"], "A new useful capability demonstrated under the constraints of its users or domain.", "Proxy success mistaken for actual usefulness or unsupported user claims."),
    "EUCR": ("Steward", "部署守护者", ["robustness", "AI safety", "deployed ML"], "Reliable value in the actual operating context, including consequential failures.", "Average gains concealing brittle behavior or an unmeasured deployment claim."),
}


def build():
    codes = ["".join(p) for p in itertools.product(*[list(a["poles"]) for a in AXES])]
    flip = {a: b for axis in AXES for a, b in [tuple(axis["poles"]), tuple(reversed(axis["poles"]))]}
    personas = []
    for code in codes:
        name, zh, domains, values, watch = CARDS[code]
        neighbors = [code[:i] + flip[c] + code[i + 1:] for i, c in enumerate(code)]
        personas.append({"id": code.lower(), "code": code, "name": name, "name_zh": zh,
                         "axis_values": dict(zip([a["id"] for a in AXES], code)),
                         "domains": domains, "domain_affinity_status": "design_hypothesis",
                         "values": values, "watch_for": watch,
                         "questions": [a["poles"][c]["question"] for a, c in zip(AXES, code)],
                         "neighbors": [n.lower() for n in neighbors],
                         "opposite": "".join(flip[c] for c in code).lower()})
    pairs = [[p["id"], p["opposite"]] for p in personas if p["id"] < p["opposite"]]
    return {"version": "0.1.0", "basis": "Four declared binary review preferences; their Cartesian product defines exactly sixteen related types.",
            "validation_status": "Designed taxonomy; psychometric validity, axis separability and review benefit not yet established.",
            "shared_floor": "Correctness, honest evidence, applicable venue standards and no fabricated objections apply equally to every pole. Preference never excuses invalidity.",
            "axes": AXES, "personas": personas, "challenge_pairs": pairs}


if __name__ == "__main__":
    dest = Path(__file__).resolve().parents[1] / "references" / "personas.json"
    dest.write_text(json.dumps(build(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(dest)
