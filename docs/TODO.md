# TODO

The phases still open. A ticked item stays while its phase is open. When a
phase closes, its items are harvested into `docs/ROADMAP.md` and removed whole.
The work not yet ready for a phase waits under Further developments.

## Phase 16 — scheduling and mastery (current)

- [ ] Port learn's FSRS replay, question states and gating into
      `algo_coach.knowledge`, with the shared fixtures passing against it. The
      mastery formula and the scheduler read them on the server, and the
      queues stay in TypeScript
- [ ] Generate `tests/fixtures/knowledge/scheduling.json` from this repo, by
      a `just` recipe. The fixture was generated outside it, so no rule
      change here can regenerate it
- [x] Write into `docs/architecture/` what a technique's mastery is derived
      from: the attempts, their claims, their verdicts and the drills, with
      recognition kept apart from execution. Mastery is never stored, so the
      derivation is the whole model
- [ ] Re-claim thirty attempts with the earlier machine claims hidden, and write
      the agreement with the first claims into `log.md`. The user's consistency
      caps every classifier score, and mastery reads claims
- [ ] Read the served statements for an unbounded input, and list each one
      found here. A problem is never edited, so a list is what decides whether
      any is worth retiring

### Mastery

- [ ] Compute each technique's execution reading from its sittings, as `log.md`
      gives, and show it on the board beside recognition read as unknown. The
      pick and the predictions both read it

### The card lifecycle

A card's study has phases a template's FSRS state does not hold: the ladder,
a spaced check that consolidates it, and a lapse after graduation. algo-prep's
drill board tracked them by hand.

- [x] Write a card's states into `content.md` and `log.md`: not started,
      acquiring, consolidating, graduated and lapsed, each derived from the log
      and never stored. `flows.md` defers what done means, and this answers it
- [ ] Write the graduation rule: the required rungs solved, every recallable
      template recalled clean after the spacing gap, and a probe solved
      unprompted. algo-prep's Pass-2 is this rule, and a rung solved warm proves
      no retention
- [ ] Write the lapse rule: a graduated card lapses when one of its templates
      fails its FSRS review. The card is offered again rather than left
      graduated on a form that went
- [ ] Show each card's state and its next due recall on `/cards` and on the
      board's cards in progress. The dashboard left both for this phase

### The schedule

The board orders by staleness and the user picks. Sitting daily makes that pick
itself the work, so the board serves one, read from FSRS, mastery and the
cards' states.

- [ ] Write into `flows.md` what counts as a review of a template: a recall
      attempt, graded by the hints taken, and a sitting on a problem whose
      `target_template_id` names the template. The matcher is unscored, so a
      review never reads a match
- [ ] Write down the FSRS parameters the schedule starts from and why each was
      chosen. A number nobody wrote down is guessed again at every change
- [ ] Write down the card spacing gap and the in-flight cap the schedule starts
      from: five days and two cards, algo-prep's measured decay edge and its
      proven limit. Each moves only on what the log measures
- [ ] Compute a due date per template with FSRS over its reviews. A template is
      one form, and a technique mixes forms that fade at different rates
- [ ] Write the pick's rule into `flows.md`: what it reads, how it aims at the
      form a failed sitting missed, what breaks a tie, and what the board offers
      beside it. `flows.md` has selection never schedule today
- [ ] Write into the pick's rule what it offers per card state: a due recall,
      an open run's next rung, an owed spaced check, a new card only below the
      cap, and a lapsed card again. Owed checks come before new starts
- [ ] Serve one pick on the board, naming a due template and a problem written
      for it, with every technique still on offer beside it. A technique with no
      template keeps the board's staleness order
- [ ] Store what each pick predicted before its attempt, from FSRS alone and
      from the mastery state. A prediction written after the outcome is fitted
      to it

### The comparison

The scheduler is worth building only if it beats a simpler policy over the same
problems. The comparison runs from the first pick, so its design lands with
the schedule.

- [ ] Write into `log.md` what ready means per technique: the bar, the
      difficulty and the time limit. A criterion written after the data is
      read is fitted to the data
- [ ] Choose the strongest baseline among a list, spacing per problem and a
      difficulty ladder, and write the choice and its reason into `flows.md`
