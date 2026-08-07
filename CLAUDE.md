# Project conventions

AI coaching layer for deliberate practice of algorithmic problem-solving.
See `README.md` for what this is; `docs/ROADMAP.md` for the phase plan.

## Stack

- Python ≥3.14, `uv` for env/deps, pydantic v2, pytest.
- `uv sync` to set up; `uv run pytest` to test.

@docs/architecture/README.md

## Where knowledge lives

- Docs matter more with an AI executor, and should be fewer: they are the only
  durable context, and they got cheap to write exactly when they got valuable.
- They carry intent, reasons, and the shape of the system — what a model
  cannot infer and would otherwise reinvent differently each session.
- Facts go where they can be enforced: tests, then hooks and types. Prose is
  the residue, for what nothing can execute.
- Implementation follows from tests and shape, and feeds back: what it
  discovers revises the doc.
- Divergence is checked on purpose. An unchecked doc becomes fiction, and a
  model implements fiction without complaint.

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
  They enforce a vocabulary guard whose word list is `.githooks/words` —
  untracked, since it names exactly what must never be committed. Without it
  the hooks fail rather than pass: a guard that goes quiet when unconfigured
  is worse than none.
