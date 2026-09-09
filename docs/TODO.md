# TODO

The phases still open. A ticked item stays while its phase is open. When a
phase closes, its items are harvested into `docs/ROADMAP.md` and removed whole.

## Phase 7 — finishing the sweep (current)

The corpus the drill loop needs, before the loop. Phase 6 closed with the gaps
run stopped by hand. At that point 31 of 37 core templates carried no
solution, and three drafts would resume.

- [x] Resume the held drafts and run `generate --gaps --count 1` to the end,
      then record what `gaps` reports. Two of the first seven targets held on
      `input_too_large`, so the count of held drafts after the sweep is the
      first number to record
- [x] Name the input generator shape behind each `input_too_large` the sweep
      leaves. Two causes are known: a list grown where runtime follows a value,
      and a separation the ceiling cannot hold. The draft's reason does not
      separate the two causes
- [x] Raise `CEILING` to 256 KiB, in `speedup.py`, in `README.md` and in
      `corpus.md`. Two quadratic naive solutions cross the 2 s cap between
      64 KiB and 256 KiB: dsu-core at 4467 elements with a 94 KB case, and
      next-greater at some 13k elements
- [x] Raise `CEILING` again, to 1 MiB. Two deque-window-max drafts proved a
      separation at 23k and 30k elements with a 393 KB case, and two
      kruskal-mst naive solutions ran 2.0 s and 2.2 s at the largest input
      256 KiB held
- [x] Re-enter the search on resume where the ceiling moved, as a resume does
      where `speedup` moved. A changed ceiling moves neither a configuration nor
      a prompt hash, so dsu-core and next-greater would stay held after the
      raise
- [x] Give `speedup` one meaning in `content.md`, then seed rotated-array and
      count-based-kth by that meaning. The card reads the flag as faster than
      the naive solution, and the search reads the flag as separable under the
      ceiling. A log-factor form is faster and is never separable
- [x] Ask the inputs site for the shape the naive solution is slowest on. Three
      holds are shape faults: kahn-indegree's graphs are all cyclic at size,
      kruskal-mst's are disconnected, and worked-framing's random digits give
      the recursion almost no branches. The moved prompt hash makes `--resume`
      re-run those three drafts
- [x] Show the naive site the technique's criterion beside the form to avoid.
      Three naive solutions reached the technique through a form no template
      names: tabulation where the form is a memo, a rolling pair where the form
      is a scan taken twice
- [x] Add `generate --reject <id>`, the by-hand exit `flows.md` names for a
      held draft no resume would separate. `drafting.reject` existed and no
      command called it, so the two single-query drafts could leave only by
      editing their files
- [x] Print a gaps run's position over every target, `[k/35]`, and the run's
      size before the first call. Today the counter reads `[1/1]` on each
      template, so a sweep's cost is readable only once the sweep has paid it
- [ ] List held drafts' statements to the generator beside the landed ones. Two
      of ten statements asked a question a listed statement asked, and a draft
      held at `searched` is not listed at all

### Exit
- [ ] Every held draft has landed or been rejected, and the sweep's numbers
      are in `docs/ROADMAP.md`

## Phase 8 — the engine serves

The first attempts the engine produces itself, through the interface a sitting
happens in. The interface ships in this phase. A practice loop that is not used
daily measures nothing, and a sitting does not happen at a command line.

- [ ] Serve every created problem and skip the retired ones. No gate stands
      between landing and serving until Phase 14
- [ ] Serve a generated problem, time the sitting, run the submission against
      the problem's own cases, and mint the attempt
- [ ] Store the verification result on `Attempt`. The field is additive, and
      every attempt written before the engine judged one leaves the field empty
- [ ] Feed the claim classifier its candidates from the problem's derived
      techniques. No other source supplies candidates now that the tag
      mapping is gone
- [ ] Offer marking a problem defective in place of the self-label. A statement
      that asked the wrong thing would otherwise be recorded as the user's own
      gap
