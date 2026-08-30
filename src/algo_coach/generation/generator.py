"""Writing a problem for one template: the statement, the canonical solution
and the first test cases.

One call for all three. Cases asked for after a solution exists describe
whatever that solution happens to do, where cases written beside the statement
describe what the problem asks. The same call is why the statement comes
first in the brief: the code and the cases are asked to follow from it.

The prompt is the whole of it here. What the reply has to come back as, and
what is done with it, are the steps after this one.
"""

from algo_coach.schema import Card, Template

SYSTEM = """You write practice problems for one form of a technique.

You are given a template: a form a solver reproduces from memory, its cue, and
the code it comes back as. Write a problem that this form solves.

Produce three things.

1. A statement. Self-contained prose: what the input is, what to return, the
   constraints that bound them, and one worked example. It must not name the
   technique, the template, or the data structure the solution uses. The solver
   has to derive the form from what is asked.
2. A canonical solution. Python, one module-level function named `solve`,
   taking its arguments positionally. Written to display the form rather than
   to be clever.
3. Test cases. Each is the positional arguments and the expected return.
   Include the edge cases the statement admits. They must separate a correct
   solution from a plausible wrong one: a solution that handles the ordinary
   input and gets the boundary wrong has to fail at least one case.

The cue and the notes name concrete settings so the form is recognisable: a
domain, an object, a scenario. Your statement uses none of them. Such a setting
is usually the published problem the cue was written from, and a solver who
recognises that problem has not derived its form. Choose a setting neither the
cue nor the notes mentions.

Write the statement first, and let the solution and the cases follow from it.
Cases read off a finished solution test what that code does rather than what
the problem asks.

The statement admits one reading. Another solver will write a solution from it
alone, and a disagreement between the two discards the problem. State how ties
are broken and what an empty input returns.

Arguments and returns are JSON values: numbers, strings, booleans, lists and
objects. A case gives its arguments in the order `solve` takes them."""


def prompt(card: Card, template: Template) -> str:
    """The brief: one form, and the technique it belongs to.

    The technique's cue is carried beside the template's because they answer
    different questions. One says when to reach for the technique at all, the
    other which of its forms is being asked for. A brief holding only the
    second would leave the model to infer the subject from a form.

    The form itself is sent, as it is to the matcher. A cue and a title name a
    shape the model would otherwise have to guess at.
    """
    return "\n".join(
        [
            f"Technique: {card.technique}",
            f"Reach for it when: {card.trigger}",
            "",
            f"Template: {template.title}",
            f"Cue: {template.trigger}",
            *notes(template),
            "Form:",
            *(f"  {line}" for line in template.code.splitlines()),
        ]
    )


def notes(template: Template) -> list[str]:
    """What to read about this form, where the template carries it. Absent
    rather than empty: a labelled heading with nothing under it reads as a
    field the author left blank."""
    if template.notes is None:
        return []
    return ["Notes:", *(f"  {line}" for line in template.notes.splitlines())]
