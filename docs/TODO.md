# TODO

The phases still open. A ticked item stays while its phase is open. When the
phase closes it is harvested into `docs/ROADMAP.md` and removed whole.

## Phase 6 — problem generation (current)

Re-cut 2026-09-02: what makes a problem **sound** stays here; what a corpus is
worth measured against another one moved to Phase 7.

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
- [x] Add `runner` to `Verification`, one opaque string naming the backend and
      the interpreter. Required, since no verification has been written yet and
      one stored without it carries nothing for good
- [x] Several solutions per problem, appended. A rung covers a core
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

- [x] Add `run(code, args, *, cap_ms, stop_early=False)`, the one call the
      executor sits behind. JSON in and JSON out, with no path and no callable
      in the signature, so a remote sandbox takes the same payload
- [x] Stop on the first crash or timeout under `stop_early`, and never on a
      wrong answer. The backend is not told what a case expects, so the
      mutation loop can use it and the attempt path cannot
- [x] Take the whole case set in one `run` call rather than one case per call.
      A per-case boundary is one network round trip per case once the executor
      is remote
- [x] Write the child as a standalone script, reading `{code, args, cap_ms}`
      and writing `{outcome, value, elapsed_ms}`. The container backend runs
      that same script, so the protocol is written once
- [x] Add `outputs` over `run`, returning a value or an outcome per case.
      Generation compares two solutions before any `expected` exists, so it
      returns values rather than verdicts
- [x] Add `verify` over `outputs`, comparing against each case's `expected` and
      returning a `CaseResult` per case. Comparison stays above the boundary,
      so a sandbox is never told what `expected` is
- [x] Fail every case as `CRASHED` where the code does not parse or defines no
      module-level `solve`, read from the syntax tree. Phase 8 reads this path
      for an attempt, so it needs a verdict rather than an error
- [x] Execute one case per subprocess, under a wall-clock cap measured in the
      child around `solve`. Module-level state must not carry from one case to
      the next
- [x] Start the child in its own session and kill the group on a timeout. A
      solution that spawned a child of its own would otherwise leave it running
- [x] Set the parent's timer to the cap plus start-up, and read a child that
      reported nothing from how it died: the timer as `TIMEOUT`, a signal as
      `CRASHED`, anything else raised as the runner's own fault
- [x] Write the child's result on a path passed in argv, and discard its
      stdout. A solution that prints would otherwise corrupt the channel
- [x] Return the child's own elapsed time per case. Process start is tens of
      milliseconds, and would swamp the separating input the speedup search
      looks for
- [x] Raise on a runner fault rather than recording `CRASHED`. A subprocess
      that fails to start says nothing about the solution
- [x] Decide every case rather than stopping at the first failure. The
      canonical stores a count, and a count needs every case decided
- [x] Report where the canonical disagrees with the `expected` the generation
      call declared. `DraftCase.expected` is read nowhere today, and a call
      whose code and cases disagree wrote one of the two wrong
- [x] Run both solutions before anything lands, and discard the problem whole
      where the canonical yielded no value, contradicted the `expected` its own
      call declared, or disagreed with the reference. The calls are recorded
      either way, so what was paid for and thrown away stays readable
- [x] Take the canonical's answer where the reference yielded none, with
      `expected_from` naming it. That is the ordinary path beyond the
      reference's reach, not a failure
- [x] Write the problem, its cases, both solutions and the asserted match in
      one act. A half-written problem is one the matcher would read as
      finished

### What a match is keyed to

A form is displayed by code, so the subject of a verdict is a solution. The
corpus carries one canonical per problem until enumeration lands, which is
Phase 12.

- [x] Re-key `TemplateMatch` from a problem to a solution. A form is displayed
      by code, so a verdict naming only a problem names no subject. The store
      holds no match, so this is a rename rather than a migration
- [x] Assert a `generator` match on the canonical the problem was generated
      with, and on no other. It is the only one a brief named a form for, so
      every template the rest display is the matcher's answer

### What the corpus derives

Views over what generation, the runner and the readings stored, derived on read
rather than written down. A problem's techniques come from readings of its
canonicals, and the gaps come from the template matches. The first generation
run is aimed by hand at the core templates, since an empty corpus reports no
gap. Every later run is aimed at the templates the gap report lists.

