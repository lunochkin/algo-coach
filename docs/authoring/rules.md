# Content rules

The rules every module's banks and lessons hold. Each rule is numbered, so a
review or a commit can cite it. `modules.md` beside this file gives how to
author a module, and a module's own `CLAUDE.md` in the content repository
adds the module's own rules, such as the supported versions.

Each rule names how it is checked:

- **seed**: `refusals()` in `src/algo_coach/knowledge/check.py` enforces it,
  and the seed refuses a module that breaks it.
- **check**: `algo-coach module check <slug>` checks it, from this repo, so
  snippets run on the project's interpreter. The run restarts itself with
  the module's `requirements.txt` installed, so a snippet importing a
  library runs too. An error fails the run, and a
  warning is printed for a reader to judge. A module's `check.toml` lists
  what a rule skips, each entry with its reason, and the other interpreters
  rule 5 compares against. The last line of a run names each import of a
  skipped snippet that no installed library provides.
  - A result is kept in the module's `.check-cache.json`, under the code, the
    interpreter and the installed libraries, so an unchanged snippet is not
    run again. `--fresh` runs everything again. A kept timeout may have been
    the machine's load, and a finding it causes names `--fresh`.
  - The content repository's pre-commit hook runs the check when a module is
    staged, and `just seed-module` runs it before seeding.
  - The check also runs every refusal the seed makes, reported as `[0]
    seed`, so a module the check passes is one the seed takes. A question's
    derived detail once passed the check and was refused by the seed.
- **script**: a program could check it, and none does yet.
- **review**: it needs a reader's judgement.

The rules come from three review passes over the Python module in November
2026. Each rule names a defect those passes found.

## Facts and execution

1. **Every question snippet runs and gives the keyed answer.** An `output`
   question's code prints exactly the keyed output on the module's
   interpreter. A question naming an exception raises that exception. A
   snippet is run before it is published, and again whenever it is edited.
   An `output` question with choices holds its printed lines in a keyed
   choice. Output shown by an unkeyed choice alone is refused. A question
   whose answer describes the output instead, or whose prompt runs the code
   another way, is listed under `skip.choice-match`. *check*
2. **Every lesson code block runs on its own and matches its shown output.**
   A block carries its own imports and creates the tables it uses, since a
   reader may jump to any section. A block that connects to Postgres names
   the `app` database (`dbname=app`, `app@localhost/app` or `DSN`), and
   the check runs it on a database of its own on the server
   `TEST_DATABASE_URL` names; with no such server it fails. A block that is a
   deliberate fragment, or that shows a timing, is listed under
   `skip.lesson-block` in the module's `check.toml` with its reason. The
   typing lessons once carried no imports, so no snippet ran as shown. *check*
3. **A `short` answer is the real output, and `accept` covers its equivalent
   spellings**, such as a qualified name, or the reply with and without
   quotes. *check*
   - In a module written by concept, a `short` question has more than two
     plausible replies. A reply with even odds is guessed rather than
     recalled, so the question is a `choice`. The pilot's review found four
     with two plausible values, such as 20 or 25. *check (the replies are
     only `True` and `False`, or yes and no), review (any other pair)*
   - `python` holds 11 questions the check would refuse, left as they are
     while `py` replaces it.
4. **A tool's output is produced by the tool, never written by hand.** Output
   from mypy, pyright or ruff is generated at the version the prompt names,
   line numbers included, and shown whole or with the cut marked `...`. A
   lesson's `$ cat` shows the file a transcript's tool reads, and a `toml`
   block above a transcript is the `pyproject.toml` it runs with. *check
   (lesson blocks and console transcripts; a question's verdict stays with
   review)*
5. **A version appears in the prompt only where behaviour differs within the
   supported range.** The module's `CLAUDE.md` names that range. A feature
   missing on part of the range, or behaving differently across it, keeps its
   version in the prompt. A version tag on behaviour identical across the
   range moves to `detail.versions`. `process-pool-lambda` printed
   `AttributeError` on 3.12 and `PicklingError` on 3.14 under a prompt naming
   no version. The same holds for the free-threaded build: a snippet printing
   something else there names its build in the prompt. *check (every
   snippet runs on each supported version and on the free-threaded build; a
   needless tag and an unnamed build are warnings), review*
6. **A third-party version is re-verified whenever it is bumped.** A library
   can change behaviour under an unchanged question. Ruff 0.17 widened its
   default rule set, and five places still described the old one. The
   module's `requirements.txt` pins each library, and a version named in a
   prompt is the installed one. *check (prompts), review (prose)*

