# TODO

The phases still open. A ticked item stays while its phase is open. When the
phase closes it is harvested into `docs/ROADMAP.md` and removed whole.

## Phase 6 — problem generation (current)

The engine writes problems: a statement, the test cases that decide it, a
canonical solution and a reference solution. Flow and its rules:
`docs/architecture/flows.md`, "Generating a problem".

Generation lands before the matcher is scored. The Phase 5 reset took every
template match with it, so no pair carries a hand reference, and none can
until the engine has written problems to annotate.

### The records

- [x] `generated_for` on `Problem`, naming the template it was written for. An
      assertion rather than a reading, which is what makes the first
      `TemplateMatch` provenance
- [x] `MachineProvenance` on `Problem`, required as it is on a match. A problem
      generated before the field exists carries none for good, and no
      configuration could then be compared over the corpus
- [x] `mint.generated_problem`, as `machine_match` mints a match. Minting in
      one place is what keeps a call site from filling provenance partly
- [x] `TestCase`, keyed to a problem, carrying arguments and an expected
      return. The first set is written in the same call as the statement, so
      the cases describe what the problem asks rather than what a solution did
- [x] `Problem.status` — created, active or retired — beside a
      `retired_reason` of `defective` or `telegraphed`. A validator ties them,
      since only the reason says whether the attempts count
- [x] `Solution`: the code, its provenance and a `role` of canonical or
      reference, and nothing about how it ran. Both roles pass the same cases,
      so nothing about the code says which one a solution is
- [x] `Verification`: one run of a solution, carrying the cap and a result per
      case. Its own record, since the cap and the machine decide a timeout
      where the code does not. The run's own outcome folds from the cases
- [x] Add `elapsed_ms` to `CaseResult`, what the child measured around
      `solve`. The speedup search reads those numbers, and a result holding
      only the outcome makes every search re-run the whole set
- [ ] Add `runner` to `Verification`, one opaque string naming the backend and
      the interpreter. Required, since no verification has been written yet and
      one stored without it carries nothing for good
- [x] Several solutions per problem, appended. A rung covers a studied
      template and an optional one only where two approaches are stored
- [x] Append-only stores for cases, solutions and verifications. A case is
      added and never revised, and two runs of one solution are two records
- [x] Add `speedup` to `Template`, saying whether the form beats the naive
      solution. Without it a missing separating input reads as a defect on
      backtracking, whose form is its own optimum
- [x] Add a field to `TestCase` naming where its expected output came from.
      Beyond the reference's reach only the canonical can compute one, and two
      cases in a set are then not equally strong evidence
- [x] A `MatchSource.GENERATOR` arm, carrying no provenance as a hand match
      does not. The generator knew what it was told to write, where a matcher
      infers it
- [x] Resolve a pair by that order rather than latest-wins, as a claim resolves
      user-first. A matcher's later reading must not supersede the assertion it
      audits

### Generation

- [x] Run one generation call on one template, and read the reply out of the
      call log before writing any of the rest. One call yielded all three
      parts, and the statement was Daily Temperatures verbatim
- [x] Write the generation prompt: a template and its cue in, a statement, a
      canonical and the cases out. One call, or the cases describe the solution
      rather than the problem
- [x] Exclude from the statement the domains the template's cue and notes name.
      The probe was given a cue saying "temperatures" and returned the problem
      that cue was written from
- [x] Define one response schema over all three parts, so a reply missing any
      of them fails rather than landing a problem to repair later
- [x] Write the reference call: the statement alone in, a solution out. Neither
      the canonical nor the cases may reach it, or the two share one reading of
      the statement
- [x] Recompute every expected output from the reference, and discard the
      problem where it disagrees with the canonical. A case the canonical
      produced passes by construction
- [x] Sample the generation call rather than running it greedy, the exception
      the provenance rule names. One model's habits would otherwise become the
      whole corpus
- [x] Give generation its own configuration, as the matcher has its own.
      Generation asks for an artifact where a reading asks for a verdict
- [x] Pass the statements already written for a template into the generation
      call, and require the new one to differ. Ten runs otherwise produce ten
      variants of one problem, each passing every gate
- [x] Set `Problem.difficulty` at generation. A selector filters on it and
      nothing writes it, so a ladder's rungs are ordered by nothing
