# Wireframes

Every page of the web app, drawn at low fidelity, and the pages Phase 11 adds
beside them. Part of the architecture, and `README.md` is the map. `pages.md`
gives the sections, the pages and the design system, and `flows.md` gives the
steps of a flow. This file draws what the user sees at each step.

- **A drawing fixes what sits on a page and in what order.** The size of a box,
  the weight of a line and the wording of a label are the design system's to
  answer, and a drawing fixing them would be redrawn at every restyle.
- **A drawing is read against `pages.md`, never against the code.** The pages
  are rebuilt on these drawings, so a drawing copied from the pages as they
  stand would license the layout the rebuild exists to replace.

## The shell

Every page under a section carries the same two rows above its body.

```
+- any page under a section ---------------------------------------------+
| algo-coach      [ Practice ]  Cards              Sign out              |
+------------------------------------------------------------------------+
|                                                                        |
| < Binary search                  the way back, named                   |
| Lower bound                      the title                             |
| binary-search . 2 templates      what the title names                  |
|                                                                        |
| +--------------------------------------------------------+             |
| |                                                        |             |
| |   the body, in one column of at most 56rem             |             |
| |                                                        |             |
| +--------------------------------------------------------+             |
+------------------------------------------------------------------------+
```

- The navigation carries the two sections and the sign-out, and it marks the
  section the page sits under.
- The header carries the way back, the title, and the one line identifying what
  the title names.
- A section's root page carries no way back, since the navigation reaches that
  page in one press.

## The board

```
+- / --------------------------------------------------------------------+
| algo-coach      [ Practice ]  Cards              Sign out              |
+------------------------------------------------------------------------+
| Pick a technique                                                       |
| Every technique a served problem carries, stalest first.               |
|                                                                        |
| Not practised yet  12                                                  |
| ( bit-manipulation ) ( breadth-first-search ) ( greedy )               |
| ( monotonic-stack ) ( sliding-window ) ( two-pointers ) ...            |
|                                                                        |
| Practised  2                                                           |
| binary-search        12 attempts    9/12 solved    3 days ago          |
| monotonic-stack       4 attempts     2/4 solved    17 days ago         |
|                                                                        |
| 3 attempts grouped nowhere . 2 on a defective problem                  |
+------------------------------------------------------------------------+
```

- The board is the landing page, so it opens under the navigation with no way
  back.
- A technique never practised ranks stalest, so the untouched techniques read
  first. Each is a name alone, since every count on such a row is zero.
- A practised technique is a row: the attempts, the share solved and when it
  was last practised.
- The line under the two groups counts the attempts no row holds: the attempts
  no technique resolved, and the attempts on a retired problem.
- Phase 15 serves the scheduler's pick above both groups, and every technique
  stays on offer below it.

## A technique's candidates

```
+- /techniques/binary-search --------------------------------------------+
| algo-coach      [ Practice ]  Cards              Sign out              |
+------------------------------------------------------------------------+
| < Board                                                                |
| binary-search                                                          |
| Cards: Binary search, Answer-space search                              |
|                                                                        |
| Pick a problem  2                                                      |
| Smallest feasible speed  (medium)  2 attempts  1/2 solved  6 days ago  |
| Split the array          (hard)    never attempted                     |
+------------------------------------------------------------------------+
```

- The cards the technique carries sit in the header, under the title. A card is
  offered, and no sitting requires one.
- A row is a problem: its difficulty as a badge, then the counts at the right.
  A problem nobody attempted reads `never attempted`.
- A row carries no statement, since the clock starts when the statement is
  served.

## The picked problem

```
+- /problems/p-7f3a?technique=binary-search -----------------------------+
| algo-coach      [ Practice ]  Cards              Sign out              |
+------------------------------------------------------------------------+
| < binary-search                                                        |
| Smallest feasible speed                                                |
| (medium)  binary-search                                                |
|                                                                        |
| +--------------------------------------------------------+             |
| |  2          1/2        6 days ago   [ Start the sitting ] |           |
| |  attempts   solved     last attempted                   |             |
| |  No statement on this page. It is served on that press, |             |
| |  and the clock starts with it.                          |             |
| +--------------------------------------------------------+             |
|                                                                        |
| Before you start                                                       |
| The card teaches the form this problem is written for. Reading it is   |
| off the clock, and no sitting requires it.                             |
| Cards: Binary search, Answer-space search                              |
+------------------------------------------------------------------------+
```

