# Pages

The web app a user practises in: which pages it serves, how the user moves
between them, and the design system every page is built on. Part of the
architecture, and `README.md` is the map.

`flows.md` gives the steps of a flow and their order. This file gives what the
user sees at a step, and which page holds it. `wireframes.md` draws each of
those steps at low fidelity.

## Sections

- **The navigation names four sections: Practice, Problems, Cards and
  Knowledge.** `## The structure` gives the tree both clients hold. Practice
  holds the board, a technique's candidates, a picked problem and the
  sitting. Problems holds the listing of every problem. Cards holds the card
  list, one card, and the recall trainer Phase 11 adds.
  Knowledge holds the knowledge modules of `knowledge.md`: their queues, their
  lessons and their certifications.
- **The scheme switch and the account menu sit at the right of the
  navigation**, apart from the sections, since neither names a page.
- **At phone width the wordmark reads as its flame dot alone, and the
  sections scroll sideways.** Four sections need more width than a phone
  holds beside the switch and the menu. The row scrolls to the marked
  section, so the reader always sees where they are.
- **The account menu names who the session signs in as**, and holds the
  link to the settings, the signed-in devices and the sign-out. The address the
  provider verified names the user, with the engine's own id under it. A user
  no provider linked is named by that id instead, since the dev login mints
  no identity to carry an address.
- **Signed-in devices open a dialog from the account menu**, listing every
  browser and app signed in as the account, by its name and when it was last
  used, with a press to revoke it. A lost phone or a browser left signed in
  elsewhere is cut off there, where its own sign-out cannot reach.
- **The list names the device it is read on**, on both clients, and that row
  signs out rather than revoking. Signing out sends the outbox first, and a
  bare revoke would leave the outbox unsent.
- **A browser is named by its agent's browser and system**, such as Chrome
  on macOS. An app is named by the device name it signed in with.
- **The settings are a page of their own, `/settings`, as on the phone.** The
  page reads as the phone's Settings screen does: the account first, then
  the Study settings, the daily limit on new questions and the exam size.
  A reader of either client then finds a standing choice in the same place.
- **A study setting is a record of the user's log**, so a change on one
  client stands on the other. `knowledge.md` gives the records. The engine's
  address, the device name and the reminder hour are about one phone, and
  stay on the phone's screen alone.
- **Problems is marked on the listing alone.** A picked problem is a step down
  from the board, from a technique or from a card, so Practice stays marked on
  it and the way back names where the pick came from.
- **A signed-in user lands on the board, on both clients.** Every sitting
  starts from a technique the user picks there, Continue starts the next
  queue there, and Phase 18 serves the scheduler's pick on the same page.
- **The board names the cards in progress before the techniques.** A card in
  progress is one
  acquiring or consolidating: a study the user declared and has not finished.
  Ranking techniques by staleness alone can bury such a card. A graduated card
  keeps its run open and is not in progress, since a graduated card is done.
  Each card in progress reads as its row on the cards list does, and opens the
  card.
- **The board then names the unlocked cards not yet started**, by depth, the
  shallowest first. A user with nothing in progress then reads the next study
  the card graph offers, rather than a list of every technique.
- **The board is the overview of the user's practice.** It reads the
  knowledge study first: the focus, Continue and the modules. The cards in
  progress and the techniques follow. A user reads every study they declared
  on one page before picking what to practise.
- **The knowledge part reads from the device's copy**, ahead of the engine's
  answer and without it. The board then works offline as the knowledge home
  does, and a phone opened on a train shows a page that works.
- **The board holds the focus as a reading, with Continue inside its
  panel.** The board names several studies, so a press in the page's bottom
  bar would not say which of them it continues. Continue serves the focus,
  so it sits in the focus's panel, or in a panel of its own where no focus
  is aimed. The panel leaves out the counts line the focus already reads.
- **The focus's other presses stay on the knowledge home**: Strict, Clear and
  the raise. The focus's panel on the board opens the home. Exam stays there
  too, as the home's second way in. A press living on two pages drifts
  apart.
- **Each module on the board reads as its row on the knowledge home**, and
  opens the module, whose way back then names the board. The board offers no
  order press, since ordering the modules belongs to the knowledge home.
- **A row's progress reads as one bar, the same on a card and a module.** A
  card's bar counts the rungs solved, and a module's counts the questions
  passed. A reader then compares two studies by one shape.
- **The listing filters by two things a problem carries: its techniques and
  its difficulty.** The tags it offers are the techniques the listing itself
  holds, and the difficulties are the three a problem can carry: easy, medium
  and hard. A question's level is a different field, as `knowledge.md` gives.
- **A second pick inside one filter widens the list, and the two filters
  narrow each other.** A problem is shown where it carries any tag the user
  picked and sits at any difficulty they asked for. Two techniques ask for
  the problems of either, where a technique and a difficulty ask for the
  problems of both.
- **Each chip counts what pressing it would leave**, so the difficulties
  count what the tags left and the tags count what the difficulties left. A
  count over the whole corpus would offer a chip that returns nothing.
- **Picking a filter moves no row of the page.** The chips keep the order the
  whole listing gives and a fixed width for their count, and the press that
  clears the filters sits in the heading rather than on a line of its own. A
  reader comparing two problems otherwise loses the one they were reading as
  the chips above rewrap.
- **The URL carries the tags, the difficulties and the page**, as `?technique=`,
  `?difficulty=` and `?page=`. A filtered listing is then a link the user can
  keep, and the three are the page's whole state.
- **The listing is read in pages of twenty rows.** Fifty problems already scroll
  past several screens, and a reader picking one compares a handful at a time.
