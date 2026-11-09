# Knowledge

Declarative knowledge: modules of questions a user answers from memory, the
schedule that spaces them, and the records the answers leave. Part of the
architecture, and `README.md` is the map.

The rules here were learn's, a personal study app merged into the engine in
Phase 14. learn's native app became the engine's client, and it carries the
same rules in TypeScript. Shared fixtures hold the app and the server to this
file.

## Modules

A module is one subject: Python first, then algorithms and system design.

- **A module holds topics, and a topic holds subtopics.** A topic carries a
  tier, which orders the listing and gates nothing. A subtopic belongs to one
  topic, and its questions are listed in the order it names them.
- **Every question sits at one of four ranks**: 0 Foundation, 1 Associate,
  2 Professional and 3 Expert. A rank measures the depth of a question. A
  problem's difficulty is a different field, on a different record.
- **A group is one subtopic at one rank.** Gating, coverage and the frontier
  are all counted per group.
- **A module is authored in files and seeded into Postgres**, as a card is. The
  authoring format lives beside the files in the private content repository.
  This file gives the rules the engine and the app apply to what is seeded.
- **A module, a topic, a subtopic, a question and a lesson each carry an
  engine-minted id**, and the seed matches each by its authored slug. A log
  record then references a minted id, as `README.md` requires of every
  append-only record.

## Seeding

The seed reads the authored files and writes the content tables. A re-seed
refreshes what the files still hold, and the log keeps every reference it
already made.

- **A seeded row a log record references is retired, never deleted.** This
  holds for a module, a topic, a subtopic, a question and a lesson. A deleted
  row would leave its answers and marks pointing at nothing.
- **A retired question is never served and never counted.** It leaves its
  group, its coverage and its certification, and its answers stay readable.
- **A question's slug names one question for good.** A fixed typo or a
  clearer wording keeps the slug, and the seed refreshes the row.
- **A question asking something new takes a new slug.** The old answers
  answered the old question, and a new slug keeps them from counting toward
  the new one. The old slug is retired.
- **A retired slug is never reused.** A reused slug would attach the old
  answers to whatever question took it.
- **The author decides which of the two an edit is.** The seed sees changed
  text and cannot tell a clearer wording from a different question.

## Questions

- **A question carries a prompt, a kind and a format.** The kind is the
  module's own vocabulary, such as concept, output, pattern or debug. A module
  names which kinds carry a code snippet.
- **A question is answered in one of three formats.**
  - `choice`: three to eight options, one or more correct. The options are
    shuffled on every display, so a position carries no answer.
  - `short`: a typed reply, matched against the accepted replies after
    whitespace, quotes and backticks are removed. Case is ignored unless the
    question says otherwise.
  - `open`: the user answers in their own head, reveals the key, and ticks the
    points recalled, the traps fallen into, and anything else said wrong.
- **An open question's key is two to six points.** Each point is one fact the
  answer has to contain. A trap is a known wrong claim, and a question carries
  up to three.
- **An open question is graded from the ticks.** Every point recalled with no
  trap and nothing else wrong grades `k`. Every point with a trap or something
  else wrong grades `p`, and so does some but not all of the points. No point
  recalled grades `n`.
- **A reply ending in `?` is a guess**, on `choice` and `short` alone. A guess
  is stored apart from whether the reply was correct, since a correct guess
  shows the fact is not yet held.
- **A question carries its explanation and its detail**: how the mechanism
  works, an example, pitfalls, version notes and a diagram, each optional but
  the mechanism. The detail is shown on request after an answer.
- **An open question is excluded from exams.** Its grade is the user's own
  report, and an exam reads a verdict the user did not give.

## The schedule

Each question's memory is FSRS-6, replayed from the user's answers.

- **Each answer becomes a rating.** An open question grades `k` to Good, `p` to
  Hard and `n` to Again. On `choice` and `short`, a correct reply that is not
  a guess rates Good, a correct guess Hard, and a wrong reply Again. Easy is
  never used.
- **An answer counts as a pass when it rates Good.**
- **A question's state is replayed from its answers in time order**, each at
  the moment it was given, starting from a new card in FSRS's sense. The
  state is stability, difficulty and the next due time. It is derived on
  every read and never stored.
- **The settings are py-fsrs's defaults**: the FSRS-6 default parameters,
  desired retention 0.9, a maximum interval of 36500 days, learning steps of
  1 and 10 minutes, and a relearning step of 10 minutes.
- **Fuzzing is off.** The state is replayed on every read and on every device,
  and unseeded fuzz would give each replay a different due time.
- **Elapsed time between answers is counted in whole days.** Under a day,
  FSRS's short-term stability applies.
- **A question's state at a moment is one of five.**
  - unseen: no answer yet.
  - weak: the last answer was not a pass, however long ago.
  - due: the due time has passed.
  - retained: stability is at least 21 days.
  - learning: any other seen question, including one waiting on a step.
- **A question is servable when it is unseen or its due time has passed.**
  Every queue serves servable questions alone. A weak question inside its
  step waits for the step.
- **A question is passed once any of its answers was a pass**, and stays
  passed. A group is done when its passed share reaches the module's pass
  ratio.

## Gating

New questions open as earlier ones are passed. A question already seen is
reviewed whatever gates it.

- **Ranks open in order within a subtopic.** A rank opens when every lower
  rank of the same subtopic is done or holds no questions. Rank 0 is always
  open.
- **A module may carry a prerequisite graph between subtopics.** An edge from
  one subtopic to another, at an offset, opens the first subtopic's rank only
  once the second subtopic is done up to that rank plus the offset. Ranks
  above a configured bound match at the bound.
