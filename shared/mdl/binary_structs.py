from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from io import BytesIO
from math import sqrt
from struct import pack

from .binary_io import BinaryReader, padding


class VertexType(IntEnum):
    SINGLE1 = 0
    SINGLE2 = 1
    SINGLE3 = 2
    SINGLE4 = 3
    UBYTE4 = 5
    USHORT4 = 17


class VertexUsage(IntEnum):
    POSITION = 0
    BLEND_WEIGHTS = 1
    BLEND_INDICES = 2
    NORMAL = 3
    UV = 4
    FLOW = 5
    TANGENT = 6
    COLOUR = 7


@dataclass
class VertexElement:
    stream: int = 0
    offset: int = 0
    type: int = VertexType.SINGLE3
    usage: int = VertexUsage.POSITION
    usage_idx: int = 0
    PADDING: int = 3

    @classmethod
    def from_bytes(cls, reader: BinaryReader) -> "VertexElement":
        element = cls()
        element.stream = reader.read_byte()
        element.offset = reader.read_byte()
        element.type = reader.read_byte()
        element.usage = reader.read_byte()
        element.usage_idx = reader.read_byte()
        reader.pos += element.PADDING
        return element

    def write(self, output: BytesIO) -> None:
        output.write(pack("<B", self.stream))
        output.write(pack("<B", self.offset))
        output.write(pack("<B", int(self.type)))
        output.write(pack("<B", int(self.usage)))
        output.write(pack("<B", self.usage_idx))
        output.write(padding(self.PADDING))


@dataclass
class VertexDeclaration:
    vertex_elements: list[VertexElement] = field(default_factory=list)

    @classmethod
    def from_bytes(cls, reader: BinaryReader) -> "VertexDeclaration":
        decl = cls()
        element = VertexElement.from_bytes(reader)
        while element.stream != 255:
            decl.vertex_elements.append(element)
            element = VertexElement.from_bytes(reader)

        reader.pos += 17 * 8 - (len(decl.vertex_elements) + 1) * 8
        return decl

    def write(self, output: BytesIO) -> None:
        for element in self.vertex_elements:
            element.write(output)

        VertexElement(stream=255).write(output)
        output.seek((17 - 1 - len(self.vertex_elements)) * 8, 1)

    def create_element(
        self,
        vtype: VertexType,
        usage: VertexUsage,
        stream: int,
        usage_idx: int = 0,
    ) -> None:
        stream_offset = 0
        for element in self.vertex_elements:
            if element.stream == stream:
                stream_offset = max(
                    stream_offset,
                    element.offset + _vertex_element_size(element.type),
                )

        self.vertex_elements.append(
            VertexElement(
                stream=stream,
                offset=stream_offset,
                type=int(vtype),
                usage=int(usage),
                usage_idx=usage_idx,
            )
        )


@dataclass
class BoundingBox:
    min: list[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 1.0])
    max: list[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 1.0])

    @classmethod
    def from_bytes(cls, reader: BinaryReader) -> "BoundingBox":
        box = cls()
        box.min = reader.read_float_array(4)
        box.max = reader.read_float_array(4)
        return box

    @classmethod
    def from_positions(
        cls,
        positions: list[tuple[float, float, float]],
    ) -> "BoundingBox":
        box = cls()
        if not positions:
            return box

        xs = [p[0] for p in positions]
        ys = [p[1] for p in positions]
        zs = [p[2] for p in positions]

        box.min = [min(xs), min(ys), min(zs), 1.0]
        box.max = [max(xs), max(ys), max(zs), 1.0]
        return box

    def radius(self) -> float:
        abs_bbox = [max(abs(self.min[i]), abs(self.max[i])) for i in range(3)]
        return sqrt(abs_bbox[0] ** 2 + abs_bbox[1] ** 2 + abs_bbox[2] ** 2)

    def write(self, output: BytesIO) -> None:
        for value in self.min:
            output.write(pack("<f", value))
        for value in self.max:
            output.write(pack("<f", value))