- **Picking either filter returns the listing to its first page.** The page the
  reader was on may hold nothing once the list is narrowed.
- **The listing names no retired problem, and the problem's own URL still
  answers.** A retired problem was never a fair test, so a reader picking one
  to sit is picking a problem the engine refuses to serve. The user's attempts
  on it stay in the log, and a link kept from before the retirement therefore
  opens a page rather than a 404.
- **A retired page says so and serves nothing.** The serving call refuses a
  retired problem, so no statement is shown and no clock starts. The page
  reads as the record of what the user did on that problem.
- **The whole listing is fetched, and a page is a slice of it.** The tags count
  every problem the corpus carries, so a page of rows cannot produce them. The
  API pages the rows instead once the corpus outgrows one request.
- **A section is marked while the user is on a page under it.** A technique and
  a picked problem are steps down from the board, so the board's own section
  stays marked on both.
- **Each page names one way back: the page the user came from.** A rung of a
  ladder is a sitting reached from a card, and the same sitting is reached from
  the board, so the section a page sits in cannot say where the user came from.
- **The sitting names its way back as a press, running or ended.** Leaving a
  sitting's page costs nothing: the clock is the user's to run, and the
  unsent code is kept. The press returns to the page the problem came from:
  the card, the technique, the listing or the board, and names that page. An
  ended sitting stays on the page after the claim, and its press is the
  page's next act.
- **An ended sitting's code is read-only.** The code reads back as it was
  submitted, and the next sitting on the problem opens on the signature, as
  `flows.md` gives. A submission typed over the solve would be a solve read
  rather than recalled.
- **The login page and the privacy policy carry no navigation.** The two pages
  open without a session, and every section behind the menu answers 401 to a
  request carrying none. The policy names the login as its way back, since the
  login is the page it is reached from.

## The pages

| URL | The user | Section |
|---|---|---|
| `/` | continues a card or picks a technique | Practice |
| `/problems` | picks a problem across every technique | Problems |
| `/techniques/:technique` | picks a problem | Practice |
| `/problems/:problem_id` | reads the statement, solves, submits and claims, or reads a retired problem | Practice |
| `/cards` | reads where each card stands, and picks one | Cards |
| `/cards/:slug` | reads a card and reveals its templates | Cards |
| `/cards/:slug/recall` | opens the recall of the template the trainer draws | Cards |
| `/cards/:slug/recall/:template` | reproduces one template from memory | Cards |
| `/knowledge` | continues the next queue, or picks another way in | Knowledge |
| `/knowledge/modules/:module` | reads where each group stands, aims the focus, and starts a filtered queue | Knowledge |
| `/knowledge/queue` | answers one question at a time | Knowledge |
| `/knowledge/exam` | picks a level exam or a certification's, and takes it | Knowledge |
| `/knowledge/lessons` | picks a lesson | Knowledge |
| `/knowledge/lessons/:module/:lesson` | reads a lesson and marks it read | Knowledge |
| `/knowledge/certifications` | reads where each certification stands | Knowledge |
| `/settings` | sets the daily limit and the exam size | none |
| `/login` | signs in | none |
| `/privacy` | reads the privacy policy | none |
| `/gallery` | reads the design system, in development alone | none |

- **A page's path names the record the page serves**, so a reload reaches the
  same page. `README.md` gives how the server answers a path naming no file.
- **A refused sign-in returns to the login page as a code.** The callback is a
  navigation from the provider's site, so a refusal answers with the page that
  explains it. `?refused=` carries a code rather than a sentence, since a
  sentence names the address that was refused and a URL is kept in the
  browser's history.
- **A query parameter names where the user came from.** The picked problem is
  `/problems/:problem_id` whichever page offered it, since Phase 11 opens the
  same problem as a rung of a card's ladder. `?technique=` names the technique
  the pick came from, `?card=` names the card, and `?from=problems` names the
  listing, which holds no record of its own to name. A listing filtered to one
  tag adds that tag as `?technique=`, since picking one tag is drilling for
  that technique as a pick from the board is. The problem's page keeps the
  technique and the card: the way back returns where the pick came from, and
  the claim answers for the card's own technique where a card offered the
  problem.
- **A page loads the record its path names.** The picked problem is read as its
  own record rather than found in the technique's candidates, since a page
  reached from two places would otherwise load a different list at each of
  them.
- **The problem's page holds the statement and the sitting.** The path serves
  the statement and stays, since serving mints nothing, as `log.md` gives. A
  retired problem's path reads as its record and serves nothing.
- **A sitting has no path of its own, and `?sitting=` names it on the
  problem's path.** Before the first clock press or submission no sitting
  exists, so the page's address cannot name one from its first load. The
  page adds the parameter once the sitting is minted, replacing the address
  rather than adding a history entry.
- **A reload reads the sitting `?sitting=` names, running or ended.** A solve
  ends the sitting, and the claim asked after it would otherwise be lost to a
  reload. Without the parameter, a reload finds the sitting the problem has
  running, where one runs.
- **The phone's Problem screen reopens the sitting the problem has running.**
  The phone has no address to carry `?sitting=`, so opening the screen, or
  the app again after it was closed, reads the running sitting with the
  statement. Its own unsent code and its clock come back with it. An ended
  sitting is not reopened, so a claim the sheet left unanswered is not asked
  again, where a reload of the web's page asks it again. The attempts it
  leaves count under the problem's own techniques, as a skipped claim's do.
- **The problem's page reads the difficulty, the techniques, the counts the
  user reached on the problem, and the cards** in one line above the
  statement, and the statement is the page's body.
