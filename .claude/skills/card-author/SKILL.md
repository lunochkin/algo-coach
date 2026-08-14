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
fundamentals, no padding. Language: Python 3.

## Output

One file, `content/cards/<slug>.json`, matching `CardSeed`
(`src/algo_coach/schema/seed.py`). Gitignored — cards are product content and
move behind a private repo later.

No id, on the card or on any template. The engine mints identity at import; the
slug is what a re-seed matches on. **Never change a slug to rename a card** — a
new slug is a new card, and the runs against the old one stay against the old
one. Change `title`.

## Steps

1. **Pick the technique code.** It must be one the vocabulary carries, or the
   seed is rejected:

   ```bash
   uv run python -c "from algo_coach.techniques import codes; print(sorted(codes()))"
   ```

   Read the code's own entry before writing — `earns` and `near_miss` are what
   the classifier and the reader are held to, and a card teaching past that
   boundary teaches the wrong code:

   ```bash
   uv run python -c "from algo_coach.techniques import criterion; print('\n'.join(criterion('two-pointers')))"
   ```

2. **Scope the card.** Several cards per technique is normal — mastery is
   estimated per technique, so a card is free to be as small as one teachable
   form. Split when a technique has forms that are learned and lost separately
   (`binary-search` on values vs on an answer space); keep one when the
   variations are decision axes within a single form.

   **Scope by the machinery, not by the vocabulary.** A code's criterion says
   what earns the label; a card says what is studied together, and the two do
   not have to agree. Peeling degree-1 leaves from an undirected graph is not a
   topological order and belongs on that card anyway: same queue, same degree
   array, and it is what a reader reaches for the technique to solve. Include a
   form when it shares the machinery or when it is what the technique gets
   confused with — and say in its notes that it is not the technique proper, so
   the card teaches the boundary instead of blurring it.

3. **Write the card's `trigger`** — what in a problem says "reach for this
   technique", including the brute force it replaces. One or two sentences.
   The load-bearing field: a probe asks whether the technique is recognised
   unprompted, which is this and nothing else. Which *form* to reach for is
   each template's own trigger, written in step 5.

   **End it with the negative, and name where to go instead.** The precondition
   that makes the technique legal, and the technique that takes over when it
   fails: not contiguous or not monotone in window size means prefix-sum, a
   heap, or DP. Recognising that this is *not* the tool is half of what the cue
   is for, and "not this" without a destination leaves the reader nowhere.

4. **Write `brief`** — markdown, read before solving. Sections, in order, and
   omit one that has nothing to say:
   - **Core idea** — the mechanic in 2–4 sentences, plus the non-obvious mental
     unlock if there is one.
   - **Mental model** — what each name in the templates means and where it is
     *not* valid: a parent pointer is not a root, a size is meaningful only on
     a root. The misreading a reader will make, named before they make it.
     State the precondition the whole technique rests on as a property that can
     be checked — the window state folds and unfolds in O(1), the predicate is
     monotone over the range — since that is what a reader tests a new problem
     against.
   - **Decision axes** — the per-problem variations to pick (direction,
     variant, comparison). **Representation is one of them** whenever the input
     can arrive keyed differently: a dict keyed by the problem's own names
     against an array behind an integer mapping. A mapping layer has to be
     total over everything that can appear, and the error class it produces —
     a name that was never mapped — is worth naming with the axis.
   - **Key insights** — 3–6 bullets, non-obvious only. Include the solve-time
     practicalities that cost minutes rather than correctness: sizing an array
     `n + 1` to work 1-indexed instead of remapping labels, and the like.
   - **Complexity** — per speed-up and per variation where they differ, with
     the bound named rather than described: the naive form, each optimisation
     alone, and both together. "Effectively constant" says nothing a reader
     can reason with; `O(α(n))`, α ≤ 4 for any real n, does.
   - **Out of scope** — what belongs to this technique and is deliberately not
     here, so the card is closed rather than merely unfinished. Name where it
     would be needed.
   - **Open** — the hard form the card's optional template answers, named as a
     thing worth deriving first. What makes it hard, and nothing that removes
     the difficulty: the answer is in the optional template, which is not read
     unless it is asked for.
   - **Pitfalls** — where time is actually lost: off-by-ones, ties, leftovers,
     sentinels. **Give the structural fix, not the warning.** "Append a
     sentinel so there is one width formula and one code path" is a fix;
     "be careful with the width" is a note to forget.

   No problem statements, no test cases — see Rules.

