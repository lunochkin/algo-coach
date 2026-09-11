import ast
import inspect
import re
from pathlib import Path

from importlinter.cli import lint_imports
from pydantic import BaseModel

import algo_coach.schema as schema
from algo_coach.calls import CallLog
from algo_coach.cards import CardStore
from algo_coach.cases import CaseLog
from algo_coach.drafts import DraftStore
from algo_coach.log import AttemptLog, SittingStore
from algo_coach.matches import MatchLog
from algo_coach.outcomes import OutcomeLog
from algo_coach.problems import ProblemStore
from algo_coach.solution_claims import SolutionClaimLog
from algo_coach.solutions import SolutionLog
from algo_coach.verifications import VerificationLog

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "algo_coach"
TESTS = ROOT / "tests"
DOCS = [*(ROOT / "docs").rglob("*.md"), ROOT / "README.md", ROOT / "CLAUDE.md"]
# `TODO.md` names the modules a phase is going to add, so its paths are checked
# once the items land rather than now
SPECS = [path for path in DOCS if path.name != "TODO.md"]

# the enums the docs enumerate: states, gates, sources, roles and kinds. Left
# out are the three scales the docs describe as scales rather than by member:
# `Confidence`, `FailureMode`, `ProblemDifficulty`
ENUMERATED = (
    schema.CallSite,
    schema.CaseOutcome,
    schema.ClaimSource,
    schema.Gate,
    schema.ExpectedSource,
    schema.Kind,
    schema.MatchSource,
    schema.ProblemStatus,
    schema.ClaimSource,
    schema.RetirementReason,
    schema.SolutionRole,
    schema.TemplateKind,
    schema.WritingState,
)

# what a module may grow to before it is split. `passage.py` is the largest,
# at just over five hundred
LINE_LIMIT = 550


def modules() -> list[tuple[str, Path, ast.Module]]:
    found = []
    for path in sorted(SRC.rglob("*.py")):
        name = ".".join(("algo_coach", *path.relative_to(SRC).with_suffix("").parts))
        if name.endswith(".__init__"):
            name = name.removesuffix(".__init__")
        found.append((name, path, ast.parse(path.read_text())))
    return found


def defined(tree: ast.Module) -> set[str]:
    """What a module defines itself, and what it declares as its own in
    `__all__`."""
    names: set[str] = set()
    for node in tree.body:
        match node:
            case ast.FunctionDef() | ast.AsyncFunctionDef() | ast.ClassDef():
                names.add(node.name)
            case ast.Assign(targets=targets, value=value):
                for target in targets:
                    if isinstance(target, ast.Name):
                        names.add(target.id)
                        if target.id == "__all__" and isinstance(value, ast.List | ast.Tuple):
                            names |= {
                                one.value for one in value.elts if isinstance(one, ast.Constant)
                            }
            case ast.AnnAssign(target=ast.Name(id=name)):
                names.add(name)
            case ast.TypeAlias(name=ast.Name(id=name)):
                names.add(name)
    return names


def exported(tree: ast.Module) -> set[str]:
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets
        ):
            assert isinstance(node.value, ast.List | ast.Tuple)
            return {one.value for one in node.value.elts if isinstance(one, ast.Constant)}
    return set()


def test_the_import_contracts_hold():
    """The package graph `pyproject.toml` states: leaves import no domain, the
    transport and vocabulary sit under it, stores are independent, nothing
    imports an adapter."""
    assert lint_imports(config_filename=str(ROOT / "pyproject.toml"), no_cache=True) == 0


def test_no_source_module_is_over_the_line_limit():
    """Past the limit a module carries two concerns; the seam is found and cut
    before a third arrives."""
    over = {
        str(path.relative_to(ROOT)): lines
        for _, path, _ in modules()
        if (lines := len(path.read_text().splitlines())) > LINE_LIMIT
    }
    assert over == {}


def test_a_name_is_imported_from_where_it_is_defined_or_declared():
    """A name reached through a module that only imports it goes when that
    module stops using it. Package inits are the exception: re-exporting is
    what they are for."""
    own = {name: (defined(tree), path.name == "__init__.py") for name, path, tree in modules()}
    through: list[str] = []
    for _, path, tree in modules():
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom) or node.module not in own:
                continue
            names, is_package = own[node.module]
            if is_package:
                continue
            through += [
                f"{path.relative_to(ROOT)}: {alias.name} via {node.module}"
                for alias in node.names
                if alias.name not in names
            ]
    assert through == []


def test_a_package_exports_only_its_own_names():
    """A name in `__all__` that came from outside the package is a second
    import path for it, and the one that breaks when the package stops
    needing it."""
    borrowed: list[str] = []
    for name, path, tree in modules():
        if path.name != "__init__.py":
            continue
        for node in tree.body:
            if not isinstance(node, ast.ImportFrom) or node.module is None:
                continue
            if node.module == name or node.module.startswith(f"{name}."):
                continue
            borrowed += [
                f"{name}: {alias.name} from {node.module}"
                for alias in node.names
                if (alias.asname or alias.name) in exported(tree)
            ]
    assert borrowed == []