- **A problem's unsent code, the clock preference and the chosen colour scheme
  are the state the browser keeps.** The code is stored under the problem's id
  with the moment it was typed, so a reload restores what the user typed, and
  the next sitting on the problem can carry it as `flows.md` gives. The clock
  preference and the scheme are about how the user practises at this machine,
  and a store holding them would carry them between machines nobody asked it
  to join. Every other reading is fetched from the API at each load.
- **The unsent code is keyed to the signed-in user, and signing out deletes
  it.** A browser can be shared between two accounts. The code a user has not
  submitted is that user's own, and the next account to sign in must not open
  it. The phone keys its copy the same way.
- **The knowledge module keeps a copy of its content and of the user's log in
  the browser too**, in IndexedDB. `knowledge.md` gives why the native app
  and the web app keep the same copy.
- **The recall's path names the template by its authored slug**, and the drawn
  path sends the browser to it. A reload then asks for the same form, and a
  user who means to practise one form reaches it by name. `flows.md` gives why
  naming the template costs the recall nothing.

## The knowledge pages

The pages of the Knowledge section. `knowledge.md` gives the rules each page
applies, and `packages/core` computes every label and count the pages show.
The native app serves the same acts, as `README.md` requires of the two
platforms.

- **The knowledge home asks for one act: Continue.** Continue starts the next
  queue. The line under the press counts the reviews due and the new
  questions left today, in the words the phone shows.
- **The home offers Exam as a second way in, at a lower weight.** A filtered
  queue starts from a module's page instead, where the groups it can serve
  are already drawn.
- **The home's header links the lessons and the certifications.** The two
  pages are destinations rather than acts, so each reads as a link, and the
  phone reaches them from its top bar.
- **The home names the focus above Continue, with three presses**: clear the
  focus, switch it between strict and relaxed, and raise today's limit.
  Clearing asks first, since aiming a focus again takes several presses on a
  module's page, as archiving a module asks first. A strict focus names the
  reviews waiting outside it, and a press serves them as a review queue.
- **The home's focus opens what the focus covers.** A focus on a module, a
  topic or a subtopic opens the module's map, centred on the subtopic or the
  topic the focus names. The map draws the focus in the flame, so the reader
  sees where the focus sits among its prerequisites. A certification's focus
  opens the certification's conditions. The web names the map tab as
  `?tab=map` on the module's path.
- **The home names a lesson ready to read and a certification ready for its
  exam**, each as a link above the focus. Each link is the next step the
  rules would take, and a reader who never opens the lessons still meets it.
- **The modules read below as rows, one per module not archived.** A row names
  the group next up with its passed share, and the reviews due, and opens the
  module's page. A paused module says so on its row.
- **The home reads the reviews ahead below the modules**: a column per
  learning day for fourteen days, `knowledge.md` giving what each counts. The
  count is printed on today and on the busiest day alone. Hover on the web, or
  a press on the phone, names any other day.
- **The forecast reads neutral, with today in ink.** A load owed is not
  progress, so it carries no flame. The forecast asks for no act, so it sits
  below the rows the home's act and its modules need.
- **The focus panel names when the focus is reached**, at the daily limit and
  at the user's own pace, on both clients. `knowledge.md` gives how each date
  is projected. The line is gone once the focus is reached.
- **The home raises today's limit and never sets the daily limit.** A raise
  answers today's practice, so the home offers it beside the focus. The daily
  limit is a standing choice, set on the settings page.
- **The home lists the modules in the user's order, and a row moves up or
  down on a press.** The phone drags a row instead. `knowledge.md` gives why
  one order holds on every device.
- **A module's page reads each topic as a panel of subtopics by level.** Each
  group reads as covered, open, locked or holding no questions.
- **The start sheet opens on four scopes, on both clients**: a group's cell,
  a subtopic's name, Start beside a topic, and Start beside the module. The
  press names the scope, and a group also names its level. The sheet adds
  the kind and the due flag, and Start counts what the choices leave.
- **Each scope is the natural drill at its depth.** The sheet narrows a scope
  and never widens one, so a scope no press opens is a drill nobody can
  start.
- **The start sheet replaces a screen of choices.** A screen of its own drew
  the module's groups a second time, beside the module's page that draws them
  already.
- **The press that opens the sheet reads Start.** Practice names the board's
  section on the web, and one word naming two places would send a reader to
  the wrong one.