## Answers

7. **Exactly the keyed choices are defensible.** No distractor also works, and
   no unkeyed reading of the prompt makes another choice right. *review*
8. **A multi-answer question leaves at least two wrong options.** "Choose 3 of
   4" reduces to spotting the one false option, so use "Choose 2 of 5" or
   similar. *check*
9. **No two choices contradict each other.** A contradicting pair tells the
   learner that exactly one of the two is keyed. *review*
10. **The correct choice is not recognisable by its form.** It is not clearly
    the longest, and it is not the only choice carrying a fix, a hedge or an
    "or" clause. Distractors are real misconceptions a learner would pick.
    Choices are shuffled, so no "all/none of the above", and no prose names a
    choice by its letter or its position. *check (length is a warning, a
    position is an error), review*
    - The key is not the one choice sharing a part with every other choice.
      A distractor built by changing one part of the key leaves the key at
      the centre, and a reader picks it from the choices alone. At least one
      distractor differs from the key in two parts, so two distractors share
      a part the key lacks. In the pilot, a reader shown the choices alone
      found 22 keys of 97 this way. *check (in a module written by concept,
      a warning), review*
    - A choice predicting what a snippet does states the outcome alone: what
      it prints, what it raises, or that it runs. The reason goes in the
      choice's `why`. A reason on some choices and not others marks a choice
      by its form, and a reason taken from the section repeats the lesson
      (rule 15). Two reviews of one bank asked for a reason, then for none.
      *review*
11. **Neither the prompt nor the code reveals the answer.** A snippet catches
    `Exception` and prints the type's name, rather than catching the exception
    the learner must type. An error message in the prompt does not name the
    answer, and a choice does not echo the prompt's wording. *review*
    - A kind does not reveal the answer either. Where a subtopic's `debug`
      questions show code that is refused, one of them shows code that runs,
      and one `output` question offers an error as a wrong choice. In the
      pilot, all five `debug` questions were keyed `SyntaxError` under one
      prompt. *review*
12. **Each choice's `why` explains that choice, and the mechanism explains the
    keyed answer.** A mechanism that only refutes a distractor leaves the
    learner without the reason the answer is right. *review*
    - In a module written by concept, a `why` does not open with "Right:" or
      "Wrong:". The client marks each choice with a tick or a cross, so the
      word repeats the mark. *check*

## Open questions

13. **An open question carries 3–4 key points, each at most 100 characters and
    readable alone.** The learner ticks one point at a time, so a point names
    its own subject. No point opens with It, This, That, Also or Both, and no
    point leans on another with "also", "too" or "instead". Examples, versions
    and secondary reasons go in the point's `key_detail`, one entry per point.
    *check*

## Structure

14. **One question asks one fact, across the whole module.** Before a question
    is added, every bank of the module is searched for its fact, not only the
    subtopic's own bank. A fact already asked elsewhere is re-angled or left
    out. A pair kept on purpose is recorded in the coverage map's
    `duplicates`. Duplicates across subtopics are the ones a review misses.
    The check's `--near <id>` lists the questions explained most like one
    question, and `--near` alone lists every pair worth a look. *check
    (warning: similar snippets, and two questions whose `explain` and
    `mechanism` read alike), review*
    - No program decides that two questions ask one fact. Of the 185 pairs
      the review of 2026-11-11 named, the warning finds 10 among its 22, and
      `--near` holds 100 among its 1070. A pair the warning names that asks
      two facts is listed under `skip.same-fact` in `check.toml`, as
      `"<id> ~ <id>"` with the reason.
15. **A lesson and its question share a concept, never an example.** A
    question may ask a fact its lesson states, since recalling that fact is
    what the schedule trains. The question puts the fact on an example the
    lesson does not show. Otherwise the learner recognises the lesson's
    example instead of recalling the rule.
    - An example is shared when the lesson holds the question's snippet,
      names, values or keyed output, in a block, in prose or in a table.
    - A copy with its names changed is the same example. So is the same shape
      with only its values changed, and so is the prompt's scenario restated
      with its figures.
    - A section heading stating a question's verdict is a shared example. The
      heading names the subject instead.
    - The lesson changes, not the question: the lesson can teach the concept
      on any example, and the question tests it on its own. A module written
      by concept is the exception: its lessons are approved before any
      question exists, so the question changes, as `concepts.md` gives.
    *check (warning: the snippet's lines in the lesson, as written or with the
    names changed; an expression of the snippet or of the prompt with its
    values; a keyed output the lesson prints; in a module written by concept,
    a name or a literal shared with the section's code), review (the same
    shape with its values changed, a restated scenario, and a heading stating
    a verdict)*
