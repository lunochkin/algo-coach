# Roadmap

Each phase ships one capability and a write-up. Ship thin.

A phase exits when its deliverable is in use by whatever consumes it: daily
practice for a phase the user runs, the next phase for one that builds a
capability. A phase can also close as superseded — built, and answered by
something later, so its exit no longer applies.

`docs/architecture/` owns the concepts, boundaries, and invariants.
This file owns only sequencing. Where the two differ, the architecture wins.

A completed phase records what landed, not why. The reasons are in the
architecture doc and in the commits. It also records what the phase measured.
`docs/TODO.md` drops a phase when it closes, and a measurement is taken once.

## Phase 1 — Push API, techniques, drill board — done

Real daily attempts in the engine, and current state visible.

- Push API: `Problem` and `Attempt` ingested from the practice client. Per
  record, so one bad line costs nothing around it, and re-running is a no-op on
  what landed.
- Techniques: the product-owned vocabulary, shipped as code. A code carries the
  criterion for claiming it and the near miss it is confused with.
- Drill board: per-technique standing derived from the log, grouped on a claim
  where one exists and on the problem's tags otherwise.

Measured:

- 485 problems in the backlog: 61 reached no technique, 183 one, 241 two or
  more. That share is what made a classifier worth building.
- 1785 attempts over 117 practice days, 159 of them in the last 30.
- The board renders 25 technique rows, and 101 attempts reach none.

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

Measured:

- Twelve configurations over a 10x price range scored within two attempts of
  each other and failed in the same cells. The model was never what to change.
- A configuration against itself, three `--fresh` passes: 1 of 31 attempts
  flips for opus, 3 for haiku and sonnet. 0.5-2.2% of decisions, and the
  ceiling any score is read against.
- Set equality compounds a per-candidate error: 95% of calls reads as 87% over
  three candidates.
- Keying reuse on the payload digest rather than on a version: editing one
  criteria entry re-derived 7 of 31 attempts.
- 100 attempts claimed blind, carrying 138 claims, so 38 revisions. 62 of them
  were read by a frontier configuration to adjudicate the set.
- Requiring `effort` and `prompt_hash` deleted the 25 machine claims already
  written, rather than re-deriving them.

Delta for generated problems: candidates come from codes derived from canonical
solutions rather than from a platform's tags. Phase 6 carries it.

## Phase 4 — Cards and template matching — done

- Card content as product data, authored by a skill into `content/` and seeded
  into the store. A card names no problem; it carries a selector.
- Template matches: one record per template and problem, negatives included,
  three writers ordered by what each of them knew.
- The matcher and its annotation pass, which writes the reference a machine
  reading is measured against.

Measured:

- Nine cards ported, each authored blind and then compared against the
  hand-written one. The diffs are what the skill's rules are.
- `statement` tightened to required and non-blank at 485 of 485, and held at
  ~4k problems across an eight-fold push.

What a card still needs — the ladder, runs, recall and probes — waits on a
corpus that can fill it. Phase 7.

## Phase 5 — Pivot to generated problems — done

One origin end to end. The engine writes its own problems, so the path that
ingested a platform's stopped being a second origin and was removed before
generation was written.

- The architecture doc first, then the code it settled: the push boundary, the
  pushed-problem rules, and every rule that existed because two origins did.
- The ingest path: the push command and package, the push payloads, the
  external-id resolution, the tag mapping, and the drill loop that waited on a
  push and diffed the log.
- The pushed corpus moved to `data/old/`, which is a calibration corpus rather
  than a store: 1785 attempts and 3962 problems, with the claims and the call
  log. Phase 6 measures the announcement floor against it.
- The live store emptied, and the records then tightened. `origin`,
  `source_status`, `external_id` and the platform fields describe a shape
  nothing produces.
- The eval set did not survive. 138 hand claims over 100 attempts key to
  pushed attempts, and a classifier scored later is scored against a set
  rebuilt by hand on generated problems.

## Phase 6 — Problem generation (current)

The engine writes problems: a statement, the test cases that decide it, and at
least one canonical solution. Nothing lands until the canonical passes them.

It is first because everything after it needs a corpus the engine owns. The
ladder resolves over problems, and the in-engine loop serves and verifies them.
A pushed corpus covers whatever the user happened to solve, and it carries no
test cases at all.

- Generation lands before the matcher is scored. The Phase 5 reset took every
  template match with it, so no pair carries a hand reference until the engine
  has written problems to annotate.
- `Problem` gains provenance before the first run. One generated without it
  carries none for good, and the corpus could then not be compared across
  generator configurations.
- The gap report is here rather than in Phase 7. It is what aims a generation
  run, and the phase exits on a card's gaps being filled.
