# Authoring a module

How a knowledge module's files are written. `docs/architecture/knowledge.md`
gives the records the seed builds from the files and the rules the engine
applies to them. `rules.md` beside this file gives the numbered rules every
bank and lesson holds, and this file does not repeat them. `concepts.md`
gives what changes for a module written from its concepts.

A module lives in the content repository as `modules/<slug>/course.toml`
beside `banks/<topic>/<subtopic>.toml`. A module's own `CLAUDE.md` there adds
its own rules, such as how its snippets are verified, and those rules take
precedence over this file.

## Questions

- **Claude writes the banks.**
- **An id is unique within a module and never changes once published.** The
  seed matches a question by its id, and the user's answers stay with that
  id. An id opens with a short tag naming its subtopic.
- **A level is judged from the question, never from the topic's
  difficulty.** Every topic calibrates the four levels the same way, and
  every level is aimed at an experienced engineer. No question asks trivia or
  the history of the language.
  - **0 Foundation**: what a feature is, and its everyday use. Someone who has
    used the feature a few times answers in under 30 seconds, in one step and
    with no trick.
  - **1 Associate**: the precise behaviour of one feature, which a casual
    user gets wrong and a daily user gets right. One concept, asked as a
    check that the user really knows the feature.
  - **2 Professional**: an edge case, or the interaction of two or more
    features. The question needs reasoning rather than recall, at the depth
    of a senior engineer's code review.
  - **3 Expert**: a production failure, an implementation mechanism, or a
    tradeoff that takes real experience to judge. Staff-level knowledge, or a
    library author's.
- **Three tie-breaks settle a level.** Obscurity alone does not raise a
  level, so an obscure fact recalled as one concept is still L1. A long
  snippet does not raise a level where the reasoning is one step. Version
  trivia is at most L1, unless the change between versions causes real bugs.
- **The levels of one subtopic form a ladder.** L0 is always open, and each
  higher level's new questions open once the level below is passed. An
  unwritten level blocks nothing, and a seen question is always reviewed. A
  subtopic's L0 is written before its higher levels are relied on.
- **The banks fill lazily.** L0 and L1 are written across the whole module
  first, and L2 and L3 near the user's frontier.
- **The format follows what the question trains.** `short` forces the recall
  of a precise token. The authoring format `card` asks why, when or at what
  cost, and the seed stores it as an open question. `choice` asks the user to
  discriminate between plausible alternatives.
- **An open question's `key` lists the points its answer has to contain**,
  ordered from the mechanism to its consequence to how it is detected or
  fixed. The user ticks the points recalled, and the grade follows from the
  ticks. Rule 13 gives the count, the length and the wording of a point.
- **An open question's `traps` are known wrong claims, zero to three**, each
  written as the wrong claim itself. A trap is added only for a misconception
  seen in a drill or clearly standard, and never to fill the field.
- **A choice showing several lines of output joins them with `, then `**, as
  in `10, then error 2`. A line holding a comma of its own is quoted.
- **The two builds of CPython are the default build and the free-threaded
  build**, named so in prompts and details. `python3.14t` names the binary
  where the binary matters.
- **A typing snippet imports every name it uses**, `reveal_type` and
  `overload` included, so the snippet runs and type-checks as shown.

## Details

- **A detail is structured, under `[q.detail]`.** `mechanism` is required:
  how the feature works and why, in one to four sentences. `example`,
  `pitfalls` (one to six), `versions` and `diagram` are optional. An example
  is verbatim code or a concrete case, run before it is published.
- **An open question adds `key_detail` and `traps_detail`**, one entry per
  point and one per trap.
- **A short accurate section is preferred over a long one**, and a section
  that would be filler is left out.
- **A diagram is added only where the structure is the content**: a
  hierarchy, an MRO or a lookup order, a state machine, a request or data
  flow, a timeline of who runs when.
- **A structure is a Mermaid diagram**: a ` ```mermaid ` fence in a lesson, or
  a question's `diagram` that is one such fence alone. The seed draws it to
  the screen's width, and a drawing made of characters scrolls sideways on a
  phone. `docs/architecture/knowledge.md` `## Diagrams` gives how it is drawn.
- **A Mermaid diagram is laid out top to bottom, as `flowchart TB`, with at
  most three nodes side by side.** A wider one shrinks to fit a phone, and its
  labels shrink below reading size. A long or wide structure is split into
  two diagrams, or into subgraphs stacked top to bottom.
- **A hierarchy puts the parent on top, joined to each child by a plain line
  (`---`)**. An arrow reads as "subclass of" in one diagram and "has
  subclass" in the next, and the reader has to learn its direction again.
