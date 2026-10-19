"""The shapes of an eval case, of what the system under test returns, and of a run's results."""

import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

CaseType = Literal["boundary", "invariant", "regression"]
Tier = Literal["core", "scenario"]
Difficulty = Literal["straightforward", "ambiguous", "edge_case"]
Status = Literal["pass", "fail"]


class StrictModel(BaseModel):
    """A model that rejects unknown fields, so a typo cannot silently disable a check."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class CaseInput(StrictModel):
    """What the system under test is given. Add fields here when it needs more than a prompt."""

    prompt: str


class Expectation(StrictModel):
    """What a case requires of the output. Every check is deterministic."""

    contains: list[str] = Field(default_factory=list)
    must_not_contain: list[str] = Field(default_factory=list)
    refuses: bool = False
    # The vacuity guard: an empty answer must not pass a case that only forbids things.
    min_length: int = 1


class HistoryEntry(StrictModel):
    """Why a case's expectation changed. Required whenever a core expectation changes."""

    date: datetime.date
    reason: str
    ref: str | None = None


class EvalCase(StrictModel):
    """One eval case, as written in `evals/cases/<category>/<id>.yaml`."""

    case_id: str = Field(alias="id")
    category: str
    type: CaseType
    tier: Tier = "scenario"
    difficulty: Difficulty = "straightforward"
    statement: str
    failure_mode: str
    input: CaseInput
    expect: Expectation
    history: list[HistoryEntry] = Field(default_factory=list)
    # The use cases or findings this case protects, by id.
    guards: list[str] = Field(default_factory=list)
    # The key metrics this case's verdict feeds, by id: the north star, a driver or a guardrail.
    metrics: list[str] = Field(default_factory=list)


class PromptVersion(StrictModel):
    """Which text of a prompt was in force: its name, its version and its content hash."""

    name: str
    version: str
    sha256: str


class TargetOutput(StrictModel):
    """What the system under test produced for one case."""

    text: str
    refused: bool = False
    prompts_used: list[PromptVersion] = Field(default_factory=list)


class CaseResult(StrictModel):
    """The verdict on one case, with the prompt versions that produced it."""

    case_id: str
    category: str
    type: CaseType
    tier: Tier
    difficulty: Difficulty
    status: Status
    failures: list[str]
    prompts: list[PromptVersion]
    # Carried from the case, so that a verdict can be traced from a use case or from a metric.
    guards: list[str] = Field(default_factory=list)
    metrics: list[str] = Field(default_factory=list)


class Versions(StrictModel):
    """Everything that names what was under test: the kit, the commit, the skills, the prompts."""

    kit: str
    git_commit: str
    skills: dict[str, str]
    prompts: list[PromptVersion]


class RunResults(StrictModel):
    """One run of the suite."""

    mode: str
    tier: str
    model: str
    versions: Versions
    cases: list[CaseResult]

    @property
    def passed_count(self) -> int:
        """How many cases passed."""
        return sum(1 for case_result in self.cases if case_result.status == "pass")

    @property
    def failed_count(self) -> int:
        """How many cases failed."""
        return len(self.cases) - self.passed_count
