Do stage {stage} step "Review" of SKILL.md, as the reviewer. You wrote nothing you review, and you edit no file of the module: you write your report and your case script alone.

{scope}

Write your report to {report}. Its first line is exactly `COUNTS WRONG=<n> DEFECT=<n> STYLE=<n>`, counting every finding of this review, a GAP counted as a DEFECT and a concept or lesson finding counted by its own severity. A finding that {scratch}/decisions.md already leaves open for the author is listed under a heading `## Open for the author` and not counted: the run cannot fix it, and counting it again forces another full review. Then one line naming the scope. Then the findings alone, each in one to three lines: its severity, where it is, what is wrong, and the fix you recommend. In stage 3, write the concept and lesson findings in a section of their own. Write no section on what passed and no summary: the fixer reads findings alone.

Write every case you run beyond the check into one script under {scratch}, and run it once; add the cases its output raises and run it a second time at most. Each command is a turn, and every turn reads your whole context again.