- **A Mermaid label writes `#gt;`, `#lt;` and `#amp;` for `>`, `<` and `&`**,
  and is quoted where it holds other punctuation. Mermaid drops a bare `>`
  from a label.
- **A `text` block holds character art alone**: a memory layout, a trace
  aligned by column, a timeline whose columns are positions in time. Its lines
  hold at most 60 characters.
- **A table is a markdown table**, in a lesson or as a question's whole
  `diagram`: a comparison, or a trace with a row per step. A phone draws a
  markdown table to its width, and scrolls a table drawn in characters
  sideways.
- **A fact in a diagram is verified as code is**, against `__mro__` or the
  real order of the output.

## Spelling

- **Spelling is British, in its Oxford form**: `-our` and `-re` (behaviour,
  centre), `-ize` (specialize, serialize, as Python's own names spell them)
  and `-yse` (analyse).
- **A heading, a slug, an id and code keep their spelling.** A question
  points at a heading's anchor, and the log keys on slugs and ids.

## Lessons

- **A lesson is a node of the graph**, declared as `[lesson.<slug>]` in
  `graph.toml`, with its body in `lessons/<slug>.md`.
- **A lesson is a micro-lesson: one concept, two to four minutes to read.**
  `pretest` is 2, and 1 for a very short lesson.
- **A lesson carries a why of one or two sentences, then `##` sections.** It
  carries a diagram or a runnable example with its real output, the common
  mistakes and a link to the docs. The output sits in an `output` fence right
  under the example's `python` fence, which rule 2 compares it against.
- **A lesson links a related lesson inline**, as `[text](lesson:slug#anchor)`.
  `needs = ["lesson:<slug>"]` sets the reading order, and names only lessons
  of the same subtopic.
- **Every question names the section teaching it**, as
  `lesson = "<slug>#<anchor>"`, and the seed refuses a question without one.
- **One lesson covers one concept cluster of one subtopic level**, usually
  six to fifteen questions, with one `##` section per concept. A new question
  joins an existing section or adds a section.
- **A lesson stays locked until the level it teaches is open**, so lessons
  surface with the frontier.
- **A lesson's slug opens with its subtopic's slug.** A lesson with a generic
  slug is prefixed by its topic, as in `typing-basics-…`.

## The module's maps

- **The prerequisites live in `graph.toml`**: direct prerequisites alone,
  with levels matched up to `match_up_to`. An `[[edge]]` carries an `offset`
  where a prerequisite needs more depth.
- **The graph is content.** An edit to the graph is followed by `just
  seed-module <slug>`, whose checker refuses a cycle and an unknown subtopic.
  The unlocks are recomputed from the answers, so an edit never loses
  progress, and adding an edge only holds back new questions. A tier groups
  the display alone.
- **The certifications live in `certs.toml`**, holding only the defaults and
  the exceptions. The defaults are the exam size, the pass share, the
  retention and the coverage. The exceptions are `[scope.<topic>]`,
  `[[edge]]` and `[[unedge]]`.
- **Every certification is implicit**: every topic and `all`, at every level.
  Their prerequisite graph is derived from `graph.toml`, the seed validates
  the file, and the Certifications page of either client shows the matrix.
- **The certified levels are `levels = [0, 1, 2]`, and Expert is practice
  alone.** A topic's Expert level is enabled with `[scope.<topic>] levels =
  [0, 1, 2, 3]` once two things hold. Its Expert pool holds at least 1.5
  times the exam size in questions other than open ones, and its L3 concepts
  are covered. A certified level with too few questions shows "not enough
  questions yet".
- **A coverage map lists each subtopic's concepts**, in
  `coverage/<topic>.toml`, each with its level, its source and the questions
  covering it.
- **The coverage map defines a complete module**: every concept has at least
  one question at its own level. A new question names its concept by joining
  that concept's `covered_by`. A concept found in a source is added to the map
  first, and covered after.
- **The duplicate groups a coverage map records do not grow.**

## Checking

- **The module check and the seed's own gate pass after every change.**
  `rules.md` names what each checks. The content repository's pre-commit hook
  and `just seed-module` both run them.

## A new module

1. Write `modules/<slug>/course.toml`, with `title`, `pass_ratio`, `kinds`,
   the optional `code_kinds`, `code_lang` and `order`, and the topic list.
   `modules/python/course.toml` is the example.
2. Write `modules/<slug>/CLAUDE.md` with the module's verification rules.
   Add `requirements.txt` where its snippets import a library, and
   `check.toml` where a rule skips something.
3. Write L1 banks for every subtopic, then run the module check and `just
   seed-module <slug>`. Both clients fetch the seeded module as their next
   snapshot.
