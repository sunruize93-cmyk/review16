# Contributing

Prefer a small reproducible case over a new reviewer adjective. Include the skill version, model/version/family, venue rubric, available materials, expected property, actual output and token budget. Share only manuscripts and review data you are authorized to redistribute. A URL plus version provenance is usually better than copying full papers into this repository.

For type-system changes, explain which axis or relation changes. Preserve the Cartesian-product invariants unless the product deliberately changes its design. Domain affinities are hypotheses; attach evidence before calling them measured preferences.

For corpus contributions, specify venue/year/track, paper type, eligibility filter, review phase, raw score scale, version alignment, public-data coverage, recognized-paper risk and missingness. A paper's final decision is not a numeric rating.

For code contributions, run `python3 -m unittest discover -s tests -v`. Test observable invariants such as withheld target identity, score-scale validation, abstention handling and uncertainty bounds. Do not add tests that only check flattering report wording. Never commit private maps, tokens, confidential papers or live user review runs.

For performance claims, use the preregistered benchmark, equal budgets and held-out cases. Preserve failed comparisons and null results. Distinguish unit tests, synthetic demonstrations, forward smoke tests and real-paper evaluations.