- [x] Add `TechniqueReading`, keyed to a solution: the codes it used, its
      provenance, and staleness by digest, as a classifier claim carries. Its
      own class, since a claim is the user's private testimony where this is
      product data. The derivation has no input until one exists
- [x] Add an append-only store for readings, as the matches have. A record
      with nowhere to land leaves the reading run with nothing to append to
- [x] Read a canonical and an attempt through one classifier, writing the two
      records apart. Two prompts asking one question would drift, and neither
      score would compare
- [x] Give the canonical reading the whole vocabulary as candidates, where an
      attempt gets the problem's own techniques. Those are derived from the
      canonicals, so constraining the reading by them is circular
- [x] Read every canonical for its techniques, skipping the ones already read
      at the current digest. Every criterion reaches every reading, so a
      criteria edit re-reads the whole corpus
- [x] Derive a problem's techniques as the union over the standing readings of
      its canonicals, excluding the reference. A view, so a canonical added
      later widens them, and counting the reference would credit the naive
      approach the form replaces
- [x] Report a core template no solution displays. The card claims to teach
      that form, so a corpus that cannot exercise it is a fact about the store
- [x] Aim a generation run at the templates carrying no match. Otherwise the
      selector fills the ladder and the missing form is never written

### The discrimination bar

Cases that separate nothing license `verified` on a canonical that is wrong.
The bar is named in `flows.md`: a blind reference, then mutants of the
canonical. What the first corpus settles is the bound.

- [x] Enumerate mutants from the canonical's syntax tree, one change per
      mutant. Mechanical, so nothing is stored and the set re-derives when the
      operators change
- [x] Kill a mutant on a wrong answer, a crash or a timeout, and report which
      ones survived. A survivor names the case that has to exist
- [x] Ask for the cases that kill the survivors, arguments only. The reference
      computes what they return, so no model writes an expected output
- [x] Choose the bound the mutation loop stops at, and write the number into
      `corpus.md`. Equivalent mutants make a full score unreachable
- [x] Search for the smallest input separating the reference from the canonical
      under the cap, doubling then halving. Only where the template claims a
      speedup
- [x] Write the generation call for an input generator: the statement in, code
      building an input of a given size out. The speedup search has no input to
      run without one
- [x] Store the separating case beside the others, so a submission is judged
      at that size. The search finds one and nothing writes it down
- [x] Run the mutation loop in the landing path, between `check` and `land`,
      and append the cases it wins to the set the problem carries. Nothing
      calls `mutation` today, so no landed problem is measured against the
      bound

### One configuration per call site

- [x] Add `Bench`: one `Configuration` per generation call site — generator,
      blind, discrimination, inputs — defaulting to the one all four share
      today. A run then names four configurations rather than one
- [x] Read one `Configuration` in the classifier and the matcher, which each
      define their own copy of the four fields `calls` now owns. Three copies
      drift, and a score compares what two of them named
- [x] Take a per-site bench override on `algo-coach generate`, so a cheaper
      model is tried without an edit
- [x] Pin `temperature: 0` on blind, discrimination and inputs, leaving the
      generator sampled. The endpoints the bench is pinned to advertise a
      temperature beside an effort, so greedy costs it no reasoning
- [x] Write the per-site configuration into `machine.md`. A record copies its
      own call's, so four models in one run stay readable

### What an eval reads back

- [x] Add an outcome record per call site and item, carrying the gate verdicts,
      the configuration and the digest of what was sent. A printed line is lost
      when the run ends
- [x] Skip an item a configuration has already read at the current digest, as
      the classifier skips a claim. A second configuration is then paid for
      only where it has not read

### What a case carries

- [x] Add provenance to `TestCase`, naming the call that proposed its
      arguments. A case won by a round was written by a different call from the
      problem's, and `mint.case` still says otherwise
- [x] Add the round that won a case, zero for the set written with the
      statement. Replaying `discrimination` needs the set as it stood: it
      decides the survivors and it is in the prompt
- [x] State in `corpus.md` that a won case carries its own provenance, beside
      the rule that the first set is written with the problem

### Killing without a call

