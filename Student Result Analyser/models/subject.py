"""Subject model — defines a single exam subject and its thresholds."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Subject:
    """Represents one exam subject with configurable marks limits."""

    name: str
    max_marks: int = field(default=100)
    passing_marks: int = field(default=33)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict suitable for JSON responses."""
        return {
            "name": self.name,
            "max_marks": self.max_marks,
            "passing_marks": self.passing_marks,
        }

    @classmethod
    def from_name(cls, name: str) -> "Subject":
        """Convenience factory: create a Subject with default thresholds."""
        return cls(name=name.strip())
