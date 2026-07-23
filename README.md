# algo-coach

AI coaching layer for deliberate practice of algorithmic problem-solving:
execution-verified spaced repetition over a technique-mastery model, with
LLM-based failure diagnosis.

Most practice tools schedule *problems*. algo-coach models mastery of
*techniques* — every attempt is executed and verified, a classifier diagnoses
*why* an attempt failed (speed / rust / gap / syntax), and scheduling targets
the diagnosed cause. Procedural-skill SRS, not fact SRS — built for
experienced engineers restoring fluency, not beginners learning concepts.

**Status: early.** Phase 1 (failure classifier + attempt log + eval harness)
in progress. Used daily by its author.

## Core loop

```
attempt (real code) → execute + verify → diagnose failure mode
      → schedule the next rep accordingly → brief before next attempt
```

## Design

- **Why-you-fail diagnosis** — a failure-mode classifier (structured LLM
  output, evaluated against self-labels) routes each attempt to
  speed / rust / gap / syntax; scheduling consumes the cause, not just the
  outcome.
- **Technique-level mastery** — skill state per technique, updated from
  execution-verified attempts; not per-problem intervals.
- **Bring your own problems** — problem access goes through the
  `ProblemSource` protocol (`get_problem` / `get_test_cases` / `verify`);
  a local file source ships with the repo.
- **Your data stays yours** — attempt logs and solutions live in `data/`
  (never committed). The schema is public; the data is not.

## Development

```
uv sync
uv run pytest
```

See `CLAUDE.md` for conventions and `docs/ROADMAP.md` for the phase plan.

## License

Apache-2.0.
