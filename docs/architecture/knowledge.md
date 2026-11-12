# Knowledge

Declarative knowledge: modules of questions a user answers from memory, the
schedule that spaces them, and the records the answers leave. Part of the
architecture, and `README.md` is the map.

The rules here were learn's, a personal study app merged into the engine in
Phase 14. learn's native app became the engine's client. The same rules in
TypeScript now live in `packages/core`, which the native app and the web app
both import. Shared fixtures hold that package and the server to this file.

## Modules

A module is one subject: Python first, then algorithms and system design.

- **A module holds topics, and a topic holds subtopics.** A topic carries a
  tier, which orders the listing and gates nothing. A subtopic belongs to one
  topic, and its questions are listed in the order it names them.
- **A subtopic may carry a title**, given by its topic, and a client shows the
  title in place of the slug. A subtopic with no title shows its slug, so a
  module authored without titles still reads.
- **A subtopic is shown with its topic's title**, except where its topic
  already heads the view. Two topics can each hold a subtopic called basics.
- **Titles are in sentence case**, as lesson and topic titles are: the first
  word and proper nouns alone are capitalized.
- **Every question sits at one of four levels**: 0 Foundation, 1 Associate,
  2 Professional and 3 Expert. A level measures the depth of a question. A
  problem's difficulty is a different field, on a different record.
- **A group is one subtopic at one level.** Gating, coverage and the frontier
  are all counted per group.
- **A module is authored in files and seeded into Postgres**, as a card is. The
  authoring format lives beside the files in the private content repository.
  This file gives the rules the engine and the clients apply to what is
  seeded.
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
- **A question is servable when it is unseen or its due time has passed.** A
  weak question inside its step waits for the step. A queue serves servable
  questions first, and `## Queues` names the two exceptions after them.
- **A question is passed once any of its answers was a pass**, and stays
  passed. A group is done when its passed share reaches the module's pass
  ratio.

## Gating

New questions open as earlier ones are passed. A question already seen is
reviewed whatever gates it.

- **Levels open in order within a subtopic.** A level opens when every lower
  level of the same subtopic is done or holds no questions. Level 0 is always
  open.
- **A module may carry a prerequisite graph between subtopics.** An edge from
  one subtopic to another, at an offset, opens the first subtopic's level only
  once the second subtopic is done up to that level plus the offset. Levels
  above a configured bound match at the bound.
- **A gate restricts new questions alone.** Every review reaches a seen
  question in a locked group, so a reordered graph never hides a fact the
  user already met.
- **The graph is content, and an unlock is never stored.** Each unlock is
  derived from the answers and the current graph, so editing the graph needs
  no migration and loses no progress.
- **The frontier is the open groups that are not done**, ordered by the
  length of the prerequisite chain below each subtopic, then by listing
  order.
- **A new question comes from the first frontier group with an unseen
  question no lesson holds.** A group stays on the frontier until enough of it
  is passed, so the first group can hold no new question at all.
- **A module names that same group as next up**, with its passed share. A
  module whose open groups all wait for a lesson names that lesson instead.
  Continue and the module then point at one place.
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
  reviews, and each lesson at most once per queue.
- **A question comes between two lessons wherever one is left to serve.** Two
  lesson stops in a row break the queue's flow. A queue with nothing but
  lessons left still offers them one after another.

## Queues

A queue picks each question at the moment it is needed, from what is servable
then. The user stops a queue at any time, and a queue ends when nothing is
left to serve.

- **A queue orders the questions it serves weak, due, unseen, learning,
  retained.** Ties break at random.
- **A step due within 20 minutes is served early** when nothing else is
  servable, so a one-minute step does not end the queue.
- **A client counts such steps apart from the due reviews**, and marks a
  question served early. A due count of zero then never sits beside a queue
  that keeps serving questions.
- **New questions are limited per day, and reviews never are.** The limit
  counts questions first answered today across every device, ten by default.
  The day starts at 04:00 local time, when almost every user is asleep.
- **Each device reads the day in its own time zone.** Midnight UTC falls in a
  US evening, the hours a user practises in. Two devices in different time
  zones disagree on today's new questions and raises for a few hours, and
  that is accepted. A user's time zone as a record of the log is deferred
  until a user practises across time zones.
