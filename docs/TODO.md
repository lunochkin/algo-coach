# TODO

The phases still open. A ticked item stays while its phase is open. When a
phase closes, its items are harvested into `docs/ROADMAP.md` and removed whole.
The work not yet ready for a phase waits under Further developments.

## Phase 15 — two platforms (current)

The web and the native app become two ways into one learner model. The
knowledge rules and what the screens show move into one TypeScript package
both apps import, and each app keeps a look of its own. Decided 2026-11-10.

### The shared core

- [x] Move `native/src/core` into `packages/core` behind npm workspaces, with
      the app importing it and its tests passing. Nothing in it names React
      Native or Expo already
- [x] Move the OpenAPI-generated types into `packages/core`, and type the
      app's sync against them. The app writes its sync shapes by hand today
- [x] Move what the screens compute for display into `packages/core` as
      tested presentation functions: the module card, the queue header, the
      empty Continue. Two screens assembling one label drift apart unnoticed

### The knowledge module on the web

- [x] Add the `daily_limits` and `limit_raises` tables with their `limit`
      and `raise` sync lines, and have the app write them instead of keeping
      the limit and the raise on the device
- [x] Rename the knowledge store's `rank` to `level`, in the migration, the
      tables and the server code. The docs, the wire and `packages/core` say
      `level` already
- [x] Rename the problems' `levels` to `difficulty` in `pages.md` and the
      Problems page. `level` now names a question's depth
- [x] Write the clients' knowledge store into `knowledge.md`: one copy of
      the snapshot and the log on the device, an outbox, and when each syncs
- [x] Key the native app's copy to the signed-in user, and have sign-out
      send the outbox and delete the copy. Pending rows outlive a sign-out
      today
- [x] Add a section for the knowledge modules to the web's navigation, and
      write its pages into `pages.md` and `wireframes.md`
- [x] Decide whether the daily limit is set from the knowledge home or a
      settings page, and write the choice into `pages.md`
- [x] Decide whether a queue keeps its state in the URL query, and write the
      choice into `pages.md`. A reload then restarts the queue
- [x] Add the `module_orders` table with its `order` sync line, and have
      the phone and the web write and read it instead of a device setting
- [x] Replace `daily_limits` with one `setting_changes` table and its
      `setting` sync line, and have the phone write the exam size there too
- [x] Open the phone's Exam screen on the focus, as Practice opens, and drop
      `queue_filters`: the focus already holds the choices both clients share
- [x] Drop Pick questions as a screen, and start a filtered queue from a
      sheet on the module's page. Starting a queue there moves no focus
- [x] Add the `/settings` page to the web, with the daily limit and the exam
      size, linked from the account menu
- [x] Add `web` to the npm workspaces, and keep the snapshot and the log in
      IndexedDB with an outbox, synced as `knowledge.md` gives. The pages
      then read the copy, not the whole log
- [x] Move what the phone's queue screen computes for display into
      `packages/core`: a result's verdict rows, its marks and its detail
      sections. The web's queue would otherwise compute them again
- [x] Move what the phone's home computes into `packages/core`: the
      catalog a client's records build, Continue's counts and the focus
      card's counts. The web's home would otherwise compute them again
- [x] Read the web's knowledge home from the copy: the counts line under
      Continue, the focus panel with its clear, strict and raise presses,
      and each module's next-up row. The phone shows the same counts
- [x] Serve the next queue and the review queue at `/knowledge/queue` from
      `packages/core`, started by Continue, with its empty notice, and by
      the reviews waiting outside a strict focus. An answer given there
      reaches the phone at its sync
- [x] Move what the module's screens compute into `packages/core`: a
      group cell's state and count, the counts per level, and the start
      sheet's counts and label. The web's page would otherwise compute them
- [x] Add `/knowledge/modules/:module` to the web: a panel of group cells
      per topic, the counts per level, the focus and status presses, and the
      home's rows opening it
- [x] Open the start sheet from the module page: a group's cell, a
      subtopic's name, and Start beside a topic and the module. Serve its
      queue at `?mode=filtered` with the choices in the query. Starting moves
      no focus
