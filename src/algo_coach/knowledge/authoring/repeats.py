"""Rule 15: a lesson neither repeats its question's snippet nor shows its
answer."""

import ast
import re
from dataclasses import dataclass

from algo_coach.knowledge.authoring.course import Course, Question, Report, fmt, norm
from algo_coach.knowledge.authoring.lessons import BLOCK, as_async

LITERAL = re.compile(r"(?<![\w.])\d+(?:\.\d+)?|'[^']+'|\"[^\"]+\"")
SHOWN = re.compile(r"```text\n(.*?)```", re.S)
COMMENT = re.compile(r"#\s*(?:→|->|=>|prints?:?)?\s*(.+)$", re.M)
EVALUATED = (ast.Call, ast.BinOp, ast.Compare, ast.Subscript)
# what a snippet wraps its point in, and every snippet shares
SCAFFOLD = {
    "try:",
    "else:",
    "finally:",
    "pass",
    "except Exception as e:",
    "except Exception as _:",
    "type(e).__name__",
    "type(_).__name__",
    "if __name__ == '__main__':",
    "import asyncio",
    "async def __main():",
    "asyncio.run(__main())",
    "async def main():",
    "asyncio.run(main())",
    "async def _():",
    "asyncio.run(_())",
}


def parsed(code: str) -> ast.Module | None:
    for text in (code, as_async(code)):
        try:
            return ast.parse(text)
        except SyntaxError:
            continue
    return None


class Plain(ast.NodeTransformer):
    """Removes what two copies of one example differ in without differing in
    what they teach: `print(x)` around a single value, and the module in
    `itertools.chain` where the other copy imported `chain` by name."""

    def __init__(self, tree: ast.AST) -> None:
        self.modules = {
            a.asname or a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names
        }

    def visit_Attribute(self, node: ast.Attribute) -> ast.AST:
        self.generic_visit(node)
        if isinstance(node.value, ast.Name) and node.value.id in self.modules:
            return ast.copy_location(ast.Name(node.attr, node.ctx), node)
        return node

    def visit_Expr(self, node: ast.Expr) -> ast.AST:
        self.generic_visit(node)
        call = node.value
        if (
            isinstance(call, ast.Call)
            and getattr(call.func, "id", "") == "print"
            and len(call.args) == 1
            and not call.keywords
        ):
            return ast.copy_location(ast.Expr(call.args[0]), node)
        return node