- [ ] Implement that baseline over the same problems, each step checked
      against the method's published description. A baseline weaker than the
      original flatters the scheduler
- [ ] Assign each technique to the scheduler or the baseline, balanced by
      difficulty, and store the assignment before the first pick. An
      assignment made later can follow the outcomes it is compared on

### Exit
- [ ] Start a sitting from the scheduler's pick on the board, and complete it
      to the claim, with the pick's prediction and its arm stored

## Phase 17 — the matcher, measured

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

## Phase 18 — the diagnosis, measured

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

## Phase 19 — modules written by a pipeline

A knowledge module written, checked and revised by Claude Code sessions, with
no call to the API. The pipeline lives in this repo, and the content
repository holds the modules alone. Planned 2026-11-11.

### The design

- [ ] Write into `knowledge.md` where authoring lives: the rules, the level
      definitions, the skills and the checks in this repo, and the modules
      with their own rules and skip lists in the content repository
- [ ] Add "Authoring a module" to `flows.md`: the steps in order, why a
      reviewer sees neither the key nor the writer's reasoning, why the fixer
      is another session, and what stops the loop
- [ ] Decide what a question written by a session records about its writer,
      and write the choice into `machine.md`. A Claude Code session leaves no
      call in the call log

### The move

- [ ] Move `RULES.md` and the authoring half of `content/modules/CLAUDE.md`
      into this repo's docs, with learn's names replaced: `courses/`,
      `just learn check`, `spec/learn.md`. A writer session follows them
- [ ] Port `content/modules/check.py` to `algo-coach module check <slug>`,
      with a test per rule it checks. Its 433 lines carry no test today, and
      every later step trusts its verdict
- [ ] Add the `Finding` record and its schema snapshot: the rule, the
      question, the reviewer, the verdict and the outcome, stored as one
      JSON-lines file per module in the content repository

### The reviewers

- [ ] Write the solver's skill: a session answers each question without its
      key, and a reply differing from the key is a finding under rules 7
      and 9
- [ ] Write the form reviewer's skill: a session picks from the choices
      alone, with no prompt, and a keyed pick above chance is a finding under
      rules 10 and 11
- [ ] Write the leveller's skill: a session assigns each question a level
      from the definitions, and a level differing from the bank's is a finding
      under rule 16
- [ ] Write the fact reviewer's skill: a session checks each claim against
      the sources the module names, under rules 4 to 6 and 12
- [ ] Write the lesson reviewer's skill: a session reads each lesson's prose
      against its example and its questions, under rules 15 and 22
- [ ] Have each reviewer read its example defects from a path in the content
      repository. The skill is public, and a real question is not
- [ ] Write the loop's skill: the writer, the check, the reviewers and a fixer
      in turn, reviewing again only a question whose text or whose rule moved
      since its last review

### The reviewers, scored

- [ ] List the defects the three passes fixed, each with its question and the
      rule it broke, read from the content repository's three fix commits
- [ ] Run the reviewers over the Python module as it stood before the first
      pass, and write each rule's recall against that list into `ROADMAP.md`
- [ ] Read by hand a sample of the findings the three passes did not make, and
      write the share that are real defects beside the recall

### System Design

- [ ] Write the module's own `CLAUDE.md`: its scope, its sources, its kinds,
      and how each kind is proved
- [ ] Add the rule for a question no interpreter proves to the rules: the
      question names its source and the date the source was read
- [ ] Write the topics, the subtopics, the graph and the coverage maps, and
      read them by hand before any question is written
- [ ] Write levels 0 and 1 of every subtopic through the loop, and seed the
      module

### AI Engineering

- [ ] Write into the module's own `CLAUDE.md` where AI Engineering ends and
      Machine Learning begins. The two share embeddings, attention and
      evaluation metrics, and rule 14 allows one question per fact
- [ ] Write levels 0 and 1 of every subtopic through the loop, and seed the
      module

### Exit
- [ ] The reviewers carry a recall per rule against the three passes, written
      in `ROADMAP.md`
- [ ] The System Design module is seeded with nothing refused and every
      finding closed

## Further developments

Blocks of work not ready for a phase, grouped and unordered. A planned phase is
a block that became ready. A block, or a single item of one, is planned into a
phase once it is clear enough to plan. An item's trigger, where it names one, is
the event that makes the item ready.