- **The module's page is one screen on both clients**, as `## The
  structure` gives. The two clients read the same numbers from
  `packages/core`, so the difference is the layout alone.
- **The module's page aims the focus and sets the module's status.** The focus
  is aimed at the module, a topic or a subtopic, by a press of its own. A
  subtopic's row carries a Focus press, since its name opens the sheet.
  Starting a queue from the sheet moves no focus, so one drill does not
  retarget Continue. The status is active, paused or archived. A status
  press asks before it archives, since an archived module leaves the home.
- **Exam opens on the focus**, on either client, as `knowledge.md` gives. The
  focus is a record of the log, so a focus aimed on the phone opens the same
  exam on the web.
- **The queue's path is `/knowledge/queue`, and `?mode=` names the queue**:
  next, review or filtered. A filtered queue's URL carries the sheet's
  choices too: `?module=`, `&topic=`, `&sub=`, `&level=`, `&kind=` and
  `&due=`.
- **A reload starts a queue of the same mode again**, a filtered queue on the
  choices its URL carries. The answers given before the reload are in the
  log already, so the next pick reads them. The web then holds one reload
  rule for its three queues.
- **A filtered queue's URL is a link to that drill.** It writes no record,
  so the choices reach no other device.
- **A choice naming content the store no longer holds degrades**, as a focus
  does. An unknown topic keeps the module, an unknown subtopic keeps the
  topic, and an unknown module returns to the home.
- **A reload of an exam returns to the exam's page**, which opens on the
  focus. An exam's sample is drawn at its start, so a second draw would be a
  different exam.
- **A reload loses the count and the score of the queue it ended.** The phone
  holds a running queue in memory alone, so a killed app loses the same. A
  copy of the running queue kept in the browser would make one client keep
  what the other loses.
- **The queue serves one question at a time, and the page asks for one act at
  a time.** An unanswered question asks for the answer. An answered one reads
  its verdict and the explanation, and Next is the act.
- **An answered question offers its detail on a press**: how it works, the
  example, the pitfalls, the version notes and the diagram, each where the
  question carries one.
- **The detail links the lessons teaching the question, and names each one
  already read.** A reader then knows before opening a lesson whether it is
  new. A lesson is marked read only on the lesson itself, since a mark given
  from a link records a reading that never happened.
- **A lesson the queue offers is a stop in the queue**, on both clients: the
  lesson's title, its reading time, why it is offered, and Read and Later as
  its presses. The reading time lets the reader choose between Read and Later
  before opening the lesson. Read
  opens the lesson over the running queue, with its minutes, Mark read and
  its links to other lessons. Closing the lesson returns to the queue, and
  so does Mark read.
- **Reading a lesson ends no queue.** The web opens the lesson in a dialog
  over the queue, and the phone opens it as a screen above the queue. A
  lesson an answer's detail links to opens the same way, so a reader never
  loses a running queue to a link.
- **An open question reveals its key on a press.** The user then ticks the
  points recalled, the traps fallen into, and whether they said anything else
  wrong. `knowledge.md` gives the grade the ticks make.
- **A keyboard answers the queue.** A digit picks an option, and Enter submits
  or moves to the next question. A reader at a keyboard answers faster than by
  pointer.
- **The phone types a `short` reply on a keyboard of the app's own, and the
  system keyboard never opens.** Two rows of symbols sit above the digits and
  the letters, so a reply needs no layer. A layer holds the rare symbols and
  `True`, `False` and `None`, behind a key that names it.
- **Stop ends the queue and stores its stint**, and the page reads a summary
  of the answers given. Leaving the queue through the navigation stops it the
  same way. A closed tab stores no stint, and the answers given stay.
- **An exam runs on the exam's page**, after its choices: a level exam's
  module, level and size, or a certification's rule, with `?cert=` naming
  the certification. The sample is drawn at the start and held by the page
  alone, so a reload returns to the choices.
- **An exam stores its answers together at its end**, as the phone does. An
  exam stopped before its last question is stored as not passed. An exam in a
  closed tab leaves no record.
- **The lessons page lists each module's lessons in order**, each row naming
  whether the lesson is locked, ready or read, and its minutes. A row opens
  the lesson, a locked one included, since reading early skips nothing.
- **A lesson's page reads its text, and Mark read is the act.** A read lesson
  offers Mark unread instead. The lessons the text links to open on the same
  page.
- **Mark read closes the lesson and returns to the page it was opened from.**
  Marking it read is the last act the lesson asks for, so a reader left on
  the page would press back anyway. Mark unread stays on the page, since a
  reader resetting a lesson is about to read it again.
- **The certifications page reads each module as a grid of scopes by level.**
  Each cell reads as earned, lapsed, ready for its exam or not yet. A cell
  opens the certification's four conditions, and offers the exam once the
  other three hold.
- **A legend above the grids names what each cell's shape stands for**, on
  both clients. A cell draws its state as an icon, and an icon nobody named
  has to be learned by opening cells one by one.

## The structure

Both clients hold one tree of sections and pages. A platform draws the tree
its own way, and holds the same pages under the same sections.

```
Practice      the board, a technique, a picked problem, a sitting
Problems      the listing, a picked problem
Cards         the list, a card, a recall
Knowledge     the home
                a module: its groups, its map, the start sheet
                a queue, an exam
                the lessons, a lesson
                the certifications, a certification's conditions
Account       the settings, the signed-in devices, the sign-out
```

- **The four sections are the destinations both clients name.** The web
  names them in its top bar. The phone names them as bottom tabs, and shows a
  tab once the phone holds a page under it. The phone then holds a subset of
  the tree rather than a tree of its own.
- **Account sits apart from the sections on both clients.** The web opens it
  from the account menu, and the phone from its top bar. Account holds the
  settings, the signed-in devices and the sign-out, since none of the three is
  a place to practise.
- **A section's root is the only page the navigation reaches.** Every other
  page is a step down with one way back, as `## Sections` gives. A shortcut
  from the navigation to a page deeper in the tree would give that page two
  ways in, and the way back could name only one.
- **The Knowledge home links its lessons and its certifications**, and a
  module row opens the module. The lessons, the certifications and every
  module are then steps down from the home on each client.
- **A module's page holds its groups and its map.** The groups read as a
  table of subtopics by level, and the map draws the prerequisite graph. The
  two are tabs of the page on both clients, since the map wants the page's
  whole width.
- **A module's focus, status and start sheet sit on the module's page.** The
  home's module row opens the module, and offers nothing else.
- **No page shows every module's groups at once.** The home names each
  module's next group and its reviews, and a module's page holds its groups.
  A page summing every module would be a second way to read the same groups.
- **The platform decides how the tree is drawn.**
  - Navigation: a top bar on the web, bottom tabs on the phone.
  - The way back: the browser's and the header's link on the web, the
    system's and the header's on the phone.
  - An overlay: a dialog on the web, a bottom sheet on the phone.
  - Two parts of one page: side by side in a wide window, stacked or tabbed in
    a narrow one.

