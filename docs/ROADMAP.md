# Roadmap

Each phase ships one capability and a write-up. Ship thin.

A phase exits when its deliverable is in use by whatever consumes it: daily
practice for a phase the user runs, the next phase for one that builds a
capability. A phase can also close as superseded — built, and answered by
something later, so its exit no longer applies.

`docs/architecture/` owns the concepts, boundaries, and invariants.
This file owns only sequencing. Where the two differ, the architecture wins.

A phase section is short: what ships, what it exits on, and for a closed one
what it measured. Reasons are in `docs/architecture/` and in the commits, and
are not repeated here. `docs/TODO.md` drops a phase when it closes.

## Phase 1 — Push API, techniques, drill board — done

- Push API: `Problem` and `Attempt` ingested per record from the practice
  client.
- Techniques: the product-owned vocabulary, shipped as code.
- Drill board: per-technique standing derived from the log.

Measured:

- 485 problems in the backlog: 61 reached no technique, 183 one, 241 two or
  more. That share is what made a classifier worth building.
- 1785 attempts over 117 practice days, 159 of them in the last 30.
- The board renders 25 technique rows, and 101 attempts reach none.

## Phase 2 — Drill loop on a pushed problem — superseded

Board, then a technique, then a problem, solved on the platform. Superseded by
Phase 8: a loop that waits on a push can verify no submission and time no
sitting. The claim and self-label prompt survives unchanged.

## Phase 3 — Technique attribution — done

- Hand claims over the backlog: the eval set, adjudicated against a frontier
  model.
- A classifier constrained to the problem's own candidates, scored per
  technique by set equality.
- The call log beneath it: one transport, one record per request.
- Provenance settled — model, effort, pin, temperature, prompt digest.

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

## Phase 4 — Cards and template matching — done

- Card content as product data, authored by a skill into `content/` and seeded
  into the store.
- Template matches: one record per template and problem, negatives included.
- The matcher and its annotation pass.

Measured:

- Nine cards ported, each authored blind and then compared against the
  hand-written one. The diffs are what the skill's rules are.
- `statement` tightened to required and non-blank at 485 of 485, and held at
  ~4k problems across an eight-fold push.

## Phase 5 — Pivot to generated problems — done

One origin end to end. The ingest path removed before generation was written.

- The architecture doc first, then the code it settled.
- The push command, payloads, external-id resolution, tag mapping and
  push-driven drill loop deleted.
- The pushed corpus moved to `data/old/` as a calibration corpus: 1785
  attempts and 3962 problems, with the claims and the call log.
- The live store emptied, then `origin`, `source_status`, `external_id` and
  the platform fields removed.
- The eval set did not survive: 138 hand claims key to pushed attempts.

## Phase 6 — Problem generation — done

The engine writes problems: a statement, the test cases that decide it, a
canonical solution and a reference solution. Everything that makes a generated
problem sound.

- Five call sites, each at its own configuration: the generator, the blind
  reference, the input builder, the naive clock, the discrimination round.
- A blind reference settles every expected value; a disagreement discards.
- Mutants of the canonical, killed by the statement's cases, then by built
  inputs, then by at most two rounds of proposed cases. A proposal lands only
  where it killed.
- A separating case where the template claims a speedup: the smallest input
  the naive clock exceeds the drill cap on, under a 64 KiB case ceiling.
- The statement ends on its `solve` signature, checked against the canonical.
- Site outcomes: what each site's gates said, per attempt, beside the call log.
- Drafts as states, held where a step failed, resumed by `generate --resume`,
  listed by `--drafts`.
- A template match keyed to a solution; the generating canonical asserts its
  own pair.
- Technique readings over canonicals, and problem techniques derived from them
  wherever a command loads problems.
- The gap report, and `generate --gaps` aimed at what it lists.
- Exit: every landed problem carries techniques derived from its canonicals
  and a case set measured against the mutation bound, and the gap report names
  the templates the next run is aimed at.

Measured:

- One problem: Opus 5 at high $0.41 over 6 calls and 190 s of model time, 70 s
  of it the round; Gemini 3.7 Flash at medium $0.031 over 4 calls and 28 s.
  Reasoning is the output: 5,263 of the round's 5,573 tokens. Ten attempts on
  one template cost $0.47 to $0.55 over 36 to 49 calls, $0.095 per landed
  problem.
- Mutants: 53 and 22 on the first two canonicals, 46 and 17 killed by the
  statement's own cases. Round one killed nothing on either; the survivors were
  equivalent by inspection. `ROUNDS` stays at two. Later landings killed 4 of 4,
  7 of 7 and 11 of 13, the round proposing nothing.
- The runner spent 76.3 s on 22 mutants, 70 s of it seven timeout kills at the
  generation cap. Process start is not the cost, so no fork server.
- Ten attempts on `answer-space`: 5 landed, 4 rejected as `misdeclared`, 1 held.
  Two rejections checked by hand had the canonical right and the declared value
  wrong, so the gate became a count. Re-run: 8 landed, 1 `untested` on an
  argument order the prose left open, 1 held on `input_too_large`.
