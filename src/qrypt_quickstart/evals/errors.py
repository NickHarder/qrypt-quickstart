"""Errors that stop a run before it can give a verdict (the runner exits 2)."""


class EvalSetupError(Exception):
    """The suite cannot run as asked: a bad case file, no cases, a missing recording."""


class CassetteMissError(EvalSetupError):
    """Replay needed an exchange that no recording holds."""
