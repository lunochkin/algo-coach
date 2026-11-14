Be the decide session of concepts.md `## Stages`. You wrote none of this subtopic's files. The digest {digest} opens with `## For you`, the questions the three stages left, and {scratch}/decisions.md holds the reasoning behind each.

For each question:

- Read the files it names and judge it yourself. The recommendation beside it is advice: check it against the rules and the layer above, and look for what it missed. A recommendation once named one construct outside the baseline, in an example that held four.
- Decide one of three: apply the change, keep the files as they are, or defer the case to a later level.
- Apply a change in the subtopic's own files alone: its concepts, its lessons and its bank. A claim you change stays true in every case its wording covers, so run the cases you rely on. Where a claim changes, its lesson section, its misconceptions and the questions resting on it follow, and each misconception keeps a wrong choice embodying it.
- A construct a subtopic this one needs teaches is taught here too: graph.toml `[needs]` names those subtopics. Such a construct needs no change to the baseline.
- Leave two kinds for the author, and change nothing for them. The first is a change outside the subtopic's files: `rules.md`, `concepts.md`, a skill, the engine, or the module's `CLAUDE.md` and its baseline. The second retires a question already on the content repository's `main`: `git -C {wt} show main:modules/{module}/banks/{topic}/{sub}.toml` lists those. Rewriting such a question as a new task retires it. A reworded prompt, choice, `explain` or `why` does not.
- Before leaving a question for the author, look for a change inside the subtopic's files that makes the outside change unneeded, such as a rewritten example, or a question not yet on `main` rewritten as a new task. Leave the question only where no such change exists. Both baseline questions of the first trial had one.

Then rewrite the digest's opening, keeping its first line `DONE` and its `## Log` unchanged:

- `## For you`: the questions left for the author, each written as before, or `Nothing.` alone.
- `## Decided`: one numbered item per question you answered, with the decision and its reason in one or two sentences.

Append one bullet per decision to {scratch}/decisions.md, under the heading `## Decide`. End when the module check reports 0 errors.
