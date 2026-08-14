---
name: card-author
description: >-
  Author a card — one technique's trigger, brief, and the templates to
  reproduce from memory — as a structured seed file under content/cards/.
  Use when asked to write, extend or revise a card ("write a card for
  monotonic stack", "add a template to the sliding-window card",
  "/card-author binary search"). Produces JSON matching CardSeed, not prose.
---

# Card authoring

One card organises studying one technique: what to read, what to reproduce from
memory, and what to solve. This skill writes the first two and the selector the
third is drawn by. It never names a problem.

Audience: an experienced solver reactivating, no editorials. Dense, no
fundamentals, nothing re-explained that the user owns. Mid-tier framing by
default. Language: Python 3.

## Output

One file, `content/cards/<slug>.json`, matching `CardSeed`
(`src/algo_coach/schema/seed.py`). Gitignored — cards are product content and
move behind a private repo later.

No id, on the card or on any template: the engine mints identity at import.
Slugs are what a re-seed matches on, so **a slug is never changed and never
repurposed** — a new slug is a new card, and the runs and recall history against
the old one stay there. Rename by changing `title`; replace a form by adding a
template, not by rewriting one whose history matters. Revising a card edits its
file in place.

## Steps

1. **Pick the technique code**, and read its entry. `earns` and `near_miss` are
   what the classifier and the reader are both held to, so what the card teaches
   *as the technique* must sit inside them.

   ```bash
   uv run python -c "from algo_coach.techniques import codes; print(sorted(codes()))"
   uv run python -c "from algo_coach.techniques import criterion; print('\n'.join(criterion('two-pointers')))"
   ```

2. **Scope the card by the machinery, not by the vocabulary.** Several cards per
   technique is normal: split when forms are learned and lost separately
   (`binary-search` on values against an answer space), keep one when the
   variations are decision axes within a form.

   The criterion decides what earns the *label*; the card decides what is
   *studied together*. Peeling degree-1 leaves is not a topological order and
   belongs on that card anyway — same queue, same degree array, and it is what a
   reader reaches for the technique to solve. Include what shares the machinery
   or what the technique is confused with, and say in its notes that it is not
   the technique proper. That is how the card teaches the boundary rather than
   blurring it, and it is why step 1's constraint binds the technique's own
   forms rather than the card's contents.

3. **Write the card's `trigger`** — what in a problem says "reach for this
   technique", plus the brute force it replaces. One or two sentences, and the
   load-bearing field: a probe asks whether the technique is recognised
   unprompted, which is this and nothing else. Which *form* to reach for is each
   template's own trigger.

   **End with the negative and name where to go instead** — the precondition
   that makes the technique legal, and what takes over when it fails: not
   contiguous or not monotone means prefix-sum, a heap, or DP. Recognising that
   this is not the tool is half of what a cue is for, and "not this" without a
   destination leaves the reader nowhere.

4. **Write `brief`** — markdown, read before solving. These sections in this
   order, omitting any with nothing to say:

   - **Core idea** — the mechanic in 2–4 sentences, plus the mental unlock if
     there is one.
   - **Mental model** — what each name in the templates means and where it is
     *not* valid (a parent pointer is not a root; a size is meaningful only on a
     root): the misreading named before it is made. State the precondition the
     technique rests on as something checkable — folds and unfolds in O(1),
     monotone over the range — since that is what a reader tests a new problem
     against. And name **what makes a solution correct here, as a sentence the
     reader says before coding**. Some techniques rest on a mechanical
     invariant; enumeration rests on a counting argument — every answer produced
     exactly once — so its sentence carries blanks: *"each answer corresponds
     one-to-one to ___; I enumerate those by ___."* The guards in the code are
     conventions pinning that correspondence and derive themselves once it is
     said.
   - **Decision axes** — the per-problem variations to pick: direction, variant,
     comparison, and **representation** whenever the input can arrive keyed
     differently (a dict on the problem's own names against an array behind an
     integer mapping). A mapping layer must be total over everything that can
     appear; name the error class it produces when it is not.
   - **Key insights** — 3–6 bullets, non-obvious only, including the solve-time
     practicalities that cost minutes rather than correctness (sizing an array
     `n + 1` to work 1-indexed instead of remapping).
   - **Complexity** — per speed-up and per variation where they differ, with the
     bound named rather than described. "Effectively constant" gives a reader
     nothing to reason with; `O(α(n))`, α ≤ 4 for any real n, does.
   - **Pitfalls** — where time is actually lost: off-by-ones, ties, leftovers,
     sentinels. **Give the structural fix, not the warning.** "Append a sentinel
     so there is one width formula and one code path" is a fix; "be careful with
     the width" is a note to forget.
   - **Out of scope** — what belongs to the technique and is deliberately not
     here, and where it would be needed, so the card is closed rather than
     merely unfinished.
   - **Open** — the hard form the optional template answers, named as worth
     deriving first: what makes it hard and nothing that removes the difficulty.

   No problem statements, no test cases — see Rules.

