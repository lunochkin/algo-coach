from pydantic import BaseModel


class Configuration(BaseModel, frozen=True):
    """Which model answered, and what a re-run has to name to ask the same way.

    No field carries a default, so a partly-named configuration cannot inherit
    the rest from whoever was written first.
    """

    model: str
    effort: str
    pin: str  # the endpoint, named to the quantization
    temperature: float | None = None  # absent is the provider's own, and a real answer

    # what meters a request: the provider caps per model per endpoint. An
    # account-wide cap on a free model is not covered
    @property
    def deployment(self) -> tuple[str, str]:
        return self.model, self.pin


__all__ = ["Configuration"]
