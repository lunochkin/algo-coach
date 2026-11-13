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
  earlier version of its own file.
- **The reviewer** is a second agent, which wrote nothing it reviews. It
  edits no file and writes its report to the scratchpad.
- **The fixer** applies a review in place. It may be the session itself.

Every agent runs code from the engine repo root with `uv run`, and runs
`uv run algo-coach module check <module>` before it reports.

## Stage 1: concepts

1. **Write.** Brief: write `concepts/<topic>/<sub>.toml` from the sources the
   module's `CLAUDE.md` names. Each concept holds every field of the record in
   `concepts.md`, and a witness whose output the check confirms on every
   build. Apply the stage 1 checklist to each concept before reporting.
2. **Review.** Brief: check each concept against the stage 1 checklist. Run
   one more case each claim's wording covers. Sort each finding as WRONG
   (false), GAP (a clause or misconception missing) or STYLE.
3. **Fix**, then repeat 2 with a fresh reviewer until a review finds no
   WRONG. Bring the disputed scopes to the user, then ask for approval.
   Record the approval in the file's header.

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
     wrong choice whose prediction it really produces for that code.
   - Rule 15: before each question, read its concept's section. The question
     shares no name, value, output, helper function or shape with it, and
     restates no expression of the claim with new values. The witness is
     never served, so its shape is free. A claim about one expression is
     asked inside a larger task.
   - Constructs: the baseline, and what the subtopic teaches at the
     question's level or below.
   - A `short` reply has more than two plausible values.
   - A kind does not reveal the answer: rule 11.
   - Each distractor is what a learner holding its misconception would
     predict, not something an unrelated fact rules out.
   - Each `why` is true and explains its own choice. No `why` claims more than
     the concept states.
   - Report a rule 15 table: each question, its section, what differs.
2. **Review.** Brief: check every question against rules 1–25, the question
   bullets of `concepts.md` and the writer's checklist. Run every snippet.
   Compare each question with its section yourself, not by the writer's
   table. For each rule 15 finding, name a new task. Sort findings as WRONG,
   DEFECT or STYLE, with concept findings apart.
3. **Fix** in place from the review. A concept finding goes to the user
   first, since it changes stage 1. In the pilot, the review's new task per
   question removed every repeated example that two fresh generations had
   kept.
