"""Errors with stable machine-readable codes."""


class HanoError(ValueError):
    """A rejected operation, without side effects."""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        self.detail = detail or code
        super().__init__(self.detail)
