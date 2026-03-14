from __future__ import annotations

from dataclasses import dataclass, field
from io import BytesIO
from struct import pack

from .binary_io import BinaryReader, padding
from .binary_structs import (
    BoneTable,
    BoundingBox,
    FileHeader,
    Lod,
    Mesh,
    MeshHeader,
    Shape,
    ShapeMesh,
    ShapeValue,
    Submesh,
    VertexDeclaration,
)


@dataclass
class MdlBinaryModel:
    FILE_HEADER_SIZE: int = 0x44
    NUM_VERTICES: int = 17

    header: FileHeader = field(default_factory=FileHeader)
    mesh_header: MeshHeader = field(default_factory=MeshHeader)
    attributes: list[str] = field(default_factory=list)
    materials: list[str] = field(default_factory=list)
    bones: list[str] = field(default_factory=list)
    bone_tables: list[BoneTable] = field(default_factory=list)
    shapes: list[Shape] = field(default_factory=list)
    shape_meshes: list[ShapeMesh] = field(default_factory=list)
    shape_values: list[ShapeValue] = field(default_factory=list)
    vertex_declarations: list[VertexDeclaration] = field(default_factory=list)
    lods: list[Lod] = field(default_factory=lambda: [Lod(), Lod(), Lod()])
    meshes: list[Mesh] = field(default_factory=list)
    submeshes: list[Submesh] = field(default_factory=list)
    submesh_bonemaps: list[int] = field(default_factory=list)
    bounding_box: BoundingBox = field(default_factory=BoundingBox)
    mdl_bounding_box: BoundingBox = field(default_factory=BoundingBox)
    water_bounding_box: BoundingBox = field(default_factory=BoundingBox)
    vertical_fog_bounding_box: BoundingBox = field(default_factory=BoundingBox)
    bone_bounding_boxes: list[BoundingBox] = field(default_factory=list)
    buffers: bytes = b""

    def _set_counts(self) -> None:
        self.header.vertex_declaration_count = len(self.vertex_declarations)
        self.header.material_count = len(self.materials)
        self.mesh_header.mesh_count = len(self.meshes)
        self.mesh_header.attribute_count = len(self.attributes)
        self.mesh_header.submesh_count = len(self.submeshes)
        self.mesh_header.material_count = len(self.materials)
        self.mesh_header.bone_count = len(self.bones)
        self.mesh_header.shape_count = len(self.shapes)
        self.mesh_header.shape_mesh_count = len(self.shape_meshes)
        self.mesh_header.shape_value_count = len(self.shape_values)
        self.mesh_header.bone_table_count = len(self.bone_tables)
        self.mesh_header.bone_table_array_count_total = sum(
            (
                (len(t.bone_idx) + 1)
                if (len(t.bone_idx) & 1) == 1
                else len(t.bone_idx)
            )
            for t in self.bone_tables
        )
        self.mesh_header.lod_count = self.header.lod_count

    def _data_offset(self) -> int:
        return (
            self.FILE_HEADER_SIZE
            + self.header.runtime_size
            + self.header.stack_size
        )

    def _update_offsets_for_write(self, total_size: int) -> None:
        for i in range(self.header.lod_count):
            self.header.vert_offset[i] += total_size
            self.header.idx_offset[i] += total_size
            self.lods[i].vertex_data_offset += total_size
            self.lods[i].idx_data_offset += total_size
            if self.lods[i].edge_geometry_data_offset:
                self.lods[i].edge_geometry_data_offset += total_size

    def to_bytes(self) -> bytes:
        self.header.stack_size = (
            len(self.vertex_declarations) * self.NUM_VERTICES * 8
        )
        self._set_counts()

        out = BytesIO()
        out.seek(self.FILE_HEADER_SIZE)

        for decl in self.vertex_declarations:
            decl.write(out)

        string_offsets = _write_string_block(
            out,
            self.attributes
            + self.bones
            + self.materials
            + [shape.name for shape in self.shapes],
        )

        self.mesh_header.write(out)

        lod_pos = out.tell()
        out.seek(Lod.size() * 3, 1)

        for mesh in self.meshes:
            mesh.write(out)

        for i in range(len(self.attributes)):
            out.write(pack("<I", string_offsets[i]))

        for submesh in self.submeshes:
            submesh.write(out)

        mat_start = len(self.attributes) + len(self.bones)
        for i in range(len(self.materials)):
            out.write(pack("<I", string_offsets[mat_start + i]))

        bone_start = len(self.attributes)
        for i in range(len(self.bones)):
            out.write(pack("<I", string_offsets[bone_start + i]))

        current_offset = len(self.bone_tables)
        for table in self.bone_tables:
            current_offset += table.write(out, current_offset)

        out.seek(self.mesh_header.bone_table_array_count_total * 2, 1)

        shape_start = (
            len(self.attributes) + len(self.bones) + len(self.materials)
        )
        for i, shape in enumerate(self.shapes):
            shape.write(out, string_offsets[shape_start + i])

        for shape_mesh in self.shape_meshes:
            shape_mesh.write(out)

        for value in self.shape_values:
            value.write(out)

        out.write(pack("<I", len(self.submesh_bonemaps) * 2))
        for bone in self.submesh_bonemaps:
            out.write(pack("<H", bone))

        pad = (out.tell() + 1) & 0b111
        if pad > 0:
            pad = 8 - pad

        out.write(pack("<B", pad))
        if pad > 0:
            out.write(
                (0xDEADBEEFF00DCAFE).to_bytes(8, byteorder="little")[:pad]
            )

        self.bounding_box.write(out)
        self.mdl_bounding_box.write(out)
        self.water_bounding_box.write(out)
        self.vertical_fog_bounding_box.write(out)
        for box in self.bone_bounding_boxes:
            box.write(out)

        total_size = out.tell()
        out.write(self.buffers)

        out.seek(0)
        self.header.runtime_size = (
            total_size - self.header.stack_size - self.FILE_HEADER_SIZE
        )
        self._update_offsets_for_write(total_size)
        self.header.write(out)

        out.seek(lod_pos)
        for lod in self.lods:
            lod.write(out)

        return out.getvalue()

    @classmethod
    def from_bytes(cls, data: bytes) -> "MdlBinaryModel":
        model = cls()
        reader = BinaryReader(data)

        model.header = FileHeader.from_bytes(reader)
        data_offset = model._data_offset()

        for i in range(model.header.lod_count):
            model.header.vert_offset[i] -= data_offset
            model.header.idx_offset[i] -= data_offset

        model.vertex_declarations = [
            VertexDeclaration.from_bytes(reader)
            for _ in range(model.header.vertex_declaration_count)
        ]

        all_strings, offsets = _read_string_block(reader)

        model.mesh_header = MeshHeader.from_bytes(reader)

        model.lods = []
        for i in range(3):
            lod = Lod.from_bytes(reader)
            if i < model.header.lod_count:
                lod.vertex_data_offset -= data_offset
                lod.idx_data_offset -= data_offset
                if lod.edge_geometry_data_offset:
                    lod.edge_geometry_data_offset -= data_offset
            model.lods.append(lod)

        model.meshes = [
            Mesh.from_bytes(reader) for _ in range(model.mesh_header.mesh_count)
        ]

        model.attributes = _read_string_refs(
            reader,
            all_strings,
            offsets,
            model.mesh_header.attribute_count,
        )

        model.submeshes = [
            Submesh.from_bytes(reader)
            for _ in range(model.mesh_header.submesh_count)
        ]

        model.materials = _read_string_refs(
            reader,
            all_strings,
            offsets,
            model.mesh_header.material_count,
        )
        model.bones = _read_string_refs(
            reader,
            all_strings,
            offsets,
            model.mesh_header.bone_count,
        )

        model.bone_tables = [
            BoneTable.from_bytes(reader)
            for _ in range(model.mesh_header.bone_table_count)
        ]
        reader.pos += model.mesh_header.bone_table_array_count_total * 2

        model.shapes = [
            Shape.from_bytes(reader, all_strings, offsets)
            for _ in range(model.mesh_header.shape_count)
        ]
        model.shape_meshes = [
            ShapeMesh.from_bytes(reader)
            for _ in range(model.mesh_header.shape_mesh_count)
        ]
        model.shape_values = [
            ShapeValue.from_bytes(reader)
            for _ in range(model.mesh_header.shape_value_count)
        ]

        submesh_bonemap_size = reader.read_uint32()
        count = submesh_bonemap_size // 2
        model.submesh_bonemaps = (
            reader.read_int_array(count, "H") if count > 0 else []
        )

        pad_size = reader.read_byte()
        reader.pos += pad_size

        model.bounding_box = BoundingBox.from_bytes(reader)
        model.mdl_bounding_box = BoundingBox.from_bytes(reader)
        model.water_bounding_box = BoundingBox.from_bytes(reader)
        model.vertical_fog_bounding_box = BoundingBox.from_bytes(reader)
        model.bone_bounding_boxes = [
            BoundingBox.from_bytes(reader)
            for _ in range(model.mesh_header.bone_count)
        ]

        reader.pos = data_offset
        model.buffers = reader.read_bytes(reader.length - reader.pos)

        return model