- [x] Add the map to the web's module page beside its groups, from the
      layout `packages/core` computes for the phone
- [x] Mark the signed-in apps web only in `pages.md`: an app token reaches
      the knowledge endpoints alone, so a phone cannot list or revoke apps
- [x] Decide how a queue offers a lesson on both clients, and write it into
      `pages.md`
- [x] Add the lessons to the web: `/knowledge/lessons` by module, the lesson
      page with Mark read and unread, the home's ready-lesson link, and the
      queue's lesson stop opening the page
- [x] Add the certifications to the web: the grid, a certification's
      conditions with its exam and its focus press, and the home's
      ready-certification link
- [x] Move what the phone's exam screens compute into `packages/core`: the
      sample, the results by topic and the missed answers
- [x] Serve exams on the web: the level exam's page, the exam at
      `?mode=exam` with its results, a certification's Take exam, and the
      home's Exam press
- [x] Add the sync's state, a sync press and the archived modules' restore
      to the web's settings page, as the phone's Settings holds them
- [x] Open a certificate node's conditions and a lesson node's lesson from
      the web's map, as the phone's map does
- [x] Correct the inventory's sign-out row: the phone signs out from its
      account menu as well as Settings
- [x] Name one review and one new question in the singular in the core's
      count lines. Both clients read "1 reviews" today

### The engine on the phone

- [x] Write the native app's screens into `pages.md` as a section of their
      own, beside the web's
- [x] Move the phone to the shared structure: bottom tabs for the sections
      it holds, an account menu for Settings, and the Knowledge home linking
      Lessons and Certifications. The top bar's shortcuts go
- [x] Join the phone's Map and Stats into one module screen of groups and
      map, with the focus, the status and the start sheet on its four
      scopes. Stats, the row menu and the course chips go
- [x] List the phone's lessons by module, as the web does
- [x] Decide whether an app token may read the board's and the cards'
      endpoints, and write the choice into `README.md`. The phone's board
      and cards wait on it
- [x] Let an app token reach every endpoint a session reaches, with a test
      per route group. The token reaches the knowledge sync alone today
- [x] Add the signed-in apps to the phone's account menu
- [x] List every signed-in device on both clients, browser sessions with
      the apps, each one revocable and the one read on marked. A session
      gains `last_used_at`, and a browser is invisible on both today
- [x] Move what the web's board and cards pages compute for display into
      `packages/core`: a technique's row, a card's row and its state line.
      The phone would otherwise compute them again
- [x] Serve the cards on the phone as a Cards tab: the list grouped by
      technique, and a card's trigger, brief and templates, each hidden
      until revealed. With no network it says so
- [x] Write into `pages.md` what a technique on the phone's board opens: no
      card, one card, or several
- [x] Carry the card state on `CardStatus`, and count a graduated card out
      of the cards in progress, as `pages.md` gives. Both clients count it
      in today
- [x] Serve the board on the phone as a Practice tab, first among the tabs:
      the cards in progress, and the techniques by staleness opening their
      problems and cards. With no network it says so. The phone still opens
      on Knowledge, and the inventory names that difference
- [x] Mint the sitting at the first clock press or the first submission, as
      `log.md` gives, so serving a statement records nothing. The web's
      problem page stays on `/problems/:problem_id`, naming its sitting as
      `?sitting=`
- [x] Add the phone's Problem screen: a problem's record and its statement,
      opened from a technique's problems, with no editor and no clock

### The phone beside the web

- [x] Audit every knowledge screen and act the inventory marks `same` against
      the web, and list each difference found under `pages.md` To fix
- [x] Move every sentence a knowledge screen says into `packages/core`, in the
      web's wording, and read it on both clients. One copy closes the wording
      entry under `pages.md` To fix
- [x] Fix the phone's side of `pages.md` To fix: the home, a module and its
      map, the certifications, the settings, the login, the lessons and a
      lesson. Each row reads `same` once its entries are gone
