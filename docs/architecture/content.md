# Content

The product-owned material a practice session reads: the technique vocabulary,
the cards that teach one technique, and which problems exercise which of a
card's templates. Part of the architecture; `README.md` is the map.

## Techniques

The vocabulary the append-only log references.

- **Versioned as code, not stored as data.** A file shipped with the package,
  not a datastore the engine writes.
- **A code carries the criterion for claiming it**, not only its name: its
  kind, what earns it, and the near miss it is confused with. The near miss
  decides cases, because disputes are about boundaries rather than definitions.
  The codes are four kinds of thing, and one question is answered differently
  for each.
  - A procedure counts when the solution performs it.
  - A structure counts when its properties carry the correctness or the
    complexity.
  - A paradigm counts when it is why the solution is correct.
  - A problem class counts when it is what the problem asks for.
- **A kind reaches both readers as its test, never as its name.** The label
  helps only a reader who already knows what it selects; one who does not will
  judge a structure on whether it was performed. The four tests live with the
  kind, so twenty-seven entries state them once.
- **A code is claimed beside the narrower ones, never instead of them.** What a
  solution does is true at several levels: a backtracking search descends, and
  a search tree is a binary tree. An exclusive rule would need a containment
  order over the codes, and nothing generates one — it could only be written by
  hand pair by pair, then disagreed with case by case. Exceptions are per code
  and stated in the entry: `recursion` names a language mechanism rather than
  an approach, so a row counting every self-call would name no skill.
- **What disqualifies a code is incidental use**, never that another candidate
  covers it. The near miss states that line in full: a sorted lookup beside a
  linear pass that dominates, a map standing in for an array. A reader taking
  the near miss for precedence drops codes the user claimed.
- **Inclusive claiming is what keeps a row coherent.** The fallback is the
  problem's own techniques, and those nest already. Under an exclusive rule a
  claimed attempt and an unclaimed one on the same problem would be counted
  differently, so board numbers would move as classification progressed while
  the practice behind them did not. A claim narrows a row; it never
  re-partitions it.
- **The criteria are the prompt.** They reach the classifier beside the
  candidates and the reader beside the code, so one rulebook answers both.
  Editing an entry changes readings, but only for the attempts carrying that
  candidate.
- **A code is never deleted**, because records carrying it outlive it.
  Retirement means an entry in an alias map, applied when grouping.
- **Membership is checked on the write path only.** A model that validated
  codes on read would make the log unreadable by its own schema the moment a
  code was retired.

## Cards

Teaching content about a technique, not the vocabulary itself.

A card organises studying one technique: what to read, what to reproduce from
memory, and what to solve. It is not an ability estimate. Mastery is what a
user can solve, per technique, and the two share no data.

- **Product data, not code.** Cards live in the engine datastore, seeded from
  `content/`, which is gitignored like `data/`. One location, whatever the
  content turns out to be worth keeping private.
- **Granularity follows teaching, not estimation.** One technique can carry
  several cards. Mastery is estimated per technique, so cards are never the
  unit of estimation, and the attempt log never references one.
- **A card names no problem.** It carries a selector: a technique, and the
  filters that narrow it. The ladder is derived from the corpus. Ids are minted
  per engine, so a card holding them would mean nothing in another store, where
  a selector ships anywhere.
- **The ladder covers every studied template.** Its rungs come from the
  template matches, at least one per template, and the selector fills the rest
  out to `size`. Drawn from the selector alone it would exercise the technique
  and leave some forms untouched, since a technique says what a problem is
  about rather than which form solves it.
- **Requiredness is derived from what a rung covers**, never stored. A rung
  covering a studied template is required. A rung covering only the optional
  template is optional. A rung covering both is required, and the optional
  template is offered on it as the alternative approach. That last case is why
  a problem matching several templates is wanted rather than a nuisance.
- **A studied template with no match is a reported gap**, not a quietly shorter
  ladder, and the gap is the input to the next generation run: a form the
  corpus cannot exercise names its own remedy. It creates the work and never
  does it — a ladder that filled itself would be one nobody inspected, and the
  corpus is the product.
- **The recognition cue is its own field**, apart from the prose it could sit
  in, because a probe asks exactly that question: is the form recognised
  unprompted. So it is shown and withheld on its own, where the rest of what to
  read is one authored block the engine never parses. It is carried at both
  levels — the card's says to reach for the technique, a template's says which
  of its forms — because recall is per template.
- **A template states whether its form is a speedup** over the naive solution
  the technique replaces. Backtracking and exhaustive search are their own
  optimum, so no input separates them from a reference. Generation cannot tell
  that from a reference written cleverly by mistake, so the template says which
  it is and a missing separation is a defect only where a speedup was claimed.
- **One template may sit outside the studied set.** A card carries at most one
  optional template, the capstone, authored whole and surfaced on request
  alone. The hard form is worth deriving before it is read, and a card showing
  it unasked would remove that chance permanently.
- **The ladder is resolved at import and re-derived whenever the corpus moves
  under it.** The selector is the truth and the ladder a derived view, so
  resolving it again costs nothing. A started card is re-derived too. Ladder
  progress is a fold over attempts rather than a mark on a rung, so what was
  solved stays solved.
- **A retired problem fills no rung.** A defective one was never a fair test,
  and a telegraphed one teaches recognition of nothing. Re-deriving is what
  removes it, which is the other reason a started card is re-derived.