## The two clients

Every screen either client holds, in one inventory. `README.md` gives the
rule: a platform may change how a thing looks and how it is used, and never
what it offers. The inventory is the list both clients build to.

- **Each row is one screen or one act**, with where it lives on the web and
  on the phone. `none` marks a client that does not hold it.
- **A row's status is one of six.**
  - `same`: both clients offer it.
  - `by platform`: both offer it, and the interaction differs. The row
    gives its reason.
  - `web for now`: held on the web alone until a named trigger moves it to
    the phone too. The list under the tables names each trigger.
  - `web only` and `phone only`: held on one client for good, for a reason
    the list gives.
  - `to fix`: the clients offer different things, and the list under the
    tables names the change.
- **A planned screen counts as held.** A screen `pages.md` gives and the web
  does not serve yet is listed on the web, so the phone is compared with what
  the web will offer.
- **`tests/test_pages_inventory.py` holds the screens table to the code.**
  Each web route and phone screen file names its row there, and a row's phone
  column reads `none` exactly where no phone screen holds it. A screen added
  without its row fails the suite.

### Screens

| Screen | Web | Phone | Status |
|---|---|---|---|
| The landing page | the board | the Practice tab | same |
| The board | `/` | the Practice tab | same |
| A technique's problems and cards | `/techniques/:technique` | Technique | same |
| The problem listing | `/problems` | the Problems tab | same |
| A picked problem's record and statement | `/problems/:problem_id` | Problem | same |
| A sitting | `/problems/:problem_id` | Problem, its Code tab | by platform |
| The cards | `/cards` | the Cards tab | same |
| A card's trigger, brief and templates | `/cards/:slug` | Card | same |
| A card's ladder and probes | `/cards/:slug` | Card | same |
| The press starting a card's run | `/cards/:slug` | Card, its bottom bar | same |
| A recall | `/cards/:slug/recall/:template` | Recall, from Card | same |
| The knowledge home | `/knowledge` | Home | same |
| A module | `/knowledge/modules/:module` | Module | same |
| The start sheet | a dialog on the module page | a sheet on Module | same |
| A queue | `/knowledge/queue` | the quiz screen | same |
| A lesson a queue offers | a stop opening the lesson over the queue | a stop opening the lesson screen | same |
| A level exam's choices | `/knowledge/exam` | Exam | same |
| An exam and its results | `/knowledge/exam` | the quiz screen | by platform |
| The lessons | `/knowledge/lessons` | Lessons | same |
| A lesson | `/knowledge/lessons/:module/:lesson` | Lesson | same |
| The certifications | `/knowledge/certifications` | Certifications | same |
| A certification's conditions | a dialog on the certifications and the map | a sheet on Certifications and Map | same |
| The settings | `/settings` | Settings | same |
| The signed-in devices | a dialog from the account menu | a screen from the account menu | same |
| The login | `/login` | Login | same |
| The privacy policy | `/privacy` | Privacy, from Login and Settings | same |
| The gallery | `/gallery`, in development | none | web only |

### Acts

| Act | Web | Phone | Status |
|---|---|---|---|
| Continue | the home | Home | same |
| Review what a strict focus leaves out | the home's counts line | Home's counts line | same |
| Raise today's limit | the focus panel and a queue | the focus card and a queue | same |
| Clear the focus, or make it strict | the focus panel | the focus card | same |
| Aim the focus at a module | the module page | Module | same |
| Aim the focus at a topic | the module page | Module | same |
| Aim the focus at a subtopic | the module page | Module, its groups and its map | same |
| Aim the focus at a certification | a certification's conditions | a certification's sheet | same |
| Start a filtered queue on a group | a module page cell | a Module cell | same |
| Start a filtered queue on a subtopic | the module page | Module, its groups and its map | same |
| Start a filtered queue on a topic or a module | the module page | Module | same |
| Order the modules | up and down presses | a drag | by platform |
| Pause, resume or archive a module | the module page | Module | same |
| Restore an archived module | the settings page | Settings | same |
| Open a lesson ready to read, or a certification ready for its exam | the home | Home | same |
| Mark a lesson read or unread | the lesson page | Lesson | same |
| Set the daily limit and the exam size | the settings page | Settings | same |
| Set the exam size for one exam | the exam page | Exam | same |
| Type a `short` reply | the browser's keyboard | the app's keyboard | by platform |
| Read the sync's state, and sync now | the settings page | Settings, and Home's footer | same |
| Sign out, naming unsent records | the account menu and the settings page | the account menu and Settings | same |
| Revoke a signed-in device | the signed-in devices | the signed-in devices | same |
| Choose the colour scheme | the switch in the navigation | Settings | by platform |
| Set the engine's address, the device name or the reminder hour | none | Settings | phone only |

- **The phone's sitting holds the statement and the editor as two tabs**,
  under one bar holding the clock, its press and End. The editor stays
  mounted under the statement, so a switch keeps what was typed. The first
  clock press or submission mints the sitting, named by the phone's device
  name, and an ended sitting's press returns to the page the problem came
  from. The phone keeps a problem's unsent code and the clock preference in
  its own copy, as the browser keeps them, and signing out deletes the code
  with the rest of the copy. The app going to the background pauses a
  running clock, and returning resumes only that pause, as a hidden page
  does on the web.
  Once the sitting ends, a sheet from the bottom asks the claim and the
  label of each attempt in turn, as the web's dialog does, and a press under
  the editor restores the last solve, which the attempts then report. The
  sitting is `by platform` for its reopening alone, which the bullet on the
  Problem screen gives.