### Algorithm practice on the phone

The phone becomes a place to practise algorithms in full, as it already is for
the knowledge modules. A solution typed on the phone's keys is slow, so the
phone's own algorithm practice asks for little typing: naming the approach,
ordering and completing a solution, and tracing what it prints. A new exercise
meant for the phone joins this block rather than opening a block of its own.

- [ ] Time five sittings on the phone and five on the web, on problems of one
      difficulty, and write the medians into `log.md`. Execution reads the
      elapsed time beside `device`, and nothing yet says what the phone's keys
      cost a solve
- [ ] Write into `pages.md` which page of the Practice section serves the
      recognition drill and the short exercises on both clients, and draw it in
      `wireframes.md`

#### The recognition drill

A problem served without its technique, answered in words with no code run.
Moved out of Phase 16 on 2026-10-02: hiding the technique matters less than
the schedule, and the mastery state reads recognition as unknown until a drill
feeds it.

- [ ] Write the rubric the framing judge grades on into `log.md`: the
      algorithm in words, why it is correct, and its runtime
- [ ] Decide the drill's record and write it into `log.md`. A drill carries no
      code and no verification, so an `Attempt` would leave both empty
- [ ] Grade a set of framings by hand, and score the framing judge against
      it. A judge that accepts vague answers raises recognition on the
      techniques the user cannot spot
- [ ] Serve a problem without its technique, take the framing as text, and
      store the judge's grade
- [ ] Show the drill on the phone's width first. A drill that needs a desk is
      a sitting with fewer steps
- [ ] Take the framing spoken, transcribed in front of the same judge.
      Triggered when the judge's score holds on text

#### Short exercises

Exercises that need little typing, and so suit a phone: ordering a solution's
shuffled lines, filling one blank in it, and tracing what it prints. Each
tests less than writing the solution does.

- [ ] Write the design of a short exercise into `log.md`: its own record
      kind, and that mastery never counts it as execution. A reordered line
      is not a solve
- [ ] Compare tracing with the knowledge module's `output` questions, and
      write into `knowledge.md` whether a traced output is one of them

### Practice with an assistant in the loop

Coding beside an AI assistant moves the skill from typing code to specifying
it and checking it. Three exercises train that skill, and the first two reuse
records the corpus already holds.

- [ ] Write the high-level design into `log.md`: the three exercises, the
      record each leaves, and which part of mastery each counts toward, if
      any. A bug found in someone else's code is not a solve
- [ ] Decide how a served mutant is named, and write the rule into
      `corpus.md`. No store holds a mutant today, and an operator set that
      changes would re-derive a different mutant under the same position
- [ ] Serve a killed mutant as code an assistant wrote, take the line the user
      names and the fix, and run the fixed code against the problem's cases
- [ ] Serve a canonical beside its naive solution, take the user's reading of
      which grows faster and at what size it fails, and check the reading
      against the problem's separating case
- [ ] Serve the instruction exercise: the user writes an instruction for a
      problem, a model writes `solve` from it alone, and the problem's cases
      judge that code. Triggered when the first two exercises are in use,
      since each attempt costs a call
- [ ] Show the bug and the comparison exercises on the phone first. Each asks
      for reading and a tap, which the block "Algorithm practice on the phone"
      is for

### Scheduling on the diagnosed cause

Waits on the scores Phase 18 produces: a cause nothing measured is a guess the
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

- [ ] Run a sweep for a technique the drill loop runs out of unseen problems
      on. Triggered when the user has attempted every candidate a technique
      offers
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
- [ ] Tell the generator to write every bound and formula as a Python
      expression in a code span, never TeX, and say so in `corpus.md`. A code
      span reads the same on both clients, where the phone reads TeX through a
      Unicode fallback. Triggered by the next generation sweep
- [ ] List every served easy problem that asks for more than the form applied
      to the input as given, and what it asks for. The list shows whether the
      generator writes past its own definition of easy or labels too low

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
      Triggered when Phase 18 scores its first tool
- [ ] Measure the repair by what it adds to the diagnosis call, the same way
      Phase 18 measures each tool. A tool nobody measured is a guess the call
      acts on

### Technique detection by static analysis