- The page asks for one press, and that press starts the clock.
- The press sits in one panel with the counts the user reached on this problem,
  so the page says what has been tried before it asks for the next sitting.
- Phase 11 opens the same page as a rung of a card's ladder. The way back then
  names the card, and the rest of the drawing stands.

## The sitting

```
+- /sittings/s-91c2, solving --------------------------------------------+
| algo-coach      [ Practice ]  Cards              Sign out              |
+------------------------------------------------------------------------+
| Smallest feasible speed              12:04  [ Pause ]  [ End ]         |
+----------------------------------+-------------------------------------+
| Smallest feasible speed          | +----------------------------+      |
|                                  | | def solve(piles, h):       |      |
| the statement, as prose          | |     |                      |      |
| ...........................      | |                            |      |
| ...........................      | |   the editor               |      |
| ...........................      | |                            |      |
|                                  | +----------------------------+      |
| The function every case calls    | [ Submit ]  Cmd+Enter . judged      |
| +-----------------------------+  |             against the problem's   |
| | def solve(piles, h) -> int: |  |             own test cases          |
| +-----------------------------+  | +----------------------------+      |
|                                  | | Not solved: 7 of 11 cases  |      |
|                                  | | + + + + + + + x + ~ ~      |      |
|                                  | | Case 8: wrong answer       |      |
|                                  | |   Arguments  [1,4,1,1] 8   |      |
|                                  | |   Expected   3             |      |
|                                  | |   Returned   4             |      |
|                                  | +----------------------------+      |
+------------------------------------------------------------------------+
```

- A bar across the top carries the clock, the pause and the end, and it stays
  at the top of the window while the statement scrolls. The clock is the
  reading the sitting is run by, so it is never scrolled out of sight.
- The bar names the problem in the quiet size. The title itself reads in the
  statement column, as every other page's title reads in its own body.
- The statement reads on the left and the editor takes the right, which is the
  one page in two columns.
- The signature is named as the function every case calls, and it is coloured
  as the editor colours it.
- The verdict sits under the editor, so a failing case is read beside the code
  that failed it.
- The case strip carries one mark per case, in the order the problem carries its
  cases: `+` passed, `x` wrong, `~` timed out, `!` crashed.
- The failing case is drawn whole: the arguments, the expected value, and the
  value the submission returned.
- The submit press sits under the editor, beside the shortcut that fires it and
  the line saying what judges the submission.

## The sitting, paused

```
+- /sittings/s-91c2, paused ---------------------------------------------+
| algo-coach      [ Practice ]  Cards              Sign out              |
+------------------------------------------------------------------------+
| Paused: the clock is stopped         12:04     [ Resume ]              |
+------------------------------------------------------------------------+
|                                                                        |
| ##### the statement and the editor, blurred and inert ####             |
| ##########################################################             |
| ##########################################################             |
+------------------------------------------------------------------------+
```

- The same bar carries the pause: the problem's name is replaced by the state,
  and the two presses by the one that resumes. No row is added, so the page
  under the cover does not move when the sitting is paused.
- The statement and the editor are covered and take no keystroke, since the time
  away is not spent on the problem.

## The sitting, at phone width

```
+- /sittings/s-91c2, at phone width -------------------------------------+
| algo-coach   [ Practice ]  Cards           Sign out                    |
+------------------------------------------------------------------------+
| Smallest feasible speed                                                |
| the statement, as prose                                                |
| ...........................                                            |
| -----------------------------------------------------------            |
| the editor                                                             |
| [ Submit ]   12:04   [ Pause ]  [ End ]                                |
| -----------------------------------------------------------            |
| the verdict                                                            |
+------------------------------------------------------------------------+
```

