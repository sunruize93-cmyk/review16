# Synthetic anchor fixture

Every manuscript, venue, score, and review declaration here is **synthetic**. The `human_scores` fields contain made-up fixture values, not actual human reviews. These complete toy manuscripts exercise file handling and ranking logic; they provide no scientific calibration or evidence that Review16 predicts acceptance.

The middle score band intentionally contains no anchors. Running the default command reports shortfalls of 9, 10, and 9; it does not invent missing papers.

From the repository root:

```sh
python3 skills/review16/scripts/anchor_rank.py prepare \
  --corpus examples/anchors/corpus.synthetic.json \
  --target examples/anchors/target.synthetic.json \
  --out /tmp/review16-synthetic-run --seed 42

python3 skills/review16/scripts/anchor_rank.py plan-pairs \
  --public /tmp/review16-synthetic-run/public/manifest.json \
  --out /tmp/review16-synthetic-run/public/plan.json --all-pairs --seed 43
```

Use a new output directory on each run. Existing paths are never overwritten. Reviewers receive only the public materials, with individual comparisons served in the frozen order. The coordinating agent keeps `private/` inaccessible until decisions are locked.

See [the schema and decisions format](../../skills/review16/references/anchor-format.md). No generated review or rank report is shipped as if it were real reviewer output.