- [ ] Write rules per core template that say from the parsed tree whether a
      solution displays the template's form. Triggered when Phase 17 names
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
      Triggered when Phase 16 has recorded predictions for a few hundred picks

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

### Tables and diagrams on a phone

A table or a diagram drawn with box-drawing characters scrolls sideways on a
phone, where a reader sees a third of it at a time. The content repository's
`modules/TODO.md` converts them to markdown tables and Mermaid, and waits on
the items below.

- [ ] Write into `pages.md` how a markdown table reads on both clients: its
      cells wrap, and a table wider than the screen reads each row as lines of
      header and value. The phone's markdown library holds every column at a
      fixed width and scrolls
- [ ] Render a markdown table that way, with the phone's own renderer and the
      web's below the phone's width
- [ ] Decide how a Mermaid diagram reaches the clients, and write the choice
      into `knowledge.md`: drawn to SVG at seed time, in both schemes, and
      carried in the snapshot. The snapshot then stops equalling learn's
      format 6, which that file states today
- [ ] Draw a ` ```mermaid ` block and a `diagram` field holding Mermaid as the
      seed's image, on both clients. Triggered when the content repository
      converts its first diagram

### Audio

Practice with the screen off: questions read aloud and answered by voice, on
the phone. Android carries an on-device speech engine and recogniser, which an
Expo module reaches. Code read aloud loses its indentation, so audio suits the
questions that carry none. The spoken framing of a recognition drill is listed
under its own block.

- [ ] Write into `knowledge.md` which questions an audio queue serves: no code
      and no diagram, `choice` and `open` alone. A `short` reply is usually
      code, which a recogniser spells badly
- [ ] Decide what a spoken answer stores, and write the choice into
      `knowledge.md`. The transcript is the user's words, and the audio is a
      recording of their voice that nothing reads afterwards
- [ ] Read a queue's prompt and choices aloud through the phone's speech
      engine, and take a `choice` answer spoken as its letter. A letter is one
      word, which an on-device recogniser hears reliably
- [ ] Transcribe a spoken answer to an `open` question, and propose the key
      points it named. The user still ticks the points, since the grade is the
      user's own report
- [ ] Score the proposed points against the user's ticks before any proposal
      is shown pre-ticked. A proposal the user accepts unread grades the answer
      by the model
- [ ] Read a lesson aloud on the phone, naming each code block rather than
      speaking it. Triggered when the audio queue is in use

### Swipe typing on the code keyboard

A spike: whether dragging one finger across the app's keys types a word
faster than tapping it. The word list is Python's keywords and the names the
file declares, the same words the name row offers, so the rule in `flows.md`
against library names still holds.

- [ ] Find a path-to-word matcher that runs in JavaScript over a word list
      the app supplies, or write down that none fits. Gboard's matcher is not
      reachable from an app's own keyboard
- [ ] Build a throwaway swipe layer on `native/src/ui/keys.tsx` with that
      matcher, behind a dev flag. A spike that ships nothing needs no polish
- [ ] Type the same three median canonicals by tapping and by swiping, and
      write down the time and the corrections for each. The name row already
      saves most retyping, so swiping has to beat tap plus the row
- [ ] Count how often the top match is wrong over those files' words. Short
      names such as `i`, `j` and `n` sit inside longer paths
- [ ] Decide from those numbers whether swipe typing ships, and write the
      decision with its numbers into `docs/architecture/README.md`, beside
      the editor's latency measurement

### Steering the knowledge queues

The next queue aims at one focus, so a user studying two subjects at once
re-aims it by hand. Nothing aims the next focus once the current one is done.

- [ ] Write the focus set into `knowledge.md`: several targets, each with a
      weight, and the share of the next queue's new questions each target
      receives. One focus per user stands across devices today
- [ ] Decide how a focus set is stored, and write the record into
      `knowledge.md` `## The records`. `focuses` is append-only, so the shape
      is fixed once the first set is stored
- [ ] Write the `focus` line's form for a set into `knowledge.md` `## The
      wire`. A line carrying one target is learn's format, which both clients
      still read
- [ ] Mix the next queue's new questions by the set's weights in
      `packages/core`, with fixtures generated from the Python side passing in
      both suites
- [ ] Add, remove and reweight a target on both clients, from the knowledge
      home and a module's page, with a row per act in `pages.md` `### Acts`