- The two columns stack, the statement above the editor.
- The sitting is designed for a keyboard and a wide window. The stack keeps a
  narrow window readable, and no layout is drawn for one.

## The claim and the label

```
+- the claim and the label, over the ended sitting ----------------------+
| The claim                                                              |
| Asked of each attempt now, while the code is minutes old.              |
|                                                                        |
| Attempt 2 of 3 . not solved . 12:04                                    |
|                                                                        |
| Which techniques did this code use?                                    |
|   [x] binary-search        the drilled one, answered for               |
|   [ ] two-pointers                                                     |
|   [ ] None of these                                                    |
|                                                                        |
| Confidence   ( guess | leaning | sure )                                |
|                                                                        |
| Why did it go that way?                                                |
|   ( ) gap      I did not hold the form                                 |
|   ( ) rust     I held the form and did not reach it                    |
|   ( ) syntax   I slipped writing code I know                           |
|                                                                        |
|                                         [ Save ]                       |
+------------------------------------------------------------------------+
```

- The claim and the label open together over the ended sitting, and the two
  are asked of each attempt the sitting minted in turn.
- The technique the problem was picked by is answered for already, since
  selection chose the problem for that technique.
- The label reads as a question about the solver rather than about the code,
  so it sits under the claim and the confidence.
- Each mode is drawn as its own word beside a gloss in the first person. A
  solver reading `rust` alone cannot tell which of the two failures it names.
- The modes are the ones the route sent, so the split by verdict lives in one
  place. An unsolved attempt is offered `gap`, `rust` and `syntax`, and a solved
  one is offered `speed` and `none`.
- An attempt that crashed on every case is offered no mode, and the overlay
  then asks for its claim alone. `log.md` gives why the record answers that
  attempt already.
- One press stores both records. The claim and the label answer two questions
  about one attempt, and a press each would ask the solver to confirm twice.
- A press with no mode selected stores no label, and `log.md` gives why a skip
  writes no record. Closing leaves the attempts to the problem's own
  techniques, and leaves them unlabelled.

## The cards

```
+- /cards ---------------------------------------------------------------+
| algo-coach      Practice  [ Cards ]               Sign out             |
+------------------------------------------------------------------------+
| Cards                                                                  |
| One card teaches one technique: when to reach for it, and the forms to |
| reproduce from memory.                                                 |
|                                                                        |
| +--------------------------------------------------------+             |
| | Monotonic stack   monotonic-stack          4 templates |             |
| | For each element, the next or previous greater ...     |             |
| | ------------------------------------------------------ |            |
| | Sliding window    sliding-window           6 templates |             |
| | The answer is about a contiguous subarray ...          |             |
| +--------------------------------------------------------+             |
|                                                                        |
| +--------------------------------------------------------+             |
| | binary-search                                  2 cards |             |
| | ------------------------------------------------------ |            |
| | Binary search                              5 templates |             |
| | A sorted array, or any space with a monotone ...       |             |
| | ------------------------------------------------------ |            |
| | Answer-space search                        1 template  |             |
| | The answer is a number in a known range ...            |             |
| +--------------------------------------------------------+             |
+------------------------------------------------------------------------+
```

- A card reads as a row: its title, how many templates it teaches, and its
  trigger cut to two lines. The trigger says when to reach for the technique,
  and a reader picks a card by that sentence.
- A technique several cards teach carries a header naming it, since the cards
  under it are one thing to choose between.
- A technique one card teaches carries no header, and that row names the
  technique itself. A header over a single row repeats what the row says.
- Every block is the same panel, so the page reads as a list of panels rather
  than as two kinds of thing.

## A card