- Separating sizes: the first two searches gave `input_too_large`, the blind
  reference having written the form, which is why the clock is its own site.
  Five then separated at 1, 2, 6, 13 and 21 against a legal 100000, the clock
  briefed too slow. Fifteen over the corpus: eight at one or two where the
  clock scans the values, six at 13 to 27 where it is exponential, four over
  the ceiling. The builder's bound is not a denominator.
- Of ten statements on one template, 1 reused a domain the cue names and 2
  asked a question a listed statement already asked, both with the twin in the
  list. Held drafts are not listed.
- 28 canonicals read at two cents, none undecided. Every problem derives
  `binary-search`; 12 that alone, 7 one code more, 5 two more.
- `generate --gaps --count 1` aimed at 35 of 37 core templates. Seven reached
  before a stop by hand: 4 landed, 2 held on `input_too_large`, 1 cut.
  `--count` is per template.

## Phase 7 — The corpus, measured (current)

What a generated corpus is worth, measured rather than asserted.

- The hand pass, which writes the matcher's reference and is the only reading
  of a generated problem no model produced.
- Annotation over pairs of a template and a solution, from the templates alone.
- The matcher scored per pair and grouped per template, positive verdicts in
  both directions.
- The announcement floor: one matcher over both corpora, the archive in
  `data/old/` and the generated one.
- A reader for `data/old/`, serving the floor measurement alone.
- How many generated statements are retrieved public problems rather than
  written ones.
- A configuration pinned before any number is quoted.
- Exit: the matcher carries a per-template score in both directions, the floor
  is measured across both corpora, and every created problem has been promoted
  or retired.

## Phase 8 — The engine serves

The first attempts the engine produces itself. It serves a generated problem,
times the sitting, runs the submission against the problem's own cases, and
records the verdict. The interface ships in this phase rather than a later
one.

- `Attempt` gains the verification result.
- The loop can mark a problem defective in place of a self-label, and the board
  stops counting that problem's attempts in either direction.
- Claims and self-labels asked as Phase 2 asked them.
- Claim candidates come from the problem's derived techniques.
- Exit: daily practice runs here, on problems the engine wrote and judged.

## Phase 9 — The engine hosted

The same loop, for people who are not the author. The difference is what may
be trusted.

- Submitted code runs in a sandbox, as a second backend behind the boundary
  `run` already defines.
- Comparison against `expected` stays above that boundary.
- The practice log becomes per-user, and is the only store that does.
- One person's log is separable and deletable without touching another's.
- Accounts are bought rather than built.
- Access is by invitation.
- Exit: someone other than the author completes a sitting.

## Phase 10 — Ladder, recall and card runs

What a card needs once there are problems to fill it.

- The ladder resolved at import from the selector and the template matches, at
  least one rung per core template. An unfilled core template is a
  reported gap.
- Studying a card is an explicit act: the ladder is measured from it, and
  probes are assigned at it.
- A recall attempt is its own record, keyed to a card and a template. A hinted
  pass is not a pass.
- The trainer never prints a template: reproduced cold, run against the card's
  own tests.
- Status rather than verdicts — the inputs a graduation rule would read.
- Graduation names no threshold. The numbers do not exist yet.
- Exit: recall and the ladder run daily.

## Phase 11 — Technique mastery, scheduling, failure mode

Per-technique skill state updated from attempts and the diagnosis signal;
scheduling targets the diagnosed cause rather than per-problem intervals.

- Failure mode lands here, not beside attribution: only the mastery state
  separates rust from gap. `SPEED` needs settling first.
- Sessions land here too, as a derived view over the log grouped on read.
- Exit: the scheduler drives daily practice.

## Phase 12 — Alternative solutions

Every other way to solve a stored problem, enumerated over the corpus rather
than asked for by template. A call proposes the approaches, each becomes its
own canonical, and the problem's own cases judge them.

Exit: one rung covers a core template and an optional one, through two
canonicals of one problem.

## Phase 13 — Program-analysis-grounded diagnosis

Ground the classifier in evidence: AST-diff against canonical solutions,
execution-trace comparison, empirical complexity measurement. Deliverable:
measured accuracy delta against LLM-only diagnosis.

## Phase 14 — Retrieval

Similar problems, patterns, and technique briefs retrieved from the corpus and
the user's own attempts; weak-spot patterns surfaced.

## Phase 15 — MCP + autonomy

Corpus and tools exposed as an MCP server. A scheduled agent runs the practice
loop: it picks drills and adapts to history.

## Phase 16 — Multi-agent (conditional)

Only once a real pipeline needs it: diagnose → retrieve → brief → schedule.

## Phase 17 — Soundness-checked synthesis

An upgrade to Phase 6's generation rather than its first appearance. Formal
constraint specs, property-based test-case generation, adversarial validation.
