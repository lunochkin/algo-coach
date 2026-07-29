# Roadmap

Each phase = real practice value + a write-up. Ship thin; a phase is done
when it's used daily, not when it's feature-complete.

## Phase 1 — MVP (current)

Run real attempts through execute-verify, classify the failure, log it.

- Drill loop
- Failure classifier: speed / rust / gap / syntax router — *why* an attempt
  failed, not just whether. Structured LLM output.
- Eval harness from day one: classifier agreement vs self-labels, measured.
- Research-grade logging schema from day one: append-only attempts +
  diagnoses — a longitudinal dataset of procedural-skill acquisition.
- Exit: classifier runs on real daily attempts.

## Phase 2 — Technique-mastery model

Per-technique skill state updated from execution-verified attempts and the
diagnosis signal; scheduling targets the diagnosed cause, not per-problem
intervals. Exit: the scheduler drives daily practice.

## Phase 3 — Program-analysis-grounded diagnosis

Ground the classifier in evidence: AST-diff vs reference solutions,
execution-trace comparison, empirical complexity measurement. Deliverable:
measured accuracy delta vs LLM-only diagnosis.

## Phase 4 — Retrieval

Similar problems, patterns, and technique briefs retrieved from a personal
solution corpus via the `CorpusSource` protocol; weak-spot patterns surfaced.

## Phase 5 — MCP + autonomy

Corpus and tools exposed as an MCP server; a scheduled agent runs the
practice loop — picks drills, adapts to history.

## Phase 6 — Multi-agent (conditional)

Only if a real pipeline earns it: diagnose → retrieve → brief → schedule.

## Phase 7 — Verified problem synthesis

Formal constraint specs, property-based test-case generation, adversarial
validation — soundness-checked generated problems.