- **A gate restricts new questions alone.** Every review reaches a seen
  question in a locked group, so a reordered graph never hides a fact the
  user already met.
- **The graph is content, and an unlock is never stored.** Each unlock is
  derived from the answers and the current graph, so editing the graph needs
  no migration and loses no progress.
- **The frontier is the open groups that are not done**, ordered by the
  length of the prerequisite chain below each subtopic, then by listing
  order. A new question comes from the frontier.
- **A graph that fails its own check opens everything.** A cycle or an
  unknown slug would otherwise lock questions nobody can unlock.

## Lessons

A lesson is a short text teaching one or more groups, read before their new
questions.

- **A lesson names the groups it teaches and what it needs**: a group done, or
  another lesson read. A lesson unlocks once its needs hold and every group
  it teaches is open.
- **A lesson is read or not, by the user's latest mark.** A mark can reset a
  read lesson.
- **A lesson holds its new questions back once its pretest is spent.** The
  pretest counts the lesson's questions a user may meet before reading it,
  two by default. The lesson's unseen questions then wait until it is read.
- **A question names its lesson, or takes the lessons teaching its group.** A
  question with several lessons waits while any one holds it.
- **A queue offers a lesson where it would serve a new question**, after the
  reviews, and at most once per queue.

## Queues

A queue picks each question at the moment it is needed, from what is servable
then. The user stops a queue at any time, and a queue ends when nothing is
left to serve.

- **Reviews come first, ordered weak, due, unseen, learning, retained.** Ties
  break at random.
- **A step due within 20 minutes is served early** when nothing else is
  servable, so a one-minute step does not end the queue.
- **New questions are limited per day, and reviews never are.** The limit
  counts questions first answered today across every device, ten by default.
  The day starts at 04:00 local time.
- **The next queue serves the reviews, then the frontier's new questions.**
  Over every active module, the modules take turns.
- **The review queue serves the weak and due questions alone**, at every rank,
  locked or not. It serves no new question.
- **The filtered queue serves chosen questions from one module**: by topic,
  subtopic, rank, kind, or weak and due alone. Locks do not apply. After the
  servable ones, it serves learning and retained questions it has not yet
  asked.
- **Stopping a queue stores a stint**: the queue's mode, how many questions
  were answered, and the score.

## The focus

The user can aim the next queue at one module, one topic, one subtopic or one
certification.

- **The latest focus record stands**, across every device. A record naming no
  module clears the focus.
- **A relaxed focus serves every servable review first**, then the focus's new
  questions. A strict focus serves the focus's own reviews alone, and counts
  the rest as waiting outside it.
- **A focus degrades with the content.** An unknown module means no focus, an
  unknown topic keeps the module, and an unknown subtopic keeps the topic.
- **A certification focus covers its scope and every prerequisite group**, so
  the unmet prerequisites come first.

## Module status

- **A module is active, paused or archived**, by the user's latest status
  record. The status is the user's, never the module's.
- **A paused module leaves the next queue, the review queue and exams**,
  unless the user names it. The filtered queue still offers it.
- **An archived module is also hidden everywhere** but the module list. Its
  answers stay, and restoring it loses nothing.

## Certifications and exams

- **A certification is a scope at a rank**: one topic, or the whole module.
  Every scope at every rank is one. A module's certification file holds the
  defaults and the exceptions, never the list.
- **Certifications form a graph derived from the prerequisite graph**, never
  stored. A topic's rank needs its rank below and every topic its subtopics
  need. The module's rank needs every topic at that rank.
- **A certification is earned on four conditions**: its prerequisites are
  earned, every subtopic's group is covered, enough questions are retained,
  and its exam was passed.
- **Coverage is the passed share of each group.** Retention is the share of
  the scope's questions at that rank whose stability reaches a set number of
  days.
- **A certification lapses back to needing a refresh** when coverage or
  retention falls short after its exam. A lapsed certification still counts
  as earned for the ones that need it, so one lapse does not cascade.
- **An exam is a fixed sample from a scope at one rank**, with no feedback
  until the end. A level exam samples every open group at a rank instead.
  Each exam answer is stored as an answer, and the exam as a stint.
- **An exam is offered only once everything else in its certification
  holds.** A certification exam passed is stored as its own record.

## The records

Six append-only tables hold the user's knowledge log, one per kind of event.
Each is private to the user, and each refuses an update and a delete by a
trigger, as `README.md` requires.

- **Every record carries the same base**: an engine-minted `id`, a
  `client_id`, the `user_id`, the `device` that wrote it, the moment the user
  acted, and `created_at`.
- **The client mints `client_id`, and a user's ids are unique.** A retried
  upload then writes nothing twice. The app works offline, so a record can
  reach the server long after the user acted.
- **The schedule reads the moment the user acted, never `created_at`.** A
  record uploaded a day late was still answered when the user answered it.
- **`answers`**: the question, whether the reply was correct, the guess flag,
  and for an open question the grade, the points missed, the traps fallen
  into and the wrong flag.
- **`stints`**: the mode, the score and the number of questions answered.
- **`module_statuses`**: the module and its status.
- **`focuses`**: the module, the topic, the subtopic and the certification,
  each optional, and whether the focus is strict.
- **`lesson_marks`**: the lesson, and whether it was read or reset.
- **`certification_exams`**: the certification, the score, the number of
  questions and whether the exam passed.
- **A certification is referenced by its module, its topic and its rank.** A
  certification is derived rather than stored, so no table holds it, and the
  three minted parts name it.
- **The content tables are refreshed by the seed.** Their columns follow the
  authoring format and may change with a migration. The six tables above are
  the part that cannot.
