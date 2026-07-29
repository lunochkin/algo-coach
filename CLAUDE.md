# algo-coach — project conventions

AI coaching layer for deliberate practice of algorithmic problem-solving.
See `README.md` for what this is; `docs/ROADMAP.md` for the phase plan.

## Stack

- Python ≥3.14, `uv` for env/deps, pydantic v2, pytest.
- `uv sync` to set up; `uv run pytest` to test.

## Architecture rules

- **Private assets cross only via protocols.** Problem access goes through
  `ProblemSource` (`get_problem` / `get_test_cases` / `verify`); personal
  corpus access will go through `CorpusSource` (Phase 4 — don't design it
  earlier). No concrete third-party problem-platform client ever enters this
  repo.
- **Schema is append-only.** `Attempt` and `Diagnosis` records are never
  rewritten or deleted; aggregates are derived views, never stored truth.
  Schema changes must be additive (new optional fields), not breaking — the
  log is a longitudinal dataset.
- **Data never enters git.** `data/` is gitignored; only the schema is
  public. No problem statements or test cases from third-party platforms
  committed anywhere (content rights).
- Prefer tools/functions over agents; a pipeline earns multi-agent, not the
  other way around.

## Code style

- Comments sparse; explain why, never what. Match pydantic/pytest idiom.
- Keep slices thin: a feature is done when it runs on real daily practice,
  not when it's feature-complete.

## Git

- Conventional Commits, imperative subject ≤50 chars, English.
- No Co-Authored-By or other trailers.
- Pre-commit + commit-msg hooks live in `.githooks/` (enable once:
  `git config core.hooksPath .githooks`). They enforce a vocabulary guard;
  extend the word list there if needed.