- **The phone's Recall screen types the form through the app's keyboard**,
  into the editor `README.md` gives. The editor's pad adds enter, indent and
  dedent, a row of the names the file declares, narrowed to the word being
  typed, and a layer of Python's keywords. Its line keys move or duplicate a
  line, and select the block around the caret by indentation, wider on each
  press, so indent and dedent move the block whole. The editor draws an
  indent level two characters wide while the file keeps four, and wraps a
  long line under its own indent. A phone fits some forty characters, where
  a median canonical's widest line is fifty-five. A press beside Run hides
  the keyboard, and the editor then holds some twenty lines, where a median
  canonical is eighteen. A key carries a keyword or a name the file
  declares, never a library name or a line of a form, as `flows.md` gives.
  The screen opens from a template's press on Card, and a drawn recall opens
  beside a run, as on the web. A menu switches between the card's templates,
  where the web's page holds the same menu.
- **The phone's Problems tab reads the listing as the web's page does.** A
  row opens the phone's Problem screen, which reads the record and the
  statement. The filters live in the tab while it is open, since the phone
  has no URL to keep them in.
- **The phone opens on the Practice tab, as the web opens on the board.** The
  board's knowledge part serves from the phone's own copy, so the first page
  works without a connection.
- **Every technique on the board opens the technique's page, whatever number
  of cards teach the technique.** A row opening a card where one card teaches
  the technique would make one press land on two kinds of screen.
- **A technique's page lists its cards, then its problems, on both clients.**
  The cards are those teaching the technique or a narrower one, each as its
  row on the cards list reads. A row carries the card's progress and its
  recall, where a link carries the title alone.
- **A technique no card teaches lists its problems alone.** The board lists
  every technique a served problem carries, and a technique can carry
  problems before any card teaches it.
- **A problem's row on the Technique screen opens the phone's Problem
  screen.** The screen reads the problem's record: its title, difficulty,
  techniques, the counts the user reached on it, and its cards, then the
  statement. Serving the statement mints nothing, so the phone reads a problem
  as the web does.
- **The phone's card reads its ladder and its probes as the web's does.** A
  rung and a probe each open the phone's Problem screen, named by the card,
  and the sitting it opens returns to that card.
- **The phone starts a card's run from the bar at the bottom of Card.** The
  run is the card's act until one is open, and the note above the press
  says the ladder counts from it. Starting draws the probes and opens the
  run on both clients, and the sittings it counts are sat on either. Once a
  run is open the bar holds the next rung, and the run's progress and its
  recall read at the top of the card, as on the web.
- **The phone reads the board and the cards from the engine and keeps no
  copy.** With no connection the Practice tab, the Cards tab and each screen
  under them say so. The knowledge copy exists so a
  queue picks offline, and reading a card picks nothing.
- **Pulling a list down on the phone syncs.** The knowledge log is sent and
  received at once, and a screen reading the engine reads it again. A phone
  has no reload, and a reader pulls to see the records another device wrote.
- **The privacy policy is one text in `packages/core`, read on both
  clients.** The web serves it at `/privacy`, which the providers' consent
  screens name. The phone holds it as a screen opened from Login and
  Settings, so it reads before any sign-in and with no connection.
- **The gallery is web only.** It is a tool for whoever styles the web.
- **An exam runs on its own page on the web and on the quiz screen on the
  phone.** The web's exam page holds its sample in memory, so a reload
  returns to its choices without discarding a record. The phone has no
  reload, and its quiz screen runs every queue and exam.
- **Ordering by drag is the phone's, and up and down presses are the
  web's.** A drag needs a long press, which a pointer does not hold well.
- **A `short` reply is typed on the app's keyboard on the phone.** The web is
  read at a physical keyboard, which holds every symbol on its keys. The
  phone's system keyboard hides them, and its suggestion strip completes words.
- **The phone chooses its colour scheme in Settings, from System, Light and
  Dark.** System follows the phone's own setting, and is the default. The web
  holds a light and dark switch in its navigation, where a reader at a desk
  reaches it. The phone keeps the choice on the device and the web keeps it in
  the browser, since the choice is about the screen rather than the account.
- **The engine's address, the device name and the reminder hour are
  phone only.** Each one is about one phone, and the web reaches the engine
  it was served from.

### To fix

A row marked `to fix` is listed here with what holds now and the change it
needs. The audit of 2026-11-10 compared every knowledge row marked `same`
with the other client's code, and both clients were brought together on each
difference it found. No row is marked `to fix` today.

## A page's areas

- **A page carries a header and a body.** The header holds the way back, the
  title, and the one line that identifies what the title names, such as the
  technique a card teaches.
- **The header reads in every reading of the page**, loading and failed
  included. A page whose header waits for its record leaves a reader on a
  failed load with no title and no way back.
- **Each part of a page is one shared component per client**: the header,
  the four readings, a row, a section's heading and its panel. Every page
  uses it, the knowledge pages and the engine pages alike. A part copied
  into one page drifts from the rest, and the two families of pages read as
  two apps.
- **One page asks for one act.** The board asks what to practise next, a card in
  progress or a technique. The candidates ask for a problem, and the sitting
  asks for a submission. The clock's press sits in the bar as a control, not as
  an act the page waits on. A page offering two acts of equal weight makes the
  user choose before the flow asks them to.
- **The act reads as the page's one primary press.** The phone holds it in
  the bar at the bottom of the screen, where the thumb rests, and the web
  holds it in the page. A second way in reads at a lower weight, as the
  knowledge home's Exam does beside Continue.
  The board is the exception, since it holds several studies, and its
  Continue sits in the focus's panel, as `## Sections` gives.