- [ ] Exclude a defective problem's attempts from the board, solved and failed
      alike. Dropping only the failures would raise a technique's solve rate
      because a problem was broken
- [ ] Ask for a claim and a self-label as the Phase 2 loop asked for them. The
      engine now witnesses the sitting, and the user still writes both records

- [ ] Add a web layer as the second adapter beside the CLI, over the same
      domain calls. Phase 9 hosts the same pages for invited users, so a
      terminal interface here would be written twice
- [ ] Serve the statement, take a submission from an editor on the page, and
      show the per-case verdict in one view. A sitting split over several
      pages is a workflow, and a workflow is not practised daily
- [ ] Time the sitting in the interface. The loop records only the timing the
      loop witnessed, so the loop never asks the user for a duration
- [ ] Show the board and the day's due work as the entry point, so the loop
      starts from what to practise. A problem id as the entry point leaves the
      selection to the user

### Exit
- [ ] Daily practice runs here, in the app, on problems the engine wrote and
      judged

## Phase 9 — the engine hosted

The same loop, for people who are not the author. The only change is the trust
the submitted code gets. The local backend is a subprocess per case, because
our own generated code on our own machine is not a threat model, and another
person's code is.

- [ ] Add a sandboxed backend behind `runner.run`. The backend keeps the
      signature and the child protocol, JSON in and JSON out. The `run` boundary
      was written for a second backend, so no second runner is needed
- [ ] Keep the comparison against `expected` above the boundary, where the
      comparison already sits. A sandbox is never told what a case expects
- [ ] Cap wall clock, memory and output per run, and give the sandbox no
      network. A submission that spawns a process or opens a connection
      fails
- [ ] Key `AttemptLog` by user. The log is the only store that changes.
      Problems, cases, solutions, matches and cards are shared product data
- [ ] Make one user's log readable and deletable without touching another's.
      The author's own log is the evidence of daily use and the set every eval
      reads, and must not mix with another user's
- [ ] Buy the account system, so no credential handling is our own
- [ ] Gate access on an invitation. Untrusted execution behind open
      registration is an abuse surface with no upside at this size
- [ ] Deploy the engine, and write down what the deployment holds and for how
      long. A user cannot check a retention claim that was never written down

### Exit
- [ ] Someone other than the author completes a sitting

## Phase 10 — the matcher, measured

How much a generated corpus is worth, measured. Moved behind the beta on
2026-09-09: the drill loop needs problems and not a score, and the attempts
the loop produces rebuild the eval set the classifier is scored against.

### Matching the generated corpus by hand

The hand pass does two jobs at once. It writes the matcher's reference, and it
is the only reading of a generated problem that no model produced. A generator
that drifted from its target shows in the hand pass whatever the matcher says.

- [ ] Match by hand a sample of the problems the sweep landed, across the core
      templates the sweep reached. `--gaps` already names those templates, so
      no aiming is left
- [ ] Sample and match by hand through `algo-coach match --by-hand`, over pairs
      of a template and a solution. The command already samples across
      templates, and only the pair's subject changes, from a problem to a
      solution
- [ ] Match the eval set by hand from the templates alone, with no matcher
      reading in view. The first hand pass set the criterion, and a score over
      those same pairs measures the criterion against itself

### Scoring the matcher

Generation asserts a match and the matcher audits that match, so an unmeasured
matcher audits at an unknown error rate. An unmeasured matcher blocks trusting
the audit. Generation goes on without the score.

- [ ] Score the matcher per pair, grouped per template, over the pairs both the
      user and the matcher read. A match asserts one pair, so a score over a set
      would hide which template the matcher over-matches
- [ ] Report the positive verdicts in both directions: the templates the user
      named and the matcher missed, and the templates the matcher named and the
      user did not. Most pairs are negative, so accuracy would score a matcher
      that names nothing in the nineties
- [ ] Skip a pair the user settled on the run path, and read that pair in the
      eval. The skip's condition follows from the shape of the matcher's record,
      which `content.md` defers