- [x] Run the input builder for every problem rather than only where the
      template claims a speedup. The fuzz pass has no inputs without one
- [x] Cap a mutant's run against what the canonical took, rather than at the
      generation cap. Seven mutants killed by timeout spent 70 of one run's 76
      seconds in the runner
- [x] Kill mutants with built inputs across sizes and seeds before any round,
      keeping the first input that kills each. No call is paid for, and only
      the deep survivors reach one
- [x] Shrink a killing input by delta debugging before it is stored. A random
      input that kills is large, and the ceiling and every later verification
      pay for it
- [x] Record which source killed each mutant: the set written with the
      statement, the fuzz pass, or round n. That is what says whether a round
      earns its call
- [x] Record per proposed case which mutants it killed, and land only the ones
      that killed. The first run stored fifteen that killed nothing, and every
      verification runs them forever

### Enforcing a claimed speedup

- [x] Separate the search's two empty answers: the reference finished at the
      largest legal input, against the built input crossing the ceiling.
      `input_too_large` hid which happened on the first run
- [x] Decide what enforces a speedup where the blind reference writes the same
      form — a third solution written deliberately naive, or `speedup` claiming
      less — and write the choice into `corpus.md`
- [x] Move the search ahead of the mutation loop, appending its case after it.
      A disagreement at the separating size then costs no round
- [x] Hold a draft at `searched` where its template claims a speedup and the
      search stored no case, so nothing lands undemonstrated. A test lands a
      separated problem and holds an unseparated one
- [x] Add a `Discard` arm for a reference that wrote the form, and reject a
      held draft with it. The four existing arms all say the statement, the
      canonical or the cases were wrong, and this one says none of them was
- [x] Add the template's `speedup` flag to what `moved_at` reads, so correcting
      it resumes the drafts the search held. A flag edit moves neither a
      configuration nor a digest
- [x] Report the held drafts at the end of a run, naming the template and what
      the search found. They are the gap the next generation run aims at
- [x] Count the draft a raised call left in that report. It is stored at the
      step it stopped and a resume reaches it, where the run prints only that
      the call failed

### The naive solution

The blind reference holds two jobs that pull apart: an independent reading of
the statement, and the clock a speedup is measured against. Two blind
configurations wrote the canonical's own form on two drafts, so the second job
moves to a site of its own. What that site may do, and what it may never do,
is in `corpus.md`.

- [x] Write the split into `corpus.md`: the reference is the independent
      reading alone, and a third solution written deliberately naive is what a
      timing bar measures against. One sentence there gives the reference both
      jobs, and every item below cites it
- [x] Add a `naive` arm to `SolutionRole`, and a test that such a solution
      reaches neither the technique reader nor the matcher. Both select
      `CANONICAL` today, so the exclusion holds and nothing pins it
- [x] Add `paced` to `WritingState`, between `built` and `searched`, and the
      naive code and its configuration to `Draft`. A resume holding neither
      would re-pay the call that wrote the clock
- [x] Add `CallSite.CLOCK` and the fifth `Bench` field, named as `Draft.clock`
      already is. A configuration is per call site, and the test pinning the
      two lists together is what fails until both move
- [x] Write the naive prompt: the statement and the template's trigger in, a
      solution out. It may name the form to avoid, since it settles no case and
      discards no problem
- [x] Sample the naive site, where the other three answering sites are greedy.
      It produces an artifact rather than a verdict, so variance costs no
      comparability — the rule `machine.md` states for the generator
- [x] Write the naive solution after the builder and before the search, and
      only where the template claims a speedup. The builder is written for
      every problem, since the fuzz pass builds its inputs with it
- [x] Verify the naive solution against the problem's cases, storing nothing
      and holding the draft where it fails. A wrong clock measures nothing, and
      being wrong says nothing about the statement
- [ ] Measure the search against the naive solution rather than the reference,
      and rename `Missing.REFERENCE_FINISHED` to `NAIVE_FINISHED`. A stored
      `unseparated` is free text, so no record carries the arm being renamed
- [ ] Settle the separating case from the reference, as every other case is
      settled. A naive solution is slow at every size, so the separating input
      is small enough for the reference to answer it