16. **A question's level follows the level definitions in `modules.md`, and one
    fact sits at one level.** The same scenario once sat at L0 in one subtopic
    and at L3 in another. *review*
17. **A question's level is not below the level of the lesson it points at.**
    The lesson opens only with its own level, so the question would wait on a
    lesson that is still locked. A lesson teaches one subtopic level. *check*
18. **Every lesson section has a question pointing at it**, or is a heading
    whose subsections do. A lesson's title names what its sections teach.
    Retiring questions leaves sections behind, and moving sections leaves
    titles stale. *check (warning), review*
19. **Every concept in a coverage map has a question at its own level, and a
    question is filed under the concept it tests.** *check, review*
    - In a module written by concept, the concepts replace the coverage map.
      Every concept has a question, every misconception is named by a wrong
      choice, and a keyed choice names none. *check (an untested concept or
      misconception, and a wrong choice naming none, are warnings)*

## Ids

20. **An id names one question for good.** Fixing a fact, rewording or
    re-levelling a question keeps its id, so the learner's answers still
    count. A question that asks something different gets a new id, and the old
    one is retired. *review*
21. **No id ever used is used again**, checked against the git history of the
    banks. A reused id attaches the old question's answers to the new one.
    *check (git history), seed (store)*

## Edits

22. **Rewriting an example re-checks the text around it.** The prose, the
    shown output and every count that describe the example change with it.
    Most errors in the third pass were lesson text that had drifted from its
    own rewritten example. *review*
23. **A bulk edit is reviewed by a reader other than its author, on its diff,
    before it is seeded.** Each fix pass introduced a new kind of defect, and
    only the next review found it. *review*

## Layout

24. **A program's output is fenced as `output`, and a `text` fence holds a
    drawing alone.** A phone wraps a long line of an `output` block and keeps
    a `text` block whole, since a wrap breaks a drawing. Output fenced as
    `text` scrolls sideways on a phone and hides the end of each long line.
    A box-drawing character appears only in a `text` block, a question's
    `diagram`, or a tool's own output in an `output` or `console` fence.
    Anywhere else it draws a structure, and a phone wraps the drawing apart
    where Mermaid or a markdown table fits the screen. *check (a `text`
    block with no box-drawing or tree characters is warned; a box-drawing
    character elsewhere is refused)*
25. **A line of code holds at most 60 characters, and 40 where it holds
    without a break.** This covers a question's `code` and `example`, a
    lesson fence naming a language, and an `output` fence. A phone fits some
    40 characters and wraps a longer line behind a `↪`. In a snippet read for
    its output, a reader can take that wrap for a line break. *check (a block
    with a line over 60 is warned)*
    - In a module written by concept, a question's `code` holds at most 40
      characters a line. A phone of 2026 wrapped a line of 44. A lesson keeps
      the limit of 60, since its prose can introduce a block split over
      several statements. *check (warning)*
    - A question's snippet holds only what its task needs, and at most 12
      lines in a module written by concept. A task invented to avoid a
      lesson's example grows, and the pilot's level 0 questions reached 15
      lines for one chained comparison. *check (warning above 12 lines),
      review*

## Concepts

Rules for a module written by concept, which `concepts.md` beside this file
describes. A module with no concept files is checked by rules 1 to 25 alone.

26. **A concept's witness prints its recorded output on every supported
    build.** The claim rests on that output, and a lesson and a question quote
    it. The output is compared exactly, since a normalized comparison passes a
    witness whose wording a lesson then misquotes. *check (the project's
    interpreter, and each version and build `check.toml` names)*
27. **A concept holds every field of its record, and a witness with its output
    or a quote of its source.** The source names a section, the level is 0 to
    3, and the concept lists at least one misconception, each with an `id`
    unique in the concept and a `text`. A question naming an unknown concept
    or misconception, or restating a field it derives from its concept, is
    refused. *check*
28. **Each `taught_by` names a section, and each section of a lesson teaching
    concepts is named by one.** A section no concept names asserts what no
    witness checks. A lesson file holds no intro and no common-mistakes or
    links section, since the seed renders them, and a copy written by hand
    drifts from the concepts. *check*
29. **A claim, a misconception and a lesson's prose follow the writing rules a
    program can check.** No sentence opens with What, Where, Neither, Both or
    Nothing, no sentence runs over 40 words, and spelling is Oxford British.
    The rest of the writing rules need a reader. *check (warning), review*
