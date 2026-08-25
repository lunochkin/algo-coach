# Roadmap

Each phase ships one capability and a write-up. Ship thin.

A phase exits when its deliverable is in use by whatever consumes it: daily
practice for a phase the user runs, the next phase for one that builds a
capability. A phase can also close as superseded — built, and answered by
something later, so its exit no longer applies.

`docs/architecture/README.md` owns the concepts, boundaries, and invariants.
This file owns only sequencing. Where the two differ, the architecture wins.

A completed phase records what landed, not why. The reasons are in the
architecture doc and in the commits.

## Phase 1 — Push API, techniques, drill board — done

Real daily attempts in the engine, and current state visible.

- Push API: `Problem` and `Attempt` ingested from the practice client. Per
  record, so one bad line costs nothing around it, and re-running is a no-op on
  what landed.
- Techniques: the product-owned vocabulary, shipped as code. A code carries the
  criterion for claiming it and the near miss it is confused with.
- Drill board: per-technique standing derived from the log, grouped on a claim
  where one exists and on the problem's tags otherwise.

## Phase 2 — Drill loop on a pushed problem — superseded

Board, then a technique, then a problem, solved on the platform. The loop mints
no attempt: it waits on a push and diffs its own log, so the engine calls
nothing and works whatever the user pushes with.

Superseded by Phase 8. The platform serves, times and judges, so this loop can
never verify a submission or time a sitting it did not witness. What survives
unchanged is the claim and self-label prompt at the moment of solving.

## Phase 3 — Technique attribution — done

Which techniques a solution used, read off the code rather than off the
problem's tags.

- Hand claims over the backlog: the eval set, adjudicated against a frontier
  model with every divergence resolved by hand.
- A classifier constrained to the problem's own candidates, scored per
  technique by set equality against the user's claims.
- The call log beneath it: one transport, one record per request, carrying the
  prompt whole, what the run cost and what it was sampled at.
- Provenance settled — model, effort, pin, temperature, prompt digest. A
  reading is greedy, and staleness keys on the digest of the question rather
  than on a version over the rulebook.

Delta for generated problems: candidates come from codes derived from canonical
solutions rather than from a platform's tags. Phase 6 carries it.

## Phase 4 — Cards and template matching — done

- Card content as product data, authored by a skill into `content/` and seeded
  into the store. A card names no problem; it carries a selector.
- Template matches: one record per template and problem, negatives included,
  three writers ordered by what each of them knew.
- The matcher and its annotation pass, which writes the reference a machine
  reading is measured against.

What a card still needs — the ladder, runs, recall and probes — waits on a
corpus that can fill it. Phase 7.

## Phase 5 — Pivot to generated problems (current)

The engine writes its own problems, so the path that ingested a platform's
stops being a second origin. Removing it before generation is written keeps
generation from being built around a distinction that no longer earns its
place.

- The architecture doc goes first. It still describes the push API as a kept
  second ingest path, and threads pushed-problem rules through Problems,
  Attempts, Boundaries and Invariants. The doc carries the intent, so it
  settles the shape the code then follows.
- The ingest path goes: the push commands, the push payloads, the external-id
  resolution, and the tag mapping that turned a platform's vocabulary into
  codes. A generated problem derives its techniques from its canonical
  solutions instead.
- The superseded drill loop goes with it. It waited on a push and diffed the
  log, and neither act has a subject once nothing is pushed.
- The pushed corpus moves to `data/old/` rather than being deleted. It is the
  reference the announcement floor is measured against, and Phase 6 reads it
  from there.
- The live store empties, and only then can the records tighten. `origin:
  push`, `source_status`, `external_id` and the platform fields describe a
  shape nothing produces, and a field kept for records that no longer exist is
  one every reader branches on forever. Tightening is legal only while no
  stored record carries the loose shape, so it follows the reset rather than
  leading it.
- The eval set does not survive. 138 hand claims over 100 attempts key to
  pushed attempts, and a classifier scored later is scored against a set
  rebuilt by hand on generated problems. That is the price of the reset, taken
  deliberately.
- Exit: one origin end to end. Nothing in the repo ingests a third-party
  record, no doc describes a path that does, and the store holds only what the
  engine wrote.

## Phase 6 — Problem generation

The engine writes problems: a statement, the test cases that decide it, and at
least one canonical solution. Nothing lands until the canonical passes them.

It is first because everything after it needs a corpus the engine owns. The
ladder resolves over problems, and the in-engine loop serves and verifies them.
A pushed corpus covers whatever the user happened to solve, and it carries no
test cases at all.

