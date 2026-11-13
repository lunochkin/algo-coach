---
name: concept-author
description: >-
  Write one subtopic of a knowledge module by concept: its concepts, then its
  lesson sections, then its questions, each stage written by one agent and
  reviewed by another. Use when asked to write, extend or review a subtopic of
  a module written by concept ("write core/functions for py", "review the py
  questions", "/concept-author py core/strings").
---

# Writing a subtopic by concept

`docs/authoring/concepts.md` gives the order, the concept record, the stages
and the stopping rule. `docs/authoring/rules.md` gives the rules the module
check and a review hold every layer to. This skill holds the steps and the
brief each agent is given. A brief points at those files and adds only its
step's checklist, so a rule changed there reaches every brief.

Read both files, and the module's `CLAUDE.md`, before the first step.

## Roles

- **The author of the module** is the user. The user approves each stage and
  decides each disputed scope.
- **The writer** is one agent per step. It is given the brief below and the
  layer above, never the layer it replaces: a fresh generation reads no
  earlier version of its own file. The session may write a step itself when
  it has read no earlier version of the file.
- **The reviewer** is a second agent, which wrote nothing it reviews. It
  edits no file and writes its report to the scratchpad.
- **The fixer** applies a review in place. It may be the session itself.

Every agent runs code from the engine repo root with `uv run`, and runs
`uv run algo-coach module check <module>` before it reports. A reviewer
judges no prose line's width, since markdown reflows prose.

Each stage ends on `concepts.md`'s stopping rule: a full review finds nothing
WRONG, the other findings are fixed in place, and each later round reviews
the last fix pass on its diff (rule 23), until a diff review finds nothing
WRONG and no DEFECT. Keep a copy of the layer before each fix pass, and the
reports, in a scratchpad folder of the stage's own.

## Stage 1: concepts

1. **Write.** Brief, with its checklist:
   - Write `concepts/<topic>/<sub>.toml` from the sources the module's
     `CLAUDE.md` names. Each concept holds every field of the record in
     `concepts.md`, and a witness whose output the check confirms on every
     build. Apply the stage 1 checklist to each concept before reporting.
   - Lay out the lessons. Add the subtopic to `course.toml` (`subs`,
     `sub_titles`) and to `graph.toml` (`needs`, and a `[lesson.<slug>]` per
     lesson, one lesson per level and cluster of concepts). Write each lesson
     file as its `##` headings alone, one per section a `taught_by` names.
     Each lesson's `needs` and its heading order follow the concept order,
     so every construct a witness uses is taught before its section.
   - Order the concepts so each term is defined before its use. A concept of
     a subtopic this one needs counts as defined.
   - Report each scope you chose that a reviewer could dispute, with a
     recommendation.
2. **Review.** Brief: check each concept against the stage 1 checklist. Run
   one more case each claim's wording covers. Check that each misconception's
   text is false in every case the claim's scope reaches, and that each
   witness uses only the baseline and earlier concepts. For each
   misconception, name an output the claim gives and the misconception does
   not, from code using only the baseline and earlier concepts. Sort each finding as
   WRONG (false), GAP (a clause or misconception missing) or STYLE.
3. **Fix**, then repeat 2 with a fresh reviewer until a review finds no
   WRONG. Bring the disputed scopes to the user, then ask for approval.
   Record the approval in the file's header, with its date and the scopes
   the user decided.

## Stage 2: lessons

1. **Write.** Brief: write each lesson section from the concepts naming it in
   `taught_by`. Apply the section bullets of `concepts.md`. The lesson file
   holds no intro, no common mistakes and no links, since the seed renders
   them.
2. **Review.** Brief: check each section against its concepts. Every claim is
   taught, no sentence goes beyond them, each example's output differs from
   what each targeted misconception predicts, and every construct is taught
   or in the baseline. Run every block.
3. **Fix**, and end on the stopping rule, as in stage 1.

## Stage 3: questions

1. **Write.** Brief, with its checklist:
   - Write `banks/<topic>/<sub>.toml` from the concepts. Read the lessons only
     to avoid them. Never write `lesson`, `level` or `detail`.
   - Every concept has a question, and every misconception is named by a
     wrong choice whose prediction it really produces for that code. A
     choice embodying another concept's misconception names it as
     `"<concept>#<id>"`.
   - Rule 15: before each question, read its concept's section. The question
     shares no name, value, output, helper function or shape with it, and
     restates no expression of the claim with new values. The witness is
     never served, so its shape is free. A claim about one expression is
     asked inside a larger task.
   - Constructs: the baseline, and what the subtopic teaches at the
     question's level or below. The facts the keyed answer rests on sit at
     that level or below too: a level 0 question once keyed on the order
     in which a call's arguments are evaluated, a level 1 fact.
   - A `short` reply has more than two plausible values.
   - A kind does not reveal the answer: rule 11.
   - Each distractor is what a learner holding its misconception would
     predict, not something an unrelated fact rules out.
   - The key is not the one choice sharing a part with every other: at
     least one distractor differs from the key in two parts (rule 10).
   - Each `why` is true and explains its own choice. No `why` claims more than
     the concept states, and none opens with "Right:" or "Wrong:", since the
     client marks each choice.
2. **Solve.** Run the `solver` skill over the new bank, and hand its
   findings to the reviewer of step 3 as findings to verify. The solver
   answers without the key, so it catches a wrong or ambiguous key that a
   reviewer reading the key passes.
3. **Review.** Brief: check every question against rules 1–25, the question
   bullets of `concepts.md` and the writer's checklist. Run every snippet.
   Compare each question with its section yourself. For each rule 15
   finding, name a new task, and check that task against the section too:
   two proposed tasks repeated a section in the pilot. Sort findings as
   WRONG, DEFECT or STYLE, with concept and lesson findings apart.
4. **Fix** in place from the review. A concept or lesson finding goes to the
   user at the end of the stage, which goes on without the change. In the pilot, the review's new task per
   question removed every repeated example that two fresh generations had
   kept.
