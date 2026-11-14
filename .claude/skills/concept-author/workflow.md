# The background run

How `run.py` takes one subtopic from queued to live in prod. Each box is one
headless `claude -p` session, except the steps marked as code. `SKILL.md`
`## Running in the background` gives the details, and
`docs/authoring/concepts.md` `## Stages` gives the rules the run follows.

Redraw this file in the same commit as a change to the order of the steps, to
the model a step runs on, to the stopping rule, or to what reaches the author.

```
 run.py --level N --jobs 1 --only <subs>
 │  starts a subtopic once every subtopic it needs is merged into py-auto
 │  one git worktree and one branch per subtopic, cut from py-auto
 ▼
┌──────────────────────────── one subtopic ───────────────────────────────┐
│                                                                         │
│  STAGE 1: concepts        STAGE 2: lessons         STAGE 3: questions   │
│  ┌──────────────┐         ┌──────────────┐         ┌──────────────┐     │
│  │ write (Opus) │         │ write (Opus) │         │ write (Opus) │     │
│  └──────┬───────┘         └──────┬───────┘         └──────┬───────┘     │
│         │ module check           │ module check           │ check       │
│         │                        │                        ▼             │
│         │                        │                 ┌──────────────┐     │
│         │                        │                 │ solver       │     │
│         │                        │                 │ blind (Opus) │     │
│         │                        │                 │ form (Haiku) │     │
│         │                        │                 └──────┬───────┘     │
│         ▼                        ▼                        ▼             │
│     ┌────────────────────── review loop ─────────────────────────┐      │
│     │                                                            │      │
│     │  review (Opus): full, at most 2; then on the last diff     │      │
│     │     │                                                      │      │
│     │     ▼                                                      │      │
│     │  confirm (code): re-run the reviewer's cases.              │      │
│     │     A WRONG whose case fails becomes a DEFECT.             │      │
│     │     │                                                      │      │
│     │     ▼                                                      │      │
│     │  fix: Haiku in stages 1-2, Sonnet in stage 3,              │      │
│     │     then the module check                                  │      │
│     │     │                                                      │      │
│     │     └── loop until a diff review finds no WRONG            │      │
│     └────────────────────────────────────────────────────────────┘      │
│                                                                         │
│  ┌───────────────┐     ┌───────────────────┐     ┌───────────────────┐  │
│  │ digest        │ ──► │ decide (Opus)     │ ──► │ diff review loop  │  │
│  │ (Sonnet)      │     │ fresh session;    │     │ (Opus, then a     │  │
│  │ "For you":    │     │ answers each      │     │ Sonnet fix that   │  │
│  │ up to 3       │     │ question; tries a │     │ also decides)     │  │
│  │ questions     │     │ fix inside the    │     │ until no WRONG    │  │
│  └───────────────┘     │ subtopic first    │     └─────────┬─────────┘  │
│                        └───────────────────┘               │            │
│        digest: "For you" = what is left, "Decided" = log   │            │
│                                                            ▼            │
│                                    commit on the branch, merge py-auto  │
└─────────────────────────────────────────────────┬───────────────────────┘
                                                  │
                    ┌─────────────────────────────┴──────────────────────┐
                    │ THE AUTHOR                                         │
                    │  reads "For you": usually Nothing, or a change to  │
                    │  rules or the baseline, or one retiring a released │
                    │  question                                          │
                    │  says when to release                              │
                    └─────────────────────────────┬──────────────────────┘
                                                  ▼
                    ┌────────────────────────────────────────────────────┐
                    │ run.py --release (code)                            │
                    │  merge py-auto into main, seed locally, seed prod  │
                    │  through the tunnel, commit STATUS.md, rewrite the │
                    │  counts of the Release items in docs/TODO.md       │
                    └────────────────────────────────────────────────────┘
```

- Each stage runs at most two full reviews, then reviews of the last fix's
  diff, until one finds no WRONG. That review's other findings are fixed with
  no further review.
- The module check, the confirmation of WRONG findings, the merges, the
  release and the resume from `state.json` are code, and no model runs them.