- **Probes are assigned when a card is started**, not at import, since what was
  unseen at import need not still be unseen. Unseen first, then least recently
  attempted, and never drawn from the ladder, which teaches the form rather
  than testing whether it is recognised unprompted.

## Template matches

Which problems exercise which of a card's templates. The ladder's coverage is
computed from these records. They are the engine's own work: an author names no
problem, so nothing is authored here either.

- **A generated problem asserts its own first match.** It was written for one
  template, so that pair is provenance rather than a reading, and the record
  names `generator` as its source. Nothing pays a call to learn what the
  generator was told to write.
- **A generator's assertion carries no configuration**, as a hand annotation
  carries none. The all-or-none rule is about readings, which are re-derivable
  and so must say by what. Nothing re-derives this pair short of writing the
  problem again, and the problem already names the call that wrote both.
- **It is only ever positive.** The generator asserts the form it was briefed
  on. What else the problem exercises is the matcher's question, and a
  generator saying nothing about a template is not a negative on it.
- **A canonical that passes demonstrates a pair**, and writes a `generator`
  record on it. Asking for the problem in a second form is a generation call
  like the first, and the canonical it produced is the evidence. A model that
  could not write that form has shown nothing about the problem, so a failure
  is not a negative either.
- **A demonstration is free ground truth on a pair a matcher read.** It
  confirms a positive, and on a pair the matcher scored negative it is a caught
  false negative. It replaces no hand pass: the pairs it reaches are the ones a
  ladder wanted, which is a sample nobody drew at random.
- **The same fact sits on the problem and in a match.** `generated_for` names
  the template, and the match is what lets the ladder read one kind of record
  instead of special-casing the problem. They cannot drift, because generation
  writes both in one act.
- **The matcher answers what generation cannot assert**: which templates a
  problem exercises besides the one it was written for, and whether the
  generator's own claim holds. The first is why a rung can cover a studied
  template and an optional one at once, the second the only check on a
  generator drifting from its brief.
- **Three writers, ordered by what each of them knew.** A hand annotation
  stands over both machine sources. A generator's assertion stands over a
  matcher's reading of the same pair, because the generator knew and the
  matcher inferred.
- **One record per template and problem, carrying a verdict.** Not a set per
  template: problems arrive one at a time, and a set record would rewrite pairs
  already settled every time the corpus grew. A claim asserts a whole set
  because the set is the assertion; a match asserts one pair, and pairs are
  independent. A problem matching several templates is the ordinary case.
- **A negative is stored.** Otherwise every re-run re-tests every non-match
  forever. What still needs testing is the pairs carrying no record at the
  current configuration, which is the rule `score` already uses for readings.
- **Written after card import, never before.** Both references are minted: the
  template at import, the problem at generation. So a match cannot be authored
  against a seed file.
- **A call is per problem and card, a record is per pair.** The candidates are
  that card's templates, and the answer is the subset the problem exercises,
  which is the classifier's shape. The records come from one answer.
- **Not every pair is asked about.** A problem is offered only to cards whose
  technique it carries, or the work is every template against every problem for
  an answer that is almost always no. Procedure templates are excluded
  outright: a framing procedure is exercised by every problem its technique
  reaches, so a per-problem verdict carries no information.
- **A card's relation to a problem is a fold over its templates**, never a
  record of its own. A rung is earned when the technique reaches the problem
  and some template matches. Nothing asserts in one place that a problem
  belongs to a card, so nothing is rewritten when one verdict changes.
- **Re-derivation is the normal path, not an exception.** A technique claim
  asks about one attempt, and the question never changes. A match is a template
  against a corpus that grows with every generation run.
- **A hand record settles what stands, not what has been read.** The run path
  skips a pair only where the hand pass settled every template of that card.
  The call asks about the card whole, and a partly annotated card is a question
  still worth asking. The eval reads annotated pairs on purpose, because that
  reading is the measurement.
- **Agreement is per pair, grouped per template.** A call carrying six pairs
  saves requests; it is not a unit of truth. Grouping follows the ladder: a
  form the matcher over-matches fills its rung with problems that do not teach
  it, and one number over the card would average that away.
- **Nothing is scored as a set, and accuracy is not the metric.** A match
  asserts a pair, and a matcher that says yes to everything is already visible
  as a false positive on every template. Most pairs are negative, so a matcher
  naming nothing would score in the nineties and resolve an empty ladder. What
  is scored is the positive verdicts, both directions: what the annotator named
  and the machine missed, and what the machine named and the annotator did
  not.
- **An empty answer is negatives, not a decline.** A claim naming nothing
  answers nothing, and the problem's own techniques keep standing. A call
  naming no template asserts that each of them does not match, which is a
  verdict on every pair and is scored as one. The record shape decides this,
  not the model's behaviour.
- **An annotation records the verdicts its author saw**, as a claim does.
  `informed_by` names them one by one, so a record made after seeing one
  matcher is still independent of another. It is written on every pair the
  answer settles, negatives included, because what the reader saw is a fact
  about the sitting rather than about the verdict.
- **The first hand pass calibrates, a blind one measures.** Annotating is where
  the line gets drawn between exercising a form and merely admitting it. A
  score taken over the pairs that drew that line measures agreement with
  itself. The eval set is annotated from the templates alone, and
  configurations are compared over the pairs both read — the claims rule,
  unchanged.

