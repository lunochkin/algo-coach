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
- [x] Address a recall by the template's slug, `/cards/:slug/recall/:template`,
      and have the drawn path send the browser to it. The path named the card
      alone, so a reload redrew and no URL asked for one form
- [x] Name the template on the recall page and offer its form on the result,
      and drop the title hint the visible name answers. `Hint` carries the
      notes and the form, and the one stored attempt taking a title was deleted
- [x] Start the recall of any form from the card's Recall section, and name
      every template of the card on the trainer to switch between. The draw
      reached one form at a time, and the form a user meant to practise was
      reachable only by exhausting the others
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

## Phase 14 — recognition, scheduling and mastery

- [ ] Write into `docs/architecture/` what a technique's mastery is derived
      from: the attempts, their claims, their verdicts and the drills, with
      recognition kept apart from execution. Mastery is never stored, so the
      derivation is the whole model
- [ ] Re-claim thirty attempts with the earlier machine claims hidden, to
      measure the user's own consistency, which caps every classifier score.
      Mastery reads claims, and a wrong claim spends practice time

### The recognition drill

Spotting a form and writing it are different skills, and the first is the one
that goes quiet. A drill that runs no code fits a spare minute, and it fills
the log faster than sittings can.

- [ ] Serve a problem without naming its technique, with the choices drawn
      from the techniques the matcher rejected for it. A distractor nothing
      rejected is a second right answer
- [ ] Store a drill as an attempt of its own mode, so the state can read
      recognition apart from execution
- [ ] Show the drill on the phone's width first. A drill that needs a desk is
      a sitting with fewer steps

### The schedule

The board orders by staleness and the user picks. Sitting daily makes that pick
itself the work, so the board serves one, read from FSRS and the mastery state.

- [ ] Write the pick's rule into `flows.md`: what it reads from FSRS and from
      mastery, what breaks a tie, and what the board offers beside the pick.
      `flows.md` has selection never schedule today
- [ ] Time reviews with FSRS, whose unit is the technique and the mode. A
      schedule over problems says when to redo one; a schedule over techniques
      says when a form is about to go
- [ ] Write down the FSRS parameters the schedule starts from and why each was
      chosen. A number nobody wrote down is guessed again at every change
- [ ] Serve one pick on the board, naming a technique and a problem, with every
      technique still on offer beside it
- [ ] Record what was predicted before each attempt, from FSRS alone and from
      the mastery state. A prediction written after the outcome is fitted to it

### Exit
- [ ] Start a sitting from the scheduler's pick on the board, and complete it
      to the claim, with a drill feeding the same state

## Phase 15 — the matcher, measured

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

### The corpus gate, on the same pass

A generated statement can name its own form, or be a public problem the model
returned. Both are read off the sample the hand pass already covers.

- [ ] Judge the same sample for whether the statement names its own form, and
      whether it is a public problem the model returned. The reader is already
      reading it, and a second pass pays twice for one reading
- [ ] Report both shares against the rate over `data/old/`, with the
      denominator the pass covered

### Exit
- [ ] The matcher carries a per-template score in both directions, and the
      gate carries a share with the denominator the pass covered

## Phase 16 — the diagnosis, measured

The machine counterpart of the self-label, and how much the program-analysis
tools add to it. The mutants make the eval set: a mutant carries its mistake by
construction, so a labelled failure exists for every one without waiting for
the log to fill.

- [ ] Narrow the diagnosis call, the model call that writes a `Diagnosis`, to
      what the record supports: a mechanical slip against a conceptual miss. A
      four-way verdict would ask the call for what the call cannot see
- [ ] Write the verdict as a `Diagnosis` carrying its provenance whole. A
      diagnosis never supersedes a self-label, because the eval scores the
      diagnosis against the self-label
- [ ] Build the eval set from the stored mutants, each one labelled by the
      mistake it was written to make
- [ ] Score the diagnosis call per failure mode, with no overall share,
      against the self-labels the loop produced and the mutants' own labels. A
      call that only ever says `gap` would score well on a corpus of gaps
- [ ] Give the call a structural diff against the nearest passing solution,
      and score again. The difference is what the tool bought
- [ ] Give it the first case where execution diverges, and score again
- [ ] Give it how the running time grows, and score again. The runner already
      times each case and minimises a separating input
