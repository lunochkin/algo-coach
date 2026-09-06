import ast
from pathlib import Path

from importlinter.cli import lint_imports

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "algo_coach"
TESTS = ROOT / "tests"

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
    imports the adapter."""
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
