from pathlib import Path

from algo_coach.schema import Draft


class DraftStore:
    """One file per draft, named by the writing id; a write replaces it.

    Working state rather than a log: a draft is revised as each step answers,
    and removed once the problem it became has landed.
    """

    def __init__(self, root: Path):
        self.drafts_path = root / "drafts"

    def put(self, draft: Draft) -> None:
        self.drafts_path.mkdir(parents=True, exist_ok=True)
        path = self.drafts_path / f"{draft.id}.json"
        path.write_text(draft.model_dump_json(indent=2) + "\n")

    def get(self, draft_id: str) -> Draft | None:
        path = self.drafts_path / f"{draft_id}.json"
        if not path.exists():
            return None
        return Draft.model_validate_json(path.read_text())

    def remove(self, draft_id: str) -> None:
        # what clearing at landing does. Missing is not an error: a run that
        # died between landing and clearing leaves the next one this to do
        self.drafts_path.joinpath(f"{draft_id}.json").unlink(missing_ok=True)

    def all(self) -> list[Draft]:
        if not self.drafts_path.exists():
            return []
        return [
            Draft.model_validate_json(path.read_text())
            for path in sorted(self.drafts_path.glob("*.json"))
        ]
