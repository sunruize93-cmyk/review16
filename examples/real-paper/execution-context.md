# Execution context for the real-paper test

Host: Codex desktop; reviewer model family: GPT-6. Exact deployment build was not exposed. All 16 first-pass agents were created using `fork_turns=none`, with a single prepared persona task path and this shared context:

- Read your own task and matching JSON template, all extracted manuscript text, and relevant PDF page renders using the image viewer.
- Shared domain: memory networks, approximate retrieval and question answering.
- Retrospective ICLR 2017 assessment: evaluate contemporaneous contribution claims, not 2026 baselines.
- Do not browse/search the paper, read human reviews, the coordinator's source directory, other reviewers or parent conclusions.
- External novelty claims remain unverified unless directly supported. No source-code execution or experimental replication.
- Write the structured JSON first pass only, then stop; no child agents.
- Use concise substantive evidence. Early dispatches suggested around 4–7 items; this was a length hint, not a praise/criticism quota.

The prepared task contains the rubric, common evidence standards and persona preferences. Workers were dispatched as capacity became free, with at most three running concurrently. They shared a filesystem; isolation was procedural and was not enforced by separate OS users or ACLs.

The source manuscript included title and author identities. This target panel was **not manuscript-anonymized**. Public-paper memorization and prestige effects remain possible even when a reviewer reports no recognition. Human score metadata was withheld from reviewer prompts; the coordinator had already inspected it while selecting the case.

After all 16 initial JSON files were frozen, the same reviewer contexts received only their four-axis opposite's initial review and manuscript. Each wrote one challenge package checking its opposite's strongest positive and negative claims. Each reviewer then received that package and responded once, retaining its initial score and evidence. No score spread or score changes were requested.

This artifact records the workflow, not independently attested model identity or semantically verified isolation. No token/cost telemetry was available; do not infer cost effectiveness.
