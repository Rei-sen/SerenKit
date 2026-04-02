from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Optional


@dataclass(frozen=True)
class PartID:
    mesh_id: int
    part_id: int

    NAME_RE = r"(\.+) (\d)\.(\d)"  # FF supports only up to 10 meshes

    def __str__(self):
        return f"{self.mesh_id}.{self.part_id}"

    @classmethod
    def parse_name(cls, name: str) -> tuple[str, Optional[PartID]]:

        match = re.match(cls.NAME_RE, name)
        if match:
            name, mesh_id, part_id = match.groups()
            return name, cls(mesh_id=int(mesh_id), part_id=int(part_id))

        return name, None

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, PartID):
            raise ValueError(f"Cannot compare PartID with {type(value)}")

        return self.mesh_id == value.mesh_id and self.part_id == value.part_id

    def __iter__(self):
        yield self.mesh_id
        yield self.part_id
