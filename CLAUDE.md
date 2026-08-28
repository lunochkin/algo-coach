# Project conventions

AI coaching layer for deliberate practice of algorithmic problem-solving.
See `README.md` for what this is; `docs/ROADMAP.md` for the phase plan.

## Stack

- Python ≥3.14, `uv` for env/deps, pydantic v2, pytest.
- `textual` where a command is a screen rather than a scroll, driven in tests
  through its pilot.
- `uv sync` to set up; `uv run pytest` to test.

@docs/architecture/README.md
@docs/architecture/content.md
@docs/architecture/corpus.md
@docs/architecture/log.md
@docs/architecture/machine.md
@docs/architecture/flows.md

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
- `docs/TODO.md` is a task list, not a log. It holds the phases still open.
- A ticked item stays while its phase is open. The phase is the unit, not the
  item, so nothing is removed as it lands.
- A closed phase is harvested into `docs/ROADMAP.md`, then removed whole. What
  survives is what it measured, since nothing re-derives it. How the work was
  sequenced is in the commits.

## Sequencing

High-level design first, without detail; then small items one at a time.
Neither big batches nor detailed design up front.

A design pass settles boundaries, record shapes and what is irreversible, then
stops. A detail only real use can answer is named as deferred rather than
reasoned out — the schema runs a phase ahead, features do not.

## Writing

Docs, `README.md`, commits, comments.

- Shortest form that keeps the reason. Cut restating, hedging, and any
  sentence that only rephrases the one before.
- **No aphorisms.** State the rule, then the reason, both literally. Don't
  compress an argument into a metaphor the reader has to unpack.
- **No personification.** Records don't wear, ride, go quiet, or flatter. Say
  what the code does.
- **One idea per sentence.** Split at the em-dash and the semicolon instead
  of chaining. Target 25 words; nothing over 40.
- **A TODO item is a task someone can finish**, not a statement about the
  system. An item that only asserts what is true has nothing to do and never
  gets ticked. State it in `docs/architecture/` instead.
- **A TODO item is one or two lines, rarely three.** It names what to do and
  the one reason that is not obvious from the name. The argument behind it
  belongs in `docs/architecture/`, and the record of how it went
  belongs in the commit.
- **Split before you compress.** An item carrying two decisions becomes two
  items, not one dense paragraph. Each is then checkable on its own, and one
  can land while the other is still open.
- Precise technical terms are unaffected — `append-only`, `digest`,
  `denominator`, `supersede`. Density comes from those, not from clause count.

Before: "A blank string is the same absence wearing a value, so it is
rejected too."
After: "A blank string is rejected too. It passes a presence check while
carrying nothing."

## Code style

- Comments sparse; explain why, never what. Match pydantic/pytest idiom.
- Keep slices thin: a feature is done when it runs on real daily practice,
  not when it's feature-complete.

## Git

- Conventional Commits, imperative subject ≤50 chars, English.
- Pre-commit + commit-msg hooks live in `.githooks/`
  (enable once: `git config core.hooksPath .githooks`).
  They enforce a vocabulary guard whose word list is `.githooks/words`. It is
  untracked, since it names exactly what must never be committed. Without the
  list the hooks fail rather than pass. A guard that silently allows everything
  when unconfigured is worse than no guard.