def _write_string_block(output: BytesIO, values: list[str]) -> list[int]:
    start_pos = output.tell()
    base_pos = start_pos + 8

    output.write(pack("<H", len(values)))
    output.write(pack("<H", 0))
    output.write(pack("<I", 0))

    offsets: list[int] = []
    for value in values:
        current = output.tell()
        output.write(value.encode("utf-8"))
        output.write(b"\0")
        offsets.append(current - base_pos)

    if output.tell() & 0b11:
        output.write(padding(4 - (output.tell() & 0b11)))

    size = output.tell() - base_pos
    return_pos = output.tell()
    output.seek(start_pos + 4)
    output.write(pack("<I", size))
    output.seek(return_pos)

    return offsets


def _read_string_block(reader: BinaryReader) -> tuple[list[str], list[int]]:
    string_count = reader.read_uint16()
    reader.read_uint16()
    string_size = reader.read_uint32()
    blob = reader.read_bytes(string_size)

    values: list[str] = []
    offsets: list[int] = []
    cursor = 0
    for _ in range(string_count):
        end = blob.index(b"\0", cursor)
        values.append(blob[cursor:end].decode("utf-8"))
        offsets.append(cursor)
        cursor = end + 1

    return values, offsets


def _read_string_refs(
    reader: BinaryReader,
    values: list[str],
    offsets: list[int],
    count: int,
) -> list[str]:
    result: list[str] = []
    for _ in range(count):
        ref = reader.read_uint32()
        try:
            idx = offsets.index(ref)
            result.append(values[idx])
        except ValueError:
            result.append("")
    return result
