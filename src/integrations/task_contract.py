"""HY-RUNE-TC v0.1.0: local, side-effect-free task interchange.

Callers must provide a stable external ID and ensure that text and metadata
contain no private information or credentials. A plan line number is not a
stable ID: it can change when the plan is edited.
"""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


TaskStatus = Literal["todo", "in_progress", "testing", "review", "done", "blocked", "cancelled"]
TaskPriority = Literal["low", "medium", "high", "critical"]


def _validate_metadata(value: Any) -> None:
    """Require JSON data and reject common credential-bearing metadata keys.

    Key screening is only a guardrail; callers are responsible for excluding
    secrets and private data even when they appear in ordinary text or values.
    """
    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("metadata must contain finite JSON numbers")
        return
    if isinstance(value, list):
        for item in value:
            _validate_metadata(item)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError("metadata keys must be strings")
            words = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", key).lower()
            words = re.split(r"[^a-z0-9]+", words)
            credential_words = {"token", "password", "secret", "credential", "credentials", "authorization"}
            key_pair = any(words[i:i + 2] in (["api", "key"], ["private", "key"])
                           for i in range(len(words) - 1))
            if set(words) & credential_words or key_pair:
                raise ValueError("metadata contains a credential-bearing key")
            _validate_metadata(item)
        return
    raise ValueError("metadata must contain only JSON values")


class TaskEnvelope(BaseModel):
    """Validated envelope; use ``model_dump(exclude_unset=True)`` for exchange.

    ``model_fields_set`` and ``exclude_unset`` preserve the distinction between
    an omitted optional field and an explicitly supplied null or empty value.
    List and metadata fields, when supplied, must not be null.
    """

    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)

    contract_version: Literal["0.1.0"]
    task_id: str
    source: str
    external_id: str
    title: str
    status: TaskStatus
    priority: TaskPriority
    description: str | None = None
    repository: str | None = None
    branch: str | None = None
    acceptance_criteria: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("task_id", "source", "external_id", "title")
    @classmethod
    def nonblank_required_string(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be empty or blank")
        return value

    @field_validator("metadata")
    @classmethod
    def valid_metadata(cls, value: dict[str, Any]) -> dict[str, Any]:
        _validate_metadata(value)
        return value

    @model_validator(mode="after")
    def matching_task_id(self) -> TaskEnvelope:
        if self.task_id != f"{self.source}:{self.external_id}":
            raise ValueError("task_id must equal source:external_id")
        return self


def from_runescript_task(
    task: Mapping[str, Any], *, external_id: str, priority: TaskPriority
) -> TaskEnvelope:
    """Normalize a PlanParser Task mapping using a caller-supplied stable ID.

    The source's checkbox-derived status is mapped explicitly. Other source
    fields are preserved under metadata.runescript; no title or line number is
    used to derive the identity, and priority is never guessed.
    """
    if not isinstance(task, Mapping):
        raise ValueError("task must be a mapping")
    status_map = {"pending": "todo", "completed": "done", "blocked": "blocked"}
    status = task.get("status")
    if not isinstance(status, str) or status not in status_map:
        raise ValueError("unknown RuneScript task status")
    if "description" not in task:
        raise ValueError("RuneScript task description is required")
    source_fields = {key: value for key, value in task.items() if key not in {"status", "description"}}
    return TaskEnvelope(
        contract_version="0.1.0",
        task_id=f"runescript:{external_id}",
        source="runescript",
        external_id=external_id,
        title=task["description"],
        status=status_map[status],
        priority=priority,
        metadata={"runescript": source_fields},
    )