- **The user can raise today's limit, five at a time**, from Home or inside the
  next and filtered queues. The raise ends when the day does, and the daily
  setting stands again the next day.
- **The daily limit is a setting, and today's raise is a record of its
  own.** `## Settings` gives how a setting is stored. A limit kept per device
  would have the phone and the web offer different counts of new questions
  on the same day.
- **Today's raise is the sum of the raises given since the day began.** Two
  devices raising on one day then add up rather than overwrite each other.
- **The next queue serves the reviews, then the frontier's new questions.**
  Over every active module, the modules take turns.
- **The review queue serves the weak and due questions alone**, at every level,
  locked or not. It serves no new question.
- **The filtered queue serves chosen questions from one module**: by topic,
  subtopic, level, kind, or weak and due alone. Locks do not apply. After the
  servable ones, it serves learning and retained questions it has not yet
  asked.
- **Stopping a queue stores a stint**: the queue's mode, how many questions
  were answered, and the score.
- **A filtered queue starts from a press on the module's groups.** The press
  names the module, the topic, the subtopic or one group, and the user adds
  the level, the kind and the due flag for that queue alone.
- **Starting a filtered queue moves no focus.** The focus aims the next
  queue, and one drill on a subtopic would otherwise retarget it.
- **A filtered queue's choices are stored nowhere.** Each narrows one queue,
  and a record of them would change at most starts. The web carries them in
  the queue's URL, which no other device reads.
- **A level exam opens on the focus's module**, and on a certification
  focus's level. Associate stands where no focus names a level. The focus
  is a record of the log, so the phone and the web open the same exam.
- **The exam size is a setting**, as `## Settings` gives.

## Settings

- **A study setting is a name and a whole number**, and the latest record of
  each name stands across every device. A setting kept per device would
  have the phone and the web serve differently on the same day.
- **Two settings exist.** `new_per_day` is the daily limit on new
  questions, from 0 to 200, ten by default. `exam_size` counts the questions
  an exam samples, from 1 to 500, forty by default.
- **One table holds every setting.** A further setting that is a whole number
  adds a name and its range, and no table.
- **A setting outside its range is refused**, by the engine and by the
  database's own check. An exam sampling no question would be no exam.

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

## Module order

- **The user orders the modules, and the latest order record stands** across
  every device. An order kept per device would list the modules differently
  on the phone and the web.
- **A module the order does not name follows the named ones**, in the order
  the seed gives. A module seeded after the user ordered the rest still
  lists, at the end.
- **The order changes no queue.** The next queue's modules take turns
  whatever the order says.

## Certifications and exams

- **A certification is a scope at a level**: one topic, or the whole module.
  Every scope at every level is one. A module's certification file holds the
  defaults and the exceptions, never the list.
- **Certifications form a graph derived from the prerequisite graph**, never
  stored. A topic's level needs its level below and every topic its subtopics
  need. The module's level needs every topic at that level.
- **A certification is earned on four conditions**: its prerequisites are
  earned, every subtopic's group is covered, enough questions are retained,
  and its exam was passed.
- **Coverage is the passed share of each group.** Retention is the share of
  the scope's questions at that level whose stability reaches a set number of
  days.
- **A certification lapses back to needing a refresh** when coverage or
  retention falls short after its exam. A lapsed certification still counts
  as earned for the ones that need it, so one lapse does not cascade.
- **An exam is a fixed sample from a scope at one level**, with no feedback
  until the end. A level exam samples every open group at one level instead.
  Each exam answer is stored as an answer, and the exam as a stint.
- **An exam is offered only once everything else in its certification
  holds.** A certification exam passed is stored as its own record.

## Projections

A projection reads the user's log forward: the practice the schedule will ask
for if the user keeps answering. A projection is derived on every read and
never stored, as a question state is.

- **The review forecast counts the reviews each learning day will hold**, over
  the next fourteen days. A learning day starts at 04:00 local time, as the
  daily limit's day does.
- **Each review in the forecast is assumed to pass.** The forecast replays a
  question with a Good rating at each due time, and counts the due time that
  rating sets as well. Any other assumption needs a failure rate the log has
  not measured.