```
+- /cards/binary-search -------------------------------------------------+
| algo-coach      Practice  [ Cards ]               Sign out             |
+------------------------------------------------------------------------+
| < Cards                                                                |
| Binary search                                                          |
| binary-search                                                          |
|                                                                        |
| ( When to reach for it )( The brief )( Ladder )( Templates )   the bar |
|                                                                        |
| v When to reach for it                                                 |
| the trigger, one or two lines                                          |
|                                                                        |
| v The brief                                                            |
| ...........................................................            |
|                                                                        |
| v Templates                                             5 templates    |
| +--------------------------------------------------------+             |
| | Lower bound  [optional]              [ Reveal the form ] |           |
| | ------------------------------------------------------ |            |
| | trigger: ............................................  |             |
| | +----------------------------------------------------+ |            |
| | | The form is hidden . 14 lines                      | |            |
| | +----------------------------------------------------+ |            |
| +--------------------------------------------------------+             |
| +--------------------------------------------------------+             |
| | Upper bound                            [ Hide the form ] |           |
| | ------------------------------------------------------ |            |
| | trigger: ............................................  |             |
| | def upper(xs, target):   the form, coloured as the      |            |
| |     ...                  editor colours it             |             |
| | the notes, as prose                                    |             |
| +--------------------------------------------------------+             |
+------------------------------------------------------------------------+
```

- A bar names the page's sections and stays at the top while the page scrolls.
  The brief runs past a screen, and the ladder under it would otherwise be
  reached by scrolling through the whole of it.
- Every heading is the press that closes its own section, and a section is open
  until the reader closes it.
- The trigger and the brief read above the templates, and both stay visible.
- A template is a panel: its title, its badges and the press that reveals the
  form in the header, then its trigger.
- A template's form is hidden until the user reveals it. The hidden state names
  how many lines the form runs to, and shows nothing of the form itself. A
  reader decides whether to try recalling the form from that length.
- A revealed template shows its form and its notes, and the press then covers
  the form again.

## The login

```
+- /login ---------------------------------------------------------------+
|                                      no navigation                     |
|                                                                        |
|   algo-coach                                                           |
|   Sign in                                                              |
|   Deliberate practice of algorithmic problem-solving. Access is by     |
|   invitation.                                                          |
|                                                                        |
|   +-------------------------------------------+  the refusal, where    |
|   | That address has no invitation.           |  one returned          |
|   +-------------------------------------------+                        |
|                                                                        |
|   +-------------------------------------------+                        |
|   |          Continue with Google             |                        |
|   +-------------------------------------------+                        |
|   +-------------------------------------------+                        |
|   |          Continue with GitHub             |                        |
|   +-------------------------------------------+                        |
|                        or                                              |
|   +-------------------------------------------+                        |
|   |          Dev login as local               |                        |
|   +-------------------------------------------+                        |
|   ---------------------------------------------                        |
|   The app stores what you attempt and what a model says about it.      |
|   Privacy policy                                                       |
+------------------------------------------------------------------------+
```

- The page carries no navigation, since every section behind the menu needs a
  session.
- The wordmark, the title and one line name the app before it asks for a
  sign-in.
- A provider with no client offers no press, and a page offering none says so.
- The dev login is separated by a word, and that separator is absent where the
  dev login is the only way in.
- A refused sign-in returns to this page and names its reason, on a strip of
  its own above the presses.
- The last line says what the app stores, and the policy is linked from it.

## The privacy policy

```
+- /privacy -------------------------------------------------------------+
|                                      no navigation                     |
|                                                                        |
| < Sign in                                                              |
| Privacy policy                                                         |
| Last updated 15 September 2026                                         |
|                                                                        |
| the policy, as prose                                                   |
| ...........................................................            |
| ...........................................................            |
+------------------------------------------------------------------------+
```

- The page carries no navigation and sends no request, so a person with no
  account reads it.
- The policy's own title and the date it was last updated are the page's
  header, and the prose under it starts at the first section.

## Any path naming no page

```
+- any path naming no page ----------------------------------------------+
| algo-coach      Practice  Cards                   Sign out             |
+------------------------------------------------------------------------+
| No page here.                                                          |
|                                                                        |
| < Board                                                                |
+------------------------------------------------------------------------+
```

- The page offers the way back to the board, since a signed-in user lands
  there.

## The three readings before the content

