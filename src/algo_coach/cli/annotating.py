"""The annotation prompt as two panes: the statement, and one form's code.

Deciding whether a problem exercises a form means reading the statement
against that form, then against the next one. So the statement stays put and
the right pane changes, rather than both scrolling past each other.

One form at a time because all of them do not fit. A card carries up to six,
and their code runs to a hundred and thirty lines — more than any pane holds,
however the screen is divided. Which form is in view is the same question the
annotator is already answering.

The prompt only collects. What lands is the caller's, so a sitting cut short
keeps every answer that was given, as an append-only log requires.
"""

from collections.abc import Callable, Mapping, Sequence

from rich.syntax import Syntax
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Footer, Markdown, Static

from algo_coach.matches import Question, candidates
from algo_coach.schema import Template, TemplateMatch

# Answering one question: the pairs it settles, positive and negative.
Answered = Callable[[Question, set[str]], None]

CUE = 60  # how much of a trigger the list shows; the code pane carries it whole

# The editor's palette rather than the terminal's: a form is read here and
# written there, and two colourings of one function are two things to learn.
SYNTAX = "xcode"


class Annotating(App[None]):
    """One question at a time, over the pool the caller sampled."""

    # Light, and stated rather than inherited. A sitting is an hour of reading
    # prose and code side by side, and the panes have to agree with each other
    # whatever the terminal is set to.
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
        # The statement on the plain arrows, the code on shifted ones. The
        # statement is what is read at length, and the pane holding it is the
        # one an unmodified key should move.
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
        # Markup off on everything the author wrote. A statement is full of
        # `[i]` and `[1, 2, 3]`, and a renderer reading those as tags would
        # drop the part of the text the annotator is deciding on.
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
        # Neither pane takes focus. A focused scrollable claims space for a
        # page down, and space is how a form is picked — the one key the
        # sitting cannot afford to lose to whatever was last clicked.
        for pane in self.query(VerticalScroll):
            pane.can_focus = False
        self.show()

    def show(self) -> None:
        """Redraw all four regions for the question and form now in view."""
        question = self.question
        self.query_one("#head", Static).update(
            f"{self.index + 1}/{len(self.pool)}  {question.card.slug}  {question.problem.title}"
        )
        # Rendered as markdown, which is how a statement is written: the
        # examples are fenced blocks and the constraints a list. Read as plain text they
        # are the part of the statement that decides the question, printed as
        # backticks and asterisks.
        self.query_one("#statement-body", Markdown).update(question.problem.statement)
        self.query_one("#forms", Static).update(self.listing())
        self.show_code()
        self.query_one("#statement", VerticalScroll).scroll_home(animate=False)

    def listing(self) -> str:
        """The card's forms, which is picked, and which is in the code pane.

        The cue is truncated here and whole in the code pane. The list says
        which form is which; deciding on one is done with it in view.
        """
        lines = []
        # The slug column takes the widest of this card's, since a fixed width
        # either wraps the cue on one card or wastes the pane on another.
        width = max(len(form.slug) for form in self.forms)
        for number, form in enumerate(self.forms, start=1):
            mark = "x" if form.id in self.picked else " "
            here = ">" if number - 1 == self.focused_form else " "
            cue = form.trigger.replace("\n", " ")
            cue = cue[: CUE - 1] + "…" if len(cue) > CUE else cue
            lines.append(f"{here} {number} [{mark}] {form.slug:<{width}}  {cue}")
        picked = len(self.picked)
        # Spelled out, because an empty answer is a verdict here rather than a
        # skip: it asserts that none of the forms match, and writes a negative
        # on every pair. A footer key alone would leave the two looking alike.
        state = f"{picked} picked" if picked else "none picked — enter records no template"
        return "\n".join([*lines, "", f"1-{len(self.forms)} view    {state}"])

    def show_code(self) -> None:
        """The focused form: its cue whole, then what has to be reproduced.

        Two widgets composed once and updated, never mounted per redraw. The
        cue is prose and the code is highlighted, so one renderable cannot
        carry both — and mounting a fresh one each time leaks a widget a
        keystroke.

        Highlighted to match the screen rather than the terminal: the code sits
        beside a rendered statement, and the two panes are read together.
        """
        form = self.forms[self.focused_form]
        self.query_one("#cue", Static).update(form.trigger + self.verdict(form) + "\n")
        self.query_one("#code-body", Static).update(
            Syntax(form.code, "python", theme=SYNTAX, word_wrap=True)
        )
        self.query_one("#code", VerticalScroll).scroll_home(animate=False)

    def verdict(self, form: Template) -> str:
        """What the matcher read this pair as, named by the model that
        answered. Shown only where the caller asked for it, and what it costs
        is that the answer is no longer independent of it."""
        match = self.read.get((form.id, self.question.problem.id))
        if match is None:
            return ""
        return f"\n\n{'yes' if match.matched else 'no'}  ({match.model})"

    def action_scroll(self, pane: str, amount: int) -> None:
        """Either pane from the keyboard, since neither can hold focus. The
        mouse wheel reaches both without this."""
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

    def action_skip(self) -> None:
        """Nothing written, and the pair stays in the pool for a later
        sitting. Not the same as recording no template, which is a verdict."""
        self.advance()

    def advance(self) -> None:
        self.index += 1
        self.picked = set()
        self.focused_form = 0
        if self.index >= len(self.pool):
            self.exit()
        else:
            self.show()
