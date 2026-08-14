# Roadmap

Each phase = real practice value + a write-up. Ship thin; a phase is done
when it's used daily, not when it's feature-complete.

`docs/architecture/README.md` owns the concepts, boundaries, and invariants.
This file owns only sequencing; where the two differ, the architecture wins.

## Phase 1 — Push API, techniques, drill board

Get real daily attempts into the engine and make current state visible.

- Record schema settled before the first real ingest: engine-minted ids on
  `Attempt` and `Problem`, `user_id` and `external_id` on `Attempt`, and
  `TechniqueClaim` as a joined record. The log is append-only, so none of it
  can be retrofitted.
- Push API: ingest `Problem` and `Attempt` from the practice client. No
  verification on this path.
- Techniques: the product-owned vocabulary, a data file rather than a
  datastore. The log references the codes, so retirement goes through an alias
  map, never a deletion.
- Drill board: read-only — per technique, attempt history and current state
  from recency, attempt count, solved/unsolved, and self-label. Grouping
  resolves to a claim if one exists, otherwise the problem's tags, so a history
  of past attempts groups without being labelled. Diagnosis is not an input
  until Phase 3. No scheduling; the user picks what to drill.
- Exit: a week of real attempts is in the store, and the board renders
  per-technique state from them. Built, and open until it does.

## Phase 2 — Drill loop

Board → pick a technique → solve on the platform → record what it cannot know.
The flow and its rules live in `docs/architecture/README.md`.

- The loop mints no attempt: it waits for the user to push and diffs its own
  log, so the engine calls nothing and works whatever they push with.
- A technique claim and a self-label per attempt. The first writer of either,
  and the only writer of self-labels there will be.
- Exit: loop runs on real daily attempts. Built, and open until it does.

## Phase 3 — Technique attribution

Which techniques a solution used. The evidence is the code and the code does
not decay, so the ground truth can be given retroactively and the phase needs
no practice to start. Whether two careful readers agree is what the phase asks,
not what it assumes: until something separates model error from annotator error
from a rule that cannot be applied, a disagreement is all three at once.

- Hand claims over a sample of the backlog: the eval set, and the correction
  path afterwards. A self-label cannot be given this way, which is why the
  failure work is not here.
- Attribution classifier constrained to the problem's own tags, so it picks
  among candidates rather than classifying freely. Tag fallback biases progress
  toward broad techniques.
- Two measurements: disagreement with the tag fallback says whether the board
  moves, agreement with the hand claims says whether the move is right.
- Exit: attribution runs on real daily attempts and its claims stand. Built,
  and open until it does. Whether the classifier beats the tag fallback is
  measured when mastery estimation reads claims, not here — until then a wrong
  claim costs a board the user reads with their own judgment.

## Phase 4 — Cards (current)

How studying a technique is organised: what to read, what to reproduce from
memory, and what to solve. Cards are why daily practice starts, which is what
Phases 1-3 all exit on.

Cards are not an ability estimate. Mastery is what a user can solve, per
technique, and it is Phase 5; the two share sequence and no data.

### Phase 4a — cards and recall

- Card content is product data, structured and seeded from files: the topic,
  its templates, and a fixed problem ladder. Authored by a skill, never
  hand-edited — prose parsed by regex is what this replaces.
- A recall attempt is not an `Attempt`: no problem, no platform, no
  submission. Its own record, keyed to a card and a template.
- The trainer never prints a template. Names hidden, blank-filed cold, run
  against the card's own tests.
- Status, not verdicts: what was recalled and when, what the ladder has left,
  which probes are available. The inputs a graduation rule would read.
- Exit: recall runs daily, and cards are authored and studied here rather than
  by hand outside the engine.

### Phase 4b — what daily use asks for

Left open deliberately. Graduation needs a timed box, a probe count and a decay
edge, and none can be chosen before the numbers exist — which is why 4a shows
the inputs and names no threshold. The other candidate is the rust jog: a card
is the full learning loop, and a technique that was once fluent wants minutes.

## Phase 5 — Technique mastery, scheduling, failure mode

Per-technique skill state updated from attempts and the diagnosis signal;
scheduling targets the diagnosed cause, not per-problem intervals. Exit: the
scheduler drives daily practice.

Failure mode lands here rather than beside attribution. Rust and gap are
identical in a single attempt, and only whether the technique was ever fluent
separates them — which is the mastery state itself. Recall history does not
stand in for it: reproducing a form cold is not recognising it unprompted, and
the gap between the two is the false-fluency trap. What a classifier adds is
narrower: reading a sitting's code for a mechanical slip against a conceptual
miss, scored per mode against the loop's self-labels. `SPEED` needs settling
first, since "solved but too slowly" is about the user while a timeout is about
the solution's complexity.

Sessions land here: a sitting is several submissions, and counting each as an
attempt over-weights the ones that took a retry. A derived view over the log,
grouped on read — never a field a client sets.

## Phase 6 — Product problems + verification

Product-owned problems and test cases seeded from the content pipeline;
attempts on them are executed and verified locally. The first attempts the
engine produces rather than ingests. `Attempt` gains whether a real test run
backs its verdict — additive, and meaningless before now. Exit: verified
attempts feed the mastery model.

## Phase 7 — Program-analysis-grounded diagnosis

Ground the classifier in evidence: AST-diff vs reference solutions,
execution-trace comparison, empirical complexity measurement. Needs the test
cases and reference solutions verification brings. Deliverable: measured accuracy delta vs
LLM-only diagnosis.

## Phase 8 — Retrieval

Similar problems, patterns, and technique briefs retrieved from the user's own
attempt corpus in the engine store; weak-spot patterns surfaced.

## Phase 9 — MCP + autonomy

Corpus and tools exposed as an MCP server; a scheduled agent runs the
practice loop — picks drills, adapts to history.

## Phase 10 — Multi-agent (conditional)

Only if a real pipeline earns it: diagnose → retrieve → brief → schedule.

## Phase 11 — Verified problem synthesis

Formal constraint specs, property-based test-case generation, adversarial
validation — soundness-checked generated problems.