- [ ] Store the naive solution at landing, as the reference is stored. A replay
      and a resume both re-run the search, and neither should re-pay the call
      that wrote the clock
- [ ] Ask the naive site on a replay, where a speedup is claimed, as the inputs
      site is asked. What a replay compares is whether a configuration writes
      the dumber solution
- [ ] Add the naive step to `ANSWERED` in `resuming.py`, so a moved naive
      configuration re-pays that call alone. A test pins that the reference and
      the builder are reused
- [ ] Re-ask the naive site on a resume where the search separated nothing,
      though its configuration and digest stand. It is sampled, so a second
      call is a second draw rather than the answer already stored
- [ ] Run `generate --count 5` on `answer-space` and record the separating size
      each landed problem carries. That number is what says the site works

### Writing a problem as states

A draft is stored as it is written, so a step that fails leaves it where it
stopped. Repair is then resumption. Phase 6 exits without these: none of its
exit criteria reads a draft.

- [x] Write the states, what a draft holds and what a resume may not do into
      `flows.md`
- [x] Add `WritingState` — drafted, checked, referenced, agreed, built,
      searched, hardened, landed, rejected — and tie `rejected` to the gate
      that reached it, as `Problem` ties a retirement to its reason
- [x] Add `Draft`, holding each step's output and the provenance of the call
      behind it
- [x] Add to `Draft` the draft it was re-run from, absent on a first attempt.
      A rejected draft is not resumed, so re-running its failing step is a new
      draft
- [x] Add the draft store under `data/`, revised in place where every other
      store appends. `README.md` already names its write semantics
- [x] Mint the draft where `writing_id` is minted today, so the four site
      outcomes and the draft carry one id
- [x] Write the draft after each step and move its state, replacing the tuple
      `write_one` returns. A test reads the state left by a run stopped at each
      step
- [x] Clear the draft at landing, naming the problem it became. A crash between
      the two then leaves a draft the next run clears rather than one it writes
      a second time
- [x] Find the first step of a draft whose configuration or digest moved. That
      is where a resume starts, and a test pins that an unchanged bench finds
      none
- [x] Add `template_id` to `Draft`, optional as on `SiteOutcome`, since a
      technique brief names no form. `moved_at` reads the template's `speedup`,
      and a sweep over held drafts has only the site outcomes to find it from
- [x] Resume a draft from that step, reporting which step it started at
- [x] Refuse to resume a rejected draft. Rejected is terminal: the generator's
      gates leave nothing to ask again but a call that writes a different
      problem, and a disagreement is evidence about the statement
- [x] Add `--resume` to `generate`, carrying every held draft forward and
      reporting the step each started at. Nothing calls the library's resume,
      so a prompt edit cannot be spent on the drafts it repairs
- [x] List the stored drafts under a flag of `generate`, naming the state, the
      gate and the step each would start at. A sweep names what it will spend
      before it spends it
- [x] Skip a step a resume re-runs whose own configuration and digest stand, as
      a replay skips a pair. A moved blind configuration re-pays the input
      generator today, and that prompt is the statement alone
- [x] Draw the states into `flows.md` as a mermaid diagram: each step, the
      state it moves the draft to, and the three ways one leaves — landed,
      rejected, or held for a resume. Prose names an exit per step, and which
      failure stops where is read by following eight bullets

### Reading what a run left

- [x] Add the stores generation writes to `scripts/views.py`: site outcomes,
      test cases, solutions, verifications, readings, and the problems, cards
      and drafts directories. Seven of the fourteen stores are queryable, and
      every question about a run joins across the ones that are not
- [x] Render one draft under `generate --draft <id>`: its state, the statement,
      both solutions, the settled cases, and the site outcomes of its writing
      id. On `generate` rather than a `view` command, since the draft store is
      generation's own working state and `--drafts` already reads it

### Transport

- [x] Retry once on a 404 whose message names no endpoints for the model. It is
      router state rather than a bad request, and a wrong model id then costs
      one extra request before it fails

### The first run

Nothing on this path has run against a model: every gate above is unit-tested
against a fake. Each item is one run and the number it writes down, and the
numbers go in the commit unless the item names a file.

