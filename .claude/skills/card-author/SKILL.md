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

3. **Write the card's `trigger`** — what in a problem says "reach for this
   technique", including the brute force it replaces. One or two sentences.
   The load-bearing field: a probe asks whether the technique is recognised
   unprompted, which is this and nothing else. Which *form* to reach for is
   each template's own trigger, written in step 5.

4. **Write `brief`** — markdown, read before solving. Sections, in order, and
   omit one that has nothing to say:
   - **Core idea** — the mechanic in 2–4 sentences, plus the non-obvious mental
     unlock if there is one.
   - **Decision axes** — the per-problem variations to pick (direction,
     variant, comparison).
   - **Key insights** — 3–6 bullets, non-obvious only.
   - **Pitfalls** — where time is actually lost: off-by-ones, ties, leftovers,
     sentinels. **Give the structural fix, not the warning.** "Append a
     sentinel so there is one width formula and one code path" is a fix;
     "be careful with the width" is a note to forget.

   No problem statements, no test cases — see Rules.

5. **Write the templates.** Each is a blank-file target: the user reproduces it
   cold, and a recall attempt is keyed to its slug forever.

   **Expect three to five for a technique worth a card**, not one. A form earns
   its own template when it is reproduced separately — the base mechanic, the
   variant that carries an aggregate on the stack, the one that folds into a DP,
   the specialisation with the sentinel. One template is a sign the card was
   scoped as a definition rather than as what gets typed.

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
   - A complete function, arguments to return value, that runs. No
     pseudo-code placeholders — no `feasible()`, no `complete()`, no bare
     `return True`. If the technique is a generic shape, describe the shape in
     the brief and make the code a concrete canonical instance (placement →
     n-queens count).
   - **It must read like real solve code**, because that is what it trains.
     Keep the names a solve would use, and let a trailing comment state the
     invariant the structure maintains (`# indices; nums[st] strictly
     decreasing`) or mark the step that is the trick. Nothing else in comments,
     and complexity goes in the brief.
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