- [x] Fix the web's side of `pages.md` To fix: the module's summary line, the
      paused mark on an exam's module, the raise after a queue ends, a failed
      sync on the home, the certifications' coverage, and the exam size saved
      at the start
- [x] Fix where the two clients behave apart: the phone's 2 s focus delay, the
      web's timestamp format, forced sign-out, an exam stopped unanswered, the
      certification exam's rules, the start sheet's preview, the load wording
- [x] Move the sync into core: the scheduler, one pass and each record line,
      behind a store each client implements. Two copies have drifted once
- [x] Move the queue run, the exam run and one question's answer into core,
      each a state the clients draw. Both hold the same flow twice today
- [x] Open the lesson a web queue offers over the running queue, as the phone
      does, so Read no longer ends the queue
- [x] Move the map's edges and node panel, the learner, one typed engine
      client and the small focus, order and certification helpers into core
- [x] Add a test in `tests/` that every web route and native screen file has
      an inventory row, matched by a table in the test, and that a row's
      phone column reads `none` exactly where no phone screen holds it
- [x] Serve the problem listing on the phone as a Problems tab, its filters,
      counts and pages computed in core, and drop the `pages.md` rule that the
      listing follows the sitting
- [x] Show a card's ladder and probes on the phone, each rung opening the
      Problem screen, and revise the `pages.md` rule that they follow the
      sitting. The sitting a rung opens stays on the web
- [x] Add the press starting a card run to the phone's card, below its
      ladder. Starting draws the probes and declares the study, and the
      sittings it measures are still sat on the web
- [x] Serve the privacy policy on the phone as a screen, opened from Login
      and Settings, with its text moved into `packages/core` for both clients

### Code on the phone

Reading and writing code in the native app, so the sitting and the recall
reach the phone beside the rest of the engine. The phone types through a
keyboard of the app's own: the system keyboard hides the symbols code and a
`short` answer are made of, and its suggestion strip completes words.

- [x] Add `device` to the sitting, as the knowledge records carry it, and
      snapshot the schema. A phone solve is slower, and an attempt's time is
      append-only, so the field lands before the first phone sitting
- [x] Draw a keyboard of the app's own, with two rows of symbols above the
      digits and the letters and the rare symbols on a layer, and answer a
      `short` question through it on the quiz screen
- [x] Type a form into CodeMirror in a WebView on the Android phone, its
      content `inputmode="none"` and the app's keyboard sending each key, and
      write the scrolling and key latency it showed into `README.md`
- [x] Move the editor's setup into shared code beside `packages/core`: the
      Python highlighting and the rule that the editor completes nothing. One
      setup keeps the two editors behaving alike
- [x] Move the recall trainer's state into core: the draw, the two hints in
      order and the result's counts. `RecallPage.tsx` holds them for the web
- [x] Add a Recall screen to the phone, opened from each template on Card and
      drawn from the card, switching between the card's templates. Its editor
      is CodeMirror in a WebView, typed through the app's keyboard
- [x] Add the editor's layer to the keyboard: a key per Python keyword, a
      strip dragging the cursor, indent and dedent. No key carries a form
- [x] Add line keys to the editor's layer: move a line, indent or dedent a
      block, duplicate a line, and select the current block
- [x] Show the phone editor's indent at two characters per level while the
      file keeps four, and wrap a long line under its own indent. A median
      canonical's widest line is 55 characters, where a phone fits 40
- [x] Hide the app's keyboard on a press, so a whole solution reads on one
      screen. A median canonical is 18 lines
- [x] Pair brackets as they are typed, in the phone's editor and the web's
      alike, so the two editors behave as one
- [x] Write into `flows.md` whether the keyboard offers the names the file
      already declares. The rule today refuses every name the code typed
- [x] Offer the names the file declares in the editor's top row, in the
      strip's place, so the row costs no height. `flows.md` gives the rule
- [x] Move the sitting's state into core: the clock with its pauses and its
      preference, the code the editor opens on, the verdict fold and the first
      failing case. `SittingView.tsx` holds them for the web
