"""The annotation prompt as two panes: the statement with its solution, and one
form's code. It only collects; what lands is the caller's."""

from collections.abc import Callable, Mapping, Sequence

from rich.syntax import Syntax
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Footer, Markdown, Static

from algo_coach.matches import Question, candidates
from algo_coach.schema import Template, TemplateMatch


def evidence(question: Question) -> str:
    """One markdown block rather than two widgets, so the two scroll
    together."""
    return "\n\n".join(
        [
            question.problem.statement,
            "---",
            f"```python\n{question.solution.code.rstrip()}\n```",
        ]
    )


# Answering one question: the pairs it settles, positive and negative.
Answered = Callable[[Question, set[str]], None]

CUE = 60  # how much of a trigger the list shows; the code pane carries it whole

# The editor's palette rather than the terminal's: a form is read here and
# typed out there.
SYNTAX = "xcode"


# One question at a time, over the pool the caller sampled.
class Annotating(App[None]):
    # Stated rather than inherited, so the panes agree whatever the terminal
    # is set to.
    theme = "textual-light"

    CSS = """
    #head { padding: 0 1; background: $panel; color: $text; }
    #statement { width: 50%; padding: 0 1; border-right: solid $panel; }
    #right { width: 50%; }
    #forms { padding: 0 1; background: $panel; }
    #code { padding: 0 1; }
    """

    BINDINGS = [
        Binding("space", "toggle", "pick/unpick"),
        Binding("enter", "record", "record"),
        Binding("s", "skip", "skip"),
        Binding("c", "clear", "clear"),
        Binding("q", "quit", "end"),
        *[Binding(str(n), f"view({n})", "", show=False) for n in range(1, 10)],
        # Plain arrows move the statement, which is what is read at length.
        Binding("down", "scroll('#statement', 3)", "", show=False),
        Binding("up", "scroll('#statement', -3)", "", show=False),
        Binding("pagedown", "scroll('#statement', 20)", "", show=False),
        Binding("pageup", "scroll('#statement', -20)", "", show=False),
        Binding("shift+down", "scroll('#code', 3)", "", show=False),
        Binding("shift+up", "scroll('#code', -3)", "", show=False),
    ]

    def __init__(
        self,
        pool: Sequence[Question],
        read: Mapping[tuple[str, str], TemplateMatch],
        answered: Answered,
    ):
        super().__init__()
        self.pool = list(pool)
        self.read = read
        self.answered = answered
        self.index = 0
        self.focused_form = 0
        self.picked: set[str] = set()
        self.count = 0

    @property
    def question(self) -> Question:
        return self.pool[self.index]

    @property
    def forms(self) -> list[Template]:
        return candidates(self.question.card)

    def compose(self) -> ComposeResult:
        # Markup off on everything the author wrote: a statement is full of
        # `[i]` and `[1, 2, 3]`, which a renderer would eat as tags.
        yield Static(id="head", markup=False)
        with Horizontal():
            yield VerticalScroll(Markdown(id="statement-body"), id="statement")
            with Vertical(id="right"):
                yield Static(id="forms", markup=False)
                with VerticalScroll(id="code"):
                    yield Static(id="cue", markup=False)
                    yield Static(id="code-body", markup=False)
        yield Footer()

    def on_mount(self) -> None:
        # Neither pane takes focus: a focused scrollable claims space for a
        # page down, and space is how a form is picked.
        for pane in self.query(VerticalScroll):
            pane.can_focus = False
        self.show()

    def show(self) -> None:
        """Redraw all four regions for the question and form now in view."""
        question = self.question
        self.query_one("#head", Static).update(
            f"{self.index + 1}/{len(self.pool)}  {question.card.slug}  {question.problem.title}"
        )
        # Markdown, which is how a statement is written: as plain text the
        # examples and constraints print as backticks and asterisks.
        self.query_one("#statement-body", Markdown).update(evidence(question))
        self.query_one("#forms", Static).update(self.listing())
        self.show_code()
        self.query_one("#statement", VerticalScroll).scroll_home(animate=False)

    def listing(self) -> str:
        """The card's forms, which is picked, and which is in the code pane."""
        lines = []
        # Widest slug of this card's, since a fixed width wraps the cue on one
        # card and wastes the pane on another.
        width = max(len(form.slug) for form in self.forms)
        for number, form in enumerate(self.forms, start=1):
            mark = "x" if form.id in self.picked else " "
            here = ">" if number - 1 == self.focused_form else " "
            cue = form.trigger.replace("\n", " ")
            cue = cue[: CUE - 1] + "…" if len(cue) > CUE else cue
            lines.append(f"{here} {number} [{mark}] {form.slug:<{width}}  {cue}")
        picked = len(self.picked)
        # Spelled out, because an empty answer is a verdict here rather than a
        # skip.
        state = f"{picked} picked" if picked else "none picked — enter records no template"
        return "\n".join([*lines, "", f"1-{len(self.forms)} view    {state}"])

    # The focused form: its cue whole, then its code. Two widgets composed once
    # and updated, since mounting a fresh pair per redraw leaks a widget a
    # keystroke.
    def show_code(self) -> None:
        form = self.forms[self.focused_form]
        self.query_one("#cue", Static).update(form.trigger + self.verdict(form) + "\n")
        self.query_one("#code-body", Static).update(
            Syntax(form.code, "python", theme=SYNTAX, word_wrap=True)
        )
        self.query_one("#code", VerticalScroll).scroll_home(animate=False)

    def verdict(self, form: Template) -> str:
        """What the matcher read this pair as, named by the model that
        answered."""
        match = self.read.get((form.id, self.question.solution.id))
        if match is None:
            return ""
        return f"\n\n{'yes' if match.matched else 'no'}  ({match.model})"

    # Either pane from the keyboard, since neither can hold focus.
    def action_scroll(self, pane: str, amount: int) -> None:
        self.query_one(pane, VerticalScroll).scroll_relative(y=amount, animate=False)

    def action_view(self, number: int) -> None:
        if number <= len(self.forms):
            self.focused_form = number - 1
            self.query_one("#forms", Static).update(self.listing())
            self.show_code()

    def action_toggle(self) -> None:
        form = self.forms[self.focused_form]
        self.picked ^= {form.id}
        self.query_one("#forms", Static).update(self.listing())

    def action_clear(self) -> None:
        self.picked = set()
        self.query_one("#forms", Static).update(self.listing())

    def action_record(self) -> None:
        """Every pair of the card, positive and negative in one write."""
        self.answered(self.question, set(self.picked))
        self.count += 1
        self.advance()

    # Nothing written, and the pair stays in the pool. Not the same as
    # recording no template, which is a verdict.
    def action_skip(self) -> None:
        self.advance()

    def advance(self) -> None:
        self.index += 1
        self.picked = set()
        self.focused_form = 0
        if self.index >= len(self.pool):
            self.exit()
        else:
            self.show()
