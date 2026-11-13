---
name: solver
description: >-
  Answer a knowledge module's questions blind, without their keys, and report
  where the answer differs from the key, was a guess, or could be read off the
  choices alone. Use after a bank is written and before its review, or over any
  existing bank ("run the solver over py core/functions", "/solver python").
---

# Solver

A reviewer who sees the key tends to agree with it. The solver answers each
question as a learner would, from the prompt, the code and the choices alone,
and a script compares the answers with the keys afterwards. It finds what a
keyed review misses: a key that is wrong, a distractor that is also defensible
(rules 7 and 9 of `docs/authoring/rules.md`), a question needing a fact
nothing taught, and a key its wording gives away (rule 10). It judges nothing
else, and it edits no file.

## Steps

The session runs the script and spawns the agents. An agent is given its file
alone: it reads no bank, no lesson, no concept and no key, since any of them
holds the answer. Work in a scratchpad folder of the run's own, `<out>`.

1. **Extract.** From the engine repo root:

   ```bash
   uv run python .claude/skills/solver/solve.py extract content/modules/<slug> <out> [<sub> ...]
   ```

   It writes `questions.json` (prompt, code and choices, shuffled), `form.json`
   (the choices alone) and `key.json`, which no agent reads. A card is
   skipped, since its key is the points a learner recalls.

2. **Solve.** Spawn one agent with this brief and `<out>/questions.json`:
   - Answer every question as a learner of the module's subject would. For a
     choice, pick as many letters as `pick` says. For a `short` question, write
     the reply exactly as it would be typed.
   - Do not run an `output` question's code, since running it reads the answer
     off. Any other kind may be run, from the engine repo root, with
     `uv run python -c '...'`.
   - Give each answer a confidence, `sure`, `likely` or `guess`, and one line
     of reasoning.
   - Write `<out>/replies.json`: a list of `{"n", "pick": [letters]}` or
     `{"n", "reply"}`, each with `"confidence"` and `"reason"`.

3. **Read the form.** Spawn a second agent with `<out>/form.json` alone. Its
   brief: for each item, pick the choice most likely keyed from its wording
   alone, with a confidence and the cue it used, such as the longest choice,
   the only hedged one, or the one echoing the others. Write
   `<out>/form-replies.json` in the same shape.

4. **Score.**

   ```bash
   uv run python .claude/skills/solver/solve.py score <out>
   ```

   It writes `<out>/findings.md`:
   - **DIFFERS**: the reply is not the key. Either the key is wrong, a
     distractor is defensible, or the solver erred. Read each against the
     question and say which.
   - **GUESSED**: right, but at confidence `guess`. The prompt is unclear, or
     the question rests on a fact its level does not teach.
   - **FORM**: the second agent found the key from the choices alone, above a
     guess.

5. **Report** each finding with its verdict: a defect, with the rule it
   breaks, or the solver's own error.
   - The module check runs an `output` or `debug` question's code and holds
     its key to what it prints (rule 1). A DIFFERS there is the solver's
     error unless another choice prints the same, or the prompt reads two
     ways. On `py`, a second run gave 7 DIFFERS, all the solver's errors.
   - The solver earns most on `principle` and `pattern` questions, and on a
     module no interpreter proves. The form pass earns on every bank: on `py`
     it found 22 keys from the choices alone, against none from the solver. A defect goes to the stage's fixer, or
   to the module's author for a module outside the `concept-author` flow.