- [x] Add `algo-coach generate`, a template in and problems out, through the
      transport the classifier and the matcher already share
- [x] Print progress per problem, as the other run loops report it: the
      template, the case run's verdict, and whether it landed

### The runner

Executing a solution against a problem's cases. Two subjects today, a canonical
and a reference. Phase 8 puts an attempt on the same path.

It comes after generation because the convention is fixed by `TestCase` and the
output is then real. Landing closes here: nothing is stored until a canonical
has passed.

Thin on purpose, and behind one boundary. The local backend is a subprocess per
case, since our own generated code on our own machine is not a threat model. A
platform serves someone else's code, and that backend is a container. What a
stored result means is settled in `corpus.md`, so neither moves a record.

- [ ] Add `run(code, args, *, cap_ms, stop_early=False)`, the one call the
      executor sits behind. JSON in and JSON out, with no path and no callable
      in the signature, so a remote sandbox takes the same payload
- [ ] Stop on the first crash or timeout under `stop_early`, and never on a
      wrong answer. The backend is not told what a case expects, so the
      mutation loop can use it and the attempt path cannot
- [ ] Take the whole case set in one `run` call rather than one case per call.
      A per-case boundary is one network round trip per case once the executor
      is remote
- [ ] Write the child as a standalone script, reading `{code, args, cap_ms}`
      and writing `{outcome, value, elapsed_ms}`. The container backend runs
      that same script, so the protocol is written once
- [ ] Add `outputs` over `run`, returning a value or an outcome per case.
      Generation compares two solutions before any `expected` exists, so it
      returns values rather than verdicts
- [ ] Add `verify` over `outputs`, comparing against each case's `expected` and
      returning a `CaseResult` per case. Comparison stays above the boundary,
      so a sandbox is never told what `expected` is
- [ ] Fail every case as `CRASHED` where the code does not parse or defines no
      module-level `solve`, read from the syntax tree. Phase 8 reads this path
      for an attempt, so it needs a verdict rather than an error
- [ ] Execute one case per subprocess, under a wall-clock cap measured in the
      child around `solve`. Module-level state must not carry from one case to
      the next
- [ ] Start the child in its own session and kill the group on a timeout. A
      solution that spawned a child of its own would otherwise leave it running
- [ ] Set the parent's timer to the cap plus start-up, and read a child that
      reported nothing from how it died: the timer as `TIMEOUT`, a signal as
      `CRASHED`, anything else raised as the runner's own fault
- [ ] Write the child's result on a path passed in argv, and discard its
      stdout. A solution that prints would otherwise corrupt the channel
- [ ] Return the child's own elapsed time per case. Process start is tens of
      milliseconds, and would swamp the separating input the speedup search
      looks for
- [ ] Raise on a runner fault rather than recording `CRASHED`. A subprocess
      that fails to start says nothing about the solution
- [ ] Decide every case rather than stopping at the first failure. The
      canonical stores a count, and a count needs every case decided
- [ ] Report where the canonical disagrees with the `expected` the generation
      call declared. `DraftCase.expected` is read nowhere today, and a call
      whose code and cases disagree wrote one of the two wrong
- [ ] Run both solutions before anything lands, and discard the problem whole
      where the canonical yielded no value on some case or the two disagree.
      There is no `expected` yet, so yielding nothing is the only way the first
      canonical fails. The calls are recorded either way, so what was paid for
      and thrown away stays readable
- [ ] Take the canonical's answer where the reference yielded none, with
      `expected_from` naming it. That is the ordinary path beyond the
      reference's reach, not a failure
- [ ] Write the problem, its cases, both solutions and the asserted match in
      one act. A half-written problem is one the matcher would read as
      finished

### What the corpus derives

Folds over what generation and the runner stored. The first run is aimed by
hand at the studied templates. Every later one is aimed by the report.

- [ ] Derive a problem's techniques from its canonical solutions, excluding
      the reference. A view, so adding a canonical can widen them, and counting
      the reference would credit the naive approach the form replaces
- [ ] Report a studied template no problem matches. The card claims to teach
      that form, so a corpus that cannot exercise it is a fact about the store