- The records come first, then generation, then the runner. `TestCase` fixes
  the calling convention, so generation and the runner do not constrain each
  other. The first generation run lands nothing and is read back from the call
  log, which is what tells the runner the shape it must execute.
- The matcher is then scored per template on positive verdicts in both
  directions. Generation asserts a match and the matcher audits it, so an
  unmeasured matcher audits at an unknown error rate. That blocks trusting the
  audit rather than generating.
- The hand pass over the generated corpus does two jobs. It writes the
  matcher's reference, and it is the only reading of a generated problem no
  model produced, so a generator drifting from its brief shows up there.
- Generation is a command in the engine, beside the classifier and the matcher.
  One transport, one call log, one provenance base. No second pipeline.
- A problem is written from a brief: a template, naming the form it must be
  solvable by, or a technique, naming only the skill. A template is where a
  problem comes from and never where its later solutions come from.
- A template match is keyed to a solution rather than a problem, since a form
  is displayed by code. The canonical a problem was generated with asserts its
  own pair, and the matcher reads solutions for the forms nobody named.
- A problem's techniques derive from readings of its canonical solutions.
  `TechniqueReading` is its own class: product data, where a claim is the
  user's private testimony about an attempt. That derivation is also what gives
  the attribution classifier its candidates on a generated problem.
- The discrimination bar is settled on the first corpus, then enforced before
  a problem lands. Cases that separate nothing license the word `verified` on a
  canonical that is wrong. Which check is the bar comes from a corpus rather
  than from an argument.
- A problem is created, cleared by the announcement floor, then served.
  Created is not a resting state: every one is promoted or retired, and a
  problem can be retired before it was ever served.
- A problem found defective is retired rather than edited, and one naming its
  own approach is retired as telegraphed. Only the first excludes its attempts
  from mastery, and neither is deleted.
- The announcement floor is measured against the archived corpus in
  `data/old/`. A form a matcher names from the statement alone was
  telegraphed, and such a problem teaches recognition of nothing.
- Exit: a card's reported gaps are filled by generated problems, and Phase 7
  resolves a ladder over them.

## Phase 7 — Ladder, recall and card runs

What a card needs once there are problems to fill it.

- The ladder resolved at import, from the selector and the template matches, at
  least one rung per studied template. A match is a fact about a solution, so a
  rung is filled by the problem that solution answers. A studied template no
  solution displays is a reported gap, and the gap is what a generation run is
  aimed at.
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

The first attempts the engine produces itself. It serves a
generated problem, times the sitting, runs the submission against the problem's
own test cases, and records the verdict.

- `Attempt` gains the verification result — which cases passed, out of how
  many. Additive, and meaningless before Phase 6.
- The interaction is answered by using it: how a solution is entered, what the
  loop does with a failing run, whether a sitting resumes.
- The loop can mark a problem defective in place of a self-label, and the
  board then stops counting that problem's attempts in either direction.
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

## Phase 10 — Alternative solutions

Every other way to solve a stored problem, enumerated over the corpus rather
than asked for by template. A call proposes the approaches, each becomes its
own canonical, and the problem's own cases judge them. Exit: one rung covers a
studied template and an optional one, through two canonicals of one problem.

A template brief reaches only the forms someone authored, and templates are
about half the vocabulary: a paradigm and a problem class have no form to
reproduce. Enumeration is what reaches the rest, and what widens a problem's
techniques past the one form its brief named.

It also restores an independence generation gives up. A scale case beyond the
reference's reach is taken from the canonical alone; a second efficient
solution cross-checks it.

What it costs is duplicates execution cannot separate — top-down and
bottom-up dynamic programming pass the same cases — and a later canonical
carrying less assurance than the first, since the case set was built to kill
mutants of that one.

## Phase 11 — Program-analysis-grounded diagnosis

Ground the classifier in evidence: AST-diff against canonical solutions,
execution-trace comparison, empirical complexity measurement. Needs the test
cases and canonicals Phase 6 brings. Deliverable: measured accuracy delta
against LLM-only diagnosis.

## Phase 12 — Retrieval

Similar problems, patterns, and technique briefs retrieved from the corpus and
the user's own attempts; weak-spot patterns surfaced.

## Phase 13 — MCP + autonomy

Corpus and tools exposed as an MCP server. A scheduled agent runs the practice
loop: it picks drills and adapts to history.

## Phase 14 — Multi-agent (conditional)

Only if a real pipeline earns it: diagnose → retrieve → brief → schedule.

## Phase 15 — Soundness-checked synthesis

An upgrade to Phase 6's generation rather than its first appearance. Formal
constraint specs, property-based test-case generation, adversarial validation.
What it buys is a guarantee that a case set discriminates, where Phase 6 has a
bar chosen from a real corpus.
