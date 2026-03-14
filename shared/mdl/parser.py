from __future__ import annotations

from typing import Callable

from .binary import MdlBinaryModel, VertexType, VertexUsage

from .structures import (
    MdlMesh,
    MdlModel,
    MdlShapeDelta,
    MdlShapeKey,
    MdlSubmesh,
    MdlVertex,
)
from .vertex_codec import (
    SkinningWeightCount,
    decode_u16,
    decode_vertex,
    vertex_stride,
)
from .checks import validate_binary_model


ProgressFn = Callable[[str, float], None]


def _default_progress(_: str, __: float) -> None:
    return


def _mesh_skinning_weight_count(
    binary_model: MdlBinaryModel, mesh_index: int
) -> SkinningWeightCount:
    if not binary_model.vertex_declarations:
        return 4

    # Writer currently emits one declaration for all meshes; keep fallback compatible.
    decl_idx = (
        mesh_index if mesh_index < len(binary_model.vertex_declarations) else 0
    )
    declaration = binary_model.vertex_declarations[decl_idx]
    for element in declaration.vertex_elements:
        if element.usage != int(VertexUsage.BLEND_WEIGHTS):
            continue
        if element.type == int(VertexType.USHORT4):
            return 8
        return 4

    return 4


def _decode_vertices_and_indices(
    binary_model: MdlBinaryModel, mesh_index: int
) -> tuple[list[MdlVertex], list[int]]:
    mesh = binary_model.meshes[mesh_index]
    skinning_weights = _mesh_skinning_weight_count(binary_model, mesh_index)
    required_stride = vertex_stride(skinning_weights)

    bone_table: list[int] = []
    if 0 <= mesh.bone_table_idx < len(binary_model.bone_tables):
        bone_table = binary_model.bone_tables[mesh.bone_table_idx].bone_idx

    stride = mesh.vertex_buffer_stride[0]
    vert_offset = mesh.vertex_buffer_offset[0]
    vert_count = mesh.vertex_count

    vertices: list[MdlVertex] = []
    for i in range(vert_count):
        start = vert_offset + i * stride
        if stride < required_stride:
            break
        if start + required_stride > len(binary_model.buffers):
            break
        vertices.append(
            decode_vertex(
                binary_model.buffers,
                start,
                bone_table,
                skinning_weights=skinning_weights,
            )
        )

    idx_base = binary_model.header.idx_offset[0]
    idx_start = idx_base + mesh.start_idx * 2
    idx_count = mesh.idx_count

    indices: list[int] = []
    for i in range(idx_count):
        byte_pos = idx_start + i * 2
        if byte_pos + 2 > len(binary_model.buffers):
            break
        index = decode_u16(binary_model.buffers, byte_pos)
        indices.append(index)

    return vertices, indices


def from_bytes(data: bytes, progress: ProgressFn | None = None) -> MdlModel:
    """Parse an MDL binary into SerenKit's high-level static mesh representation.

    The current parser fully decodes the MVP vertex/index layout used by the
    standalone writer (position, normal, uv0 in stream 0).
    """

    if progress is None:
        progress = _default_progress

    progress("parsing_header", 0.0)
    binary_model = MdlBinaryModel.from_bytes(data)
    validate_binary_model(binary_model)
    progress("parsing_header", 1.0)

    progress("parsing_meshes", 0.0)
    lod0_meshes: list[MdlMesh] = []
    decoded_all_vertices: dict[int, list[MdlVertex]] = {}
    total = len(binary_model.meshes)
    for idx, mesh in enumerate(binary_model.meshes):
        material_path = ""
        if 0 <= mesh.material_idx < len(binary_model.materials):
            material_path = binary_model.materials[mesh.material_idx]

        submeshes: list[MdlSubmesh] = []
        start = mesh.submesh_index
        end = start + mesh.submesh_count
        for sub in binary_model.submeshes[start:end]:
            local_submesh_start = sub.idx_offset - mesh.start_idx
            if local_submesh_start < 0:
                local_submesh_start = 0
            submeshes.append(
                MdlSubmesh(
                    start_index=local_submesh_start,
                    index_count=sub.idx_count,
                    attribute_mask=sub.attribute_idx_mask,
                )
            )

        vertices, indices = _decode_vertices_and_indices(binary_model, idx)
        decoded_all_vertices[idx] = vertices
        base_vertex_count = (max(indices) + 1) if indices else len(vertices)

        lod0_meshes.append(
            MdlMesh(
                name=f"mesh_{idx}",
                material_path=material_path,
                vertices=vertices[:base_vertex_count],
                indices=indices,
                submeshes=submeshes if submeshes else [MdlSubmesh()],
            )
        )

        if total:
            progress("parsing_meshes", float(idx + 1) / float(total))

    progress("parsing_meshes", 1.0)

    shapekeys: list[MdlShapeKey] = []
    mesh_index_offset_to_mesh_idx = {
        mesh.start_idx: mesh_idx
        for mesh_idx, mesh in enumerate(binary_model.meshes)
    }
    for shape in binary_model.shapes:
        mesh_start = shape.mesh_start_idx[0]
        mesh_count = shape.mesh_count[0]
        mesh_deltas: dict[int, list[MdlShapeDelta]] = {}

        for i in range(mesh_start, mesh_start + mesh_count):
            if i < 0 or i >= len(binary_model.shape_meshes):
                continue
            shape_mesh = binary_model.shape_meshes[i]

            deltas: list[MdlShapeDelta] = []
            value_start = shape_mesh.shape_value_offset
            value_end = value_start + shape_mesh.shape_value_count
            mesh_idx = mesh_index_offset_to_mesh_idx.get(
                shape_mesh.mesh_idx_offset
            )
            if mesh_idx is None:
                continue

            mesh_indices = lod0_meshes[mesh_idx].indices
            decoded_vertices = decoded_all_vertices.get(mesh_idx, [])
            seen_vertex_indices: set[int] = set()
            for j in range(value_start, value_end):
                if j < 0 or j >= len(binary_model.shape_values):
                    continue
                sv = binary_model.shape_values[j]

                if sv.base_indices_idx >= len(mesh_indices):
                    continue
                vertex_index = mesh_indices[sv.base_indices_idx]
                if vertex_index in seen_vertex_indices:
                    continue
                seen_vertex_indices.add(vertex_index)

                if vertex_index >= len(lod0_meshes[mesh_idx].vertices):
                    continue
                if sv.replace_vert_idx >= len(decoded_vertices):
                    continue

                base_pos = lod0_meshes[mesh_idx].vertices[vertex_index].position
                replace_pos = decoded_vertices[sv.replace_vert_idx].position

                deltas.append(
                    MdlShapeDelta(
                        vertex_index=vertex_index,
                        delta=(
                            replace_pos[0] - base_pos[0],
                            replace_pos[1] - base_pos[1],
                            replace_pos[2] - base_pos[2],
                        ),
                    )
                )

            if deltas:
                mesh_deltas[mesh_idx] = deltas

        shapekeys.append(MdlShapeKey(name=shape.name, mesh_deltas=mesh_deltas))

    return MdlModel(
        lod_meshes=[lod0_meshes],
        materials=binary_model.materials.copy(),
        attributes=binary_model.attributes.copy(),
        bones=binary_model.bones.copy(),
        shapekeys=shapekeys,
    )
