"""What one request names, apart from the prompt itself."""

from pydantic import BaseModel


class Configuration(BaseModel, frozen=True):
    """Which model answered, and what a re-run has to name to ask the same way.

    Domain-free, as the call log is: a classifier, a matcher and each
    generation call site all name the same four things. No field carries a
    default, so a caller names its own whole and a partly-named one cannot
    inherit the rest from whoever was written first.
    """

    model: str
    effort: str
    pin: str  # the endpoint, named to the quantization
    temperature: float | None = None  # absent is the provider's own, and a real answer

    # What meters a request: OpenRouter caps nothing on a paid model, the
    # provider caps per model per endpoint. Account-wide caps on free models
    # and one key driven by two runs at once are not covered.
    @property
    def deployment(self) -> tuple[str, str]:
        return self.model, self.pin


__all__ = ["Configuration"]
