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
|                                                                        |
| Technique            Attempts   Solved   Last practised                |
| -----------------------------------------------------------            |
| binary-search              12     9/12   3 days ago                    |
| monotonic-stack             4      2/4   17 days ago                   |
| two-pointers                0        -   never                         |
| ...                                                                    |
|                                                                        |
| 3 attempts grouped nowhere . 2 on a defective problem                  |
+------------------------------------------------------------------------+
```

- The board is the landing page, so it opens under the navigation with no way
  back.
- A row is a technique. The line under the table counts the attempts no row
  holds: the attempts no technique resolved, and the attempts on a retired
  problem.
- Phase 14 serves the scheduler's pick above the table, and every technique
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
| Pick a problem                                                         |
| Problem                 Difficulty  Attempts  Solved  Last             |
| -----------------------------------------------------------            |
| Smallest feasible speed     medium         2     1/2  6d ago           |
| Split the array             hard           0       -  never            |
| ...                                                                    |
+------------------------------------------------------------------------+
```

- The cards the technique carries sit in the header, under the title. A card is
  offered, and no sitting requires one.
- A row carries no statement, since the clock starts when the statement is
  served.

## The picked problem

```
+- /problems/p-7f3a?technique=binary-search -----------------------------+
| algo-coach      [ Practice ]  Cards              Sign out              |
+------------------------------------------------------------------------+
| < binary-search                                                        |
| Smallest feasible speed                                                |
| medium . 2 attempts, 1 solved . last 6 days ago                        |
|                                                                        |
| Cards: Binary search, Answer-space search                              |
|                                                                        |
|         +---------------------+                                        |
|         |  Start the sitting  |   the one act, and the                 |
|         +---------------------+   press the clock starts on            |
|                                                                        |
| No statement on this page.                                             |
+------------------------------------------------------------------------+
```

- The page asks for one press, and that press starts the clock.
- The counts are the user's own on this problem, and they say whether the
  problem has been sat before.
- Phase 11 opens the same page as a rung of a card's ladder. The way back then
  names the card, and the rest of the drawing stands.

## The sitting

```
+- /sittings/s-91c2, solving --------------------------------------------+
| algo-coach      [ Practice ]  Cards              Sign out              |
+----------------------------------+-------------------------------------+
| Smallest feasible speed          | +----------------------------+      |
|                                  | | def solve(piles, h):       |      |
| the statement, as prose          | |     |                      |      |
| ...........................      | |                            |      |
| ...........................      | |   the editor               |      |
| ...........................      | |                            |      |
|                                  | +----------------------------+      |
| +-----------------------------+  | [ Submit ]  Cmd+Enter               |
| | def solve(piles, h) -> int: |  |   12:04  [ Pause ]  [ End ]         |
| +-----------------------------+  | +----------------------------+      |
| the signature the statement      | | Not solved: 7 of 11 cases  |      |
| ends on                          | | + + + + + + + x + ~ ~      |      |
|                                  | | Case 8: wrong answer       |      |
|                                  | |   Arguments  [1,4,1,1] 8   |      |
|                                  | |   Expected   3             |      |
|                                  | |   Returned   4             |      |
|                                  | +----------------------------+      |
+------------------------------------------------------------------------+
```

- The statement reads on the left and the editor takes the right, which is the
  one page in two columns.
- The verdict sits under the editor, so a failing case is read beside the code
  that failed it.
- The case strip carries one mark per case, in the order the problem carries its
  cases: `+` passed, `x` wrong, `~` timed out, `!` crashed.
- The failing case is drawn whole: the arguments, the expected value, and the
  value the submission returned.
- The clock, the pause and the end sit in one row with the submit press, so the
  sitting is run from one place.

## The sitting, paused

```
+- /sittings/s-91c2, paused ---------------------------------------------+
| algo-coach      [ Practice ]  Cards              Sign out              |
+------------------------------------------------------------------------+
| +--------------------------------------------------------+             |
| | Paused: the clock is stopped   12:04   [ Resume ]      |             |
| +--------------------------------------------------------+             |
|                                                                        |
| ##### the statement and the editor, blurred and inert ####             |
| ##########################################################             |
| ##########################################################             |
+------------------------------------------------------------------------+
```