- [x] Move the claim and the self-label into core: the drilled default, the
      glosses and the words. The modes an outcome allows stay the engine's,
      which sends them with each attempt and refuses a label outside them
- [x] Add the sitting to the phone's Problem screen, the statement and the
      editor as two tabs: the clock, Submit, the verdict, End and the press
      back to the card. With no connection it says so
- [x] Keep a problem's unsent code and the clock preference on the phone, and
      pause a running clock while the app is in the background
- [x] Reopen a running sitting when the Problem screen opens, where the web
      reads `?sitting=`, and write the phone's rule into `pages.md`
- [x] Ask the claim and the label in a bottom sheet after each attempt, and
      offer the press restoring the last solve
- [x] Revise `pages.md` and `README.md` for code on the phone: the sitting and
      recall rows, the Problem screen's missing editor, and the rejected
      WebView. Name the new screens in `tests/test_pages_inventory.py`

### One look across the pages

The knowledge pages came from learn and the engine pages were built after,
and an audit on 2026-11-11 found them laid out two ways. `pages.md`, A
page's areas, gives the rules each item brings the pages to, on both
clients.

- [x] Read every list as rows in one bordered panel, the whole row the link:
      the modules, the lessons, the problems and the card's own lists. The
      phone draws a card per item on the knowledge screens today
- [x] Give every section one heading component with its count, and every
      panel one ground. The knowledge screens and the engine panels each
      write their own
- [x] Draw every header outside the four readings, and route every page's
      loading, failed and empty through the one component. The queue and
      the exam build their own header and skip it
- [x] Add the section bar and collapsing headings to the long pages: the
      module, a lesson, the lessons and the certifications
- [x] Hold each page's act as one primary press, in the bottom bar on the
      phone, and turn the phone's dialogs into bottom sheets
- [x] Move every word the pages still type inline into `packages/core`,
      the engine pages' titles, intros and empty lines first
- [x] Replace the raw sizes, the hex colours and the flame used for status
      with tokens: the map, the certifications grid, `tones()` and the
      verdict colours

### One look, second pass

An audit on 2026-11-11, after the pass above, still found parts drawn two
ways inside each client. Each item covers both clients.

- [x] Draw every panel with one edge and every list on `PickRow`: the
      archived modules, the card rows, the ladder's rungs, the devices, the
      exam's results, the ready lesson and certification, and the strips
      heading a panel. The phone's Card border and its own panels differ
- [x] Give each press one look per role: the focus press, the raise, the
      primary's size and place, and the phone's acts still outside the
      bottom bar. A press beside an equivalent one carries its icon too
- [x] Draw every selectable chip, link and option one way: the filters and
      the toggle groups, links underlined on hover, a lesson's links as
      links on the phone, and the quiz's two kinds of option tile
- [x] Draw every error, small label, meta line and header note one way,
      and move the words still typed inline into `packages/core`. The web
      shows an error four ways, and the phone its header note three ways
- [x] Bring the rest onto shared parts: the dialogs, the code blocks, the
      badges, the two grid tables, the gaps as tokens, and the phone's
      readings still outside `Loaded`

### The board as the overview

- [x] List the knowledge modules on the board, between the cards in progress
      and the techniques, each as its row on the knowledge home. The board is
      the one page reading every study the user declared
- [x] Draw a module's progress as the bar a card's row draws, on both
      clients: the questions passed against the module's questions
- [x] Hold the focus and Continue on the board, the focus as a reading that
      opens the knowledge home, and open the phone on the Practice tab, as
      the web opens on the board

### One logic across the clients

An audit on 2026-11-11 found the clients each running the same act on their
own: the requests, the form state and the pick of the next press. Each item
moves one piece into `packages/core` with its tests, puts both clients on it,
and removes the drift the audit found.

- [x] Move the sitting's controller into core, with the clock's press: the
      start, pause, resume and end, the touch, and the submission. The web
      keeps touching an ended sitting, and the two pick the clock's press apart
- [x] Move a question's answer state and the press it asks for into core,
      and the claim's send with it. Each client keeps eight fields of state
      and decides next, reveal, grade or submit on its own
