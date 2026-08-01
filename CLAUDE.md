# Project conventions

AI coaching layer for deliberate practice of algorithmic problem-solving.
See `README.md` for what this is; `docs/ROADMAP.md` for the phase plan.

## Stack

- Python ≥3.14, `uv` for env/deps, pydantic v2, pytest.
- `uv sync` to set up; `uv run pytest` to test.

@docs/architecture/README.md

## Writing

- Docs, commits, comments: shortest form that keeps the reason. Cut restating,
  hedging, and any sentence that only rephrases the one before.

## Code style

- Comments sparse; explain why, never what. Match pydantic/pytest idiom.
- Keep slices thin: a feature is done when it runs on real daily practice,
  not when it's feature-complete.

## Git

- Conventional Commits, imperative subject ≤50 chars, English.
- Pre-commit + commit-msg hooks live in `.githooks/`
  (enable once: `git config core.hooksPath .githooks`).
  They enforce a vocabulary guard; extend the word list there if needed.
