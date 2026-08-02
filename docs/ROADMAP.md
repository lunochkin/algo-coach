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
  per-technique state from them.

## Phase 2 — Drill loop (current)

Board → pick a technique → solve on the platform → record what it cannot know.
The flow and its rules live in `docs/architecture/README.md`.

- The loop mints no attempt: its last step invokes the client's export, and the
  records arrive through the push path.
- A technique claim and a self-label per attempt. The first writer of either,
  and the only one until a classifier exists.
- Exit: loop runs on real daily attempts.

## Phase 3 — Classification

What an attempt used, and why it failed. Both are LLM classifiers over the same
records, and both are scored against something the loop wrote by hand — which
is why they follow it rather than accompany it.

- Attribution classifier: which of the problem's tags the solution actually
  used, constrained to those tags, so it picks among candidates rather than
  classifying freely. Tag fallback biases progress toward broad techniques.
- Failure classifier: speed / rust / gap / syntax router. Structured LLM output.
- Eval: attribution agreement vs the user's claims, diagnosis agreement vs
  self-labels. Measured, not asserted.
- Exit: both run on real daily attempts.

## Phase 4 — Technique mastery + cards

Per-technique skill state updated from attempts and the diagnosis signal;
scheduling targets the diagnosed cause, not per-problem intervals. Exit: the
scheduler drives daily practice.

Cards land here: teaching content referencing a technique, shown as a brief
before an attempt. Progress per card is the mastery number under another name,
so the two are one thing, and choosing what to show is what the scheduler does.

Sessions land here: a sitting is several submissions, and counting each as an
attempt over-weights the ones that took a retry. A derived view over the log,
grouped on read — never a field a client sets.

## Phase 5 — Product problems + verification

Product-owned problems and test cases seeded from the content pipeline;
attempts on them are executed and verified locally. The first attempts the
engine produces rather than ingests. `Attempt` gains whether a real test run
backs its verdict — additive, and meaningless before now. Exit: verified
attempts feed the mastery model.

## Phase 6 — Program-analysis-grounded diagnosis

Ground the classifier in evidence: AST-diff vs reference solutions,
execution-trace comparison, empirical complexity measurement. Needs Phase 5's
test cases and reference solutions. Deliverable: measured accuracy delta vs
LLM-only diagnosis.

## Phase 7 — Retrieval

Similar problems, patterns, and technique briefs retrieved from the user's own
attempt corpus in the engine store; weak-spot patterns surfaced.

## Phase 8 — MCP + autonomy

Corpus and tools exposed as an MCP server; a scheduled agent runs the
practice loop — picks drills, adapts to history.

## Phase 9 — Multi-agent (conditional)

Only if a real pipeline earns it: diagnose → retrieve → brief → schedule.

## Phase 10 — Verified problem synthesis

Formal constraint specs, property-based test-case generation, adversarial
validation — soundness-checked generated problems.