5. **Write the templates.** Each is a blank-file target: reproduced cold, and a
   recall attempt is keyed to its slug forever.

   ### What earns a template

   **Three to five studied templates per card** — not per technique, and the
   optional one sits outside the count. One template means the card was scoped
   as a definition rather than as what gets typed.

   The test is whether the form is *reproduced separately*. A different mechanic
   is the usual evidence (a disjoint set carrying a ratio has a different
   `find`); an index trick on the same mechanic is not (union-find over a grid),
   and goes in `notes` as a fenced delta showing only the changed lines. Two
   exceptions decide the close calls:

   - **Promote what the user fails at.** Where the source names a variant idiom
     as the gap — fought twice, patched instead of learned — it is a template
     however few lines separate it from the base. A delta is read; a template is
     reproduced, and only a template is measured.
   - **Two templates may not blank-file to the same code.** If the second
     reproduces the first's lines, reproducing it proves nothing. Either it is a
     delta, or what it actually adds — the bounds, the feasibility predicate,
     the setup — must be typed concretely, and the template is the whole solve
     rather than the skeleton.

   **One optional template, and usually one.** Mark it `"optional": true`: the
   capstone, a stretch rather than the day's work, authored in full and outside
   the default study set. Never two — a second means the card was scoped wrong.

   ### What a template carries

   - **Its own `trigger`** — what says this form rather than another of the same
     technique (fixed-width window against expanding; binary search on values
     against an answer space). Recall is per template, so the cue that must fire
     is too. Never a paste of the card's.
   - **`notes` for what is true of this form only**: when it applies, its
     unlock, its variations, what it transfers to, and the derivation of the
     line that goes wrong — the derivation, not a warning. Omit when the trigger
     says everything.
   - **Code that must never be shipped lives here too**, never as a template:
     the naive form that shows why the optimisation exists is a contrast to
     read, marked as one. A template is drilled until automatic, so the wrong
     version must not be one.

   ### How the code is written

   - **A complete runnable unit in the shape it is actually typed** — a function
     where a solve types a function, a class where a solve types a class. A
     structure carried across a whole solve (a disjoint set, a trie node) is a
     class with its methods; forcing it into a standalone function trains a form
     nobody writes.
   - **A later template may use an earlier one by name**, since that is the
     typing order: the base structure, then the lines that use it. Order the
     templates accordingly.
   - **No placeholder standing for work** — no `feasible()`, no `complete()`, no
     bare `return True`. A *callable parameter* is not a placeholder: a base
     taking a predicate is the reusable skeleton, and a lambda at the call site
     is how it is used. For a generic shape, describe the shape in the brief and
     make the code a concrete canonical instance (placement → n-queens count).
   - **The canonical form is the one that cannot produce the known bug**, not
     the shortest or the cleverest. Where a source records what went wrong — a
     stale index, a diverging second code path — the template is the shape that
     makes it structurally impossible, and the tempting variant goes in `notes`
     named as the trap. A card drilling the elegant form re-teaches the bug its
     own notes warn about.
   - **It reads like real solve code**, because that is what it trains: the
     names a solve would use, one statement per line, never `;`-joined and never
     a single-line body. A trailing comment may state the invariant a structure
     maintains (`# indices; nums[st] strictly decreasing`) or mark the step that
     is the trick — nothing else, and complexity goes in the brief.
   - **Run it before writing it into the card**, against a brute force over
     random inputs wherever one is cheap to write. A template that compiles and
     is subtly wrong is worse than none, since it is drilled until automatic.

6. **Write the selector** — `technique`, optional `difficulty`, `size`. The
   ladder is resolved from the corpus at import, so authoring names no problem:
   the selector says what to draw from and how many rungs. Check what the corpus
   holds before choosing a size:

   ```bash
   uv run algo-coach board
   ```

7. **Validate**, and fix what it reports:

   ```bash
   uv run python .claude/skills/card-author/validate.py content/cards/<slug>.json
   ```

## Rules

- **No third-party problem statements or test cases**, in the file or anywhere
  else in any repo. Name a problem and link it; never paste it.
- **Never print a template's code into the conversation** — not while authoring,
  not when reporting what was written, not when summarising a revision. Write it
  to the file and name the template by its slug. A card is read when its reader
  chooses to read it; a solution pasted into a session is read whether or not it
  was wanted. Print only when explicitly asked to.
- **A form the source reserves goes in the optional template.** A note may mark
  something withheld or unsolved on purpose — "solve it cold", "no hints". The
  card still holds the answer, which is what makes it a card; the flag is what
  keeps it from arriving uninvited, and **Open** names the difficulty without
  removing it. Never reproduce a pointer to where a solution lives either — a
  reference is a spoiler with an extra step.
- **A card holds no history.** No recall dates, no graduation stamp, no "5 WA on
  this in March", no ladder checkboxes: those are per-user records, and a card is
  product content that one store seeds and another seeds identically. What
  survives from a personal note is the depersonalised lesson — not "my repeat
  offender", but which line the bug lives on and what structural change removes
  the place it hides.
- **Be correct on the algorithm.** State a subtle variant rather than
  hand-waving it.
