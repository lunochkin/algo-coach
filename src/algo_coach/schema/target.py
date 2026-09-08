"""The target a problem was written for, as the records that carry it name it."""


def one_target(target_template_id: str | None, target_technique: str | None) -> None:
    """Rejects a record naming both kinds. A target is one thing the
    generator was told, and two would be two prompts."""
    if target_template_id is not None and target_technique is not None:
        raise ValueError("a target is a template or a technique, not both")


__all__ = ["one_target"]