- [ ] Report the score per tool, not only the best one. A stack of tools with
      one carrying all of it is a simpler product

### Exit
- [ ] The call carries a per-mode score, and each tool carries the difference
      it made

## Further developments

Blocks of work not ready for a phase, grouped and unordered. A planned phase is
a block that became ready. A block, or a single item of one, is planned into a
phase once it is clear enough to plan. An item's trigger, where it names one, is
the event that makes the item ready.

### Scheduling on the diagnosed cause

Waits on the scores Phase 16 produces: a cause nothing measured is a guess the
board would act on.

- [ ] Have the pick read the diagnosed cause beside mastery, once the call
      carries a per-mode score

### Alternative solutions

Every other way to solve a stored problem, by the flow in `flows.md`,
"Enumerating a problem's other solutions". The schema and the match's subject
are in place already, and nothing yet writes a second canonical.

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

### Repair as diagnosis

- [ ] Write the repair search: a failing attempt and the problem's canonicals
      in, the smallest edit on the parsed tree passing every case out. The
      search returns no edit when none is found within a stated budget.
      Triggered when Phase 16 scores its first tool
- [ ] Measure the repair by what it adds to the diagnosis call, the same way
      Phase 16 measures each tool. A tool nobody measured is a guess the call
      acts on

### Technique detection by static analysis

- [ ] Write rules per core template that say from the parsed tree whether a
      solution displays the template's form. Triggered when Phase 15 names
      templates the matcher reads badly
- [ ] Compare the rules with the matcher per template on the hand pass, and
      send each pair where the two disagree to adjudication

### Misconception discovery

- [ ] Mine the log for failed attempts that no failure mode and no known
      mutant explains, grouped by the edit that repairs them. Triggered when
      the log holds enough failed attempts per technique to group
- [ ] Write each proposed mistake as a mutant of the canonical. Keep the
      proposal only where a case kills the proposal's mutant and no known
      mutant fails the same cases

### Soundness-checked synthesis

- [ ] Search for an input killing each survivor after the fuzz pass, with a
      solver over the input's constraints or a coverage-guided search.
      Triggered when survivors remain after the fuzz pass on a core template
- [ ] Compare each remaining survivor with the canonical on every input up to
      a bound, and label the survivor equivalent when no input separates the
      two. An unlabelled survivor leaves the case set's assurance unstated
- [ ] Write the guarantee a landed case set carries into `corpus.md`: the
      mutants the case set kills, and the bound up to which the rest are
      equivalent

### Judging concurrent code

- [ ] Choose how a concurrent submission is judged, by repeated runs under the
      race detector, by a scheduler exploring thread interleavings, or by
      both. Write the choice into `corpus.md`. Triggered when problems about
      concurrent code are planned

### Knowledge tracing

- [ ] Fit a knowledge-tracing model to the log, and score the model on the
      predictions each pick records against FSRS alone and the mastery state.
      Triggered when Phase 14 has recorded predictions for a few hundred picks

### Forgetting per technique

- [ ] Fit the decay of the chance of passing per technique and mode, and
      compare the decay with FSRS's forgetting curve. Triggered by the same
      count of recorded picks

### Difficulty calibrated from attempts

- [ ] Estimate each problem's difficulty with item response theory from pass
      and fail records, and store the estimate with its provenance. Triggered
      when problems carry attempts from more than one user
- [ ] Aim generation at a stated difficulty, and score each landing by the gap
      between the stated and the estimated difficulty. Triggered when
      difficulty estimates exist

### Retrieval

- [ ] Write the high-level design of retrieval: what is indexed from the
      corpus and the user's own attempts, and which page or call reads what is
      retrieved. Triggered when a flow needs a similar problem that the
      technique alone cannot select

### MCP and autonomy

- [ ] Expose the corpus and the engine's commands as an MCP server.
      Triggered when an agent outside the engine needs to read the corpus
- [ ] Run the practice loop as a scheduled agent over the MCP server, serving
      the scheduler's pick. Triggered when Phase 14's pick is served on the
      board

### Design simulation

- [ ] Write the high-level design of the simulator: the component kinds, the
      load and failure scenarios, and the numbers a run reports. Triggered when
      system design is planned as a track

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
