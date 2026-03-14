from __future__ import annotations

from dataclasses import replace
from struct import pack
from typing import Callable

from .binary import (
    BoneTable,
    BoundingBox,
    Lod,
    MdlBinaryModel,
    Mesh,
    Shape,
    ShapeMesh,
    ShapeValue,
    Submesh,
    VertexDeclaration,
    VertexType,
    VertexUsage,
)

from .structures import MdlMesh, MdlModel
from .vertex_codec import (
    SkinningWeightCount,
    encode_vertex,
    skinning_weight_count,
    vertex_stride,
)
from .checks import validate_binary_model, validate_model


ProgressFn = Callable[[str, float], None]


def _default_progress(_: str, __: float) -> None:
    return


def _pack_mesh_vertex_buffer(
    mesh: MdlMesh, skinning_weights: SkinningWeightCount
) -> tuple[bytes, int]:
    chunks = [
        encode_vertex(vertex, skinning_weights=skinning_weights)
        for vertex in mesh.vertices
    ]
    return b"".join(chunks), vertex_stride(skinning_weights)


def _collect_mesh_bones(mesh: MdlMesh) -> list[int]:
    used: list[int] = []
    for vert in mesh.vertices:
        for idx, weight in zip(vert.bone_indices, vert.bone_weights):
            if weight <= 0.0:
                continue
            if idx not in used:
                used.append(idx)
    used.sort()
    return used


def _remap_mesh_bone_indices(mesh: MdlMesh, bone_table: list[int]) -> MdlMesh:
    if not bone_table:
        return mesh

    table_lookup = {
        global_idx: local_idx for local_idx, global_idx in enumerate(bone_table)
    }

    remapped_vertices = []
    for vert in mesh.vertices:
        source_indices = list(vert.bone_indices)
        source_weights = list(vert.bone_weights)
        while len(source_indices) < 8:
            source_indices.append(0)
        while len(source_weights) < 8:
            source_weights.append(0.0)

        remapped = []
        for idx, weight in zip(source_indices[:8], source_weights[:8]):
            if weight <= 0.0:
                remapped.append(0)
            else:
                remapped.append(table_lookup.get(idx, 0))

        remapped_vertices.append(
            replace(
                vert,
                bone_indices=(
                    remapped[0],
                    remapped[1],
                    remapped[2],
                    remapped[3],
                    remapped[4],
                    remapped[5],
                    remapped[6],
                    remapped[7],
                ),
            )
        )

    return replace(mesh, vertices=remapped_vertices)


def _build_shape_payload(
    model: MdlModel, meshes: list[MdlMesh]
) -> tuple[list[MdlMesh], list[Shape], list[ShapeMesh], list[ShapeValue]]:
    updated_meshes = [
        replace(mesh, vertices=list(mesh.vertices)) for mesh in meshes
    ]

    shapes: list[Shape] = []
    shape_meshes: list[ShapeMesh] = []
    shape_values: list[ShapeValue] = []

    shape_mesh_cursor = 0
    shape_value_cursor = 0

    for shapekey in model.shapekeys:
        per_mesh = sorted(shapekey.mesh_deltas.items(), key=lambda x: x[0])
        shape_start_idx = shape_mesh_cursor
        emitted_shape_meshes = 0

        for mesh_idx, deltas in per_mesh:
            if mesh_idx < 0 or mesh_idx >= len(updated_meshes):
                continue
            mesh = updated_meshes[mesh_idx]

            # Shape values reference index-buffer positions, not vertex IDs.
            index_positions_by_vertex: dict[int, list[int]] = {}
            for index_pos, vertex_idx in enumerate(mesh.indices):
                index_positions_by_vertex.setdefault(vertex_idx, []).append(
                    index_pos
                )

            local_value_start = shape_value_cursor
            local_value_count = 0
            for delta in deltas:
                base_idx = delta.vertex_index
                if base_idx < 0 or base_idx >= len(mesh.vertices):
                    continue

                base_index_positions = index_positions_by_vertex.get(
                    base_idx, []
                )
                if not base_index_positions:
                    continue

                base_vert = mesh.vertices[base_idx]
                replacement_vert = replace(
                    base_vert,
                    position=(
                        base_vert.position[0] + delta.delta[0],
                        base_vert.position[1] + delta.delta[1],
                        base_vert.position[2] + delta.delta[2],
                    ),
                )

                replace_idx = len(mesh.vertices)
                if replace_idx > 0xFFFF:
                    raise ValueError(
                        f"Shapekey {shapekey.name} replacement vertex index {replace_idx} exceeds uint16 range"
                    )
                if shape_value_cursor >= 0x10000:
                    raise ValueError(
                        f"Total shape values exceed uint16 limit (65535) while processing shapekey {shapekey.name}"
                    )
                mesh.vertices.append(replacement_vert)

                for base_index_pos in base_index_positions:
                    if base_index_pos > 0xFFFF:
                        raise ValueError(
                            f"Shapekey {shapekey.name} base index position {base_index_pos} exceeds uint16 range"
                        )
                    if shape_value_cursor >= 0x10000:
                        raise ValueError(
                            f"Total shape values exceed uint16 limit (65535) while processing shapekey {shapekey.name}"
                        )
                    shape_values.append(
                        ShapeValue(
                            base_indices_idx=base_index_pos,
                            replace_vert_idx=replace_idx,
                        )
                    )
                    shape_value_cursor += 1
                    local_value_count += 1

            shape_meshes.append(
                ShapeMesh(
                    mesh_idx_offset=mesh_idx,
                    shape_value_count=local_value_count,
                    shape_value_offset=local_value_start,
                )
            )
            shape_mesh_cursor += 1
            emitted_shape_meshes += 1

        shapes.append(
            Shape(
                name=shapekey.name,
                mesh_start_idx=[shape_start_idx, 0, 0],
                mesh_count=[emitted_shape_meshes, 0, 0],
            )
        )

    return updated_meshes, shapes, shape_meshes, shape_values