- [ ] Lift the scorer out of `claims` for the matcher to share. The scorer
      already prints denominators and reports both directions, which is the
      shape a per-pair score needs
- [ ] Let the matcher read the pair the generator's match asserts, and report
      the disagreements. The disagreements mean something only once the matcher
      carries a score

### Exit
- [ ] The matcher carries a per-template score in both directions

## Phase 11 — ladder, recall and card runs

- [ ] Resolve the ladder from the matches, the selector filling out to `size`.
      A retired problem fills no rung
- [ ] Derive requiredness from the templates a rung covers. A rung covering a
      core template is required. A rung covering only the optional template is
      optional. A rung covering both is required, with the optional template
      offered as the alternative approach
- [ ] Re-derive the ladder whenever the corpus moves under the ladder, a
      started card included. Progress is a fold over attempts, so a solved rung
      stays solved
- [ ] Add `CardRun`, minted where a card is started, since the ladder is
      measured from that start. The run holds when the run began and the
      probes assigned, and later probes append
- [ ] Add `RecallAttempt`, keyed to a card and a template. A recall attempt has
      no problem and no submission, so no field keys the record to an attempt.
      The hints taken before a pass are part of the record
- [ ] Generate probes from the corpus, as a skill, since choosing a probe is
      judgment
- [ ] Build the recall trainer. The template's name is hidden, the user types
      the form into a blank file from memory, and the file runs against the
      card's own tests. The template is never printed, since reading the form
      is not recalling the form
- [ ] Show a card's status: when each template was last recalled, which rungs
      are outstanding, and which probes are available. Those are the inputs a
      graduation rule reads, and no threshold is set yet

### Exit
- [ ] Recall and the ladder run daily

## Phase 12 — mastery, scheduling, failure mode

- [ ] Land `rust` against `gap` with the mastery model, or drop the
      distinction. The two labels differ only in whether the technique was ever
      fluent, and a single attempt does not carry that history
- [ ] Settle what `speed` means before anything writes the label. "Solved but
      too slowly" is about the user, a timeout is about the solution's
      complexity, and only the timeout is in the record
- [ ] Narrow the diagnosis call, the model call that writes a `Diagnosis`, to
      what the record supports: a mechanical slip against a conceptual miss. A
      four-way verdict would ask the call for what the call cannot see
- [ ] Write the verdict as a `Diagnosis` carrying its provenance whole. A
      diagnosis never supersedes a self-label, because the eval scores the
      diagnosis against the self-label
- [ ] Score the diagnosis call per failure mode, with no overall share, against
      self-labels the loop produced. A call that only ever says `gap` would
      score well on a corpus of gaps

## Phase 13 — alternative solutions

Every other way to solve a stored problem, by the flow in `flows.md`,
"Enumerating a problem's other solutions". The schema and the match's subject
are in place already, and nothing before this phase writes a second canonical.

Enumeration buys a rung covering two forms at once, a scale case cross-checked
between two efficient solutions, and a problem's techniques widening past the
one form its target named.

- [ ] Write the enumeration call: a landed problem in, the approaches that
      solve the problem out, each a name and a one-line idea. The reply carries
      no code. A reply carrying code for every approach would fail whole on one
      bad entry, where a proposal costs one call
- [ ] Generate a canonical per approach, one call each, and store the canonicals
      the problem's cases pass. A failure rejects nothing. The cases judge the
      solution, and an enumerated canonical is no reading of the statement
- [ ] Add `algo-coach enumerate`, a problem in and canonicals out, through the
      transport the other commands share
- [ ] Decide what two canonicals of one form cost, once a corpus shows how
      often enumeration proposes two of one form. Execution cannot separate
      the two: top-down and bottom-up dynamic programming pass the same cases
- [ ] Re-run the mutation loop over a canonical enumeration added, or record
      that a later canonical carries less assurance. The case set was built to
      kill mutants of the first canonical, so a later canonical was never
      tested on its own failure modes

## Deferred

A backlog outside the phase order. Each item names a trigger: the event that
has to happen before the item is worth doing. An item is picked up when its
trigger fires, whatever phase is current.

