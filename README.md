# algo-coach

AI coaching layer for deliberate practice of algorithmic problem-solving:
spaced repetition over a technique-mastery model, with LLM-based failure
diagnosis.

Most practice tools schedule *problems*. algo-coach models mastery of
*techniques* — a classifier diagnoses *why* an attempt failed
(speed / rust / gap / syntax), and scheduling targets the diagnosed cause.
Procedural-skill SRS, not fact SRS — built for experienced engineers restoring
fluency, not beginners learning concepts.

**Status: early.** Phase 1 (push API + cards + drill board) in progress.
Used daily by its author.

## Core loop

```
attempt (real code) → record → diagnose failure mode
      → schedule the next rep accordingly → brief before next attempt
```

## Design

- **Why-you-fail diagnosis** — a failure-mode classifier (structured LLM
  output, evaluated against self-labels) routes each attempt to
  speed / rust / gap / syntax; scheduling consumes the cause, not just the
  outcome.
- **Technique-level mastery** — skill state per technique, updated from
  attempts and their diagnoses; not per-problem intervals.
- **Push your practice in** — you solve wherever you already solve; your client
  pushes `Problem` and `Attempt` records through the push API. The engine
  contacts no external platform, and no third-party platform client lives in
  this repo.
- **Verification where it's owned** — problems the project ships carry test
  cases and are executed and verified locally; pushed attempts are recorded
  as-is.
- **Your data stays yours** — attempt logs and solutions live in `data/`
  (never committed). The schema is public; the data is not.

## Development

```
uv sync
uv run pytest
```

`docs/architecture/README.md` is the primary design document — concepts,
boundaries, invariants. `docs/ROADMAP.md` sequences the phases; `CLAUDE.md`
holds conventions.

## License

Apache-2.0.
