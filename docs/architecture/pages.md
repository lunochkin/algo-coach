# Pages

The web app a user practises in: which pages it serves, how the user moves
between them, and the design system every page is built on. Part of the
architecture, and `README.md` is the map.

`flows.md` gives the steps of a flow and their order. This file gives what the
user sees at a step, and which page holds it. `wireframes.md` draws each of
those steps at low fidelity.

## Sections

- **The navigation names four sections: Practice, Problems, Cards and
  Knowledge.** Practice holds the board, a technique's candidates, a picked
  problem and the sitting. Problems holds the listing of every problem. Cards
  holds the card list, one card, and the recall trainer Phase 11 adds.
  Knowledge holds the knowledge modules of `knowledge.md`: their queues, their
  lessons and their certifications.
- **The scheme switch and the account menu sit at the right of the
  navigation**, apart from the sections, since neither names a page.
- **At phone width the wordmark reads as its flame dot alone, and the
  sections scroll sideways.** Four sections need more width than a phone
  holds beside the switch and the menu. The row scrolls to the marked
  section, so the reader always sees where they are.
- **The account menu names who the session signs in as**, and holds the
  link to the settings, the signed-in apps and the sign-out. The address the
  provider verified names the user, with the engine's own id under it. A user
  no provider linked is named by that id instead, since the dev login mints
  no identity to carry an address.
- **Signed-in apps open a dialog from the account menu**, listing each native
  app by its device and when it was last used, with a press to revoke it. A
  lost phone is cut off there, where its own sign-out cannot reach.
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
- **A signed-in user lands on the board.** Every sitting starts from a technique
  the user picks there, and Phase 16 serves the scheduler's pick on the same
  page.
- **The board names the cards in progress first.** A card in progress is one
  acquiring or consolidating: a study the user declared and has not finished.
  Ranking techniques by staleness alone can bury such a card. A graduated card
  keeps its run open and is not in progress, since a graduated card is done.
  Each card in progress reads as its row on the cards list does, and opens the
  card.
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
  retired problem, so opening one mints no sitting. The page reads as the
  record of what the user did on that problem.
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
  unsent code is kept. The press returns to the card the problem came from, or
  to the board. An ended sitting stays on the page after the claim, and its
  press is the page's next act.
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
| `/problems/:problem_id` | opens the problem, which serves it, or reads a retired one | Practice |
| `/sittings/:sitting_id` | solves, submits, claims | Practice |
| `/cards` | reads where each card stands, and picks one | Cards |
| `/cards/:slug` | reads a card and reveals its templates | Cards |
| `/cards/:slug/recall` | opens the recall of the template the trainer draws | Cards |
| `/cards/:slug/recall/:template` | reproduces one template from memory | Cards |
| `/knowledge` | continues the next queue, or picks another way in | Knowledge |
| `/knowledge/modules/:module` | reads where each group stands, and aims the focus | Knowledge |
| `/knowledge/questions` | picks the questions a filtered queue serves | Knowledge |
| `/knowledge/queue` | answers one question at a time | Knowledge |
| `/knowledge/exam` | picks a level exam | Knowledge |
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
  that technique as a pick from the board is. The sitting carries the
  technique and the card on: the way back returns where the pick came from, and
  the claim answers for the card's own technique where a card offered the
  problem.
- **A page loads the record its path names.** The picked problem is read as its
  own record rather than found in the technique's candidates, since a page
  reached from two places would otherwise load a different list at each of
  them.
- **Opening a served problem sends the browser to its sitting.** The problem's
  path serves the statement and replaces itself with `/sittings/:sitting_id`,
  so a reload reaches the sitting rather than serving the problem again. A
  retired problem's path reads as its record and serves nothing.
- **The sitting page carries what the picked problem's page carried**: the
  difficulty, the techniques, the counts the user reached on the problem, and
  the cards. Those facts sit in one line above the statement, and the
  statement is the page's body.
- **A problem's unsent code, the clock preference and the chosen colour scheme
  are the state the browser keeps.** The code is stored under the problem's id
  with the moment it was typed, so a reload restores what the user typed, and
  the next sitting on the problem can carry it as `flows.md` gives. The clock
  preference and the scheme are about how the user practises at this machine,
  and a store holding them would carry them between machines nobody asked it
  to join. Every other reading is fetched from the API at each load.
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
- **The home offers two other ways in, at a lower weight: Pick questions and
  Exam.** Pick questions opens the filtered queue's choices, and Exam opens a
  level exam's.
- **The home's header links the lessons and the certifications.** The two
  pages are destinations rather than acts, so each reads as a link, and the
  phone reaches them from its top bar.
- **The filtered queue is named Pick questions on both clients.** The phone
  names it Practice today. On the web Practice names the board's section, and
  one word naming two places would send a reader to the wrong one.
- **The home names the focus above Continue, with three presses**: clear the
  focus, switch it between strict and relaxed, and raise today's limit. A
  strict focus names the reviews waiting outside it, and a press serves them
  as a review queue.
- **The home names a lesson ready to read and a certification ready for its
  exam**, each as a link above the focus. Each link is the next step the
  rules would take, and a reader who never opens the lessons still meets it.
- **The modules read below as rows, one per module not archived.** A row names
  the group next up with its passed share, and the reviews due, and opens the
  module's page. A paused module says so on its row.
- **The home raises today's limit and never sets the daily limit.** A raise
  answers today's practice, so the home offers it beside the focus. The daily
  limit is a standing choice, set in the settings dialog.
- **The home lists the modules in the user's order, and a row moves up or
  down on a press.** The phone drags a row instead. `knowledge.md` gives why
  one order holds on every device.
