import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = ROOT / "docs" / "architecture" / "pages.md"
APP = ROOT / "web" / "src" / "App.tsx"
SCREENS = ROOT / "native" / "src" / "app"

# each web route, by its path in App.tsx, and the inventory row it serves
WEB = {
    "": "The board",
    "problems": "The problem listing",
    "cards": "The cards",
    "cards/:slug": "A card's trigger, brief and templates",
    "cards/:slug/recall": "A recall",
    "cards/:slug/recall/:template": "A recall",
    "techniques/:technique": "A technique's problems and cards",
    "problems/:problemId": "A picked problem's record and statement",
    "knowledge": "The knowledge home",
    "knowledge/queue": "A queue",
    "knowledge/modules/:module": "A module",
    "knowledge/lessons": "The lessons",
    "knowledge/lessons/:module/:lesson": "A lesson",
    "knowledge/certifications": "The certifications",
    "knowledge/exam": "A level exam's choices",
    "settings": "The settings",
    "LOGIN": "The login",
    "PRIVACY": "The privacy policy",
    "gallery": "The gallery",
}
# routes that serve no row: the page answering a path nothing else does
WEB_UNLISTED = {"*"}

# each phone screen file, by its path under native/src/app, and its row
PHONE = {
    "(tabs)/practice.tsx": "The board",
    "(tabs)/problems.tsx": "The problem listing",
    "(tabs)/cards.tsx": "The cards",
    "(tabs)/index.tsx": "The knowledge home",
    "technique.tsx": "A technique's problems and cards",
    "problem.tsx": "A picked problem's record and statement",
    "card.tsx": "A card's trigger, brief and templates",
    "module.tsx": "A module",
    "quiz.tsx": "A queue",
    "exam.tsx": "A level exam's choices",
    "lessons.tsx": "The lessons",
    "lesson.tsx": "A lesson",
    "certs.tsx": "The certifications",
    "settings.tsx": "The settings",
    "devices.tsx": "The signed-in devices",
    "login.tsx": "The login",
    "privacy.tsx": "The privacy policy",
}
# files that are no screen: the layouts, and the sign-in callback that only
# hands the token over
PHONE_UNLISTED = {"_layout.tsx", "(tabs)/_layout.tsx", "signed-in.tsx"}
# rows the phone holds inside a screen the table above already names
PHONE_PARTS = {
    "The landing page": "(tabs)/index.tsx",
    "The start sheet": "module.tsx",
    "A lesson a queue offers": "quiz.tsx",
    "An exam and its results": "quiz.tsx",
    "A certification's conditions": "certs.tsx",
    "A card's ladder and probes": "card.tsx",
    "The press starting a card's run": "card.tsx",
}


def inventory() -> dict[str, dict[str, str]]:
    text = PAGES.read_text()
    table = text[text.index("### Screens") : text.index("### Acts")]
    rows = {}
    for line in table.splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 4 or cells[0] in ("Screen", "---"):
            continue
        rows[cells[0]] = {"web": cells[1], "phone": cells[2], "status": cells[3]}
    return rows


def web_routes() -> set[str]:
    text = APP.read_text()
    found = set(re.findall(r'<Route path="([^"]*)"', text))
    found |= set(re.findall(r"<Route path=\{(\w+)\}", text))
    if "<Route index" in text:
        found.add("")
    return found


def phone_files() -> set[str]:
    return {str(path.relative_to(SCREENS)) for path in SCREENS.rglob("*.tsx")}


def test_every_web_route_is_in_the_table():
    """A route added to App.tsx fails here until the test names its row."""
    assert web_routes() - WEB_UNLISTED == set(WEB)


def test_every_phone_screen_is_in_the_table():
    """A new screen under native/src/app fails here until its row is named."""
    assert phone_files() - PHONE_UNLISTED == set(PHONE)


def test_every_row_the_tables_name_is_in_the_inventory():
    """A row renamed in pages.md fails here until the tables follow it."""
    rows = inventory()
    named = set(WEB.values()) | set(PHONE.values()) | set(PHONE_PARTS)
    assert named - set(rows) == set()


def test_a_row_the_web_serves_names_the_web():
    """A route serving a row the inventory says the web lacks is a stale row."""
    rows = inventory()
    assert [row for row in set(WEB.values()) if rows[row]["web"] == "none"] == []


def test_the_phone_column_reads_none_exactly_where_no_screen_holds_the_row():
    """A screen shipped with its row still `none`, or a row claiming a screen
    the phone lacks, makes the inventory say what the phone does not do."""
    rows = inventory()
    held = set(PHONE.values()) | set(PHONE_PARTS)
    assert {name for name, row in rows.items() if row["phone"] != "none"} == held


def test_a_row_the_phone_holds_is_not_web_alone():
    """`web for now` and `web only` name a row the phone lacks."""
    rows = inventory()
    held = set(PHONE.values()) | set(PHONE_PARTS)
    stale = [name for name in held if rows[name]["status"] in ("web for now", "web only")]
    assert stale == []