class Unnamed(ast.NodeTransformer):
    """Replaces every name the code itself binds with one placeholder, so a
    copy whose variables, functions and classes were renamed reads the same."""

    def __init__(self, tree: ast.AST) -> None:
        walked = list(ast.walk(tree))
        self.bound = {
            n.id for n in walked if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)
        }
        self.bound |= {n.arg for n in walked if isinstance(n, ast.arg)}
        self.bound |= {
            n.name
            for n in walked
            if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef)
        }

    def visit_Name(self, node: ast.Name) -> ast.Name:
        return ast.copy_location(
            ast.Name("_" if node.id in self.bound else node.id, node.ctx), node
        )

    def visit_arg(self, node: ast.arg) -> ast.arg:
        return ast.copy_location(ast.arg("_", None), node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        node.name = "_"
        return self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AST:
        node.name = "_"
        return self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.AST:
        node.name = "_"
        return self.generic_visit(node)


def weight(line: str) -> int:
    """A line's letters and digits: `_ = _ + 1` carries none of its own."""
    return len(re.sub(r"[\W_]", "", line))


def code_lines(code: str) -> tuple[list[str], list[str]]:
    """A snippet's lines as written and with its own names removed, both
    without comments, imports, scaffolding and formatting. Code that does not
    parse gives its raw lines and no second form."""
    tree = parsed(code)
    if tree is None:
        raw = [re.sub(r"\s+", " ", re.sub(r"#.*", "", line)).strip() for line in code.splitlines()]
        kept = [line for line in raw if line and line not in SCAFFOLD]
        return [line for line in kept if not line.startswith(("import ", "from "))], []
    imports = (n for n in ast.walk(tree) if isinstance(n, ast.Import | ast.ImportFrom))
    skip = SCAFFOLD | {ast.unparse(n) for n in imports}
    tree = ast.fix_missing_locations(Plain(tree).visit(tree))
    exact = [line.strip() for line in ast.unparse(tree).splitlines() if line.strip() not in skip]
    unnamed = ast.unparse(Unnamed(tree).visit(tree)).splitlines()
    shape = [line.strip() for line in unnamed if line.strip() not in skip]
    return exact, [line for line in shape if weight(line) >= 4]


def raw_lines(code: str) -> list[str]:
    """A snippet's lines as typed, for a lesson that holds one in its prose,
    in a table or in a block that is not Python."""
    found = [
        norm(re.sub(r"#.*", "", line))
        for line in code.splitlines()
        if not line.strip().startswith(("import ", "from "))
    ]
    scaffold = {norm(x) for x in SCAFFOLD}
    return [line for line in found if len(line) >= 10 and line not in scaffold]


def loose(text: str) -> str:
    """norm, blind to a string literal's prefix and to doubled backslashes."""
    return norm(re.sub(r"\b[rRbBfF]{1,2}(?=[\"'])", "", text)).replace("\\\\", "\\")


def values(node: ast.AST) -> int:
    """How many numbers and strings an expression carries. One is an API
    with its usual argument, `get_context("spawn")`; two are an example."""
    return sum(
        isinstance(n, ast.Constant)
        and isinstance(n.value, int | float | str | bytes)
        and not isinstance(n.value, bool)
        for n in ast.walk(node)
    )


def quoted(code: str) -> list[str]:
    """The expressions a snippet evaluates that carry a value, such as
    `divmod(17, 5)`, longest first: a lesson can hold one in another
    statement."""
    tree = parsed(code)
    found: set[str] = set()
    if tree is None:
        return []
    for node in ast.walk(tree):
        if (
            isinstance(node, EVALUATED)
            and getattr(getattr(node, "func", None), "id", "") != "print"
        ):
            text = ast.unparse(node)
            if values(node) and weight(text) >= 5 and len(norm(text)) >= 10:
                found.add(text)
    return sorted(found, key=len, reverse=True)


def asked(prompt: str) -> list[str]:
    """The expressions a prompt asks about in backticks, where the question
    has no snippet: `bisect_right([1, 3, 3, 5], 3)`."""
    found: list[str] = []
    for span in re.findall(r"`([^`]+)`", prompt):
        tree = parsed(span)
        if tree and len(tree.body) == 1 and isinstance(tree.body[0], ast.Expr):
            node = tree.body[0].value
            if isinstance(node, EVALUATED) and values(node) >= 2 and len(norm(span)) >= 12:
                found.append(span)
    return found


def share(mine: list[str], theirs: set[str]) -> float:
    total = sum(weight(line) for line in mine)
    return sum(weight(line) for line in mine if line in theirs) / total if total else 0.0


def answers(q: Question) -> list[str]:
    """What a learner types or picks as the output: the first accepted reply
    of a short question, and the keyed choice of an output question."""
    if q["kind"] not in ("output", "debug") or "code" not in q:
        return []  # a concept's answer is the term its lesson teaches
    if fmt(q) == "short":
        return q["accept"][:1]
    if fmt(q) == "choice" and q["kind"] == "output":
        return [q["choices"][ord(a) - 65] for a in q["answer"]]
    return []


def distinctive(answer: str) -> bool:
    """Specific enough that a lesson holding it anywhere gives the question
    away: not a bare name such as an exception, and not only True, False and
    None."""
    return (
        len(norm(answer)) >= 8
        and not re.fullmatch(r"[\w.]+", answer.strip())
        and not re.fullmatch(r"(True|False|None|[\s,()])+", answer.strip())
    )


@dataclass
class Lesson:
    exact: set[str]
    shape: set[str]
    outputs: set[str]
    whole: str
    spelled: str


def _lesson(text: str) -> Lesson:
    blocks = [m[1] for m in BLOCK.finditer(text)]
    exact: set[str] = set()
    shape: set[str] = set()
    for block in blocks:
        e, sh = code_lines(block)
        exact |= set(e)
        shape |= set(sh)
    outputs = {norm(line) for m in SHOWN.finditer(text) for line in m[1].splitlines()}
    outputs |= {norm(m[1]) for block in blocks for m in COMMENT.finditer(block)}
    return Lesson(exact, shape, outputs, norm(text), loose(text))


def repeats(course: Course, report: Report) -> None:
    skipped = course.skip.get("lesson-repeat", {})
    lessons = {slug: _lesson(text) for slug, text in course.lessons.items()}
    for q in course.questions:
        slug = q["lesson"].split("#")[0]
        if slug in lessons and q["id"] not in skipped and (found := _repeat(q, lessons[slug])):
            report.warn(15, f"{q['id']} ~ lessons/{slug}.md", found)


def _repeat(q: Question, lesson: Lesson) -> str | None:
    code = q.get("code", "")
    mine, unnamed = code_lines(code) if code else ([], [])
    typed = raw_lines(code)
    in_text = sum(len(line) for line in typed if line in lesson.whole)
    elsewhere = in_text / sum(map(len, typed)) if typed else 0.0
    same = max(share(mine, lesson.exact), elsewhere) if sum(map(len, mine)) >= 15 else 0.0
    # a renamed copy shares its values. Lines sharing only an API are the
    # lesson teaching that API
    literals = sum(len(LITERAL.findall(line)) for line in unnamed if line in lesson.shape)
    renamed = share(unnamed, lesson.shape) if len(unnamed) >= 2 and literals >= 2 else 0.0
    mine = [line for line in mine if line]
    inline = [e for e in quoted(code) if loose(e) in lesson.spelled]
    in_prompt = [e for e in asked(q["prompt"]) if loose(e) in lesson.spelled] if not code else []
    printed = [a for a in answers(q) if distinctive(a) and norm(a) in lesson.whole]
    shown = [a for a in answers(q) if norm(a) in lesson.outputs] if same or inline else []
    told = f" and shows its answer {shown[0][:40]!r}" if shown else ""
    if same >= 0.7:
        return "the lesson repeats the snippet" + told
    if renamed >= 0.8:
        return "the lesson repeats the snippet with its names changed"
    if printed:
        return f"the lesson prints the answer {printed[0][:40]!r}"
    if _evaluates(inline, mine, shown):
        return f"the lesson evaluates {inline[0][:40]!r}, as the snippet does" + told
    if in_prompt:
        return f"the lesson evaluates {in_prompt[0][:40]!r}, which the prompt asks about"
    if same >= 0.3 and shown:
        return f"the lesson shares code with the snippet{told}"
    return None


def _evaluates(inline: list[str], mine: list[str], shown: list[str]) -> bool:
    return bool(
        inline
        and weight(inline[0]) >= 0.6 * sum(map(weight, mine))
        and (shown or values(ast.parse(inline[0])) >= 2)
    )