- **The body reads in one column of at most 56rem.** A line of prose wider than
  that is hard to track back to the next line's start.
- **The sitting is the exception, and reads in two columns.** The statement and
  the editor sit side by side, and a reading column is too narrow to hold both.
- **Every page but the sitting reads at phone width.** A sitting on the web
  wants a wide window, and a narrow one stacks the statement above the editor
  rather than shrinking both. The phone's sitting holds the two as tabs
  instead, as `## The two clients` gives.
- **A page has four readings: loading, failed, empty and the content.** One
  component renders the first three, so a page that failed reads the same
  whichever request failed.
- **A bordered chip is a control, and a destination reads as a link.** The
  listing's filters are chips, since a press toggles one. The techniques the
  board offers are names that underline on hover, since a press opens the
  technique. Two shapes that look alike and act differently teach a reader the
  wrong thing about both.
- **A list of picks reads as rows, and the whole row is the link.** The board's
  techniques, a technique's problems and the cards are each such a list. A
  table spreads one pick over four columns, and the reader then joins the
  columns back together to judge the pick.
- **The cards list reads the card graph by depth.** The roots come first, and
  each depth is a section under its own heading. A row names its card's
  technique, its card state, and the required cards a locked card waits on. A
  reader then sees where to start and what each card opens.
- **The web draws the edges between the rows, and the phone names them on
  each row.** A drawn graph needs a page's width, and the phone's screen holds
  one column. The two clients read the same depths, the same rows and the
  same locks, as `## The two clients` requires.
- **A list split into sections reads each section under a plain heading with
  its count, above a bordered panel of rows.** The board and the cards list
  split their lists the same way, so a reader learns one shape.
- **One record reads as one row wherever it is listed.** A card in progress on
  the board is the same row as on the cards list, so a reader never learns a
  second shape for it.
- **A panel's header strip names a record, and opens it.** A strip that named
  a record and opened nothing would be a dead end.
- **A row's counts read as one cluster at its right**, each count beside the
  word it counts. A row with nothing counted says so in one word, since three
  counts of nothing say less than `never` does.
- **A panel holds what a page carries beside its reading**: a bordered block on
  the card surface. The counts a card run reached and a submission's verdict
  are each one. Every panel carries the same
  border, radius and ground, so a reader tells a panel from the reading by its
  shape alone.
- **A page longer than a screen carries a bar naming its sections.** The bar
  stays at the top of the window while the page scrolls, and it marks the
  section the reader is in. A press on it jumps to that section.
- **The bar scrolls sideways to keep the marked section in view**, as the
  navigation does at phone width. A phone holds two or three of a lesson's
  sections, and a mark the reader cannot see says nothing.
- **An edge of the bar fades where more sections lie past it.** A row cut at
  the screen's edge reads as a row that ends there.
- **At the end of the page the bar marks the last section.** The last section
  is often shorter than the screen, so its heading never reaches the top, and
  the mark would otherwise stay on the section before it.
- **A section pressed on the bar stays marked until the reader scrolls by
  hand.** A jump near the end lands at the end of the page, where the rule
  above would mark the last section rather than the one pressed.
- **A section collapses from its own heading**, and every section is open until
  the reader closes it. The count beside the heading stays readable while the
  section is closed.
- **A section of rows sits in a bordered panel under its heading**, the rows
  edge to edge. The border groups the rows into one list.
- **A section of prose reads bare under its heading.** A code block inside it
  is then the only box on the page. A panel around the prose put a box inside
  a box and cost four characters of a phone's code width.
- **A lesson and a card's brief are cut at their `##` headings**, each heading
  a section of the page. Without a panel, a heading inside a section would
  read as a section of its own, so no section holds one. Text before the first
  heading reads under the brief's own title.
- **Which sections a reader closed is not stored**, in the browser or
  anywhere else, so a reload opens every section again.

## The design system

- **Consistency across pages outranks fitting one page better.** A shape that
  reads one way on one page and another way on the next teaches the reader two
  rules for one thing. A page that wants an exception gets a different layout
  of the shared shapes instead, and a shape changes everywhere or nowhere.

- **The tokens are the only place a colour, a radius, a spacing step, a type
  size or a font family is defined**: `web/src/index.css` on the web and
  `native/src/ui/tokens.ts` on the phone, named by the same roles. Every
  component reads a token. A value set inside one component alone is a design
  no other component follows.
- **The app takes the site's palette and shapes**, so the product reads as one
  thing from the landing page to a sitting. The neutrals, the type, the code
  colours and the verdict colours were already shared. The flame and the
  rounder shapes come from the site.
- **The flame marks the brand, the focus and progress, and nothing else.** The
  wordmark carries a flame dot, the focus ring is its deep shade, and a
  ladder's progress is a thin flame bar. Progress is the study's own rather
  than a verdict, so it reads in the brand. The press a page
  asks for is an ink pill, as the site's navigation press is: a flame press on
  every working page read louder than the page around it. No verdict reads in
  the flame either: its hue sits between wrong and timed out.
- **The knowledge focus reads in the flame**, on the subtopic or the
  module it is aimed at. The focus names the groups the study aims at next,
  so it reads as progress does. A node picked on the map is a selection and
  reads neutral.
- **A state that asks for an act reads neutral.** A certification ready for
  its exam, one that needs a refresh and a lesson ready to read are states
  rather than progress. In the flame each would read as progress made.
- **A recall's pass and fail read in the verdict's colours**, since they are the
  same outcomes: a clean recall in passed, a failed one in wrong. A hinted pass
  and a form never recalled stay grey.
- **A running clock carries a green dot.** The press's label alone left a
  running clock and a stopped one looking alike. The dot has a token of its
  own, since a running clock is not a passed case.
