# TODO

The phases still open. A ticked item stays while its phase is open. When the
phase closes it is harvested into `docs/ROADMAP.md` and removed whole.

## Phase 7 — the corpus, measured (current)

The worth of a generated corpus, measured rather than asserted. Split from
Phase 6 on 2026-09-02: every item here needs a corpus to exist first.

### Finishing the sweep

Phase 6 closed with the gaps run stopped by hand: 31 of 37 core templates
carry no solution, and three drafts would resume.

- [x] Resume the held drafts and run `generate --gaps --count 1` to the end,
      then record what `gaps` reports. Two of the first seven targets held on
      `input_too_large`, so the count of held drafts after the sweep is the
      first number
- [x] Name the input generator shape behind each `input_too_large` the sweep
      leaves. Two causes are known: a list grown where runtime follows a value,
      and a separation the ceiling cannot hold. The draft's reason does not
      separate them
- [ ] Raise `CEILING` to 256 KiB, in `speedup.py` and the two docs that quote
      64 KiB. Two quadratic naive solutions cross the 2 s cap between the two
      sizes: dsu-core at 4467 with a 94 KB case, next-greater at some 13k
      elements
- [ ] Re-enter the search on resume where the ceiling moved, as a resume does
      where `speedup` moved. A constant moves neither a configuration nor a
      prompt hash, so the two drafts above would stay held after the raise
- [ ] Give `speedup` one meaning in `content.md`, and seed rotated-array and
      count-based-kth by it. The card reads the flag as faster than the naive
      solution, the search as separable under the ceiling, and a log factor is
      the first and never the second
- [ ] Ask the inputs site for the shape the naive solution is slowest on. Three
      holds are shape faults: kahn-indegree's graphs are all cyclic at size,
      kruskal-mst's are disconnected, worked-framing's random digits branch
      nowhere. The moved prompt hash makes `--resume` re-run the three
- [ ] Name the technique's other templates to the naive site beside the form
      to avoid. top-down-memo's naive solution wrote tabulation, the same
      complexity under another form
- [x] Print a gaps run's position over every target, `[k/35]`, and its size
      before the first call, where the counter reads `[1/1]` on each template
      today. A sweep's cost is otherwise readable only once the sweep has paid
      it
- [ ] List held drafts' statements to the generator beside the landed ones. Two
      of ten statements asked a question a listed one asked, and a draft held
      at `searched` is not listed at all

### Matching the generated corpus by hand

The hand pass does two jobs at once. It writes the matcher's reference, and it
is the only reading of a generated problem that no model produced. A generator
that wandered from its target shows up there whatever the matcher says.

- [ ] Match by hand a sample of what the sweep lands, across the core templates
      it reached. The aiming is done: `--gaps` names them
- [ ] Sample and match by hand through `algo-coach match --by-hand`, over pairs
      of a template and a solution. It already samples across templates, and
      only the subject of a pair moves
- [ ] Match the eval set by hand from the templates alone, with no matcher
      reading in view. A score over the pairs that drew the line is agreement
      with itself

### Scoring the matcher

Generation asserts a match and the matcher audits it, so an unmeasured matcher
audits at an unknown error rate. An unmeasured matcher blocks trusting the
audit, not generating.

- [ ] Score the matcher per pair, grouped per template, over the pairs both
      read. Not as a set: a match asserts a pair
- [ ] Report the positive verdicts in both directions. Accuracy would score a
      matcher that names nothing in the nineties
- [ ] Skip a pair the user settled on the run path, and read it in the eval.
      The skip's condition follows from the reading's record shape, which is
      deferred
- [ ] Lift the scorer out of `claims` rather than copying it. It already prints
      denominators and reports both directions, which is the shape a per-pair
      score needs
- [ ] Let the matcher read the pair generation asserted, and report the
      disagreements. Actionable once the matcher carries a score

### Exit
- [ ] The matcher carries a per-template score in both directions

## Phase 8 — the engine serves

The first attempts the engine produces itself, through the interface they are
produced in. The interface is part of the phase rather than a later skin: a
practice loop is used or it is not, and a command line is not where a sitting
happens.

- [ ] Serve every created problem and skip the retired ones. No gate stands
      between landing and serving until Phase 13
- [ ] Serve a generated problem, time the sitting, run the submission against
      the problem's own cases, and mint the attempt
- [ ] Store the verification result on `Attempt`. Additive, and meaningless
      before Phase 6
