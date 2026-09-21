# TODO

The phases still open. A ticked item stays while its phase is open. When a
phase closes, its items are harvested into `docs/ROADMAP.md` and removed whole.
The work not yet ready for a phase waits under Further developments.

## Phase 13 — the loop in use (current)

The author practises on the deployed engine, and the sittings decide the work.
This phase starts with almost no items. An item is written when a sitting finds
a fault, a page reads badly, or a flow wants a step nothing serves, and it is
written as any item here is: an imperative naming what exists when it is done.

The phase closes when its own backlog is empty and a stretch of sittings has
opened nothing new. No count of sittings is its exit, since the phase measures
what use surfaces rather than how much use happened.

### Sitting on the deployed engine

- [ ] Sit one problem through on the deployed engine, from the board to the
      claim and the label, which is Phase 12's unmet exit
- [x] Write down, per sitting, what read badly or worked badly, as items under
      the headings below. A fault nobody wrote down is fixed twice or never

### The design

- [x] Rework every list of picks as rows and panels, and give a long page a bar
      naming its sections. A table spread one pick over four columns, and the
      reader joined them back together to judge it
- [x] Move the neutrals to a warm paper ground and square the radii, with each
      colour token declaring both schemes in one `light-dark()` call. A solver
      reads a statement for many minutes
- [x] Offer a scheme switch in the navigation, stored in the browser and
      applied before the first paint. The app followed the browser's preference
      alone, which left a reader on a machine set the other way no way to read
- [x] Bind the prose renderer and the Python colouring to the tokens, one
      mapping for the editor and for a template's form. Each shipped a scale
      and a palette of its own
- [x] Read every page against real data and list what the design gets wrong,
      one item per page. Phase 10 designed against seeded readings
- [x] Add the panel, the pick row, the section bar, the account menu, the
      scheme switch and the template panel to `/gallery`. `pages.md` has the
      gallery show every component the pages use, and it shows none of the six
- [x] Drop the table from `/gallery`, or restore a page that reads as a table.
      The rework replaced every table with rows, and `components/ui/table` is
      imported by the gallery alone
- [ ] Read the sitting page against a real submission on a narrow window. Every
      other page was reworked as rows and panels, and the sitting is the one
      page `pages.md` exempts from phone width

### The flows

- [x] Serve `GET /api/problems` and a `/problems` listing the reader filters by
      tag and by level, with both filters and the page in the URL. The board
      reached problems one technique at a time
- [x] Serve `GET /api/me` and put the account in a menu at the right of the
      navigation. Sign out sat among the sections, which name places, and the
      pages knew nothing about the user behind the session
- [ ] Carry a single picked tag into the problem as `?technique=`, or write
      into `pages.md` why a listing pick names no technique. A row links with
      `?from=problems` alone, so the claim opens with nothing ticked where a
      pick from the board ticks the technique it was drilled for
- [x] Decide what `/problems` does with a retired problem, and write the
      decision into `pages.md`. `GET /api/problems` answers the served ones, so
      a retired problem is absent where the board still counts its attempts

### The corpus

- [ ] Run a sweep for a technique the drill loop runs out of unseen problems
      on. The trigger is a technique whose candidates the user has all attempted

### Exit
- [ ] Every item this phase opened is ticked, and a stretch of sittings opened
      no new one

## Phase 14 — the matcher, measured

The matcher says which templates a generated solution displays, and every
ladder is built from those matches. No number says how often the matcher is
right. This phase matches a sample of pairs by hand and scores the matcher
against them. The phase sits behind the beta: the drill loop needs problems
rather than a score, and the attempts the loop produces rebuild the eval set
the classifier is scored against.

### Matching the generated corpus by hand

The hand pass does two jobs at once. It writes the matcher's reference, and it
is the only reading of a generated problem that no model produced. A generator
that drifted from its target shows in the hand pass whatever the matcher says.

- [ ] Match by hand a sample of pairs through `algo-coach match --by-hand`,
      across the core templates the sweep reached. The command samples and
      writes a record per candidate already
- [ ] Match the eval set by hand with no matcher reading in view, which is
      `--by-hand` without `--verdict`. The first pass set the criterion, and a
      score over those same pairs measures the criterion against itself
- [ ] Write down how many pairs the two passes settled, and over how many
      templates. A score prints a denominator, and nothing else says what the
      reference covers

### Scoring the matcher

Generation asserts a match and the matcher audits that match, so an unmeasured
matcher audits at an unknown error rate. An unmeasured matcher blocks trusting
the audit. Generation goes on without the score.

- [ ] Lift the scorer out of `attempt_claims/score.py` for the matcher to
      share. It prints denominators and reports both directions already, which
      is the shape a per-pair score needs
- [ ] Score the matcher per pair, over the pairs both the user and the matcher
      read. A match asserts one pair, and a score over a solution's whole set
      would hide which pair moved
- [ ] Group the score per template. A form the matcher over-matches fills its
      rung with problems that do not teach it, and one number over the card
      would average that away
- [ ] Report the positive verdicts in both directions: the templates the user
      named and the matcher missed, and the templates the matcher named and the
      user did not. Most pairs are negative, so accuracy would score a matcher
      naming nothing in the nineties
- [ ] Serve the score from a command, `algo-coach match --score`, beside the
      run and the hand pass. `algo-coach score` reads attempts, and a second
      subject on it would make every flag mean two things
- [ ] Skip a question the hand pass settled whole, and read those pairs in the
      eval alone. A user match carries no configuration, so the run path counts
      the pair unread and pays for a verdict that can never stand
- [ ] Report where the matcher disagrees with the generator's own match. The
      run already reads those pairs, and the disagreement means something only
      once the matcher carries a score
- [ ] Pin one configuration before any number is quoted, as the classifier's
      score does. A score read at a configuration nobody recorded compares with
      nothing

### Exit
- [ ] The matcher carries a per-template score in both directions

## Phase 15 — mastery and scheduling

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

### The diagnosis

The machine counterpart of the self-label, which Phase 12 writes. The eval
scores one against the other, so a body of self-labels has to exist first.

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

- [ ] Page the rows in `GET /api/problems`, and keep the tag counts over the
      whole corpus. The listing fetches every problem today, since a page of
      rows cannot count the tags. Triggered when the corpus outgrows one
      request
- [ ] Let a user request a problem's retirement, as a private record an admin
      reads before retiring the problem by hand. Problems are served to every
      user, so no user retires one directly. Triggered when someone other than
      the author sits

### Docs

- [ ] Read the architecture doc against the code, landing every divergence as
      an item in this file. The goal is not that no divergence exists, since
      the doc is target state. The goal is that no divergence is unknown.
      Triggered when a phase closes