def _pack_mesh_index_buffer(mesh: MdlMesh) -> bytes:
    if any(index > 65535 for index in mesh.indices):
        raise ValueError(
            "Direct MDL writer currently supports up to 65535 vertices per mesh"
        )

    return b"".join(pack("<H", index) for index in mesh.indices)


def _build_vertex_declaration(
    skinning_weights: SkinningWeightCount,
) -> VertexDeclaration:
    decl = VertexDeclaration()
    decl.create_element(VertexType.SINGLE3, VertexUsage.POSITION, stream=0)
    decl.create_element(VertexType.SINGLE3, VertexUsage.NORMAL, stream=0)
    decl.create_element(VertexType.SINGLE2, VertexUsage.UV, stream=0)

    skinning_vertex_type = (
        VertexType.USHORT4 if skinning_weights == 8 else VertexType.UBYTE4
    )
    decl.create_element(
        skinning_vertex_type, VertexUsage.BLEND_INDICES, stream=0
    )
    decl.create_element(
        skinning_vertex_type, VertexUsage.BLEND_WEIGHTS, stream=0
    )
    return decl


def _all_positions(meshes: list[MdlMesh]) -> list[tuple[float, float, float]]:
    rows: list[tuple[float, float, float]] = []
    for mesh in meshes:
        for vertex in mesh.vertices:
            rows.append(vertex.position)

    return rows