- [x] Run `generate --card binary-search --template predicate-first-true
      --count 1` and read what it stored: the problem, its cases, both
      solutions and the generator match
- [x] Record what one problem costs, from the call log: tokens and wall clock
      per call. How large a corpus is affordable follows from that number
- [x] Record how many mutants a real canonical yields and how many each round
      kills. Revise `ROUNDS` in `corpus.md` where the second round kills
      nothing
- [x] Record what the mutation loop spends in the runner. A per-case
      subprocess is what the deferred fork server replaces, and nothing has
      measured it
- [ ] Run `generate --count 10` on one template and record the discard rate
      per gate: no_value, misdeclared, untested, disagreed. A gate rejecting
      most problems is a defect in the prompt rather than a bar
- [ ] Count how many of those ten held at `searched`, and which `unseparated`
      reason each gave. Counting `reference_finished` alone reads zero, since
      the case ceiling reports `input_too_large` before the reference is judged
- [ ] Count how many of those ten reuse a domain their template's cue names.
      The exclusion is prompted and nothing enforces it
- [ ] Count how many of those ten ask the same question in a new setting. The
      list of what a form already carries is what prevents that
- [x] Run `generate` on a template claiming a speedup and record the
      separating size, or which `unseparated` reason came back
- [ ] Run `read` over the stored canonicals and record the techniques each
      problem derives. Nothing has read a generated solution
- [ ] Run `gaps`, then `generate --gaps --count 1`, and record which templates
      the run was aimed at

### Exit
- [ ] A run has stored problems, each carrying techniques derived from its
      canonicals and a case set measured against the mutation bound, and the
      gap report names the templates the next run is aimed at
- [ ] What one problem costs and what each mutation round kills are recorded.
      Nothing re-derives them once the corpus has grown past that run

## Phase 7 — the corpus, measured

What a generated corpus is worth, measured rather than asserted. Split from
Phase 6 on 2026-09-02: every item here needs a corpus to exist first.

### Annotating the generated corpus

The hand pass does two jobs at once. It writes the matcher's reference, and it
is the only reading of a generated problem that no model produced. A generator
that wandered from its brief shows up there whatever the matcher says.

- [ ] Aim the first run at the core templates, 37 of the 45 across nine
      cards, and annotate a sample of what lands
- [ ] Sample and annotate through `algo-coach annotate`, over pairs of a
      template and a solution. It already samples across templates, and only
      the subject of a pair moves
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
      What a skip needs settled follows from the reading's record shape, which
      is deferred
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
- [ ] The matcher carries a per-template score in both directions, the floor
      is measured across both corpora, and every created problem has been
      promoted or retired

## Phase 8 — the engine serves

The first attempts the engine produces itself, through the interface they are
produced in. The interface is part of the phase rather than a later skin: a
practice loop is used or it is not, and a command line is not where a sitting
happens.

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

- [ ] Serve the statement, take a submission and show the per-case verdict in
      one view. A sitting is one screen or it is a workflow, and a workflow is
      not practised daily
- [ ] Time the sitting in the interface rather than asking for a number. What
      the loop witnessed is the only timing it may record
- [ ] Show the board and the day's due work as the entry point, so the loop
      starts from what to practise rather than from a problem id

### Exit
- [ ] Daily practice runs here, in the app, on problems the engine wrote and
      judged

## Phase 9 — the engine hosted

The same loop, for people who are not the author. What changes is entirely
what may be trusted: the local backend is a subprocess per case because our
own generated code on our own machine is not a threat model, and another
person's is.

- [ ] Add a sandboxed backend behind `runner.run`. Same signature, same child
      protocol, JSON in and JSON out — a second backend rather than a second
      runner, which is what that boundary was written for
- [ ] Keep the comparison against `expected` above the boundary, as it already
      is. A sandbox is never told what a case expects
- [ ] Cap wall clock, memory and output per run, and give the sandbox no
      network. A submission that spawns a process or opens a connection
      fails
- [ ] Key `AttemptLog` by user. It is the only store that changes: problems,
      cases, solutions, matches and cards are shared product data
- [ ] Make one user's log readable and deletable without touching another's.
      The author's own log is the dogfooding evidence and the measurement
      substrate, and must not mix with a user's