5. **Write the templates.** Each is a blank-file target: the user reproduces it
   cold, and a recall attempt is keyed to its slug forever.

   **Expect three to five studied templates on a card**, not one — the
   optional template, if there is one, sits outside that count. Per card, not
   per technique: a technique carrying several cards carries several such sets.
   A form earns its own template when it is reproduced separately — the base
   mechanic, the variant that carries an aggregate on the stack, the one that
   folds into a DP, the specialisation with the sentinel. One template is a sign
   the card was scoped as a definition rather than as what gets typed.

   - **Each carries its own `trigger`** — what says this *form* rather than
     another form of the same technique (a window of fixed width vs one that
     expands; binary search on values vs on an answer space). Recall is per
     template, so the cue that has to fire is too. With one template it may
     restate the card's more narrowly; do not paste the card's verbatim.
   - **`notes` carry what is true of this form only**: when it applies, its
     unlock, its variations, and what it transfers to. The derivation of the
     line that goes wrong belongs here — write the derivation, not a warning.
     Omit `notes` when the trigger already says everything.
   - One statement per line. Never `;`-joined, never a single-line body
     (`if x: return` puts the body on its own line).
   - **A complete runnable unit in the shape it is actually typed** — a
     function where a solve types a function, a class where a solve types a
     class. A structure carried across a whole solve (a disjoint set, a trie
     node) is typed as a class with its methods, and forcing it into a
     standalone function trains a form nobody writes.
   - **A later template may use an earlier one by name**, since that is how it
     is typed: the base structure, then the twenty lines that use it. Order the
     templates so the base comes first. What is forbidden is a placeholder that
     stands for work — no `feasible()`, no `complete()`, no bare `return True`.
     If the technique is a generic shape, describe the shape in the brief and
     make the code a concrete canonical instance (placement → n-queens count).
   - **A variation that is a few lines on top of a base is a delta, not a
     template.** Put it in the base template's `notes` as a fenced fragment
     showing only the changed lines. Retyping the base to change three lines
     makes four templates out of one form, and recall is per template — the
     count would say four forms were learned where one was.
   - **A form earns its own template when the mechanic differs**, not when the
     problem does. Union-find over a grid is the same mechanic with an index
     trick, so it is a delta; a disjoint set carrying a ratio has a different
     `find`, so it is a template.
   - **Two templates may not blank-file to the same code.** If the second one
     reproduces the first's lines, reproducing it proves nothing and the
     recall count says two forms where there is one. Either it is a delta, or
     what it actually adds — the bounds, the feasibility predicate, the setup —
     is the part that must be typed concretely, and the template is the whole
     solve rather than the skeleton.
   - **A callable parameter is not a placeholder.** A base template taking a
     predicate is the reusable skeleton, and passing a lambda at the call site
     is how it is used. What is forbidden is a named helper that stands for
     unwritten work.
   - **The canonical form is the one that cannot produce the known bug**, not
     the shortest or the cleverest. Where a source records what went wrong —
     a stale index, a diverging second code path — the template is the shape
     that makes that mistake structurally impossible, and the tempting variant
     goes in `notes` named as the trap it is. A card that drills the elegant
     form re-teaches the bug the notes warn about.
   - **It must read like real solve code**, because that is what it trains.
     Keep the names a solve would use, and let a trailing comment state the
     invariant the structure maintains (`# indices; nums[st] strictly
     decreasing`) or mark the step that is the trick. Nothing else in comments,
     and complexity goes in the brief.
   - **A card may carry one optional template, and usually should.** Mark it
     `"optional": true`. It is the capstone — the hard problem's method, the
     variant that is a stretch rather than the day's work — and it sits outside
     the card's default study set. Zero or one, never two: a second one means
     the card was scoped wrong. It is authored in full, code included; what
     makes it optional is that nothing surfaces it unless it is asked for by
     name.
   - **Code that must never be shipped goes in `notes`, never in a template.**
     The naive form that shows why the optimisation exists earns its place —
     as a contrast to read, marked as one. A template is drilled until it is
     automatic, so the wrong version must not be one.
   - **Run every template before writing it into the card.** Against a brute
     force over random inputs where one is cheap to write — a template that
     compiles and is subtly wrong is worse than none, since it is drilled until
     it is automatic.

6. **Write the selector** — `technique`, optional `difficulty`, and `size`.
   The ladder is resolved from the corpus at import, so authoring names no
   problem: it says what to draw from and how many rungs. Check what the
   corpus holds for the technique before choosing a size:

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
- **Never print a template's code into the conversation.** Not while
  authoring, not when reporting what was written, not when summarising a
  revision — write it to the file and name the template by its slug. A card is
  read when the reader chooses to read it, and a solution pasted into a session
  is read whether or not it was wanted. This holds for every template and
  doubly for the optional one; print it only when explicitly asked to.
- **A form the source reserves goes in the optional template**, not into the
  ordinary set. A note may mark something withheld, unsolved on purpose, or a
  stretch — "solve it cold", "no hints". The card still holds the answer, which
  is what makes it a card; the optional flag is what keeps it from arriving
  uninvited, and the brief's **Open** section names the difficulty without
  removing it. Never reproduce a pointer to where a solution lives either — a
  reference is a spoiler with an extra step.
- **A card holds no history.** No recall dates, no graduation stamp, no "5 WA
  on this in March", no ladder checkboxes. Those are records the engine keeps
  per user, and a card is product content one store seeds and another store
  seeds the same. What survives from a personal note is the depersonalised
  lesson: not "my repeat offender", but which line the bug lives on and what
  structural change removes the place it hides.
- Be correct on the algorithm. State a subtle variant rather than hand-waving
  it.
- Revising an existing card edits its file in place. Templates are matched by
  slug at import, so keep a slug whose recall history matters and add a new one
  rather than repurposing it.
- Do not re-explain what the user owns. Mid-tier framing by default.