@dataclass
class FileHeader:
    version: int = 0x01000006
    stack_size: int = 0
    runtime_size: int = 0
    vertex_declaration_count: int = 0
    material_count: int = 0
    vert_offset: list[int] = field(default_factory=lambda: [0, 0, 0])
    idx_offset: list[int] = field(default_factory=lambda: [0, 0, 0])
    vert_buffer_size: list[int] = field(default_factory=lambda: [0, 0, 0])
    idx_buffer_size: list[int] = field(default_factory=lambda: [0, 0, 0])
    lod_count: int = 0
    enable_idx_buffer_stream: bool = False
    enable_edge_geometry: bool = False
    PADDING: int = 1

    @classmethod
    def from_bytes(cls, reader: BinaryReader) -> "FileHeader":
        header = cls()
        header.version = reader.read_uint32()
        header.stack_size = reader.read_uint32()
        header.runtime_size = reader.read_uint32()
        header.vertex_declaration_count = reader.read_uint16()
        header.material_count = reader.read_uint16()
        header.vert_offset = reader.read_int_array(3)
        header.idx_offset = reader.read_int_array(3)
        header.vert_buffer_size = reader.read_int_array(3)
        header.idx_buffer_size = reader.read_int_array(3)
        header.lod_count = reader.read_byte()
        header.enable_idx_buffer_stream = reader.read_bool()
        header.enable_edge_geometry = reader.read_bool()
        reader.pos += header.PADDING
        return header

    def write(self, output: BytesIO) -> None:
        output.write(pack("<I", self.version))
        output.write(pack("<I", self.stack_size))
        output.write(pack("<I", self.runtime_size))
        output.write(pack("<H", self.vertex_declaration_count))
        output.write(pack("<H", self.material_count))
        for value in self.vert_offset[:3]:
            output.write(pack("<I", value))
        for value in self.idx_offset[:3]:
            output.write(pack("<I", value))
        for value in self.vert_buffer_size[:3]:
            output.write(pack("<I", value))
        for value in self.idx_buffer_size[:3]:
            output.write(pack("<I", value))
        output.write(pack("<B", self.lod_count))
        output.write(pack("<?", self.enable_idx_buffer_stream))
        output.write(pack("<?", self.enable_edge_geometry))
        output.write(padding(self.PADDING))