- **The forecast is therefore a lower bound on the load.** A failed review adds
  a relearning step and shortens the next interval, and the forecast counts
  neither.
- **An overdue review counts on the first day.** The review is owed now, and a
  forecast dropping it would show less than the review queue serves.
- **Only questions already seen are counted.** A new question enters the load
  on the day the user first answers it, and the user chooses that day. The
  page says so under the forecast.
- **The forecast reads the modules the review queue serves.** A paused module
  and an archived one add nothing.
- **The focus does not narrow the forecast.** A strict focus defers the
  reviews outside it and removes none, so those reviews still fall due.
- **A day counts 24 hours from its start.** A shift to or from summer time
  moves one boundary of the fourteen by an hour, and that is accepted.

### When the focus is reached

The focus panel names the day the focus is projected to be reached, at two
paces side by side.

- **A focus on a module, a topic or a subtopic is reached once every group in
  it is done.** A group is done at the module's pass ratio, as `## The
  schedule` gives.
- **A certification focus is reached once the certification is earned.** A
  lapsed certification still counts, as it does for the certifications that
  need it.
- **The route reads the same rule** to aim its next target.
- **The remaining work is the new questions the focus still needs answered.**
  Each group needs its pass ratio's share passed. A question seen and not yet
  passed is taken to pass on its next review, so it takes no new question's
  place.
- **The first pace is the daily limit**, the `new_per_day` setting. Today's
  room is today's limit less the new questions answered today.
- **The second pace is the user's own**: the new questions first answered per
  day over the last fourteen complete learning days. A day with no answer
  counts as zero. A log younger than fourteen days is read over the days it
  holds, and a log with no complete day yet has no pace.
- **The pace counts every module.** The next queue takes its new questions
  from the focus, so a pace measured before the focus was aimed still applies.
- **Two dates are shown, because they answer different questions.** The
  limit's date says what the setting allows. The pace's date says what the
  user's practice reaches. The gap between them says which of the two is
  holding the user back.
- **A certification's date waits for retention too.** Every review is assumed
  to pass, as in the forecast, and the date is the day enough of its questions
  reach the rule's stability. A question not yet seen is taken to be first
  answered on the day coverage is reached. The exam is taken that day.
- **The date is a lower bound.** A failed review, the time spent reading a
  lesson and a failed exam each push it later, and the projection counts none
  of them.
- **A date more than three years away is not named.** No user plans by it.

Deferred, since only use answers each:

- The retention and the exams of a certification's prerequisite
  certifications. The date counts their coverage alone.
- A forecast per module, on the module's page.

## The records

Nine append-only tables hold the user's knowledge log, one per kind of event.
Each is private to the user, and each refuses an update and a delete by a
trigger, as `README.md` requires.

- **Every record carries the same base**: an engine-minted `id`, a
  `client_id`, the `user_id`, the `device` that wrote it, the moment the user
  acted, and `created_at`.
- **The client mints `client_id`, and a user's ids are unique.** A retried
  upload then writes nothing twice. A client works offline, so a record can
  reach the server long after the user acted.
- **The schedule reads the moment the user acted, never `created_at`.** A
  record uploaded a day late was still answered when the user answered it.
- **`answers`**: the question, whether the reply was correct, the guess flag,
  and for an open question the grade, the points missed, the traps fallen
  into and the wrong flag.
- **`stints`**: the mode, the score and the number of questions answered.
- **`module_status_changes`**: the module and its status.
- **`focuses`**: the module, the topic, the subtopic and the certification,
  each optional, and whether the focus is strict.
- **`lesson_marks`**: the lesson, and whether it was read or reset.
- **`certification_exams`**: the certification, the score, the number of
  questions and whether the exam passed.
- **`setting_changes`**: the setting's name and its new value.
- **`limit_raises`**: how many new questions the raise adds to today's limit.
- **`module_orders`**: the modules, first to last.
- **A certification is referenced by its module, its topic and its level.** A
  certification is derived rather than stored, so no table holds it, and the
  three minted parts name it.
- **The content tables are refreshed by the seed.** Their columns follow the
  authoring format and may change with a migration. The nine tables above are
  the part that cannot.

## The wire

The native app came from learn and still reads and writes learn's formats, and
the web app reads and writes them through the same `packages/core`. The engine
translates at its edge, so the store keeps this project's names.

- **The content reaches a client as one snapshot**, learn's `courses.json` at
  format 6. The snapshot rebuilt from Postgres equals learn's own, so the
  loader in `packages/core` stays as it was.
- **A client syncs learn's log lines**: `attempt`, `session`, `status`,
  `focus`, `lesson` and `cert`. Each line carries a `client_id` and names its
  content by slug.
- **Three lines are the engine's own**: `setting`, `raise` and `order`.
  learn kept the settings, the raise and the module order on the device, so
  its format carries no line for any of the three.
- **A `setting` line carries the name and the value**, as `name` and `n`.
- **An `order` line names every module by slug, as `courses`.** A line naming
  a module the store does not hold is refused, as any line naming unknown
  content is.
- **Two names change at the edge.** learn's `card` format is stored as an
  open question, and its `drill` queue as the filtered queue. A line read
  back carries learn's names again.
- **A line naming content the store does not hold is refused alone.** The
  rest of the upload is stored, and the reply names each refused line.
- **A sync returns the user's records since a cursor**, one append order per
  table. A client merges them into its copy by `client_id`.

## A client's store

The web app and the native app keep the knowledge log the same way. Each app
runs the rules from `packages/core`, and each keeps a copy of the content and
of the user's log on the device. A platform differs from the other only where
the platform itself cannot do the same.

- **A client keeps the snapshot and the user's log between launches.** The
  native app keeps them in SQLite, and the web app keeps them in IndexedDB.
  A launch reads the copy first, so the first question waits for no round
  trip.
- **A launch then syncs from the copy's cursor.** A copy that is gone, after
  a cleared browser or a reinstalled app, syncs with no cursor and receives
  the whole log again. The engine's log is the truth, and a copy is only
  ever rebuilt from it.
- **The snapshot is revalidated by its ETag.** The content moves only at a
  seed, so an unchanged snapshot answers 304 and the copy stands.
- **A record the engine has not acknowledged waits in the outbox.** The
  outbox is part of the copy, so a record survives a closed tab, a killed app
  and a lost connection.
- **An answer is sent within ten seconds of being given.** Answers given in
  quick succession then travel in one upload. Every other record is sent at
  once, since a focus, a status or a limit changes what another device
  serves.
- **A client also syncs when it returns to the foreground**: the app becoming
  active, or the page becoming visible. Records another device wrote in the
  meantime then reach the schedule before the next pick.
- **Every upload returns the records written since the cursor.** An answer
  given on the phone reaches an open web page at the page's next sync.
- **A record leaves the outbox once the engine stored it, knew it already
  or refused it.** A refused line names content the store does not hold, so
  sending the line again would be refused again.
- **The copy is keyed to the signed-in user.** A second account signed in on
  the same device would otherwise read the first account's log and upload
  its outbox under the wrong user. The native app marks each row with its
  owner. The web app keeps one IndexedDB database per user, named by the
  user's id, and the session names the user before the database opens.
- **The engine names the user when it issues a token and in every sync
  reply.** A copy kept before the owner was recorded is then claimed by the
  account whose token wrote it, at that account's next sync.
- **A token the engine revoked keeps the copy.** The app returns to the login
  page, and the outbox waits for the same user's next sign-in. Another
  account signing in reads only its own rows.
- **Signing out sends the outbox, then deletes the copy.** A copy left behind
  keeps a user's log readable on a shared device. An outbox that cannot be
  sent is named before sign-out discards it, so the user decides whether
  those answers are lost.
- **A queue keeps serving while the connection is down**, on both clients,
  since the rules and the copy are on the device.
- **The web app does not start without a connection, where the native app
  does.** The browser fetches the page's own files from the engine on each
  load. A service worker serving those files offline is deferred until a
  user practises on the web away from a connection.
- **The web app's records name the device `web`.** A browser carries no
  stable device name, and telling one browser from another would answer no
  question the schedule asks.
