# TODO

The phases still open. A ticked item stays while its phase is open. When a
phase closes, its items are harvested into `docs/ROADMAP.md` and removed whole.
The work not yet ready for a phase waits under Further developments.

## Phase 11 — ladder, recall and card runs (current)

### The flows written first

- [x] Write starting a card run as a sequence in `flows.md`: the start, the
      probes assigned, and what the card shows once a run is open. A detail only
      use can answer is named as deferred
- [x] Write solving a rung as a sequence in `flows.md`: the ladder on a card,
      the rung picked, the sitting it opens, and where that sitting returns
- [ ] Write recalling a template as a sequence in `flows.md`: what names the
      template, the hints offered, the blank file and the card's own tests
- [ ] Draw a low-fidelity wireframe per step of those three flows into
      `docs/architecture/wireframes.md`. A sequence says what happens in what
      order, and a wireframe says what the user sees

### The records and the pages

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
- [ ] Go through a card run by hand: start a card, solve a rung of its ladder,
      recall a template cold against the card's tests, and see a probe
      offered

## Phase 12 — the matcher, measured

How much a generated corpus is worth, measured. Behind the beta: the drill loop
needs problems and not a score, and the attempts the loop produces rebuild the
eval set the classifier is scored against.

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

## Phase 13 — mastery and scheduling

- [ ] Write into `docs/architecture/` what a technique's mastery is derived
      from: the attempts, their claims and their verdicts. Mastery is never
      stored, so the derivation is the whole model
- [ ] Write into `flows.md` how the scheduler picks the next sitting from
      mastery, and what the board offers beside the pick. The user picks every
      technique and problem today
- [ ] Serve the scheduler's pick on the board, with every technique still on
      offer beside it
- [ ] Re-claim thirty attempts with the earlier machine claims hidden, to
      measure the user's own consistency, which caps every classifier score.
      Mastery reads claims, and a wrong claim spends practice time

### Exit
- [ ] Start a sitting from the scheduler's pick on the board, and complete it
      to the claim

## Further developments

Blocks of work not ready for a phase, grouped and unordered. A planned phase is
a block that became ready. A block, or a single item of one, is planned into a
phase once it is clear enough to plan. An item's trigger, where it names one, is
the event that makes the item ready.

### Failure mode

- [ ] Land `rust` against `gap` with the mastery model, or drop the
      distinction. The two labels differ only in whether the technique was ever
      fluent, and a single attempt does not carry that history
- [ ] Settle what `speed` means before anything writes the label. "Solved but
      too slowly" is about the user, a timeout is about the solution's
      complexity, and only the timeout is in the record
- [ ] Write the `SelfLabel` the loop asks for at the moment of solving, once
      `speed`, `rust` and `gap` are settled. A label cannot be given later, so
      one written under a meaning that later moved can never be corrected
- [ ] Offer only the failure modes an attempt's verification leaves open. A
      crash on every case and a timeout are in the record already, and a label
      contradicting the verdict would be a second answer to one question
- [ ] Narrow the diagnosis call, the model call that writes a `Diagnosis`, to
      what the record supports: a mechanical slip against a conceptual miss. A
      four-way verdict would ask the call for what the call cannot see
- [ ] Write the verdict as a `Diagnosis` carrying its provenance whole. A
      diagnosis never supersedes a self-label, because the eval scores the
      diagnosis against the self-label
- [ ] Score the diagnosis call per failure mode, with no overall share, against
      self-labels the loop produced. A call that only ever says `gap` would
      score well on a corpus of gaps

### Alternative solutions

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
- [ ] Choose what a matcher reading of a solution stores, a verdict per
      candidate template or one record naming the templates the matcher found,
      and write the choice into `content.md`. Scoping through the problem's
      techniques bounds the pairs until enumeration adds a canonical displaying
      a form outside them

### Classifier and matcher

- [ ] Classify an attempt over the whole vocabulary and intersect with the
      problem's techniques in code, once the user claims can score that
      configuration against the one constrained to the problem's techniques. A
      verdict naming a technique outside the problem's own is the only signal
      that the problem's techniques are incomplete
- [ ] Point the matcher at an attempt as well as a canonical, and keep the
      records apart as attempt claims and solution claims are kept apart.
      Triggered when a rung or a recall probe needs to know which form the
      user's own solution used

### Problem generation

- [ ] Write the generation call for a technique target: a technique and its
      criteria in, a problem out, carrying `target_technique`. A paradigm and a
      problem class have no template, so nothing else reaches those two kinds.
      Triggered when a technique with no card needs problems
- [ ] Decide whether a canonical that yields no value on a proposed case is a
      defect rather than an input the statement excludes, and write the choice
      into `flows.md`. Triggered when a run drops such cases often enough to
      show in the run's report
- [ ] Decide how long a rejected draft is kept, and write the choice into
      `flows.md`. Triggered when the draft store outgrows the corpus the drafts
      produced
- [ ] Read the naive solution with the classifier, and hold the draft where the
      verdict names the card's technique. One call per naive solution, and it
      catches what the prompt misses rather than hoping. Triggered when a sweep
      still holds drafts whose naive solution reached the form
- [ ] Write the inputs and naive site outcomes where a resume re-ran the search
      and re-asked neither site. A site that made no call writes no record, so
      the separating size and the count of a resumed landing are readable
      nowhere once the draft is cleared. Triggered when a report reads the
      separating size of a problem a resume landed

### Cases and verdicts

- [ ] Choose how a case with several correct returns is decided, by a
      normaliser over the returned value or by a checker per problem, and write
      the choice into `corpus.md`. Triggered when a core template can only be
      exercised by a problem whose answer is not unique
- [ ] Name on the verification the rule that decided a case, once that rule is
      no longer JSON equality. A verdict stored without the rule cannot be
      re-read after the rule moves. Triggered by a second deciding rule landing
- [ ] Carry a tolerance on a case, and name on the verification that the
      tolerance decided it. A statement asks for exactly comparable values
      today, so a real-valued answer cannot be asked for at all. Triggered when
      a core template's answer is neither an integer nor a reduced fraction
- [ ] Settle the full shape of a verification's environment, which the `runner`
      string stands in for. The machine decides a timeout as much as the cap
      does. Triggered when two runs under one backend disagree

### Transport

- [ ] Fall back to another endpoint of the same transport shape on an outage,
      never to Anthropic direct, whose compatibility layer ignores
      `response_format`, `strict` and `reasoning_effort`. Triggered when an
      outage blocks a run

### Product

- [ ] Let a user request a problem's retirement, as a private record an admin
      reads before retiring the problem by hand. Problems are served to every
      user, so no user retires one directly. Triggered when someone other than
      the author sits

### Docs

- [ ] Read the architecture doc against the code, landing every divergence as
      an item in this file. The goal is not that no divergence exists, since
      the doc is target state. The goal is that no divergence is unknown.
      Triggered when a phase closes