- [ ] Re-claim thirty attempts with the earlier machine claims hidden, to
      measure the user's own consistency, which caps every classifier score.
      Triggered when mastery estimation reads claims, and a wrong claim starts
      spending practice time
- [ ] Read the architecture doc against the code, landing every divergence as
      an item in this file. The goal is not that no divergence exists, since
      the doc is target state. The goal is that no divergence is unknown
- [ ] Classify an attempt over the whole vocabulary and intersect with the
      problem's techniques in code, once the user claims can score that
      configuration against the one constrained to the problem's techniques. A
      verdict naming a technique outside the problem's own is the only signal
      that the problem's techniques are incomplete
- [ ] Point the matcher at an attempt as well as a canonical, and keep the
      records apart as attempt claims and solution claims are kept apart.
      Triggered when a rung or a recall probe needs to know which form the
      user's own solution used
- [ ] Write the generation call for a technique target: a technique and its
      criteria in, a problem out, carrying `target_technique`. A paradigm and a
      problem class have no template, so nothing else reaches those two kinds.
      Triggered when a technique with no card needs problems
- [ ] Choose what a matcher reading of a solution stores, a verdict per
      candidate template or one record naming the templates the matcher found,
      and write the choice into `content.md`. Scoping through the problem's
      techniques bounds the pairs today. Triggered when a canonical displays a
      form outside the problem's techniques, which enumeration produces
- [ ] Decide whether a canonical that yields no value on a proposed case is a
      defect rather than an input the statement excludes, and write the choice
      into `flows.md`. Triggered when a run drops such cases often enough to
      show in the run's report
- [ ] Run each case in its own subinterpreter inside a pooled worker, where
      the children are started ahead of their cases today. A subinterpreter
      cannot be preempted, so a case over the cap kills its worker instead of
      receiving a signal. Triggered when interpreter start is again the largest
      cost of a run
- [ ] Decide how long a rejected draft is kept, and write the choice into
      `flows.md`. Triggered when the draft store outgrows the corpus the drafts
      produced
- [ ] Choose how a case with several correct returns is decided, by a
      normaliser over the returned value or by a checker per problem, and write
      the choice into `corpus.md`. Triggered when a core template can only be
      exercised by a problem whose answer is not unique
- [ ] Name on the verification the rule that decided a case, once that rule is
      no longer JSON equality. A verdict stored without the rule cannot be
      re-read after the rule moves. Triggered by a second deciding rule landing
- [ ] Add a container backend behind `runner.run`, with no network, a read-only
      root filesystem, memory and pid limits, a non-root user, and the cap
      enforced from outside as well as in the child. Triggered when the
      platform serves code someone else wrote
- [ ] Settle the full shape of a verification's environment, which the `runner`
      string stands in for. The machine decides a timeout as much as the cap
      does. Triggered when two runs under one backend disagree
- [ ] Fall back to another endpoint of the same transport shape on an outage,
      never to Anthropic direct, whose compatibility layer ignores
      `response_format`, `strict` and `reasoning_effort`. Triggered when an
      outage blocks a run
- [ ] Add `repeats` to a case, and grow it in the search where the size walk
      ends at the ceiling with the naive solution still under the cap. The
      runner calls `solve` that many times, each call isolated from the last,
      and the cap covers the sum. A form whose one application is sublinear
      then separates on the statement it naturally has. Triggered when a ladder
      needs a rung for a form no input separates, which rotated-array and
      count-based-kth are the first two of
- [ ] Read the naive solution with the classifier, and hold the draft where the
      verdict names the card's technique. One call per naive solution, and it
      catches what the prompt misses rather than hoping. Triggered when a sweep
      still holds drafts whose naive solution reached the form
- [ ] Carry a tolerance on a case, and name on the verification that the
      tolerance decided it. A statement asks for exactly comparable values
      today, so a real-valued answer cannot be asked for at all. Triggered when
      a core template's answer is neither an integer nor a reduced fraction
