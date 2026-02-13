
from dataclasses import dataclass
import re
from collections import defaultdict
from typing import DefaultDict, List, Tuple, Optional

from bpy.types import Collection, Object


NAME_RE: re.Pattern[str] = re.compile(r"(.+)\s+(\d)\.(\d)$")


@dataclass
class PartNameInfo:
    base_name: str
    mesh_index: int
    part_index: int


class ModelScanner:
    """Scan collections and parse part names."""

    @staticmethod
    def _parse_part_name(name: str) -> Optional[PartNameInfo]:
        match = NAME_RE.match(name)

        if not match:
            return None

        base, mesh, part = match.groups()
        return PartNameInfo(base, int(mesh), int(part))

    @staticmethod
    def scan_collection(
        col: Collection
    ) -> DefaultDict[int, List[Tuple[Object, str, int]]]:
        """Scan a collection and group mesh objects by mesh index."""
        meshes: DefaultDict[int,
                            List[Tuple[Object, str, int]]] = defaultdict(list)

        for obj in col.objects:
            if obj.type != "MESH":
                continue

            parsed_name = ModelScanner._parse_part_name(obj.name)
            if not parsed_name:
                continue

            meshes[parsed_name.mesh_index].append((
                obj,
                parsed_name.base_name,
                parsed_name.part_index,
            ))

        return meshes
