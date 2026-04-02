from __future__ import annotations

from typing import Any, Any, Optional


class ProfileInfo:
    summary: Optional[str]
    instructions: Optional[list[str]]
    links: Optional[list[tuple[str, str]]]

    def __init__(
        self,
        summary: Optional[str] = None,
        instructions: Optional[list[str]] = None,
        links: list[tuple[str, str]] = [],
    ):
        self.summary = summary
        self.instructions = instructions
        self.links = links

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProfileInfo:
        summary = data.get("summary")
        instructions = data.get("instructions")
        links = data.get("links", [])

        return cls(summary, instructions, links)