```
+- the three readings before the content --------------------------------+
| +--------------------------------------------------------+             |
| | Loading the board...                                   |             |
| +--------------------------------------------------------+             |
|                                                                        |
| +--------------------------------------------------------+             |
| | The board did not load: 503 from the API   [ Retry ]   |             |
| +--------------------------------------------------------+             |
|                                                                        |
| +--------------------------------------------------------+             |
| | No served problem carries a technique yet.             |             |
| +--------------------------------------------------------+             |
+------------------------------------------------------------------------+
```

- One component renders the three, so a page that is loading, failed or empty
  reads the same wherever the user stands.
- The failure names what failed and offers the request again.

## A card, before a run

```
+- /cards/binary-search, no run open ------------------------------------+
| algo-coach      Practice  [ Cards ]               Sign out             |
+------------------------------------------------------------------------+
| < Cards                                                                |
| Binary search                                                          |
| binary-search                                                          |
|                                                                        |
| +--------------------------------------------------------+             |
| | The ladder is measured from the start, so a problem     |            |
| | solved before it counts toward nothing.                 |            |
| |                        [ Start studying this card ]     |            |
| +--------------------------------------------------------+             |
|                                                                        |
| ( When to reach for it )( The brief )( Ladder )( Templates )           |
|                                                                        |
| v When to reach for it                                                 |
| the trigger, one or two lines                                          |
|                                                                        |
| v The brief                                                            |
| ...........................................................            |
|                                                                        |
| v Ladder                                              5 rungs          |
|    Smallest feasible speed                           required          |
|    covers Lower bound                                                  |
|    Split the array                                   required          |
|    covers Lower bound, Upper bound                                     |
|    No problem covers 'Upper bound' yet                  (gap)          |
|                                                                        |
| v Templates                                       5 templates          |
| +--------------------------------------------------------+             |
| | Lower bound                          [ Reveal the form ] |           |
| | ------------------------------------------------------ |            |
| | trigger: ............................................  |             |
| | The form is hidden . 14 lines                          |             |
| +--------------------------------------------------------+             |
+------------------------------------------------------------------------+
```

- The trigger, the brief and the templates read before a run opens, so starting
  a run is not the price of reading the card.
- The press that starts the run sits in a panel at the top, beside the one line
  saying what the start measures from.
- The ladder is listed before the start, since the user decides the start on
  the list of problems it names. No rung carries progress yet.
- A rung names the templates it covers under the problem's title, so the user
  reads why this problem is on this ladder.
- A core template no problem covers is named on the card as a gap, and the card
  starts anyway.

## A card, once a run is open

```
+- /cards/binary-search, a run open -------------------------------------+
| algo-coach      Practice  [ Cards ]               Sign out             |
+------------------------------------------------------------------------+
| < Cards                                                                |
| Binary search                                                          |
| binary-search . studying since 3 days ago                              |
|                                                                        |
| +--------------------------------------------------------+             |
| |  2/5          1/5           1        [ Recall a form ] |             |
| |  rungs solved forms recalled probes drawn              |             |
| +--------------------------------------------------------+             |
|                                                                        |
| ( When to reach for it )( The brief )( Ladder )( Recall )( Probes )    |
|                                                                        |
| v Ladder                              2 of 5 solved                    |
|    [x] Smallest feasible speed                       required          |
|    [x] Split the array                               required          |
|    [ ] Ship within days                              optional          |
|                                                                        |
| v Recall                                                               |
|    Lower bound                  2 days ago . passed . no hint taken    |
|    Upper bound                                    never recalled       |
|                                                                        |
| v Probes           drawn at the start, never from the ladder           |
|    Kth smallest pair distance                    not attempted         |
|                                                                        |
| v Templates                       the trigger and the form, as above   |
+------------------------------------------------------------------------+
```

- The same card, with three views the run makes readable: the ladder's
  progress, the recall state of each template, and the probes the start drew.
- The three read as counts in one panel at the top, and each has its own
  section below. The panel says how far the run has got without the reader
  scrolling to the sections.
