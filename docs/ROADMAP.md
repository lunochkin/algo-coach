# Roadmap

Each phase = real practice value + a write-up. Ship thin; a phase is done
when it's used daily, not when it's feature-complete.

`docs/architecture/README.md` owns the concepts, boundaries, and invariants.
This file owns only sequencing; where the two differ, the architecture wins.

## Phase 1 — MVP (current)

Get real daily attempts into the engine and make current state visible.

- Record schema settled before the first real ingest: engine-minted ids on
  `Attempt` and `Problem`, `user_id` and `external_id` on `Attempt`, and
  `AttemptTechnique` as a joined record. The log is append-only — none of these
  can be retrofitted once real data lands.
- Push API: ingest `Problem` and `Attempt` records from the practice client.
  Validate and append; no verification on this path.
- Techniques: the product-owned vocabulary, a data file in this repo rather
  than a datastore. Codes are referenced by the log, so retirement goes through
  an alias map, never a deletion.
- Drill board: read-only — per technique, attempt history and current state,
  derived from recency, attempt count, solved/unsolved, and the user's
  self-label. Grouping comes from `AttemptTechnique`, the user's own claim;
  problem tags are a hint, never the key. Diagnosis is not an input until
  Phase 3. No scheduling; the user picks what to drill.
- Exit: a week of real attempts is in the store, and the board renders
  per-technique state from them.

## Phase 2 — Drill loop

- Interactive drill loop: board → pick a technique → attempt → record.
- Cards: teaching content referencing a technique — briefs shown before an
  attempt. The first thing cards are actually for.
- Exit: loop runs on real daily attempts.

## Phase 3 — Diagnosis

Why an attempt failed, not just whether.

- Failure classifier: speed / rust / gap / syntax router. Structured LLM output.
- Eval: classifier agreement vs self-labels, measured.
- Exit: classifier runs on real daily attempts.

## Phase 4 — Technique-mastery model

Per-technique skill state updated from attempts and the diagnosis signal;
scheduling targets the diagnosed cause, not per-problem intervals. Exit: the
scheduler drives daily practice.

## Phase 5 — Product problems + verification

Product-owned problems and test cases seeded from the content pipeline;
attempts on them are executed and verified locally. The first attempts the
engine produces rather than ingests. Exit: verified attempts feed the mastery
model.

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
