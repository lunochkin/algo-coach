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
- [ ] Aim a generation run at the templates carrying no match. Otherwise the
      selector fills the ladder and the missing form is never written

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

### Exit
- [ ] Every landed problem carries techniques derived from its canonicals and
      a case set measured against the mutation bound, and the gap report names
      the templates the next run is aimed at

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