- [ ] Buy the account system rather than building one. No credential handling
      of our own
- [ ] Gate access on an invitation. Untrusted execution behind open
      registration is an abuse surface with no upside at this size
- [ ] Deploy it, and write down what the deployment holds and for how long.
      A user cannot check a retention claim that was never written down

### Exit
- [ ] Someone other than the author completes a sitting

## Phase 10 — ladder, recall and card runs

- [ ] Resolve the ladder from the matches, the selector filling out to `size`.
      A retired problem fills no rung
- [ ] Derive requiredness from what a rung covers: core means required, the
      optional template alone means optional, both means required with the
      optional template offered as the alternative
- [ ] Re-derive the ladder whenever the corpus moves under it, a started card
      included. Progress is a fold over attempts, so nothing is lost
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

## Phase 11 — mastery, scheduling, failure mode
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

## Phase 12 — alternative solutions

Every other way to solve a stored problem, by the flow in `flows.md`,
"Enumerating a problem's other solutions". The schema and the match's subject
are in place already; nothing before this phase writes a second canonical.

What it buys is a rung covering two forms at once, a scale case cross-checked
between two efficient solutions, and a problem's techniques widening past the
one form its brief named.

- [ ] Write the enumeration call: a landed problem in, the approaches that
      solve it out, each a name and a one-line idea. No code in that reply, so
      one bad proposal costs one call rather than the batch
- [ ] Generate a canonical per approach, one call each, and store the ones the
      problem's cases keep. A failure discards nothing, since the cases judge a
      solution rather than the statement
- [ ] Add `algo-coach enumerate`, a problem in and canonicals out, through the
      transport the other commands share
- [ ] Decide what two canonicals of one form cost, once a corpus shows how
      often enumeration proposes them. Execution cannot separate them: top-down
      and bottom-up dynamic programming pass the same cases
- [ ] Re-run the mutation loop over a canonical enumeration added, or record
      that a later canonical carries less assurance. The case set was built to
      kill mutants of the first

## Deferred

An unstructured backlog, outside the phase order and last because nothing
sequences it. Known gaps with a trigger rather than a date: each names what has
to happen before the item is worth doing, and it is picked up when that fires,
whatever phase is current.

- [ ] Re-annotate thirty attempts with the earlier readings hidden, for the
      annotator's own ceiling. Triggered when mastery estimation reads claims,
      and a wrong one starts spending practice time
- [ ] Read the architecture doc against the code, landing every divergence
      here. The goal is not that none exists, since the doc is target state.
      The goal is that none is unknown
- [ ] Classify freely over the whole vocabulary and intersect in code, once the
      hand claims can score it against the constrained one. A verdict outside
      the problem's own techniques is the only signal that they are the gap
- [ ] Point the matcher at an attempt as well as a canonical, and keep the
      records apart as the technique readers do. Triggered when a rung or a
      recall probe needs to know which form the user's own solution used
- [ ] Write the generation call for a technique brief: a technique and its
      criteria in, a problem out, carrying no `generated_for`. A paradigm and a
      problem class have no template, so nothing else reaches them. Triggered
      when a technique with no card needs problems
- [ ] Choose what a classifier reading of a solution stores — a verdict per
      candidate template, or one record naming the templates it found — and
      write the choice into `content.md`. Scoping through the problem's
      techniques bounds the pairs today. Triggered when a canonical displays a
      form outside them, which enumeration is what produces
- [ ] Decide whether a canonical that yields no value on a proposed case is a
      defect rather than an input the statement excludes, and write the choice
      into `flows.md`. Triggered when a run drops such cases often enough to
      show in its report
- [ ] Run each case in its own subinterpreter inside a pooled worker, where
      the children are started ahead of their cases today. A subinterpreter
      cannot be preempted, so a case over the cap costs its worker rather than
      a signal. Triggered when interpreter start is again what a run spends its
      seconds on
- [ ] Decide how long a rejected draft is kept, and write the choice into
      `flows.md`. Triggered when the draft store outgrows the corpus it
      produced
- [ ] Choose how a case with several correct returns is decided — a normaliser
      over the returned value, or a checker per problem — and write the choice
      into `corpus.md`. Triggered when a core template can only be exercised
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
