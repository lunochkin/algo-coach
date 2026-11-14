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

- **The author of the module** is the user, who approves by exception, as
  `concepts.md` `## Stages` gives. A session applies each recommended fix
  and records it in the subtopic's digest, and writes there what it must
  ask instead of stopping to ask. A decide session then answers those
  questions, and only two kinds reach the author.
- **The writer** is one agent per step. It is given the brief below and the
  layer above, never the layer it replaces: a fresh generation reads no
  earlier version of its own file. The session may write a step itself when
  it has read no earlier version of the file.
- **The reviewer** is a second agent, which wrote nothing it reviews. It
  edits no file and writes its report to the scratchpad.
- **The fixer** applies a review in place. It may be the session itself.

Every agent runs code from the engine repo root with `uv run`, and runs
`uv run climb module check <module> --sub <sub>` before it reports.
`--sub` lists the subtopic's own findings and counts the rest, so the
output stays short as the module grows. A reviewer
judges no prose line's width, since markdown reflows prose.

A reviewer runs the check first and checks nothing the check reports by
itself: the witnesses and the snippets against their outputs, line widths
and snippet lengths, names and literals shared with a section, a key at
the centre of its choices, a `why` opening with its verdict, a `short`
reply of yes or no, the concept and lesson records, and every refusal the
seed makes. The reviewer reads the check's warnings and judges them, and
spends its time on what only a reader can judge.

Each stage ends on `concepts.md`'s stopping rule: a full review finds nothing
WRONG, or two full reviews have run, the other findings are fixed in place,
and each later round reviews the last fix pass on its diff (rule 23), until
a diff review finds nothing WRONG, whose findings are fixed without a
further review. Keep a copy of the layer
before each fix pass, and the reports, in a scratchpad folder of the
stage's own.

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
   not, from code using only the baseline and earlier concepts. Sort each
   finding as WRONG (false), GAP (a clause or misconception missing) or
   STYLE.
3. **Fix**, then repeat 2 with a fresh reviewer until a review finds no
   WRONG. Record each scope decided, and each disputed one, in the digest.
   The concept file's header records the stage's date and the digest's
   name.

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
   - A choice predicting what a snippet does states the outcome alone, and
     its reason goes in its `why` (rule 10).
   - Each `why` is true and explains its own choice. No `why` claims more than
     the concept states, and none opens with "Right:" or "Wrong:", since the
     client marks each choice.
2. **Solve.** Run the `solver` skill over the new bank, and hand its
   findings to the reviewer of step 3 as findings to verify. The form pass
   runs on every choice question. The answer pass runs on the questions
   whose key no interpreter proves, `principle` and `pattern`, since the
   check already proves an `output` or `debug` key by running it.
3. **Review.** Brief: check every question against the rules the check does
   not enforce, the question bullets of `concepts.md` and the writer's
   checklist. The check runs every snippet and holds each `output` and
   `debug` key to what it prints, so run a snippet only to test a
   distractor's prediction. Spend the time on what only a reader judges:
   each question against its section (rule 15), each distractor against
   its misconception, each `why`, and whether a kind or a name gives the
   key away. Compare each question with its section yourself. For each rule 15
   finding, name a new task, and check that task against the section too:
   two proposed tasks repeated a section in the pilot. Sort findings as
   WRONG, DEFECT or STYLE, with concept and lesson findings apart.
4. **Fix** in place from the review. A concept or lesson finding is decided
   as `concepts.md` gives: applied and recorded in the digest, or written
   there as a question for the user, the stage going on without it. In the
   pilot, the review's new task per question removed every repeated example
   that two fresh generations had kept.

## Running in the background

`workflow.md` beside this file draws the run as a diagram.
`run.py` beside this file writes a module's subtopics with no session
attending, one level at a time, as `concepts.md` `## Stages` allows once the
author approves by exception.

```bash
nohup uv run python .claude/skills/concept-author/run.py --level 0 \
    > ../py-runs/run-L0.out 2>&1 &
```