- The press that opens the recall trainer sits in that panel, since recall is
  the one act the card offers while a run is open.
- Every one of the three is a fold rather than a stored verdict, so a corpus
  that moved under the card re-derives them.
- The probes sit apart from the ladder, since a probe is never drawn from it.

## A rung of the ladder

```
+- the ladder, one rung -------------------------------------------------+
| [ ] Split the array                            required                |
|     covers: lower bound, upper bound                                   |
|     hard . 0 attempt(s) since the run began                            |
+------------------------------------------------------------------------+
```

- A rung names the templates it covers, so the user reads why this problem is
  on this ladder.
- The templates decide whether the rung is required, which no record stores.
- The count is the attempts since the run began, since an earlier attempt
  counts for nothing.

## The picked problem, opened from a card

```
+- /problems/p-8c21?card=binary-search ----------------------------------+
| algo-coach      [ Practice ]  Cards              Sign out              |
+------------------------------------------------------------------------+
| < Binary search                                                        |
| Split the array                                                        |
| hard . 0 attempt(s), - solved . last never                             |
|                                                                        |
| Cards: Binary search                                                   |
|                                                                        |
|         +---------------------+                                        |
|         |  Start the sitting  |   the sitting returns to               |
|         +---------------------+   the card it came from                |
|                                                                        |
| No statement on this page.                                             |
+------------------------------------------------------------------------+
```

- The page is the one a technique's candidates open, with the card named in
  place of the technique.
- The way back returns to the card, and the sitting returns there when it ends.

## The recall trainer, before a hint

```
+- the recall trainer, before a hint ------------------------------------+
| algo-coach      Practice  [ Cards ]               Sign out             |
+------------------------------------------------------------------------+
| < Binary search                                                        |
| Recall a form                                                          |
| the title and the form are withheld                                    |
|                                                                        |
| When to reach for it                                                   |
|    the template's trigger, one or two lines                            |
|                                                                        |
| +--------------------------------------------------------+             |
| | def solve(xs, target):                                 |             |
| |     |                                                  |             |
| |                                                        |             |
| |          the blank file                                |             |
| +--------------------------------------------------------+             |
|                                                                        |
| [ Run ]                        [ Hint: the title ]                     |
+------------------------------------------------------------------------+
```

- The trigger names the template. The title and the form are withheld, and
  mapping the trigger to the form is the recall being measured.
- The signature is shown, since the cases call the form with a parameter order
  the user cannot infer.
- The file is otherwise blank, and the editor proposes nothing.

## The recall trainer, with hints taken

```
+- the recall trainer, two hints taken ----------------------------------+
| < Binary search                                                        |
| Recall a form                                                          |
|                                                                        |
| When to reach for it                                                   |
|    the template's trigger, one or two lines                            |
|                                                                        |
| Title    Lower bound                        hint 1                     |
| Notes    the authored notes, as prose       hint 2                     |
|                                                                        |
| +--------------------------------------------------------+             |
| | def solve(xs, target):                                 |             |
| |     lo, hi = 0, len(xs)                                |             |
| |     while lo < hi:                                     |             |
| |         |                                              |             |
| +--------------------------------------------------------+             |
|                                                                        |
| [ Run ]                         [ Hint: the form ]                     |
+------------------------------------------------------------------------+
```

- The hints arrive in one order, and each one stays on the page: the title,
  then the notes, then the form.
- The press names the hint it gives next, so the user knows the price before
  taking it.

## A recall attempt, run

```
+- the recall attempt, run ----------------------------------------------+
| Lower bound                                                            |
| 6 of 6 cases passed, 2 hints taken                                     |
| + + + + + +                                                            |
|                                                                        |
| A hinted pass is not a pass: the record keeps both.                    |
|                                                                        |
| [ Recall another ]              [ Back to the card ]                   |
+------------------------------------------------------------------------+
```

- The cases decide the attempt, and the strip reads as the verdict's does.
- The hints taken are shown beside the outcome, since a hinted pass is not a
  pass.
