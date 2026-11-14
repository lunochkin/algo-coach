Two reviews of the same files, written by two reviewers given the same brief, are compared here. Review A is the reference: {a}. Review B is the candidate: {b}. Read both, and no other file.

For each finding of A marked WRONG, and each marked DEFECT or GAP, decide whether B reports the same problem: the same place and the same fault, in any words, with any fix. A finding B places elsewhere, or a different fault at the same place, is missed. Count also B's WRONG and DEFECT findings that A does not report.

Write {out} as one JSON object and nothing else:
`{{"wrong": <A's WRONG findings>, "wrong_missed": <of those, missed by B>, "defect": <A's DEFECT and GAP findings>, "defect_missed": <of those, missed by B>, "b_only": <B's WRONG and DEFECT findings A lacks>, "missed": ["<one line per finding B missed>"]}}`
