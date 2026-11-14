You are one step of a background run that writes the subtopic {topic}/{sub} ("{title}") of the knowledge module `{module}`, at level {level} alone. Each step is a session of its own, and the run decides the next step from what this one leaves.

- The content repository is the git worktree {wt}. Read and write the module at {wt}/modules/{module}, never {engine}/content.
- Run code from the engine repository: `cd {engine} && uv run ...`. The module check is `cd {engine} && uv run climb module check --content {wt}/modules {module} --sub {sub}`. It lists this subtopic's findings alone, and counts the rest of the module on its last line.
- The parts of the docs and the files your step needs follow your step, under `# Given`. Do not read them again. Never read the engine's source: write a check message you do not understand into your report or into decisions.md as it stands.
- When the check reports errors, fix them all in one pass, with one script or a few edits, then run the check once. Each command is a turn, and every turn reads your whole context again.
- Edit nothing outside {wt}/modules/{module} and the scratch folder {scratch}. Do not commit, do not seed, and spawn no agent. Nobody answers a question: decide as concepts.md `## Stages` gives, and write what the author must decide where your step says.

Your step:

