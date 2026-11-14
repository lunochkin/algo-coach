Write the subtopic {topic}/{sub} ("{title}") of the knowledge module `{module}`, at level {level} alone.

Follow the skill at {engine}/.claude/skills/concept-author/SKILL.md through all three stages, and approve by exception as {engine}/docs/authoring/concepts.md `## Stages` gives: apply each fix a review recommends, and write what needs the author into the digest instead of stopping to ask.

This run's content repository is the git worktree {wt}, not {engine}/content. Use it for every path, read the module at {wt}/modules/{module}, and run the check as `uv run algo-coach module check --content {wt}/modules {module}` from {engine}. The subtopic is already named in course.toml and in graph.toml `[needs]`: lay out its lessons and write the rest. The subtopics it needs are written already; read their concepts, and ask nothing a needed subtopic asks.

Edit nothing outside {wt}/modules/{module}, and nothing in {engine}. Do not commit and do not seed. Keep scratch files in {scratch}.

End when stage 3 meets the stopping rule and the check reports 0 errors. Write the digest to {wt}/modules/{module}/review/{topic}-{sub}-L{level}.md, its first line `DONE` or `FAILED: <reason>`.
