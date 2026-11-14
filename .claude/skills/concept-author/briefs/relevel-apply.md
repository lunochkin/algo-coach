Apply the agreed level moves of this subtopic, as `docs/authoring/concepts.md` `### Re-levelling` step 3 gives. The moves are in {moves}, each with the rule it rests on.

- Set each moved concept's `level`. Move its lesson section into a lesson file of its new level: graph.toml's `[lesson.<slug>]` entries name the lesson files, their levels and what each teaches. Where the subtopic has no lesson at the new level, add one, as stage 1 lays lessons out, and point the concept's `taught_by` at the moved section.
- Find what each move breaks, and fix only that. A witness, a lesson block or a question of the old level that uses a fact moved up now uses something taught later. A moved concept's own witness and questions may use a construct its new level does not hold. Keep every question's id.
- A question already on the content repository's `main` keeps asking what it asks: `git -C {wt} show main:modules/{module}/banks/{topic}/{sub}.toml` lists those. Where a move would require rewriting such a question as a new task, leave that move unapplied, and write it under the digest's `## For you`, with what it would change.
- Add to the digest {digest}, after `## Decided`, a section `## Re-levelled`: one line per move, applied or left, with its reason.

End when the module check reports 0 errors.