- [ ] Aim a run at the templates carrying no match. A form the corpus cannot
      exercise names its own remedy

### The discrimination bar

Cases that separate nothing license `verified` on a canonical that is wrong.
The bar is named in `flows.md`: a blind reference, then mutants of the
canonical. What the first corpus settles is the operators and the bound.

- [ ] Enumerate mutants from the canonical's syntax tree, one change per
      mutant. Mechanical, so nothing is stored and the set re-derives when the
      operators change
- [ ] Kill a mutant on a wrong answer, a crash or a timeout, and report which
      ones survived. A survivor names the case that has to exist
- [ ] Ask for the cases that kill the survivors, arguments only. The reference
      computes what they return, so no model writes an expected output
- [ ] Choose the bound the mutation loop stops at, and write the number into
      `corpus.md`. Equivalent mutants make a full score unreachable
- [ ] Search for the smallest input separating the reference from the canonical
      under the cap, and store the case at it. Only where the template claims a
      speedup

### Annotating the generated corpus

The hand pass does two jobs at once. It writes the matcher's reference, and it
is the only reading of a generated problem that no model produced. A generator
that wandered from its brief shows up there whatever the matcher says.

- [ ] Aim the first run at the studied templates, 38 of the 45 across nine
      cards, and annotate a sample of what lands
- [ ] Annotate through `algo-coach annotate` unchanged. It already samples
      across templates, and the cards are seeded
- [ ] Annotate the eval set from the templates alone, with no matcher reading
      in view. A score over the pairs that drew the line is agreement with
      itself

### Scoring the matcher

Generation asserts a match and the matcher audits it, so an unmeasured matcher
audits at an unknown error rate. What that blocks is trusting the audit, not
generating.

- [ ] Score the matcher per pair, grouped per template, over the pairs both
      read. Not as a set: a match asserts a pair
- [ ] Report the positive verdicts in both directions. Accuracy would score a
      matcher that names nothing in the nineties
- [ ] Skip a pair the hand settled on the run path, and read it in the eval.
      The skip needs every template of the card settled, since the call asks
      about the card whole
- [ ] Lift the scorer out of `claims` rather than copying it. It already prints
      denominators and reports both directions, which is the shape a per-pair
      score needs
- [ ] Let the matcher read the pair generation asserted, and report the
      disagreements. Actionable once the matcher carries a score

### The announcement floor

The archive half can start as soon as the matcher runs, and needs no scored
matcher. The floor is one matcher over two corpora, so a systematic error
largely cancels in the comparison.

- [ ] Write the reader for `data/old/`, used by the floor measurement alone. It
      is a corpus rather than a store, so nothing on the run path may point at
      it
- [ ] Measure the announcement floor over the archived statements: how often
      the matcher names a form from the statement alone
- [ ] Promote a created problem to active, or retire it as telegraphed.
      `created` is not a resting state, so nothing may leave a problem sitting
      in it
- [ ] Read the generated corpus against that floor before growing it. A problem
      the matcher names instantly was telegraphed, and teaches recognition of
      nothing
- [ ] Measure how many generated statements are public problems the model
      retrieved rather than wrote, and record the share. Excluding the cue's
      domains renames a retrieval instead of preventing it

### Exit
- [ ] A card's reported gaps are filled by generated problems, and Phase 7
      resolves a ladder over them

## Phase 7 — ladder, recall and card runs

- [ ] Resolve the ladder from the matches, the selector filling out to `size`.
      A retired problem fills no rung
- [ ] Derive requiredness from what a rung covers: studied means required, the
      optional template alone means optional, both means required with the
      optional template offered as the alternative
- [ ] Re-derive the ladder whenever the corpus moves under it, a started card
      included. Progress is a fold over attempts, so nothing is lost
- [ ] Generate a canonical for a second template from the statement, judged by
      the cases the problem already carries. A passing one demonstrates the
      pair and writes a `generator` match, where the matcher only infers one
- [ ] Add `CardRun`, minted where a card is started, since the ladder is
      measured from it. Holds when it began and the probes assigned; later
      probes append
- [ ] Add `RecallAttempt`, keyed to a card and a template rather than to an
      attempt, since there is no problem and no submission. What was hinted
      before a pass is part of it
