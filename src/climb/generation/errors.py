"""How a generation call fails. Its own module because every site raises it and
none of them owns it."""


class GenerationError(Exception):
    """The model wrote nothing — a refusal, or an answer cut short."""


__all__ = ["GenerationError"]