def to_binary_model(
    model: MdlModel, progress: ProgressFn | None = None
) -> MdlBinaryModel:
    if progress is None:
        progress = _default_progress

    validate_model(model)

    lod0_meshes = model.lod_meshes[0] if model.lod_meshes else []
    lod0_meshes, shape_defs, shape_mesh_defs, shape_value_defs = (
        _build_shape_payload(model, lod0_meshes)
    )

    skinning_weights: SkinningWeightCount = 4
    for mesh in lod0_meshes:
        for vertex in mesh.vertices:
            if skinning_weight_count(vertex) == 8:
                skinning_weights = 8
                break
        if skinning_weights == 8:
            break

    binary_model = MdlBinaryModel()
    binary_model.header.lod_count = 1
    binary_model.header.enable_idx_buffer_stream = True
    binary_model.header.enable_edge_geometry = False
    binary_model.vertex_declarations = [
        _build_vertex_declaration(skinning_weights)
    ]
    binary_model.materials = model.materials.copy()
    binary_model.bones = model.bones.copy()
    binary_model.bone_bounding_boxes = [
        BoundingBox() for _ in binary_model.bones
    ]
    # HasBonelessParts/STATIC_MESH is only valid for boneless furniture-style models.
    # Keep flags2 clear for skinned exports unless explicitly needed later.
    binary_model.mesh_header.flags2 = 0

    vertex_blob_parts: list[bytes] = []
    index_blob_parts: list[bytes] = []

    current_vert_offset = 0
    global_index_start = 0
    # Map mesh_idx → index-buffer start offset (needed to fix up ShapeMesh later)
    mesh_index_starts: dict[int, int] = {}

    progress("packing_meshes", 0.0)
    total = len(lod0_meshes)

    for mesh_idx, source_mesh in enumerate(lod0_meshes):
        mesh_bones = _collect_mesh_bones(source_mesh)
        binary_model.bone_tables.append(
            BoneTable(bone_idx=mesh_bones, bone_count=len(mesh_bones))
        )
        mapped_mesh = _remap_mesh_bone_indices(source_mesh, mesh_bones)
        mesh_index_starts[mesh_idx] = global_index_start

        vert_data, stride = _pack_mesh_vertex_buffer(
            mapped_mesh, skinning_weights
        )
        idx_data = _pack_mesh_index_buffer(mapped_mesh)

        if (
            mapped_mesh.material_path
            and mapped_mesh.material_path not in binary_model.materials
        ):
            binary_model.materials.append(mapped_mesh.material_path)

        material_idx = 0
        if mapped_mesh.material_path in binary_model.materials:
            material_idx = binary_model.materials.index(
                mapped_mesh.material_path
            )

        source_submeshes = (
            mapped_mesh.submeshes
            if mapped_mesh.submeshes
            else [
                MdlSubmesh(
                    start_index=0,
                    index_count=len(mapped_mesh.indices),
                    attribute_mask=0,
                )
            ]
        )

        mesh = Mesh(
            vertex_count=len(mapped_mesh.vertices),
            idx_count=len(mapped_mesh.indices),
            material_idx=material_idx,
            submesh_index=len(binary_model.submeshes),
            submesh_count=len(source_submeshes),
            bone_table_idx=mesh_idx,
            start_idx=global_index_start,
            vertex_buffer_offset=[current_vert_offset, 0, 0],
            vertex_buffer_stride=[stride, 0, 0],
            vertex_stream_count=1,
        )
        binary_model.meshes.append(mesh)

        for source_submesh in source_submeshes:
            submesh_bone_start = len(binary_model.submesh_bonemaps)
            # TT stores per-part/local bone lists, so duplicate the local mapping
            # slice for each exported submesh.
            binary_model.submesh_bonemaps.extend(range(len(mesh_bones)))

            local_submesh_start = max(0, int(source_submesh.start_index))
            if local_submesh_start > len(mapped_mesh.indices):
                local_submesh_start = len(mapped_mesh.indices)

            binary_model.submeshes.append(
                Submesh(
                    idx_offset=global_index_start + local_submesh_start,
                    idx_count=source_submesh.index_count,
                    attribute_idx_mask=source_submesh.attribute_mask,
                    bone_start_idx=submesh_bone_start,
                    bone_count=len(mesh_bones),
                )
            )

        vertex_blob_parts.append(vert_data)
        index_blob_parts.append(idx_data)

        current_vert_offset += len(vert_data)
        global_index_start += len(mapped_mesh.indices)

        if total:
            progress("packing_meshes", float(mesh_idx + 1) / float(total))

    vertex_blob = b"".join(vertex_blob_parts)
    index_blob = b"".join(index_blob_parts)

    binary_model.buffers = vertex_blob + index_blob

    binary_model.header.vert_offset = [0, 0, 0]
    binary_model.header.idx_offset = [len(vertex_blob), 0, 0]
    binary_model.header.vert_buffer_size = [len(vertex_blob), 0, 0]
    binary_model.header.idx_buffer_size = [len(index_blob), 0, 0]

    lod0 = Lod(
        mesh_idx=0,
        mesh_count=len(binary_model.meshes),
        model_lod_range=0.0,
        texture_lod_range=0.0,
        water_mesh_idx=0,
        water_mesh_count=0,
        shadow_mesh_idx=0,
        shadow_mesh_count=0,
        terrain_shadow_mesh_idx=0,
        terrain_shadow_mesh_count=0,
        vertical_fog_mesh_idx=0,
        vertical_fog_mesh_count=0,
        edge_geometry_size=0,
        edge_geometry_data_offset=0,
        polygon_count=sum(len(m.indices) // 3 for m in lod0_meshes),
        neck_morph_offset=0,
        neck_morph_count=0,
        unknown1=0,
        vertex_buffer_size=len(vertex_blob),
        idx_buffer_size=len(index_blob),
        vertex_data_offset=0,
        idx_data_offset=len(vertex_blob),
    )
    binary_model.lods[0] = lod0
    binary_model.lods[1] = Lod()
    binary_model.lods[2] = Lod()

    positions = _all_positions(lod0_meshes)
    if positions:
        bbox = BoundingBox.from_positions(positions)
        binary_model.bounding_box = bbox
        binary_model.mdl_bounding_box = BoundingBox(
            min=bbox.min[:], max=bbox.max[:]
        )
        binary_model.mesh_header.radius = bbox.radius()

    binary_model.shapes = shape_defs
    # Fix each ShapeMesh's mesh_idx_offset from a raw mesh array index (0,1,2…)
    # to the actual start index in the flat index buffer, which is what TexTools
    # uses to match shape parts back to their mesh (via IndexDataOffset lookup).
    for sm in shape_mesh_defs:
        sm.mesh_idx_offset = mesh_index_starts.get(sm.mesh_idx_offset, 0)
    binary_model.shape_meshes = shape_mesh_defs
    binary_model.shape_values = shape_value_defs

    # Keep header counts in sync before validation so overflow/range checks
    # evaluate the exact values that will be serialized.
    binary_model._set_counts()

    validate_binary_model(binary_model)

    progress("packing_meshes", 1.0)
    return binary_model


def to_xiv_model(
    model: MdlModel, progress: ProgressFn | None = None
) -> MdlBinaryModel:
    # Backward-compatible alias. Internally this no longer depends on xivpy.
    return to_binary_model(model, progress=progress)


def model_to_bytes(
    model: MdlModel, progress: ProgressFn | None = None
) -> bytes:
    binary_model = to_binary_model(model, progress=progress)
    return binary_model.to_bytes()