- **One session a step.** `stages.py` holds the order of the steps and the
  stopping rule, and runs each step (write, review, fix, the solver's two
  passes, the digest) as a `claude -p` session of its own, given the
  step's brief from `briefs/`. A session that orchestrated every step
  itself spent four fifths of the run's tokens, rereading a context that
  grew to 115k on every turn. A review's first line is `COUNTS WRONG=<n>
  DEFECT=<n> STYLE=<n>`, which the run reads to pick the next step. The run
  stages the module in git before each fix pass, so `git diff` is the
  fix's diff alone, and runs the module check after each writing step.
- **The decide step answers the digest's questions.** After the digest,
  a fresh Opus session decides each question in `## For you`, as
  `concepts.md` `## Stages` gives, from `briefs/decide.md`. Diff reviews
  then check its edits until one finds no WRONG, and the digest gains
  `## Decided`. `--decide --only <sub> ...` runs the step over subtopics
  already written, commits what it changed and merges it again.
- **A WRONG finding names the case that shows it.** The reviewer writes
  each case into `review-<n>-cases.py` through a helper the brief gives,
  and the run executes that script after the review. A WRONG finding whose
  case is missing or does not hold is counted as a DEFECT, since only a
  WRONG finding keeps a stage going. A finding no code can show says
  `[no case]` and quotes its source.
- **A small context.** A session starts in the subtopic's worktree, with
  no MCP server, no user settings and four tools: Bash, Read, Write and
  Edit. It starts at 9k tokens, against 46k for a session in the engine,
  and every turn reads that context again. `inputs.py` puts in its prompt
  the parts of the docs its step needs, the files it judges, and the
  check's output, so it spends no turn reading them.
- **The models.** Opus writes, reviews and solves; Sonnet writes the
  digest; Haiku reads the solver's form and fixes stages 1 and 2. A fix
  there follows findings written out in full, and a diff review reads every
  fix but the last. Sonnet fixes stage 3, since a stage 3 fix writes whole
  questions anew: in `classes`, the diff review after Haiku's fix found six
  DEFECTs, all on questions the fix rewrote. The flags `--writer`,
  `--reviewer`, `--fixer`, `--fixer3`, `--solver`, `--form` and `--digest`
  change a role's model. `scratch/<sub>-L<n>/tokens.tsv` holds
  each step's tokens and cost.
- **Where the work goes.** The content repository gets a branch, `py-auto`,
  and a worktree of it in `../py-runs/wt/integration`. Each subtopic is
  written in a worktree of its own, on a branch cut from `py-auto`. A
  subtopic whose digest reads `DONE` is committed there, the pre-commit hook
  running the module check, and merged into `py-auto`. A run never touches
  `main`.
- **Re-levelling.** `run.py --relevel` re-levels the written concepts,
  as `concepts.md` `### Re-levelling` gives. An assess session proposes
  moves from a table of every claim, a fresh verify session keeps the moves
  it agrees with, and each subtopic with agreed moves is changed on a branch
  of its own, with diff reviews, then merged into `py-auto`. The proposals
  and the verdicts stay in `../py-runs/relevel/`.
- **Releasing.** `run.py --release`, given when the author says, merges
  `py-auto` into the content repository's `main` and seeds the module
  locally, then in prod through the deployment repo's tunnel. It rewrites
  `modules/py/STATUS.md` from `climb module status py` and commits it.
  It also rewrites each `Release` item's count in `docs/TODO.md`, ticking a
  complete topic, and leaves that change for a commit the author asks for.
- **Order.** A subtopic starts once every subtopic it `needs` is merged, at
  most `--jobs` at a time. One that fails, or a step running past
  `--hours`, stops the subtopics needing it, which the report marks as
  skipped.
- **Watching and stopping.** `run.py --level <n> --status` prints a line
  per subtopic: queued, running, done or failed, minutes since its last
  activity, and its last line in `progress.md`, which the run appends to
  after every step. A running subtopic silent for 20 minutes is flagged.
  `../py-runs/report-L<level>.md` gains a line per finished subtopic, and
  `../py-runs/logs/` holds each session's events as they happen. Creating
  `../py-runs/STOP` starts no new subtopic and lets the running ones finish.
- **Resuming.** Running the same command again resumes: a subtopic with a
  digest on `py-auto` is skipped, and `scratch/<sub>-L<n>/state.json`
  names the steps a subtopic finished, so it goes on from the next.
- **The usage limit.** A session ending on the usage limit fails nothing.
  The step waits until the reset the message names, five minutes past it,
  or 15 minutes when the message names no hour, then runs again.
- **Before a long run,** write one subtopic with `--only <sub>` and read its
  digest, since a fault in a brief repeats in every subtopic.