- The pause bar takes the top of the page, and it carries the frozen clock and
  the press that resumes.
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
- An unsolved attempt is offered `gap`, `rust` and `syntax`, and a solved one
  is offered `speed` and `none`. `log.md` gives why the five split that way.
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
|                                                                        |
| binary-search                                                          |
|   Binary search                        2 templates                     |
|   Answer-space search                  1 template                      |
|                                                                        |
| monotonic-stack                                                        |
|   Monotonic stack                      2 templates                     |
+------------------------------------------------------------------------+
```

- The cards are grouped by the technique they teach, since one technique can
  carry several cards.

## A card

```
+- /cards/binary-search -------------------------------------------------+
| algo-coach      Practice  [ Cards ]               Sign out             |
+------------------------------------------------------------------------+
| < Cards                                                                |
| Binary search                                                          |
| binary-search                                                          |
|                                                                        |
| When to reach for it                                                   |
| the trigger, one or two lines                                          |
|                                                                        |
| the brief, as prose                                                    |
| ...........................................................            |
|                                                                        |
| Templates                                                              |
| +--------------------------------------------------------+             |
| | Lower bound                                [optional]  |             |
| | trigger: ............................................  |             |
| | ########  the form, blurred  ########                  |             |
| |            [ Reveal the form ]                         |             |
| +--------------------------------------------------------+             |
| +--------------------------------------------------------+             |
| | Upper bound                                            |             |
| | trigger: ............................................  |             |
| | def upper(xs, target):        revealed                 |             |
| |     ...                                                |             |
| | the notes, as prose                          [ Hide ]  |             |
| +--------------------------------------------------------+             |
+------------------------------------------------------------------------+
```

- The trigger and the brief read above the templates, and both stay visible.
- A template's form is covered until the user reveals it, and the template's own
  trigger stays visible over the cover.
- A revealed template shows its form and its notes, and the press that covers
  the form again.

## The login

```
+- /login ---------------------------------------------------------------+
|                                      no navigation                     |
|                                                                        |
|               Sign in to algo-coach                                    |
|                                                                        |
|               +---------------------------+                            |
|               |   Sign in with Google     |                            |
|               +---------------------------+                            |
|               +---------------------------+                            |
|               |   Sign in with GitHub     |                            |
|               +---------------------------+                            |
|                                                                        |
|               This address is not invited.  the refusal                |
|                                                                        |
|               Privacy policy                                           |
+------------------------------------------------------------------------+
```

- The page carries no navigation, since every section behind the menu needs a
  session.
- A provider with no client offers no press, and a page offering none says so.
- A refused sign-in returns to this page and names its reason.

## The privacy policy

```
+- /privacy -------------------------------------------------------------+
|                                      no navigation                     |
|                                                                        |
| Privacy policy                                                         |
| the policy, as prose                                                   |
| ...........................................................            |
| ...........................................................            |
+------------------------------------------------------------------------+
```

- The page carries no navigation and sends no request, so a person with no
  account reads it.

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
| When to reach for it                                                   |
| the trigger, one or two lines                                          |
|                                                                        |
| the brief, as prose                                                    |
| ...........................................................            |
|                                                                        |
|         [ Start studying this card ]                                   |
|                                                                        |
| Ladder                                        5 rungs                  |
|    Smallest feasible speed                    required                 |
|    Split the array                            required                 |
|    Ship within days                           optional                 |
|    ...                                                                 |
|    No problem covers 'upper bound' yet             a gap               |
|                                                                        |
| Templates                                                              |
| +--------------------------------------------------------+             |
| | Lower bound                                            |             |
| | trigger: ............................................  |             |
| | ########  the form, blurred  ########                  |             |
| |            [ Reveal the form ]                         |             |
| +--------------------------------------------------------+             |
+------------------------------------------------------------------------+
```

- The trigger, the brief and the templates read before a run opens, so starting
  a run is not the price of reading the card.
- The ladder is listed before the start, since the user decides the start on
  the list of problems it names. No rung carries progress yet.
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
| Ladder                            2 of 5 rungs solved                  |
|    [x] Smallest feasible speed                required                 |
|    [x] Split the array                        required                 |
|    [ ] Ship within days                       optional                 |
|    [ ] Minimise the maximum                   required                 |
|                                                                        |
| Recall                                                                 |
|    Lower bound        2 days ago, no hint taken                        |
|    Upper bound        never recalled                                   |
|    [ Recall a form ]                                                   |
|                                                                        |
| Probes                             drawn at the start                  |
|    Kth smallest pair distance      not attempted                       |
|                                                                        |
| Templates                          the trigger and the                 |
|                                    form, as above                      |
+------------------------------------------------------------------------+
```

- The same card, with three views the run makes readable: the ladder's
  progress, the recall state of each template, and the probes the start drew.
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
