from __future__ import annotations

from .binary import MdlBinaryModel, VertexType, VertexUsage
from .structures import MdlModel
from .vertex_codec import vertex_stride


def validate_model(model: MdlModel) -> None:
    meshes = model.lod_meshes[0] if model.lod_meshes else []

    for mesh_idx, mesh in enumerate(meshes):
        if not mesh.indices:
            raise ValueError(f"Mesh {mesh_idx} has no indices")
        if not mesh.vertices:
            raise ValueError(f"Mesh {mesh_idx} has no vertices")

        max_index = max(mesh.indices)
        if max_index >= len(mesh.vertices):
            raise ValueError(
                f"Mesh {mesh_idx} index {max_index} out of bounds for {len(mesh.vertices)} vertices"
            )

        for vert_idx, vert in enumerate(mesh.vertices):
            if len(vert.bone_indices) not in (4, 8):
                raise ValueError(
                    f"Mesh {mesh_idx} vertex {vert_idx} has unsupported bone index count {len(vert.bone_indices)}"
                )
            if len(vert.bone_weights) not in (4, 8):
                raise ValueError(
                    f"Mesh {mesh_idx} vertex {vert_idx} has unsupported bone weight count {len(vert.bone_weights)}"
                )

            if any(i < 0 for i in vert.bone_indices):
                raise ValueError(
                    f"Mesh {mesh_idx} vertex {vert_idx} has negative bone index"
                )
            if any(
                i >= len(model.bones) and w > 0.0
                for i, w in zip(vert.bone_indices, vert.bone_weights)
            ):
                raise ValueError(
                    f"Mesh {mesh_idx} vertex {vert_idx} references missing bone"
                )

            weight_sum = sum(vert.bone_weights)
            if weight_sum < -1e-6 or weight_sum > 1.001:
                raise ValueError(
                    f"Mesh {mesh_idx} vertex {vert_idx} has invalid total bone weight {weight_sum}"
                )

    for shape in model.shapekeys:
        for mesh_idx, deltas in shape.mesh_deltas.items():
            if mesh_idx < 0 or mesh_idx >= len(meshes):
                raise ValueError(
                    f"Shapekey {shape.name} references invalid mesh {mesh_idx}"
                )
            mesh = meshes[mesh_idx]
            for delta in deltas:
                if delta.vertex_index < 0 or delta.vertex_index >= len(
                    mesh.vertices
                ):
                    raise ValueError(
                        f"Shapekey {shape.name} has invalid vertex index {delta.vertex_index} for mesh {mesh_idx}"
                    )


