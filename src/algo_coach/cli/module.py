import argparse
import json
import os
import sys
from pathlib import Path

from algo_coach.knowledge.authoring import Checked, check, in_sub, load, near

# set once the run has restarted itself with the module's libraries
RESTARTED = "CHECK_REQUIREMENTS"


def module(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    root = Path(args.content) / args.slug
    if not (root / "course.toml").exists():
        parser.exit(2, f"module check: no module at {root}\n")
    requirements = root / "requirements.txt"
    if requirements.exists() and os.environ.get(RESTARTED) != str(requirements):
        # snippets run on this interpreter, which holds the module's libraries
        os.environ[RESTARTED] = str(requirements)
        argv = ["uv", "run", "--with-requirements", str(requirements), "algo-coach"]
        os.execvp("uv", [*argv, *sys.argv[1:]])
    if args.near is not None:
        for line in near(load(root), args.near):
            print(line)
        return
    checked = check(
        root, run=not args.no_run, other_versions=not args.no_versions, fresh=args.fresh
    )
    elsewhere = ""
    if args.sub:
        report, named = checked.report, in_sub(load(root), args.sub)
        errors = [e for e in report.errors if named(e)]
        warnings = [w for w in report.warnings if named(w)]
        others = (len(report.errors) - len(errors), len(report.warnings) - len(warnings))
        report.errors, report.warnings = errors, warnings
        elsewhere = f"outside {args.sub}: {others[0]} errors, {others[1]} warnings"
    if args.json:
        report = checked.report
        whole = {
            "errors": report.errors,
            "warnings": report.warnings,
            "ran": checked.ran,
            "missing": report.missing,
        }
        print(json.dumps(whole, indent=2))
    else:
        for line in summary(checked):
            print(line)
        if elsewhere:
            print(elsewhere)
    if checked.report.errors:
        parser.exit(1)


def summary(checked: Checked) -> list[str]:
    report = checked.report
    found = [f"warning {line}" for line in sorted(report.warnings)]
    found += [f"error   {line}" for line in sorted(report.errors)]
    runs = ", ".join(f"{n} {kind}" for kind, n in checked.ran.items())
    if checked.ran:
        runs += f", {checked.executed} of them executed and the rest kept"
    total = f"{len(report.errors)} errors, {len(report.warnings)} warnings"
    found.append(total + (f"; ran {runs}" if runs else ""))
    if report.missing:
        names = ", ".join(f"{name} ({n})" for name, n in sorted(report.missing.items()))
        found.append(f"not run, importing a module that is not installed: {names}")
    if report.fragments:
        found.append(
            f"not compared: {report.fragments} output snippets that need what their prompt "
            "describes, and raise NameError or SyntaxError alone"
        )
    if report.unreplayed:
        found.append(
            f"not replayed: {', '.join(report.unreplayed)}, which read a file the transcript "
            "does not show"
        )
    if report.made_up:
        found.append(
            f"not run: {report.made_up} snippets importing a module check.toml lists as made up"
        )
    return found
