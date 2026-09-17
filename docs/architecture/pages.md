# Pages

The web app a user practises in: which pages it serves, how the user moves
between them, and the design system every page is built on. Part of the
architecture, and `README.md` is the map.

`flows.md` gives the steps of a flow and their order. This file gives what the
user sees at a step, and which page holds it. `wireframes.md` draws each of
those steps at low fidelity.

## Sections

- **The navigation names two sections, Practice and Cards.** Practice holds the
  board, a technique's candidates, a picked problem and the sitting. Cards holds
  the card list, one card, and the recall trainer Phase 12 adds. Two sections
  cover every page the roadmap plans, so no later page needs a third menu entry.
- **A signed-in user lands on the board.** Every sitting starts from a technique
  the user picks there, and Phase 13 serves the scheduler's pick on the same
  page.
- **A section is marked while the user is on a page under it.** A technique and
  a picked problem are steps down from the board, so the board's own section
  stays marked on both.
- **Each page names one way back: the page the user came from.** A rung of a
  ladder is a sitting reached from a card, and the same sitting is reached from
  the board, so the section a page sits in cannot say where the user came from.
- **The login page and the privacy policy carry no navigation.** The two pages
  open without a session, and every section behind the menu answers 401 to a
  request carrying none.

## The pages

| URL | The user | Section |
|---|---|---|
| `/` | picks a technique | Practice |
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
- **A query parameter names where the user came from.** The picked problem is
  `/problems/:problem_id` whichever page offered it, since Phase 12 opens the
  same problem as a rung of a card's ladder. `?technique=` names the technique
  the pick came from, and the sitting carries it on as the claim's default
  answer.
- **A page loads the record its path names.** The picked problem is read as its
  own record rather than found in the technique's candidates, since a page
  reached from two places would otherwise load a different list at each of
  them.
- **A sitting's unsent code is the only state the browser keeps.** The code is
  stored under the sitting's id, so a reload during a sitting restores what the
  user typed. Every other reading is fetched from the API at each load.
- **The pages Phase 12 adds are deferred to Phase 12**, which writes its flows
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
- **Code reads in one mono family, named as a token.** The editor, a template's
  form and a failing case's arguments are all code, and a reader who sees three
  mono families reads three kinds of thing.
- **The app follows the browser's colour-scheme preference and offers no
  switch.** A switch is a stored preference, and no store holds a user's
  settings.
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