@dataclass
class MeshHeader:
    radius: float = 1.0
    mesh_count: int = 0
    attribute_count: int = 0
    submesh_count: int = 0
    material_count: int = 0
    bone_count: int = 0
    bone_table_count: int = 0
    shape_count: int = 0
    shape_mesh_count: int = 0
    shape_value_count: int = 0
    lod_count: int = 0
    flags1: int = 0
    element_id_count: int = 0
    terrain_shadow_mesh_count: int = 0
    flags2: int = 0
    model_clip_distance: float = 0.0
    shadow_clip_distance: float = 0.0
    culling_grid_count: int = 0
    terrain_shadow_submesh_count: int = 0
    flags3: int = 0
    bg_change_material_idx: int = 0
    bg_crest_change_material_idx: int = 0
    neck_morph_count: int = 0
    bone_table_array_count_total: int = 0
    UNKNOWN8: int = 0
    face_data_count: int = 0
    PADDING: int = 4

    @classmethod
    def from_bytes(cls, reader: BinaryReader) -> "MeshHeader":
        header = cls()
        header.radius = reader.read_float()
        header.mesh_count = reader.read_uint16()
        header.attribute_count = reader.read_uint16()
        header.submesh_count = reader.read_uint16()
        header.material_count = reader.read_uint16()
        header.bone_count = reader.read_uint16()
        header.bone_table_count = reader.read_uint16()
        header.shape_count = reader.read_uint16()
        header.shape_mesh_count = reader.read_uint16()
        header.shape_value_count = reader.read_uint16()
        header.lod_count = reader.read_byte()
        header.flags1 = reader.read_byte()
        header.element_id_count = reader.read_uint16()
        header.terrain_shadow_mesh_count = reader.read_byte()
        header.flags2 = reader.read_byte()
        header.model_clip_distance = reader.read_float()
        header.shadow_clip_distance = reader.read_float()
        header.culling_grid_count = reader.read_uint16()
        header.terrain_shadow_submesh_count = reader.read_uint16()
        header.flags3 = reader.read_byte()
        header.bg_change_material_idx = reader.read_byte()
        header.bg_crest_change_material_idx = reader.read_byte()
        header.neck_morph_count = reader.read_byte()
        header.bone_table_array_count_total = reader.read_uint16()
        header.UNKNOWN8 = reader.read_uint16()
        header.face_data_count = reader.read_uint32()
        reader.pos += header.PADDING
        return header

    def write(self, output: BytesIO) -> None:
        output.write(pack("<f", self.radius))
        output.write(pack("<H", self.mesh_count))
        output.write(pack("<H", self.attribute_count))
        output.write(pack("<H", self.submesh_count))
        output.write(pack("<H", self.material_count))
        output.write(pack("<H", self.bone_count))
        output.write(pack("<H", self.bone_table_count))
        output.write(pack("<H", self.shape_count))
        output.write(pack("<H", self.shape_mesh_count))
        output.write(pack("<H", self.shape_value_count))
        output.write(pack("<B", self.lod_count))
        output.write(pack("<B", self.flags1))
        output.write(pack("<H", self.element_id_count))
        output.write(pack("<B", self.terrain_shadow_mesh_count))
        output.write(pack("<B", self.flags2))
        output.write(pack("<f", self.model_clip_distance))
        output.write(pack("<f", self.shadow_clip_distance))
        output.write(pack("<H", self.culling_grid_count))
        output.write(pack("<H", self.terrain_shadow_submesh_count))
        output.write(pack("<B", self.flags3))
        output.write(pack("<B", self.bg_change_material_idx))
        output.write(pack("<B", self.bg_crest_change_material_idx))
        output.write(pack("<B", self.neck_morph_count))
        output.write(pack("<H", self.bone_table_array_count_total))
        output.write(pack("<H", self.UNKNOWN8))
        output.write(pack("<I", self.face_data_count))
        output.write(padding(self.PADDING))


@dataclass
class Mesh:
    vertex_count: int = 0
    idx_count: int = 0
    material_idx: int = 0
    submesh_index: int = 0
    submesh_count: int = 0
    bone_table_idx: int = 0
    start_idx: int = 0
    vertex_buffer_offset: list[int] = field(default_factory=lambda: [0, 0, 0])
    vertex_buffer_stride: list[int] = field(default_factory=lambda: [0, 0, 0])
    vertex_stream_count: int = 1
    PADDING: int = 2

    @classmethod
    def from_bytes(cls, reader: BinaryReader) -> "Mesh":
        mesh = cls()
        mesh.vertex_count = reader.read_uint16()
        reader.pos += mesh.PADDING
        mesh.idx_count = reader.read_uint32()
        mesh.material_idx = reader.read_uint16()
        mesh.submesh_index = reader.read_uint16()
        mesh.submesh_count = reader.read_uint16()
        mesh.bone_table_idx = reader.read_uint16()
        mesh.start_idx = reader.read_uint32()
        mesh.vertex_buffer_offset = reader.read_int_array(3)
        mesh.vertex_buffer_stride = reader.read_int_array(3, "B")
        mesh.vertex_stream_count = reader.read_byte()
        return mesh

    def write(self, output: BytesIO) -> None:
        output.write(pack("<H", self.vertex_count))
        output.write(padding(self.PADDING))
        output.write(pack("<I", self.idx_count))
        output.write(pack("<H", self.material_idx))
        output.write(pack("<H", self.submesh_index))
        output.write(pack("<H", self.submesh_count))
        output.write(pack("<H", self.bone_table_idx))
        output.write(pack("<I", self.start_idx))
        for value in self.vertex_buffer_offset:
            output.write(pack("<I", value))
        for value in self.vertex_buffer_stride:
            output.write(pack("<B", value))
        output.write(pack("<B", self.vertex_stream_count))