- The matcher is scored first, per template on positive verdicts in both
  directions. Generation asserts a match and the matcher audits it, so an
  unmeasured matcher would audit at an unknown error rate.
- Generation is a command in the engine, beside the classifier and the matcher.
  One transport, one call log, one provenance base. No second pipeline.
- A generated problem asserts the template it was written for. The matcher
  reads it later for the templates it was not written for, and audits that
  assertion.
- A problem's techniques derive from its canonical solutions. That is also what
  gives the attribution classifier its candidates on a generated problem.
- The discrimination bar comes first. Cases that separate nothing license the
  word `verified` on a canonical that is wrong. Which check is the bar is
  settled from a real corpus rather than argued.
- The announcement floor is measured against the archived corpus in
  `data/old/`. A form a matcher names from the statement alone was
  telegraphed, and such a problem teaches recognition of nothing.
- Exit: a card's reported gaps are filled by generated problems, and Phase 7
  resolves a ladder over them.

## Phase 7 — Ladder, recall and card runs

What a card needs once there are problems to fill it.

- The ladder resolved at import, from the selector and the template matches, at
  least one rung per studied template. A studied template with no match is a
  reported gap, and the gap is what a generation run is aimed at.
- Studying a card is an explicit act: the ladder is measured from it, and
  probes are assigned at it.
- A recall attempt is not an `Attempt`: no problem, no platform, no submission.
  Its own record, keyed to a card and a template. A hinted pass is not a pass.
- The trainer never prints a template. Names hidden, reproduced cold, run
  against the card's own tests.
- Status, not verdicts: what was recalled and when, what the ladder has left,
  which probes are available. The inputs a graduation rule would read.
- Graduation names no threshold. A timed box, a probe count and a decay edge
  cannot be chosen before the numbers exist. The rust jog is the other
  candidate: a technique that was once fluent wants minutes, not a card.
- Exit: recall and the ladder run daily.

## Phase 8 — In-engine drill loop

The first attempts the engine produces rather than ingests. It serves a
generated problem, times the sitting, runs the submission against the problem's
own test cases, and records the verdict.

- `Attempt` gains the verification result — which cases passed, out of how
  many — beside the platform status string it already carries. Additive, and
  meaningless before Phase 6.
- The interaction is answered by using it: how a solution is entered, what the
  loop does with a failing run, whether a sitting resumes.
- Claims and self-labels are asked as Phase 2 asked them. The writers do not
  change; what changes is who witnessed the sitting.
- Exit: daily practice runs here, on problems the engine wrote and judged.

## Phase 9 — Technique mastery, scheduling, failure mode

Per-technique skill state updated from attempts and the diagnosis signal;
scheduling targets the diagnosed cause, not per-problem intervals. Exit: the
scheduler drives daily practice.

Failure mode lands here rather than beside attribution. Rust and gap are
identical in a single attempt. Only whether the technique was ever fluent
separates them, and that is the mastery state itself. Recall history does not
stand in for it: reproducing a form cold is not recognising it unprompted, and
the gap between the two is the false-fluency trap. What a classifier adds is
narrower. It reads a sitting's code for a mechanical slip against a conceptual
miss, scored per mode against the loop's self-labels. `SPEED` needs settling
first, since "solved but too slowly" is about the user while a timeout is about
the solution's complexity.

Sessions land here too. A sitting is several submissions, and counting each as
an attempt over-weights the ones that took a retry. It is a derived view over
the log, grouped on read, and never a field a client sets.

## Phase 10 — Program-analysis-grounded diagnosis

Ground the classifier in evidence: AST-diff against canonical solutions,
execution-trace comparison, empirical complexity measurement. Needs the test
cases and canonicals Phase 6 brings. Deliverable: measured accuracy delta
against LLM-only diagnosis.

## Phase 11 — Retrieval

Similar problems, patterns, and technique briefs retrieved from the corpus and
the user's own attempts; weak-spot patterns surfaced.

## Phase 12 — MCP + autonomy

Corpus and tools exposed as an MCP server. A scheduled agent runs the practice
loop: it picks drills and adapts to history.

## Phase 13 — Multi-agent (conditional)

Only if a real pipeline earns it: diagnose → retrieve → brief → schedule.

## Phase 14 — Soundness-checked synthesis

An upgrade to Phase 6's generation rather than its first appearance. Formal
constraint specs, property-based test-case generation, adversarial validation.
What it buys is a guarantee that a case set discriminates, where Phase 6 has a
bar chosen from a real corpus.