- **Each of a verdict's four outcomes carries a token**: passed, wrong, timed
  out and crashed. One `destructive` token cannot separate a wrong answer from a
  timeout, and the drill loop shows that difference on every failing submission.
- **The type scale is named by the role a page reads a size in**: title,
  heading, body, meta, code and micro. Micro is a chart's smallest label, such
  as a ring's share. A page asking for a size by its role cannot choose a size
  no other page uses.
- **The phone's colours come from the device's Material palette**, and the
  colours that palette holds no role for live in one file of the phone's
  own. A verdict's four outcomes are among them, each apart, as on the web.
- **Code inside a line of prose takes a step below the code role.** The mono
  family has a larger x-height than the sans beside it, so mono set at the code
  role reads larger than the prose around it. The step is its own token.
- **Code reads in one mono family, named as a token.** The editor, a template's
  form and a failing case's arguments are all code, and a reader who sees three
  mono families reads three kinds of thing.
- **A long line of code wraps, and continues under its own indent.** This
  holds for a question's code, a detail's example, a template's form and a
  fenced block whose fence names a language or `output`, on both clients. A
  phone fits some forty characters, and a block scrolled sideways hides the
  end of a line, which is often the part a question asks about. The indent
  keeps the structure readable across the wrap, as the editor does.
- **A wrapped part opens on a dim `↪`, which no copy carries.** Without the
  mark a reader cannot tell a wrap from a new line, and in a question about
  what code prints the difference is the answer. Python has no symbol for a
  wrap the screen adds, and the backslash would read as Python's own line
  joining.
- **`packages/core` cuts the rows, at a column count each client measures.**
  The phone and the web then break a line at the same place. A line breaks
  where VS Code breaks one: at a space, after a comma, a dot or a closing
  bracket, or before an opening bracket. A word is cut only where none of
  those sits near the edge.
- **A copy returns the lines as written.** A wrap is drawn and never copied,
  as in every editor's soft wrap. Code copied with a break at each wrap would
  not run as it was written.
- **A diagram keeps its lines whole and scrolls sideways.** A detail's diagram
  and a fence naming `text` or no language may be drawn in characters, and
  wrapping would break the drawing. A program's output is fenced `output`
  instead, so its long lines wrap as code does.
- **A Mermaid diagram reads as the drawing the seed made, in the page's
  scheme**, scaled to the reading width and never wider than drawn.
  `knowledge.md` `## Diagrams` gives how it is drawn. A source with no drawing
  reads as its text, which a diagram drawn on the device would replace only
  after a second or more.
- **A detail's diagram that is one markdown table alone reads as a table**,
  as a table in a lesson does. A table drawn in characters scrolls sideways on
  a phone, and the reader sees a third of its columns at a time.
- **A markdown table reads as a grid where its columns fit the reading
  width, and as one block per row where they do not, on both clients.** A
  phone is too narrow for most tables of three columns. A grid squeezed to fit
  wraps each cell to a few words a line, and a grid scrolled sideways hides
  its last columns.
- **A table read as blocks opens each row on its first cell, and gives every
  other cell under its header.** A table's first column usually names the
  row, so the name stays beside its values.
- **`packages/core` decides a table's shape**, from the length of each cell's
  text and a column count each client measures in characters of prose. A
  table then reads the same on the phone and in a narrow window on the web.
- **One mapping colours Python wherever it appears.** The editor and a
  template's form read the same mapping from the language's tags to the five
  code tokens, so a form on a card is coloured as the editor colours it. A
  form on a card is rendered from that mapping rather than by mounting an
  editor, which takes no input and would ship the editor to show ten lines.
- **Authored prose reads on these tokens too.** The markdown renderer ships a
  scale and a palette of its own, and each of its variables is bound to a
  token. A document's own title reads at the title role, and its headings at
  the heading role.
- **A link in authored prose that leaves the app carries a `↗` after its
  text, on both clients.** A lesson's links to the Python docs read like its
  links to other lessons, and a reader pressing one leaves the lesson
  unwarned. The web opens such a link in a new tab, and the phone in the
  browser.
- **The web opens in the browser's colour-scheme and carries a switch.** The
  switch writes the chosen scheme to the browser, and a reader who never
  presses it follows their browser for as long as they never press it. No
  store holds the choice, since the choice is about the machine the reader is
  at rather than about the user.
- **Each colour token carries both schemes in one declaration**, and the root
  says which of the two is read. A token declared twice would be a value in
  two places, and the two drift.
- **The neutrals carry a warm cast, and the light ground is paper rather than
  white.** A solver reads a statement for many minutes, and a warm ground is
  easier to sit in front of than white. The dark ground is a warm charcoal for
  the same reason.
- **Every radius is derived from one base**, so a single edit rounds or squares
  the whole app. The base follows the site's rounder panels.
- **A press is a pill**, as on the site. The pill is set once in
  `web/src/index.css`, so the copied button component stays as it ships.
- **The gallery is a page showing every token and every component the pages
  use.** A component restyled there shows every use of it at once.
- **The gallery is built in development alone.** The deployed bundle carries
  neither the gallery nor its examples, so a page written for whoever styles the
  app is never served to a user.

## Rules a page holds, specified elsewhere

- A candidate is offered without its statement, since opening the problem
  serves it (`flows.md`).
- A template's code is hidden until the user reveals it (`content.md`).
- The editor proposes no name from the standard library or from the code already
  typed (`flows.md`).
- A failing submission shows its first failing case whole, at whatever size
  (`flows.md`).
- A card is offered beside a problem, and no sitting requires reading it
  (`flows.md`).