@dataclass
class Submesh:
    idx_offset: int = 0
    idx_count: int = 0
    attribute_idx_mask: int = 0
    bone_start_idx: int = 0
    bone_count: int = 0

    @classmethod
    def from_bytes(cls, reader: BinaryReader) -> "Submesh":
        value = cls()
        value.idx_offset = reader.read_uint32()
        value.idx_count = reader.read_uint32()
        value.attribute_idx_mask = reader.read_uint32()
        value.bone_start_idx = reader.read_uint16()
        value.bone_count = reader.read_uint16()
        return value

    def write(self, output: BytesIO) -> None:
        output.write(pack("<I", self.idx_offset))
        output.write(pack("<I", self.idx_count))
        output.write(pack("<I", self.attribute_idx_mask))
        output.write(pack("<H", self.bone_start_idx))
        output.write(pack("<H", self.bone_count))


@dataclass
class BoneTable:
    bone_idx: list[int] = field(default_factory=list)
    bone_count: int = 0

    @classmethod
    def from_bytes(cls, reader: BinaryReader) -> "BoneTable":
        table = cls()

        start_pos = reader.pos
        offset = reader.read_uint16()
        size = reader.read_uint16()
        return_pos = reader.pos

        reader.pos = start_pos + offset * 4
        table.bone_idx = reader.read_int_array(size, "H")
        table.bone_count = len(table.bone_idx)

        reader.pos = return_pos
        return table

    def write(self, output: BytesIO, current_offset: int) -> int:
        self.bone_count = len(self.bone_idx)

        output.write(pack("<H", current_offset))
        output.write(pack("<H", self.bone_count))
        header_pos = output.tell()

        output.seek((current_offset - 1) * 4, 1)
        for bone in self.bone_idx:
            output.write(pack("<H", bone))

        if (self.bone_count & 1) == 1:
            output.write(padding(2))

        output.seek(header_pos)
        return ((self.bone_count + 1) // 2) - 1


@dataclass
class Lod:
    mesh_idx: int = 0
    mesh_count: int = 0
    model_lod_range: float = 0.0
    texture_lod_range: float = 0.0
    water_mesh_idx: int = 0
    water_mesh_count: int = 0
    shadow_mesh_idx: int = 0
    shadow_mesh_count: int = 0
    terrain_shadow_mesh_idx: int = 0
    terrain_shadow_mesh_count: int = 0
    vertical_fog_mesh_idx: int = 0
    vertical_fog_mesh_count: int = 0
    edge_geometry_size: int = 0
    edge_geometry_data_offset: int = 0
    polygon_count: int = 0
    neck_morph_offset: int = 0
    neck_morph_count: int = 0
    unknown1: int = 0
    vertex_buffer_size: int = 0
    idx_buffer_size: int = 0
    vertex_data_offset: int = 0
    idx_data_offset: int = 0

    @classmethod
    def from_bytes(cls, reader: BinaryReader) -> "Lod":
        lod = cls()
        lod.mesh_idx = reader.read_uint16()
        lod.mesh_count = reader.read_uint16()
        lod.model_lod_range = reader.read_float()
        lod.texture_lod_range = reader.read_float()
        lod.water_mesh_idx = reader.read_uint16()
        lod.water_mesh_count = reader.read_uint16()
        lod.shadow_mesh_idx = reader.read_uint16()
        lod.shadow_mesh_count = reader.read_uint16()
        lod.terrain_shadow_mesh_idx = reader.read_uint16()
        lod.terrain_shadow_mesh_count = reader.read_uint16()
        lod.vertical_fog_mesh_idx = reader.read_uint16()
        lod.vertical_fog_mesh_count = reader.read_uint16()
        lod.edge_geometry_size = reader.read_uint32()
        lod.edge_geometry_data_offset = reader.read_uint32()
        lod.polygon_count = reader.read_uint32()
        lod.neck_morph_offset = reader.read_byte()
        lod.neck_morph_count = reader.read_byte()
        lod.unknown1 = reader.read_uint16()
        lod.vertex_buffer_size = reader.read_uint32()
        lod.idx_buffer_size = reader.read_uint32()
        lod.vertex_data_offset = reader.read_uint32()
        lod.idx_data_offset = reader.read_uint32()
        return lod

    def write(self, output: BytesIO) -> None:
        output.write(pack("<H", self.mesh_idx))
        output.write(pack("<H", self.mesh_count))
        output.write(pack("<f", self.model_lod_range))
        output.write(pack("<f", self.texture_lod_range))
        output.write(pack("<H", self.water_mesh_idx))
        output.write(pack("<H", self.water_mesh_count))
        output.write(pack("<H", self.shadow_mesh_idx))
        output.write(pack("<H", self.shadow_mesh_count))
        output.write(pack("<H", self.terrain_shadow_mesh_idx))
        output.write(pack("<H", self.terrain_shadow_mesh_count))
        output.write(pack("<H", self.vertical_fog_mesh_idx))
        output.write(pack("<H", self.vertical_fog_mesh_count))
        output.write(pack("<I", self.edge_geometry_size))
        output.write(pack("<I", self.edge_geometry_data_offset))
        output.write(pack("<I", self.polygon_count))
        output.write(pack("<B", self.neck_morph_offset))
        output.write(pack("<B", self.neck_morph_count))
        output.write(pack("<H", self.unknown1))
        output.write(pack("<I", self.vertex_buffer_size))
        output.write(pack("<I", self.idx_buffer_size))
        output.write(pack("<I", self.vertex_data_offset))
        output.write(pack("<I", self.idx_data_offset))

    @staticmethod
    def size() -> int:
        return 60


@dataclass
class Shape:
    name: str = ""
    mesh_start_idx: list[int] = field(default_factory=lambda: [0, 0, 0])
    mesh_count: list[int] = field(default_factory=lambda: [0, 0, 0])

    def write(self, output: BytesIO, name_offset: int) -> None:
        output.write(pack("<I", name_offset))
        for value in self.mesh_start_idx[:3]:
            output.write(pack("<H", value))
        for value in self.mesh_count[:3]:
            output.write(pack("<H", value))

    @classmethod
    def from_bytes(
        cls,
        reader: BinaryReader,
        strings: list[str],
        offsets: list[int],
    ) -> "Shape":
        shape = cls()
        name_offset = reader.read_uint32()
        try:
            idx = offsets.index(name_offset)
            shape.name = strings[idx]
        except ValueError:
            shape.name = ""

        shape.mesh_start_idx = reader.read_int_array(3, "H")
        shape.mesh_count = reader.read_int_array(3, "H")
        return shape


@dataclass
class ShapeMesh:
    mesh_idx_offset: int = 0
    shape_value_count: int = 0
    shape_value_offset: int = 0

    def write(self, output: BytesIO) -> None:
        output.write(pack("<I", self.mesh_idx_offset))
        output.write(pack("<I", self.shape_value_count))
        output.write(pack("<I", self.shape_value_offset))

    @classmethod
    def from_bytes(cls, reader: BinaryReader) -> "ShapeMesh":
        value = cls()
        value.mesh_idx_offset = reader.read_uint32()
        value.shape_value_count = reader.read_uint32()
        value.shape_value_offset = reader.read_uint32()
        return value


@dataclass
class ShapeValue:
    base_indices_idx: int = 0
    replace_vert_idx: int = 0

    def write(self, output: BytesIO) -> None:
        output.write(pack("<H", self.base_indices_idx))
        output.write(pack("<H", self.replace_vert_idx))

    @classmethod
    def from_bytes(cls, reader: BinaryReader) -> "ShapeValue":
        value = cls()
        value.base_indices_idx = reader.read_uint16()
        value.replace_vert_idx = reader.read_uint16()
        return value


def vertex_element_size(vtype: int) -> int:
    mapping = {
        int(VertexType.SINGLE1): 4,
        int(VertexType.SINGLE2): 8,
        int(VertexType.SINGLE3): 12,
        int(VertexType.SINGLE4): 16,
        int(VertexType.UBYTE4): 4,
        int(VertexType.USHORT4): 8,
    }
    return mapping.get(vtype, 4)


def _vertex_element_size(vtype: int) -> int:
    return vertex_element_size(vtype)
