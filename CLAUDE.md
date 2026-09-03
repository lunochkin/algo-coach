# Project conventions

AI coaching layer for deliberate practice of algorithmic problem-solving.
See `README.md` for what this is; `docs/ROADMAP.md` for the phase plan.

## Stack

- Python ≥3.14, `uv` for env/deps, pydantic v2, pytest.
- `textual` where a command is a screen rather than a scroll, driven in tests
  through its pilot.
- `uv sync` to set up; `uv run pytest` to test. `-n auto` for the whole suite,
  which runs it in 13s against 44s; the workers cost two seconds to start, so
  one file is faster without them.

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
- Facts go where they can be enforced: tests, then hooks and types. Prose
  carries what nothing can execute.
- Implementation follows from tests and shape, and feeds back: what it
  discovers revises the doc.
- Divergence is checked on purpose. An unchecked doc describes a system that
  does not exist, and a model implements that description anyway.
- `docs/TODO.md` is a task list, not a log. It holds the phases still open.
- A ticked item stays while its phase is open. Items are removed a whole phase
  at a time, never one by one as each lands.
- A closed phase is harvested into `docs/ROADMAP.md`, then removed whole. What
  survives is what it measured, since nothing re-derives it. How the work was
  sequenced is in the commits.
- A roadmap section is compact: what ships as a short bullet list, what the
  phase exits on, and for a closed one what it measured. No argument for why,
  and no detail a reader can get from `docs/architecture/` or the commits.

## Sequencing

High-level design first, without detail; then small items one at a time.
Neither big batches nor detailed design up front.

A design pass settles boundaries, record shapes and what is irreversible, then
stops. A detail only real use can answer is named as deferred rather than
reasoned out. The schema is designed a phase ahead of the features.

A phase's exit depends on its own items alone. Working ahead into the next
phase is fine. An exit that waits on an item there is not: nothing then decides
when the phase closes, and two phases close together on whichever item lands
last.

## Writing

Docs, `README.md`, commits, comments.

- Shortest form that keeps the reason. Cut restating, hedging, and any
  sentence that only rephrases the one before.
- **No aphorisms.** State the rule, then the reason, both literally. Don't
  compress an argument into a metaphor the reader has to unpack.
- **Name what every noun refers to.** A noun the doc has not defined — `the
  work`, `the point`, `the product`, `the unit` — means the sentence restates
  the previous one in more abstract words rather than adding a fact. Cut it,
  or name what it stands for.
- **A bullet ends on its reason, never on a summary.** A closing clause that
  can be deleted without losing a fact is a summary. Check the last sentence
  of every bullet against the test above.
- **No personification.** Records don't wear, ride, go quiet, or flatter. Say
  what the code does.
- **One idea per sentence.** Split at the em-dash and the semicolon instead
  of chaining. Target 25 words; nothing over 40.
- **A TODO item is a task someone can finish**, not a statement about the
  system. An item that only asserts what is true has nothing to do and never
  gets ticked. State it in `docs/architecture/` instead.
- **An item opens with an imperative verb**: write, add, run, measure, delete,
  rename. A noun phrase names a topic, and a reader cannot tell whether the
  work is to build it, decide it or check it.
- **An item names what exists when it is done** — a file, a field, a passing
  test, a number written down. Without that, two readers tick it at different
  points, and the phase closes on whichever read it loosest.
- **An investigation is written as the run and its output**, never as the
  question. "Whether X holds is what decides Y" is a statement; the task is to
  run X once and record what it showed. Keep the question in
  `docs/architecture/` if it needs stating at all.
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

- Match pydantic/pytest idiom. Keep slices thin: a feature is done when it runs
  on real daily practice, not when it's feature-complete.
- **A docstring and its comments stay shorter than the code they sit on.** Over
  that, the reason belongs in `docs/architecture/` and the code cites it.
- **No docstring where the name and the signature already say it.**
  `candidates() -> list[str]` returning `sorted(codes())` needs none.
- **Never restate a reason `docs/architecture/` already gives.** Docs are the
  durable context; a copy in the code drifts from it. Point instead:
  `# sorted: the digest is taken over this order`.
- **One comment carries one non-obvious fact** — the alternative rejected, the
  invariant that would break. Not the argument for it.
- The `## Writing` rules are for docs and commits. They do not license prose in
  a module.
- Tests are the exception to the budget. A test keeps a one-line docstring
  saying what it pins, since the body is two lines and the name cannot carry
  the reason.
- **A test module carries no docstring**, and one already there is deleted. The
  exception above is per test. A module-level one restates what the filename
  says or what `docs/architecture/` already carries, and a fact it holds alone
  belongs on the test that pins it.

## Git

- Conventional Commits, imperative subject ≤50 chars, English.
- Pre-commit + commit-msg hooks live in `.githooks/`
  (enable once: `git config core.hooksPath .githooks`).
  They enforce a vocabulary guard whose word list is `.githooks/words`. It is
  untracked, since it names exactly what must never be committed. Without the
  list the hooks fail rather than pass. A guard that silently allows everything
  when unconfigured is worse than no guard.
