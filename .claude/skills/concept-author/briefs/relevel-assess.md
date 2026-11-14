You assess the levels of a knowledge module's written concepts, as `docs/authoring/concepts.md` `### Re-levelling` step 1 gives. The test is `## Levels` of that file, which follows under `# Given` with every written concept: its subtopic, its id, its level and its claim.

- Judge each concept against `## Levels` alone. The levels the concepts hold now were set without a rubric, so they are no evidence for themselves.
- Propose a move only where the test clearly gives another level. A concept that fits two levels about equally stays where it is.
- Respect the floor: a concept sits at least at the level of every fact its claim needs. Where a concept moves up, check each concept of the same subtopic that rests on it.
- Read no file and run nothing: the claims are all you judge.

Write {out} as one JSON array and nothing else, one object per move: `{{"topic": "...", "subtopic": "...", "concept": "...", "from": 0, "to": 1, "rule": "<the rule of ## Levels, quoted in a few words>", "reason": "<one sentence>"}}`. Write `[]` where nothing moves.