- [ ] Generate probes from the corpus, as a skill rather than code, since
      choosing one is judgment. An agent later, possibly
- [ ] Build the recall trainer: names hidden, the template typed into a blank
      file cold, run against the card's own tests, never printed
- [ ] Show card status: recalled when, ladder outstanding, probes available.
      The inputs a graduation rule reads, and no threshold

### Exit
- [ ] Recall and the ladder run daily

## Phase 8 — in-engine drill loop

The first attempts the engine produces itself.

- [ ] Serve active problems, and created ones while the floor has not run.
      Reading only active would serve nothing until the gate exists
- [ ] Serve a generated problem, time the sitting, run the submission against
      the problem's own cases, and mint the attempt
- [ ] Store the verification result on `Attempt`. Additive, and meaningless
      before Phase 6
- [ ] Feed the claim classifier its candidates from the problem's derived
      techniques. Nothing else supplies them now the tag mapping is gone
- [ ] Offer marking a problem defective in place of the self-label. A statement
      that asked the wrong thing would otherwise be recorded as the user's own
      gap
- [ ] Exclude a defective problem's attempts from the board, both directions.
      Dropping only the failures would raise a technique's solve rate because
      a problem was broken
- [ ] Ask for a claim and a self-label as Phase 2 asked them. What changes is
      who witnessed the sitting, not who writes

### Exit
- [ ] Daily practice runs here, on problems the engine wrote and judged

## Deferred

Known gaps with a trigger, not a date. Each names what has to happen first.

- [ ] Re-annotate thirty attempts with the earlier readings hidden, for the
      annotator's own ceiling. Triggered when mastery estimation reads claims,
      and a wrong one starts spending practice time
- [ ] Read the architecture doc against the code, landing every divergence
      here. The goal is not that none exists, since the doc is target state.
      The goal is that none is unknown
- [ ] Classify freely over the whole vocabulary and intersect in code, once the
      hand claims can score it against the constrained one. A verdict outside
      the problem's own techniques is the only signal that they are the gap
- [ ] Settle how a case forcing a timeout carries its input, and add the field
      it needs. Literal arguments put a megabyte of JSON in the store per case,
      where a seed and a size do not. Triggered when the first performance case
      is written
- [ ] Replace the per-case subprocess with a fork server, importing the
      solution once and forking per case. Triggered when a generation run
      spends minutes on process start, which mutation testing is what brings
      on
- [ ] Choose how a case with several correct returns is decided — a normaliser
      over the returned value, or a checker per problem — and write the choice
      into `corpus.md`. Triggered when a studied template can only be exercised
      by a problem whose answer is not unique
- [ ] Name on the verification the rule that decided a case, once that rule is
      no longer JSON equality. A verdict stored without it cannot be re-read
      after the rule moves. Triggered by the item above landing
- [ ] Add a container implementation of `run`: no network, read-only rootfs,
      memory and pids limits, non-root, and the cap enforced from outside as
      well as in the child. Triggered when the platform serves code someone
      else wrote
- [ ] Settle the full shape of a verification's environment, which the `runner`
      string stands in for. The machine decides a timeout as much as the cap
      does. Triggered when two runs under one backend disagree
- [ ] Fall back to another endpoint of the same shape on an outage, never to
      Anthropic direct, whose compatibility layer ignores `response_format`,
      `strict` and `reasoning_effort`. Triggered when an outage blocks a run

## Later phases

### Phase 9 — mastery, scheduling, failure mode
- [ ] Land rust against gap with the mastery model, or drop it. Only whether
      the technique was ever fluent separates them, and a single attempt does
      not carry that
- [ ] Settle what `SPEED` means before anything writes it. "Solved but too
      slowly" is about the user, a timeout is about the solution's complexity,
      and only the second is in the record
- [ ] Narrow the failure classifier to what the record supports: a mechanical
      slip against a conceptual miss. A four-way router would ask it for what
      it cannot see
- [ ] Write the verdict as a `Diagnosis` with model and prompt version. It
      never supersedes a self-label, because the eval scores one against the
      other
- [ ] Score the diagnoser per mode rather than overall, against self-labels the
      loop produced. A router that only ever says `gap` would score well on a
      corpus of gaps
