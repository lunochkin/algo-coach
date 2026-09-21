# Pages

The web app a user practises in: which pages it serves, how the user moves
between them, and the design system every page is built on. Part of the
architecture, and `README.md` is the map.

`flows.md` gives the steps of a flow and their order. This file gives what the
user sees at a step, and which page holds it. `wireframes.md` draws each of
those steps at low fidelity.

## Sections

- **The navigation names three sections: Practice, Problems and Cards.**
  Practice holds the board, a technique's candidates, a picked problem and the
  sitting. Problems holds the listing of every problem. Cards holds the card
  list, one card, and the recall trainer Phase 11 adds.
- **Problems is marked on the listing alone.** A picked problem is a step down
  from the board, from a technique or from a card, so Practice stays marked on
  it and the way back names where the pick came from.
- **A signed-in user lands on the board.** Every sitting starts from a technique
  the user picks there, and Phase 15 serves the scheduler's pick on the same
  page.
- **The listing filters by the techniques a problem carries**, and the tags it
  offers are the techniques the listing itself holds. A problem is shown where
  it carries any tag the user picked, so a second tag widens the list rather
  than narrowing it to the problems carrying both.
- **The tags picked and the page are in the URL**, so a filtered listing is a
  link the user can keep. The two are the page's whole state.
- **The listing is read in pages of twenty rows.** Fifty problems already scroll
  past several screens, and a reader picking one compares a handful at a time.
- **Picking a tag returns the listing to its first page.** The page the reader
  was on may hold nothing once the list is narrowed.
- **The whole listing is fetched, and a page is a slice of it.** The tags count
  every problem the corpus carries, so a page of rows cannot produce them. The
  API pages the rows instead once the corpus outgrows one request.
- **A section is marked while the user is on a page under it.** A technique and
  a picked problem are steps down from the board, so the board's own section
  stays marked on both.
- **Each page names one way back: the page the user came from.** A rung of a
  ladder is a sitting reached from a card, and the same sitting is reached from
  the board, so the section a page sits in cannot say where the user came from.
- **The sitting names no way back.** A sitting ends on the End press rather
  than on leaving the page, so a link reading as the way out would end nothing.
  The navigation is the way off the page.
- **The login page and the privacy policy carry no navigation.** The two pages
  open without a session, and every section behind the menu answers 401 to a
  request carrying none. The policy names the login as its way back, since the
  login is the page it is reached from.

## The pages

| URL | The user | Section |
|---|---|---|
| `/` | picks a technique | Practice |
| `/problems` | picks a problem across every technique | Practice |
| `/techniques/:technique` | picks a problem | Practice |
| `/problems/:problem_id` | reads the pick and starts the sitting | Practice |
| `/sittings/:sitting_id` | solves, submits, claims | Practice |
| `/cards` | picks a card | Cards |
| `/cards/:slug` | reads a card and reveals its templates | Cards |
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
  listing, which holds no record of its own to name. The sitting carries the
  technique and the card on: the way back returns where the pick came from, and
  the claim answers for the card's own technique where a card offered the
  problem.
- **A page loads the record its path names.** The picked problem is read as its
  own record rather than found in the technique's candidates, since a page
  reached from two places would otherwise load a different list at each of
  them.
- **A sitting's unsent code and the chosen colour scheme are the state the
  browser keeps.** The code is stored under the sitting's id, so a reload
  during a sitting restores what the user typed. Every other reading is fetched
  from the API at each load.
- **The pages Phase 11 adds are deferred to Phase 11**, which writes its flows
  before it builds them: starting a card run, the ladder on a card, and the
  recall trainer.

## A page's areas

- **A page carries a header and a body.** The header holds the way back, the
  title, and the one line that identifies what the title names, such as the
  technique a card teaches.
- **One page asks for one act.** The board asks for a technique, the candidates
  ask for a problem, and the picked problem asks for the press that starts the
  clock. A page offering two acts of equal weight makes the user choose before
  the flow asks them to.
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
- **A list of picks reads as rows, and the whole row is the link.** The board's
  techniques, a technique's problems and the cards are each such a list. A
  table spreads one pick over four columns, and the reader then joins the
  columns back together to judge the pick.
- **A row's counts read as one cluster at its right**, each count beside the
  word it counts. A row with nothing counted says so in one word, since three
  counts of nothing say less than `never` does.
- **A panel holds what a page carries beside its reading**: a bordered block on
  the card surface. The counts a card run reached, the press that starts a
  sitting and a submission's verdict are each one. Every panel carries the same
  border, radius and ground, so a reader tells a panel from the reading by its
  shape alone.
- **A page longer than a screen carries a bar naming its sections.** The bar
  stays at the top of the window while the page scrolls, and it marks the
  section the reader is in. A press on it jumps to that section.
- **A section collapses from its own heading**, and every section is open until
  the reader closes it. The count beside the heading stays readable while the
  section is closed.
- **Which sections a reader closed is not stored**, in the browser or
  anywhere else, so a reload opens every section again.

## The design system

- **The tokens in `web/src/index.css` are the only place a colour, a radius, a
  spacing step, a type size or a font family is defined.** Every component reads
  a token. A value set inside one component alone is a design no other component
  follows.
- **The palette carries no brand hue.** The pages show code, prose and verdicts,
  and colour carries meaning on the verdict alone, so a brand hue would compete
  with the colours a verdict is read by.
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
  the whole app.
- **The gallery is a page showing every token and every component the pages
  use.** A component restyled there shows every use of it at once.
- **The gallery is built in development alone.** The deployed bundle carries
  neither the gallery nor its examples, so a page written for whoever styles the
  app is never served to a user.

## Rules a page holds, specified elsewhere

- A candidate is offered without its statement, since the clock starts when the
  statement is served (`flows.md`).
- A template's code is hidden until the user reveals it (`content.md`).
- The editor proposes no name from the standard library or from the code already
  typed (`flows.md`).
- A failing submission shows its first failing case whole, at whatever size
  (`flows.md`).
- A card is offered beside a problem, and no sitting requires reading it
  (`flows.md`).
