"""Deterministic checks of an output against a case's expectation.

Only these decide the gate. A model judge may be reported beside the results; it does not pass or
fail anything.
"""

from .models import Expectation, TargetOutput


def score(expectation: Expectation, output: TargetOutput) -> list[str]:
    """Return every way the output falls short of the expectation; an empty list is a pass."""
    lowered_text = output.text.lower()
    missing_phrases = [
        f"expected to contain {phrase!r}"
        for phrase in expectation.contains
        if phrase.lower() not in lowered_text
    ]
    forbidden_phrases = [
        f"must not contain {phrase!r}"
        for phrase in expectation.must_not_contain
        if phrase.lower() in lowered_text
    ]
    length_failures = (
        [f"answer is {len(output.text)} characters; at least {expectation.min_length} required"]
        if len(output.text) < expectation.min_length
        else []
    )
    refusal_failures = (
        [f"expected refused={expectation.refuses} but the system returned refused={output.refused}"]
        if output.refused != expectation.refuses
        else []
    )
    return [*missing_phrases, *forbidden_phrases, *length_failures, *refusal_failures]