def test_a_package_exports_only_what_something_imports():
    """A name in `__all__` no module outside the package imports, in `src` or in
    `tests`, is surface nothing pays for. `cli` is exempt: it is the entry
    point, and its names are reached by the console script and by attribute."""
    imported: dict[str, set[str]] = {}
    for path in [*SRC.rglob("*.py"), *TESTS.glob("*.py")]:
        for node in ast.walk(ast.parse(path.read_text())):
            if not isinstance(node, ast.ImportFrom) or node.module is None:
                continue
            if path.is_relative_to(SRC.parent / Path(*node.module.split("."))):
                continue
            imported.setdefault(node.module, set()).update(alias.name for alias in node.names)
    unpaid = [
        f"{name}: {export}"
        for name, path, tree in modules()
        if path.name == "__init__.py" and name not in ("algo_coach", "algo_coach.cli")
        for export in sorted(exported(tree))
        if export not in imported.get(name, set())
    ]
    assert unpaid == []


def test_a_test_module_carries_no_docstring():
    """`CLAUDE.md`: a module-level one restates the filename, and a fact it
    holds alone belongs on the test that pins it."""
    with_one = [
        path.name
        for path in sorted(TESTS.glob("test_*.py"))
        if ast.get_docstring(ast.parse(path.read_text())) is not None
    ]
    assert with_one == []


def prose(paths: list[Path] = DOCS) -> str:
    return "\n".join(path.read_text() for path in paths)


def test_the_docs_name_every_state_gate_and_source():
    """`CLAUDE.md`: an unchecked doc describes a system that does not exist. A
    member the docs never name is a state a reader cannot find."""
    text = prose()
    unnamed = [
        f"{kind.__name__}.{member.value}"
        for kind in ENUMERATED
        for member in kind
        # `problem-class` is written `problem class`
        if not re.search(rf"\b{re.escape(member.value).replace(r'\-', '[- ]')}\b", text)
    ]
    assert unnamed == []


def test_every_path_the_docs_name_exists():
    """A backticked path or module in the docs points at something in the
    tree, or the doc is describing a repo that moved under it."""
    pattern = r"`((?:src/|docs/|tests/|scripts/)[\w./-]+|algo_coach(?:\.\w+)+)`"
    named = set(re.findall(pattern, prose(SPECS)))
    missing = []
    for ref in sorted(named):
        if ref.startswith("algo_coach"):
            path = ROOT / "src" / Path(*ref.split("."))
            found = path.with_suffix(".py").exists() or path.is_dir()
        else:
            found = (ROOT / ref).exists()
        if not found:
            missing.append(ref)
    assert missing == []


def test_a_record_keyed_to_an_attempt_carries_what_the_log_needs():
    """`README.md`: an engine-minted `id`, its `attempt_id` and `created_at`,
    each required, so one reader orders all of them."""
    keyed = [
        cls
        for _, cls in inspect.getmembers(schema, inspect.isclass)
        if issubclass(cls, BaseModel) and "attempt_id" in cls.model_fields
    ]
    assert {cls.__name__ for cls in keyed} >= {"AttemptClaim", "SelfLabel", "Diagnosis"}
    lacking = [
        f"{cls.__name__}.{field}"
        for cls in keyed
        for field in ("id", "attempt_id", "created_at")
        if field not in cls.model_fields or not cls.model_fields[field].is_required()
    ]
    assert lacking == []


APPEND_ONLY = (
    CaseLog,
    SolutionLog,
    SolutionClaimLog,
    OutcomeLog,
    MatchLog,
    CallLog,
    VerificationLog,
)


def test_the_stores_write_as_the_data_class_table_says():
    """`README.md`: attempts, claims, cases, solutions, solution claims,
    matches, site outcomes and calls are append-only; drafts and sittings are
    revised in place; a problem is created once and only its status moves; cards
    are re-seeded by slug."""
    # by what a store can do rather than by its base: a store's backend moves
    # under it, and its write semantics do not
    for log in APPEND_ONLY:
        assert hasattr(log, "append") and hasattr(log, "all"), log.__name__
        assert not hasattr(log, "put") and not hasattr(log, "remove"), log.__name__
    assert not any(name.startswith(("put", "remove")) for name in vars(AttemptLog))
    for revised in (DraftStore, SittingStore, CardStore, ProblemStore):
        assert hasattr(revised, "put") and hasattr(revised, "get"), revised.__name__
    assert hasattr(DraftStore, "remove")
    # kept once it ends: the pause history is readable in this store alone
    assert not hasattr(SittingStore, "remove")
    assert not hasattr(CardStore, "remove")
    # created once: the store's own `put` refuses a change beyond the status
    assert "put" in vars(ProblemStore)