- [ ] Feed the claim classifier its candidates from the problem's derived
      techniques. No other source supplies candidates now that the tag
      mapping is gone
- [ ] Offer marking a problem defective in place of the self-label. A statement
      that asked the wrong thing would otherwise be recorded as the user's own
      gap
- [ ] Exclude a defective problem's attempts from the board, both directions.
      Dropping only the failures would raise a technique's solve rate because
      a problem was broken
- [ ] Ask for a claim and a self-label as Phase 2 asked them. The only change
      is who witnessed the sitting, not who writes

- [ ] Serve the statement, take a submission and show the per-case verdict in
      one view. A sitting is one screen or it is a workflow, and a workflow is
      not practised daily
- [ ] Time the sitting in the interface rather than asking for a number. The
      loop may record only the timing it witnessed
- [ ] Show the board and the day's due work as the entry point, so the loop
      starts from what to practise rather than from a problem id

### Exit
- [ ] Daily practice runs here, in the app, on problems the engine wrote and
      judged

## Phase 9 — the engine hosted

The same loop, for people who are not the author. The only change is the trust
the submitted code gets. The local backend is a subprocess per case, because
our own generated code on our own machine is not a threat model, and another
person's code is.

- [ ] Add a sandboxed backend behind `runner.run`. Same signature, same child
      protocol, JSON in and JSON out: a second backend rather than a second
      runner. That boundary was written for a second backend
- [ ] Keep the comparison against `expected` above the boundary, as it already
      is. A sandbox is never told what a case expects
- [ ] Cap wall clock, memory and output per run, and give the sandbox no
      network. A submission that spawns a process or opens a connection
      fails
- [ ] Key `AttemptLog` by user. The log is the only store that changes:
      problems, cases, solutions, matches and cards are shared product data
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
      measured from it. The run holds when it began and the probes assigned,
      and later probes append
- [ ] Add `RecallAttempt`, keyed to a card and a template rather than to an
      attempt, since there is no problem and no submission. The hints taken
      before a pass are part of the record
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
- [ ] Write the verdict as a `Diagnosis` carrying its provenance whole. It
      never supersedes a self-label, because the eval scores one against the
      other
- [ ] Score the diagnoser per mode rather than overall, against self-labels the
      loop produced. A router that only ever says `gap` would score well on a
      corpus of gaps

## Phase 12 — alternative solutions

Every other way to solve a stored problem, by the flow in `flows.md`,
"Enumerating a problem's other solutions". The schema and the match's subject
are in place already, and nothing before this phase writes a second canonical.

Enumeration buys a rung covering two forms at once, a scale case cross-checked
between two efficient solutions, and a problem's techniques widening past the
one form its target named.

- [ ] Write the enumeration call: a landed problem in, the approaches that
      solve it out, each a name and a one-line idea. No code in that reply, so
      one bad proposal costs one call rather than the batch
- [ ] Generate a canonical per approach, one call each, and store the ones the
      problem's cases keep. A failure rejects nothing, since the cases judge a
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

- [ ] Re-claim thirty attempts with the earlier machine claims hidden, for the
      user's own ceiling. Triggered when mastery estimation reads claims,
      and a wrong one starts spending practice time
- [ ] Read the architecture doc against the code, landing every divergence
      here. The goal is not that none exists, since the doc is target state.
      The goal is that none is unknown
- [ ] Classify freely over the whole vocabulary and intersect in code, once the
      user claims can score it against the constrained one. A verdict outside
      the problem's own techniques is the only signal that they are the gap
- [ ] Point the matcher at an attempt as well as a canonical, and keep the
      records apart as the technique readers do. Triggered when a rung or a
      recall probe needs to know which form the user's own solution used
- [ ] Write the generation call for a technique target: a technique and its
      criteria in, a problem out, carrying `target_technique`. A paradigm and a
      problem class have no template, so nothing else reaches them. Triggered
      when a technique with no card needs problems
- [ ] Choose what a classifier reading of a solution stores, a verdict per
      candidate template or one record naming the templates it found, and
      write the choice into `content.md`. Scoping through the problem's
      techniques bounds the pairs today. Triggered when a canonical displays a
      form outside them, which enumeration produces
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
- [ ] Choose how a case with several correct returns is decided, by a
      normaliser over the returned value or by a checker per problem, and write
      the choice into `corpus.md`. Triggered when a core template can only be
      exercised by a problem whose answer is not unique
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