def validate_binary_model(binary_model: MdlBinaryModel) -> None:
    if binary_model.header.lod_count < 1:
        raise ValueError("Binary model has no active LOD")

    # MeshHeader count fields are serialized as uint16 and must stay in range.
    uint16_fields = {
        "mesh_count": binary_model.mesh_header.mesh_count,
        "attribute_count": binary_model.mesh_header.attribute_count,
        "submesh_count": binary_model.mesh_header.submesh_count,
        "material_count": binary_model.mesh_header.material_count,
        "bone_count": binary_model.mesh_header.bone_count,
        "bone_table_count": binary_model.mesh_header.bone_table_count,
        "shape_count": binary_model.mesh_header.shape_count,
        "shape_mesh_count": binary_model.mesh_header.shape_mesh_count,
        "shape_value_count": binary_model.mesh_header.shape_value_count,
        "bone_table_array_count_total": binary_model.mesh_header.bone_table_array_count_total,
    }
    for field_name, field_value in uint16_fields.items():
        if field_value < 0 or field_value > 0xFFFF:
            raise ValueError(
                f"Mesh header field {field_name}={field_value} exceeds uint16 range"
            )

    if binary_model.mesh_header.mesh_count != len(binary_model.meshes):
        raise ValueError(
            "Mesh header mesh_count does not match mesh array length"
        )
    if binary_model.mesh_header.submesh_count != len(binary_model.submeshes):
        raise ValueError(
            "Mesh header submesh_count does not match submesh array length"
        )
    if binary_model.mesh_header.material_count != len(binary_model.materials):
        raise ValueError(
            "Mesh header material_count does not match material array length"
        )
    if binary_model.mesh_header.bone_count != len(binary_model.bones):
        raise ValueError(
            "Mesh header bone_count does not match bone array length"
        )
    if binary_model.mesh_header.shape_count != len(binary_model.shapes):
        raise ValueError(
            "Mesh header shape_count does not match shape array length"
        )
    if binary_model.mesh_header.shape_mesh_count != len(
        binary_model.shape_meshes
    ):
        raise ValueError(
            "Mesh header shape_mesh_count does not match shape mesh array length"
        )
    if binary_model.mesh_header.shape_value_count != len(
        binary_model.shape_values
    ):
        raise ValueError(
            "Mesh header shape_value_count does not match shape value array length"
        )

    if binary_model.header.vert_buffer_size[
        0
    ] + binary_model.header.idx_buffer_size[0] > len(binary_model.buffers):
        raise ValueError("Binary model buffer sizes exceed payload size")
    valid_index_offsets = {m.start_idx for m in binary_model.meshes}
    mesh_by_start_idx = {m.start_idx: m for m in binary_model.meshes}

    for shape_idx, shape in enumerate(binary_model.shapes):
        start = shape.mesh_start_idx[0]
        count = shape.mesh_count[0]
        if start < 0 or count < 0:
            raise ValueError(f"Shape {shape_idx} has invalid mesh range")
        if start + count > len(binary_model.shape_meshes):
            raise ValueError(
                f"Shape {shape_idx} mesh range overflows shape mesh array"
            )

    for shape_mesh_idx, shape_mesh in enumerate(binary_model.shape_meshes):
        if shape_mesh.mesh_idx_offset < 0:
            raise ValueError(
                f"Shape mesh {shape_mesh_idx} has negative mesh index offset"
            )
        if (
            binary_model.meshes
            and shape_mesh.mesh_idx_offset not in valid_index_offsets
        ):
            raise ValueError(
                f"Shape mesh {shape_mesh_idx} index offset {shape_mesh.mesh_idx_offset} "
                f"does not match any mesh start_idx"
            )
        if shape_mesh.shape_value_offset < 0:
            raise ValueError(
                f"Shape mesh {shape_mesh_idx} has negative shape value offset"
            )
        if shape_mesh.shape_value_count < 0:
            raise ValueError(
                f"Shape mesh {shape_mesh_idx} has negative shape value count"
            )

        shape_end = shape_mesh.shape_value_offset + shape_mesh.shape_value_count
        if shape_end > len(binary_model.shape_values):
            raise ValueError(
                f"Shape mesh {shape_mesh_idx} overflows shape value array"
            )

        mesh = mesh_by_start_idx.get(shape_mesh.mesh_idx_offset)
        if mesh is None:
            continue

        for value_idx in range(shape_mesh.shape_value_offset, shape_end):
            value = binary_model.shape_values[value_idx]
            if value.base_indices_idx >= mesh.idx_count:
                raise ValueError(
                    f"Shape mesh {shape_mesh_idx} base index position {value.base_indices_idx} "
                    f"out of bounds for mesh idx_count {mesh.idx_count}"
                )
            if value.replace_vert_idx >= mesh.vertex_count:
                raise ValueError(
                    f"Shape mesh {shape_mesh_idx} replacement vertex {value.replace_vert_idx} "
                    f"out of bounds for mesh vertex_count {mesh.vertex_count}"
                )

    for shape_value_idx, shape_value in enumerate(binary_model.shape_values):
        if (
            shape_value.base_indices_idx < 0
            or shape_value.base_indices_idx > 0xFFFF
        ):
            raise ValueError(
                f"Shape value {shape_value_idx} base vertex index out of uint16 range"
            )
        if (
            shape_value.replace_vert_idx < 0
            or shape_value.replace_vert_idx > 0xFFFF
        ):
            raise ValueError(
                f"Shape value {shape_value_idx} replacement vertex index out of uint16 range"
            )

    for mesh_idx, mesh in enumerate(binary_model.meshes):
        if not binary_model.vertex_declarations:
            raise ValueError("Binary model has no vertex declaration")

        if mesh.submesh_index < 0 or mesh.submesh_count < 0:
            raise ValueError(
                f"Binary mesh {mesh_idx} has invalid submesh range"
            )
        submesh_end = mesh.submesh_index + mesh.submesh_count
        if submesh_end > len(binary_model.submeshes):
            raise ValueError(
                f"Binary mesh {mesh_idx} submesh range overflows submesh array"
            )

        mesh_bone_count = 0
        if 0 <= mesh.bone_table_idx < len(binary_model.bone_tables):
            mesh_bone_count = len(
                binary_model.bone_tables[mesh.bone_table_idx].bone_idx
            )

        for submesh_idx in range(mesh.submesh_index, submesh_end):
            submesh = binary_model.submeshes[submesh_idx]
            if submesh.bone_start_idx < 0 or submesh.bone_count < 0:
                raise ValueError(
                    f"Binary submesh {submesh_idx} has invalid bone range"
                )

            bone_end = submesh.bone_start_idx + submesh.bone_count
            if bone_end > len(binary_model.submesh_bonemaps):
                raise ValueError(
                    f"Binary submesh {submesh_idx} bone range overflows submesh bonemap array"
                )

            if mesh_bone_count > 0:
                for local_bone_idx in binary_model.submesh_bonemaps[
                    submesh.bone_start_idx : bone_end
                ]:
                    if local_bone_idx < 0 or local_bone_idx >= mesh_bone_count:
                        raise ValueError(
                            f"Binary submesh {submesh_idx} references invalid local bone index {local_bone_idx} "
                            f"for mesh {mesh_idx} bone table size {mesh_bone_count}"
                        )

        decl_idx = (
            mesh_idx if mesh_idx < len(binary_model.vertex_declarations) else 0
        )
        declaration = binary_model.vertex_declarations[decl_idx]

        skinning_weights = 4
        for element in declaration.vertex_elements:
            if element.usage != int(VertexUsage.BLEND_WEIGHTS):
                continue
            if element.type not in (
                int(VertexType.UBYTE4),
                int(VertexType.USHORT4),
            ):
                raise ValueError(
                    f"Binary mesh {mesh_idx} uses unsupported blend weight type {element.type}"
                )
            skinning_weights = (
                8 if element.type == int(VertexType.USHORT4) else 4
            )
            break

        required_stride = vertex_stride(skinning_weights)
        if mesh.vertex_buffer_stride[0] <= 0:
            raise ValueError(
                f"Binary mesh {mesh_idx} has invalid vertex stride"
            )
        if mesh.vertex_buffer_stride[0] < required_stride:
            raise ValueError(
                f"Binary mesh {mesh_idx} has stride {mesh.vertex_buffer_stride[0]} but requires at least {required_stride}"
            )

        vb_end = (
            mesh.vertex_buffer_offset[0]
            + mesh.vertex_count * mesh.vertex_buffer_stride[0]
        )
        if vb_end > binary_model.header.vert_buffer_size[0]:
            raise ValueError(
                f"Binary mesh {mesh_idx} vertex payload overflows vertex buffer"
            )

        ib_end = mesh.start_idx * 2 + mesh.idx_count * 2
        if ib_end > binary_model.header.idx_buffer_size[0]:
            raise ValueError(
                f"Binary mesh {mesh_idx} index payload overflows index buffer"
            )

        if mesh.bone_table_idx < 0 or mesh.bone_table_idx >= len(
            binary_model.bone_tables
        ):
            raise ValueError(
                f"Binary mesh {mesh_idx} has invalid bone table index"
            )