- [x] Write into `knowledge.md` when a focus target counts as done, for each
      of the four kinds: module, topic, subtopic and certification. A route
      advances on that rule, and the focus has none today
- [ ] Write the route into `knowledge.md`: an ordered list of focus targets,
      the next aimed once the one before is done, with gating unchanged
- [ ] Decide whether a route fills one target of a focus set or the whole
      set, and write the choice into `knowledge.md`
- [ ] Decide how a route is stored, and write the record into `knowledge.md`
      `## The records`. The table is append-only, so the shape is fixed once
      the first route is stored
- [ ] Create, reorder and clear a route on both clients, from a page under
      Knowledge, with its rows in `pages.md` `### Screens` and `### Acts`

### Projections

`knowledge.md` gives the review forecast and the focus's projected date.

- [ ] Count the reviews a failed question needs in the focus's date, once the
      log holds a failure rate per level. The date now takes every failed
      question to pass on its next review
- [ ] Show a module's own forecast on its page. Triggered when the home's
      forecast reads two modules' load and the user asks which one it is

### The algorithms module

Mastery's knowledge part counts answers to the questions a technique carries,
and no question carries a technique yet.

- [ ] Decide how a subtopic names the technique it teaches, and write the field
      into `knowledge.md`. `log.md` defers how a question is tied to its
      technique, and the field settles it
- [ ] Write into `content.md` how a card and a subtopic share one technique:
      the card holds the trigger, the templates and the ladder, the subtopic
      the facts. Without the split a lesson and a brief restate each other
- [ ] Add the technique field to the seed and the snapshot, checked against
      the vocabulary as the seed runs
- [ ] Author the algorithms module in the content repository, first a subtopic
      per technique a card teaches
- [ ] Link a card's page to its technique's subtopic on both clients, with the
      row in `pages.md` `### Acts`
- [ ] Count a technique's knowledge reading from the answers to its subtopic's
      questions, as `log.md` gives, and show it on the board

### Output questions typed

An `output` question answered by picking an option tests recognition. Typing
the output tests recall, which is what a syntax trainer measures.

- [ ] Decide whether changing a question's format keeps its slug, and write the
      rule into `knowledge.md` `## Seeding`. The fact asked stays the same, and
      a new slug would discard every answer already given
- [ ] Write into `knowledge.md` `## Questions` how a `short` reply to an
      `output` question is matched. The rule today strips whitespace and
      quotes, which can erase the difference the question asks about
- [ ] Rewrite the Python module's `output` questions from `choice` to `short`
      in the content repository

### Variants of an output question

An `output` question with fixed values is memorised after a few reviews: the
user recalls the answer rather than the semantics.

- [ ] Write the variant into `knowledge.md`: a template, its parameter sets,
      every variant scheduled under the question's slug, and the kinds that
      may carry one
- [ ] Decide whether an answer records the variant it met, and write the field
      into `knowledge.md` `## The records`. Without it a wrong answer cannot be
      traced to the values behind it
- [ ] Compute each variant's output by running it as the seed runs, and carry
      the variants in the snapshot. No client runs a question's code
- [ ] Serve a variant at random on both clients, with the shared fixtures
      passing in both suites

### Questions served by the engine

- [ ] Serve the next question from the engine. Triggered when a client that
      cannot run `packages/core` asks to practise questions: an MCP agent, a
      terminal mode. Weigh first a thin client running the core in Node,
      which keeps one copy of the queues

### MCP and autonomy

- [ ] Expose the corpus and the engine's commands as an MCP server.
      Triggered when an agent outside the engine needs to read the corpus
- [ ] Run the practice loop as a scheduled agent over the MCP server, serving
      the scheduler's pick. Triggered when Phase 16's pick is served on the
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
- [ ] Print the seed's progress to stderr as it runs: one line per stage,
      modules, questions, lessons, cards, with its count. A seed through the
      tunnel runs for minutes and prints nothing before its closing summary

### Docs

- [ ] Read the architecture doc against the code, landing every divergence as
      an item in this file. The goal is not that no divergence exists, since
      the doc is target state. The goal is that no divergence is unknown.
      Triggered when a phase closes
