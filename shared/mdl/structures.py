from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MdlVertex:
    position: tuple[float, float, float]
    normal: tuple[float, float, float]
    uv0: tuple[float, float] = (0.0, 0.0)
    bone_indices: tuple[int, int, int, int, int, int, int, int] = (0, 0, 0, 0, 0, 0, 0, 0)
    bone_weights: tuple[float, float, float, float, float, float, float, float] = (
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
    )
    source_vertex_index: int = -1


@dataclass
class MdlSubmesh:
    start_index: int = 0
    index_count: int = 0
    attribute_mask: int = 0


@dataclass
class MdlMesh:
    name: str
    material_path: str
    material_name: str = ""
    vertices: list[MdlVertex] = field(default_factory=list)
    indices: list[int] = field(default_factory=list)
    submeshes: list[MdlSubmesh] = field(default_factory=lambda: [MdlSubmesh()])


@dataclass
class MdlShapeDelta:
    vertex_index: int
    delta: tuple[float, float, float]


@dataclass
class MdlShapeKey:
    name: str
    mesh_deltas: dict[int, list[MdlShapeDelta]] = field(default_factory=dict)


@dataclass
class MdlModel:

    lod_meshes: list[list[MdlMesh]] = field(default_factory=lambda: [[]])
    materials: list[str] = field(default_factory=list)
    attributes: list[str] = field(default_factory=list)
    bones: list[str] = field(default_factory=list)
    shapekeys: list[MdlShapeKey] = field(default_factory=list)

    def all_meshes(self) -> list[MdlMesh]:
        result: list[MdlMesh] = []
        for lod in self.lod_meshes:
            result.extend(lod)
        return result