- **A module's page reads each topic as a panel of subtopics by level.** Each
  group reads as covered, open, locked or holding no questions. A press on a
  group starts a filtered queue over that subtopic.
- **The module's page joins the phone's Map and Stats.** A wide window holds
  the groups and the counts per level together. The two clients read the same
  numbers from `packages/core`, so the difference is the layout alone.
- **The module's page aims the focus and sets the module's status.** The focus
  is aimed at the module, a topic or a subtopic. The status is active, paused
  or archived. A status press asks before it archives, since an archived
  module leaves the home.
- **Pick questions and Exam open on the user's last filters**, on either
  client. The filters are a record of the user's log, as `knowledge.md`
  gives, so a filter chosen on the phone stands on the web.
- **The queue's path is `/knowledge/queue`, and `?mode=` names the queue**:
  next, review, filtered or exam. The filters come from the log, so the URL
  carries the mode alone, as the phone's route does.
- **A reload starts the same queue again.** The answers given before the
  reload are in the log already, so the next pick reads them.
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
- **An open question reveals its key on a press.** The user then ticks the
  points recalled, the traps fallen into, and whether they said anything else
  wrong. `knowledge.md` gives the grade the ticks make.
- **A keyboard answers the queue.** A digit picks an option, and Enter submits
  or moves to the next question. A reader at a keyboard answers faster than by
  pointer, and the phone offers no keyboard to match.
- **Stop ends the queue and stores its stint**, and the page reads a summary
  of the answers given. Leaving the queue through the navigation stops it the
  same way. A closed tab stores no stint, and the answers given stay.
- **An exam stores its answers together at its end**, as the phone does. An
  exam stopped before its last question is stored as not passed. An exam in a
  closed tab leaves no record.
- **The lessons page lists each module's lessons in order**, each row naming
  whether the lesson is locked, ready or read, and its minutes. A row opens
  the lesson, a locked one included, since reading early skips nothing.
- **A lesson's page reads its text, and Mark read is the act.** A read lesson
  offers Mark unread instead. The lessons the text links to open on the same
  page.
- **The certifications page reads each module as a grid of scopes by level.**
  Each cell reads as earned, lapsed, ready for its exam or not yet. A cell
  opens the certification's four conditions, and offers the exam once the
  other three hold.

## A page's areas

- **A page carries a header and a body.** The header holds the way back, the
  title, and the one line that identifies what the title names, such as the
  technique a card teaches.
- **One page asks for one act.** The board asks what to practise next, a card in
  progress or a technique. The candidates ask for a problem, and the sitting
  asks for a submission. The clock's press sits in the bar as a control, not as
  an act the page waits on. A page offering two acts of equal weight makes the
  user choose before the flow asks them to.
- **The body reads in one column of at most 56rem.** A line of prose wider than
  that is hard to track back to the next line's start.
- **The sitting is the exception, and reads in two columns.** The statement and
  the editor sit side by side, and a reading column is too narrow to hold both.
- **Every page but the sitting reads at phone width.** A sitting needs a
  keyboard and a wide window, and a narrow window stacks the statement above the
  editor rather than shrinking both.
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
- **The cards list groups cards by the technique each is a kind of.** A card
  on `knapsack` sits under the `dynamic-programming` heading and names its own
  technique on its row. A reader looking for DP then finds every DP card in
  one place.
- **A list split into sections reads each section under a plain heading with
  its count, above a bordered panel of rows.** The board and the cards list
  split their lists the same way, so a reader learns one shape.
- **One record reads as one row wherever it is listed.** A card in progress on
  the board is the same row as on the cards list, so a reader never learns a
  second shape for it.
- **A panel's header strip names a record, and opens it.** A family on the
  cards list opens its technique. A strip that named a record and opened
  nothing would be a dead end.
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
- **A section collapses from its own heading**, and every section is open until
  the reader closes it. The count beside the heading stays readable while the
  section is closed.
- **A section's body sits in a bordered panel under its heading**, prose padded
  and rows edge to edge, on a long page as on a list. A card's brief carries
  headings of its own, and the panel keeps them inside one section.
- **Which sections a reader closed is not stored**, in the browser or
  anywhere else, so a reload opens every section again.

## The design system

- **Consistency across pages outranks fitting one page better.** A shape that
  reads one way on one page and another way on the next teaches the reader two
  rules for one thing. A page that wants an exception gets a different layout
  of the shared shapes instead, and a shape changes everywhere or nowhere.

- **The tokens in `web/src/index.css` are the only place a colour, a radius, a
  spacing step, a type size or a font family is defined.** Every component reads
  a token. A value set inside one component alone is a design no other component
  follows.
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
  heading, body, meta and code. A page asking for a size by its role cannot
  choose a size no other page uses.
- **Code inside a line of prose takes a step below the code role.** The mono
  family has a larger x-height than the sans beside it, so mono set at the code
  role reads larger than the prose around it. The step is its own token.
- **Code reads in one mono family, named as a token.** The editor, a template's
  form and a failing case's arguments are all code, and a reader who sees three
  mono families reads three kinds of thing.
- **One mapping colours Python wherever it appears.** The editor and a
  template's form read the same mapping from the language's tags to the five
  code tokens, so a form on a card is coloured as the editor colours it. A
  form on a card is rendered from that mapping rather than by mounting an
  editor, which takes no input and would ship the editor to show ten lines.
- **Authored prose reads on these tokens too.** The markdown renderer ships a
  scale and a palette of its own, and each of its variables is bound to a
  token. A document's own title reads at the title role, and its headings at
  the heading role.
- **The app opens in the browser's colour-scheme and carries a switch.** The
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