- [x] Move the recall trainer's requests and its template menu into core,
      and a card's progress and note. The phone's card has no progress block,
      and the two menus name a missing template differently
- [x] Move an exam's choice and a queue's start by mode into core, with the
      lookup of a certification by its id. The phone offers the reviews
      outside a focus only where the focus is strict, and the web on any
- [x] Move the small helpers both clients repeat into core, and use what
      core already holds: the lessons' sections, closing a section, the
      module grid, a value's cut, the map's opening, and the joined lines

### From use on the phone

The author's first sittings on the phone, on 2026-11-11, found these.

- [x] Show a lesson stop's reading time on both clients, so Read or Later is
      chosen before the lesson opens
- [x] Serve a question between two lesson stops wherever one is left, with
      the shared fixture's lesson case moved to say so
- [x] Build one board per scope for each log, and freeze the phone's tabs out
      of view. Every record rebuilt several boards on every mounted screen
- [x] Give each press in the queue's bottom bar the height every other bar
      press has
- [x] Sync on a pull down the phone's browsing screens, and read their engine
      data again

### A second audit

A second pass on 2026-11-11 compared both clients' screens once more, after
the five moves above. Each item moves one piece into `packages/core` and
removes the difference the pass found.

- [x] Key the web's unsent code to the signed-in user, and delete every draft
      at sign-out. A second account on one browser opened the first's code
- [x] Move a template's view into core. The phone left out the note that a
      form no case checks is read and never recalled
- [x] Move the certifications legend's words into core, and give the web the
      legend the phone draws
- [x] Move a problem's facts into core, and read a retired problem by the
      same facts on both clients. A missing difficulty read on one alone
- [x] Move a lesson's page and whether it is read into core. The title
      fallback differed, and the phone dropped the lessons around a lesson
      with no text
- [x] Move the phone's last literal words into core, read the exam's levels by
      their full names, and offer the signed-in devices from the phone's
      Settings
- [x] Move the phone's knowledge counts onto a clock that moves each minute,
      as the web's do
- [x] Move the knowledge home's rows, its lesson to read and its
      certification to take into core, and Continue's act where nothing is
      ready
- [x] Move starting a card's run and revoking a device into core. The phone
      read a refused start as started, and a refused revoke as revoked
- [x] Move a card's sections, a page's four readings, a device's title and
      the phone's own settings checks into core
- [ ] Offer Copy on a long failing value on the phone, once a clipboard
      module is in the app's build

### Exit
- [ ] Practise questions on the web and the phone against one log, with both
      showing the same state
- [x] Read the inventory with no row `to fix` and no row `web for now`
- [ ] Sit a problem and recall a form on the phone, through the app's keyboard
- [ ] Read the knowledge pages and the engine pages on both clients with no
      part drawn two ways

## Phase 16 — scheduling and mastery

- [ ] Port FSRS replay, the question states and gating into
      `algo_coach.knowledge`, with the shared fixtures passing against it. The
      mastery formula and the scheduler read them on the server, and the
      queues stay in TypeScript
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

## Further developments

Blocks of work not ready for a phase, grouped and unordered. A planned phase is
a block that became ready. A block, or a single item of one, is planned into a
phase once it is clear enough to plan. An item's trigger, where it names one, is
the event that makes the item ready.

### The recognition drill

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

### Exercises for the phone

Exercises that need little typing, and so suit a phone: ordering a solution's
shuffled lines, filling one blank in it, and tracing what it prints. Each
tests less than writing the solution does.

- [ ] Write the design of a short exercise into `log.md`: its own record
      kind, and that mastery never counts it as execution. A reordered line
      is not a solve. Triggered when a phone sitting proves too slow to use
- [ ] Compare tracing with the knowledge module's `output` questions, and
      write into `knowledge.md` whether a traced output is one of them

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

### Docs

- [ ] Read the architecture doc against the code, landing every divergence as
      an item in this file. The goal is not that no divergence exists, since
      the doc is target state. The goal is that no divergence is unknown.
      Triggered when a phase closes
