from shared.mdl.parser import from_bytes
from shared.mdl.checks import validate_binary_model, validate_model
from shared.mdl.binary import (
    Mesh,
    MdlBinaryModel,
    ShapeMesh,
    VertexDeclaration,
    VertexType,
    VertexUsage,
)
from shared.mdl.structures import (
    MdlMesh,
    MdlModel,
    MdlShapeDelta,
    MdlShapeKey,
    MdlSubmesh,
    MdlVertex,
)
from shared.mdl.writer import model_to_bytes
from xivpy.model import XIVModel


def test_model_to_bytes_creates_binary() -> None:
    model = MdlModel(
        lod_meshes=[
            [
                MdlMesh(
                    name="body",
                    material_path="mt_test",
                    material_name="mt_test",
                    vertices=[
                        MdlVertex(
                            (0.0, 0.0, 0.0),
                            (0.0, 0.0, 1.0),
                            (0.0, 0.0),
                            (0, 1, 0, 0, 0, 0, 0, 0),
                            (0.7, 0.3, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
                        ),
                        MdlVertex(
                            (1.0, 0.0, 0.0),
                            (0.0, 0.0, 1.0),
                            (1.0, 0.0),
                            (1, 0, 0, 0, 0, 0, 0, 0),
                            (1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
                        ),
                        MdlVertex(
                            (0.0, 1.0, 0.0),
                            (0.0, 0.0, 1.0),
                            (0.0, 1.0),
                            (0, 0, 0, 0, 0, 0, 0, 0),
                            (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
                        ),
                    ],
                    indices=[0, 1, 2],
                    submeshes=[MdlSubmesh(start_index=0, index_count=3)],
                )
            ]
        ],
        materials=["mt_test"],
        bones=["root", "spine"],
        shapekeys=[
            MdlShapeKey(
                name="Smile",
                mesh_deltas={
                    0: [MdlShapeDelta(vertex_index=1, delta=(0.1, 0.0, 0.0))]
                },
            )
        ],
    )

    payload = model_to_bytes(model)

    assert isinstance(payload, bytes)
    assert len(payload) > 64


def test_parser_reads_basic_mesh_metadata() -> None:
    model = MdlModel(
        lod_meshes=[
            [
                MdlMesh(
                    name="body",
                    material_path="mt_test",
                    material_name="mt_test",
                    vertices=[
                        MdlVertex(
                            (0.0, 0.0, 0.0),
                            (0.0, 0.0, 1.0),
                            (0.0, 0.0),
                            (0, 1, 0, 0, 0, 0, 0, 0),
                            (0.7, 0.3, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
                        ),
                        MdlVertex(
                            (1.0, 0.0, 0.0),
                            (0.0, 0.0, 1.0),
                            (1.0, 0.0),
                            (1, 0, 0, 0, 0, 0, 0, 0),
                            (1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
                        ),
                        MdlVertex(
                            (0.0, 1.0, 0.0),
                            (0.0, 0.0, 1.0),
                            (0.0, 1.0),
                            (0, 0, 0, 0, 0, 0, 0, 0),
                            (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
                        ),
                    ],
                    indices=[0, 1, 2],
                    submeshes=[MdlSubmesh(start_index=0, index_count=3)],
                )
            ]
        ],
        materials=["mt_test"],
        bones=["root", "spine"],
        shapekeys=[
            MdlShapeKey(
                name="Smile",
                mesh_deltas={
                    0: [MdlShapeDelta(vertex_index=1, delta=(0.1, 0.0, 0.0))]
                },
            )
        ],
    )

    payload = model_to_bytes(model)
    parsed = from_bytes(payload)

    assert len(parsed.lod_meshes) == 1
    assert len(parsed.lod_meshes[0]) == 1
    assert parsed.materials == ["mt_test"]
    assert parsed.bones == ["root", "spine"]
    assert parsed.lod_meshes[0][0].submeshes[0].index_count == 3
    assert parsed.shapekeys
    assert parsed.shapekeys[0].name == "Smile"
    assert 0 in parsed.shapekeys[0].mesh_deltas
    parsed_delta = parsed.shapekeys[0].mesh_deltas[0][0].delta
    assert parsed_delta[0] > 0.09
    assert abs(parsed_delta[1]) < 1e-6
    assert abs(parsed_delta[2]) < 1e-6


def test_validate_model_rejects_invalid_indices() -> None:
    model = MdlModel(
        lod_meshes=[
            [
                MdlMesh(
                    name="bad",
                    material_path="",
                    vertices=[MdlVertex((0.0, 0.0, 0.0), (0.0, 0.0, 1.0))],
                    indices=[0, 1, 2],
                    submeshes=[MdlSubmesh(start_index=0, index_count=3)],
                )
            ]
        ]
    )

    failed = False
    try:
        validate_model(model)
    except ValueError:
        failed = True

    assert failed


def test_eight_weight_skinning_uses_ushort4_and_roundtrips() -> None:
    model = MdlModel(
        lod_meshes=[
            [
                MdlMesh(
                    name="weighted",
                    material_path="mt_test",
                    material_name="mt_test",
                    vertices=[
                        MdlVertex(
                            (0.0, 0.0, 0.0),
                            (0.0, 0.0, 1.0),
                            (0.0, 0.0),
                            (0, 1, 2, 3, 4, 5, 6, 7),
                            (0.2, 0.18, 0.16, 0.14, 0.12, 0.1, 0.06, 0.04),
                        ),
                        MdlVertex(
                            (1.0, 0.0, 0.0),
                            (0.0, 0.0, 1.0),
                            (1.0, 0.0),
                            (0, 1, 2, 3, 4, 5, 6, 7),
                            (0.2, 0.18, 0.16, 0.14, 0.12, 0.1, 0.06, 0.04),
                        ),
                        MdlVertex(
                            (0.0, 1.0, 0.0),
                            (0.0, 0.0, 1.0),
                            (0.0, 1.0),
                            (0, 1, 2, 3, 4, 5, 6, 7),
                            (0.2, 0.18, 0.16, 0.14, 0.12, 0.1, 0.06, 0.04),
                        ),
                    ],
                    indices=[0, 1, 2],
                    submeshes=[MdlSubmesh(start_index=0, index_count=3)],
                )
            ]
        ],
        materials=["mt_test"],
        bones=["b0", "b1", "b2", "b3", "b4", "b5", "b6", "b7"],
    )

    payload = model_to_bytes(model)
    binary = MdlBinaryModel.from_bytes(payload)
    declaration = binary.vertex_declarations[0]

    blend_weight_elements = [
        element
        for element in declaration.vertex_elements
        if element.usage == int(VertexUsage.BLEND_WEIGHTS)
    ]
    assert blend_weight_elements
    assert blend_weight_elements[0].type == int(VertexType.USHORT4)

    parsed = from_bytes(payload)
    parsed_vertex = parsed.lod_meshes[0][0].vertices[0]
    assert parsed_vertex.bone_weights[4] > 0.0
    assert parsed_vertex.bone_indices[7] == 7


def test_validate_binary_model_rejects_shape_value_count_overflow() -> None:
    binary = MdlBinaryModel()
    binary.header.lod_count = 1
    binary.mesh_header.shape_value_count = 70000

    failed = False
    try:
        validate_binary_model(binary)
    except ValueError as exc:
        failed = "shape_value_count" in str(exc)

    assert failed


def test_validate_binary_model_rejects_shape_mesh_value_overflow() -> None:
    binary = MdlBinaryModel()
    binary.header.lod_count = 1
    decl = VertexDeclaration()
    decl.create_element(VertexType.SINGLE3, VertexUsage.POSITION, stream=0)
    decl.create_element(VertexType.SINGLE3, VertexUsage.NORMAL, stream=0)
    decl.create_element(VertexType.SINGLE2, VertexUsage.UV, stream=0)
    decl.create_element(VertexType.UBYTE4, VertexUsage.BLEND_INDICES, stream=0)
    decl.create_element(VertexType.UBYTE4, VertexUsage.BLEND_WEIGHTS, stream=0)
    binary.vertex_declarations = [decl]
    binary.meshes = [
        Mesh(
            vertex_count=0,
            idx_count=0,
            vertex_buffer_stride=[24, 0, 0],
            vertex_stream_count=1,
        )
    ]
    binary.mesh_header.mesh_count = len(binary.meshes)
    binary.mesh_header.shape_mesh_count = 1
    binary.mesh_header.shape_value_count = 0
    binary.shape_meshes = [
        ShapeMesh(mesh_idx_offset=0, shape_value_count=1, shape_value_offset=0)
    ]

    failed = False
    try:
        validate_binary_model(binary)
    except ValueError as exc:
        failed = "overflows shape value array" in str(exc)

    assert failed


def test_shape_values_use_index_buffer_positions() -> None:
    model = MdlModel(
        lod_meshes=[
            [
                MdlMesh(
                    name="body",
                    material_path="mt_test",
                    material_name="mt_test",
                    vertices=[
                        MdlVertex((0.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
                        MdlVertex((1.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
                        MdlVertex((1.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
                        MdlVertex((0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
                    ],
                    indices=[0, 1, 2, 0, 2, 3],
                    submeshes=[MdlSubmesh(start_index=0, index_count=6)],
                )
            ]
        ],
        materials=["mt_test"],
        bones=["root"],
        shapekeys=[
            MdlShapeKey(
                name="shp_test",
                mesh_deltas={
                    0: [MdlShapeDelta(vertex_index=0, delta=(0.1, 0.0, 0.0))]
                },
            )
        ],
    )

    payload = model_to_bytes(model)
    binary = MdlBinaryModel.from_bytes(payload)

    assert binary.shape_meshes
    shape_mesh = binary.shape_meshes[0]
    assert shape_mesh.mesh_idx_offset == binary.meshes[0].start_idx

    shape_values = binary.shape_values[
        shape_mesh.shape_value_offset : shape_mesh.shape_value_offset
        + shape_mesh.shape_value_count
    ]
    assert len(shape_values) == 2
    assert {value.base_indices_idx for value in shape_values} == {0, 3}


def test_submeshes_get_independent_bonemap_slices() -> None:
    model = MdlModel(
        lod_meshes=[
            [
                MdlMesh(
                    name="body",
                    material_path="mt_test",
                    material_name="mt_test",
                    vertices=[
                        MdlVertex(
                            (0.0, 0.0, 0.0),
                            (0.0, 0.0, 1.0),
                            bone_indices=(0, 1, 0, 0, 0, 0, 0, 0),
                            bone_weights=(
                                0.8,
                                0.2,
                                0.0,
                                0.0,
                                0.0,
                                0.0,
                                0.0,
                                0.0,
                            ),
                        ),
                        MdlVertex(
                            (1.0, 0.0, 0.0),
                            (0.0, 0.0, 1.0),
                            bone_indices=(0, 1, 0, 0, 0, 0, 0, 0),
                            bone_weights=(
                                0.7,
                                0.3,
                                0.0,
                                0.0,
                                0.0,
                                0.0,
                                0.0,
                                0.0,
                            ),
                        ),
                        MdlVertex(
                            (1.0, 1.0, 0.0),
                            (0.0, 0.0, 1.0),
                            bone_indices=(0, 1, 0, 0, 0, 0, 0, 0),
                            bone_weights=(
                                0.6,
                                0.4,
                                0.0,
                                0.0,
                                0.0,
                                0.0,
                                0.0,
                                0.0,
                            ),
                        ),
                        MdlVertex(
                            (0.0, 1.0, 0.0),
                            (0.0, 0.0, 1.0),
                            bone_indices=(0, 1, 0, 0, 0, 0, 0, 0),
                            bone_weights=(
                                0.5,
                                0.5,
                                0.0,
                                0.0,
                                0.0,
                                0.0,
                                0.0,
                                0.0,
                            ),
                        ),
                    ],
                    indices=[0, 1, 2, 0, 2, 3],
                    submeshes=[
                        MdlSubmesh(start_index=0, index_count=3),
                        MdlSubmesh(start_index=3, index_count=3),
                    ],
                )
            ]
        ],
        materials=["mt_test"],
        bones=["root", "spine"],
    )

    binary = MdlBinaryModel.from_bytes(model_to_bytes(model))
    assert len(binary.submeshes) == 2
    assert len(binary.submesh_bonemaps) == 4
    assert binary.submeshes[0].bone_start_idx == 0
    assert binary.submeshes[0].bone_count == 2
    assert binary.submeshes[1].bone_start_idx == 2
    assert binary.submeshes[1].bone_count == 2


def test_submesh_offsets_are_global_in_binary_and_local_in_parser() -> None:
    model = MdlModel(
        lod_meshes=[
            [
                MdlMesh(
                    name="m0",
                    material_path="mt0",
                    vertices=[
                        MdlVertex((0.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
                        MdlVertex((1.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
                        MdlVertex((0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
                    ],
                    indices=[0, 1, 2],
                    submeshes=[MdlSubmesh(start_index=0, index_count=3)],
                ),
                MdlMesh(
                    name="m1",
                    material_path="mt1",
                    vertices=[
                        MdlVertex((0.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
                        MdlVertex((1.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
                        MdlVertex((0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
                    ],
                    indices=[0, 1, 2],
                    submeshes=[MdlSubmesh(start_index=0, index_count=3)],
                ),
            ]
        ],
        materials=["mt0", "mt1"],
        bones=["root"],
    )

    payload = model_to_bytes(model)
    binary = MdlBinaryModel.from_bytes(payload)
    assert len(binary.meshes) == 2
    assert len(binary.submeshes) == 2
    assert binary.submeshes[0].idx_offset == binary.meshes[0].start_idx
    assert binary.submeshes[1].idx_offset == binary.meshes[1].start_idx

    parsed = from_bytes(payload)
    assert parsed.lod_meshes[0][0].submeshes[0].start_index == 0
    assert parsed.lod_meshes[0][1].submeshes[0].start_index == 0


def test_header_enables_index_buffer_streaming() -> None:
    model = MdlModel(
        lod_meshes=[
            [
                MdlMesh(
                    name="body",
                    material_path="mt_test",
                    vertices=[
                        MdlVertex((0.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
                        MdlVertex((1.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
                        MdlVertex((0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
                    ],
                    indices=[0, 1, 2],
                    submeshes=[MdlSubmesh(start_index=0, index_count=3)],
                )
            ]
        ],
        materials=["mt_test"],
        bones=["root"],
    )

    binary = MdlBinaryModel.from_bytes(model_to_bytes(model))
    assert binary.header.enable_idx_buffer_stream


def test_export_parses_with_xivpy_and_matches_textools_index_invariants() -> (
    None
):
    model = MdlModel(
        lod_meshes=[
            [
                MdlMesh(
                    name="body_a",
                    material_path="mt_a",
                    vertices=[
                        MdlVertex(
                            (0.0, 0.0, 0.0),
                            (0.0, 0.0, 1.0),
                            bone_indices=(0, 1, 0, 0, 0, 0, 0, 0),
                            bone_weights=(
                                0.7,
                                0.3,
                                0.0,
                                0.0,
                                0.0,
                                0.0,
                                0.0,
                                0.0,
                            ),
                        ),
                        MdlVertex(
                            (1.0, 0.0, 0.0),
                            (0.0, 0.0, 1.0),
                            bone_indices=(0, 1, 0, 0, 0, 0, 0, 0),
                            bone_weights=(
                                0.6,
                                0.4,
                                0.0,
                                0.0,
                                0.0,
                                0.0,
                                0.0,
                                0.0,
                            ),
                        ),
                        MdlVertex(
                            (1.0, 1.0, 0.0),
                            (0.0, 0.0, 1.0),
                            bone_indices=(0, 1, 0, 0, 0, 0, 0, 0),
                            bone_weights=(
                                0.8,
                                0.2,
                                0.0,
                                0.0,
                                0.0,
                                0.0,
                                0.0,
                                0.0,
                            ),
                        ),
                        MdlVertex(
                            (0.0, 1.0, 0.0),
                            (0.0, 0.0, 1.0),
                            bone_indices=(0, 1, 0, 0, 0, 0, 0, 0),
                            bone_weights=(
                                0.5,
                                0.5,
                                0.0,
                                0.0,
                                0.0,
                                0.0,
                                0.0,
                                0.0,
                            ),
                        ),
                    ],
                    indices=[0, 1, 2, 0, 2, 3],
                    submeshes=[
                        MdlSubmesh(start_index=0, index_count=3),
                        MdlSubmesh(start_index=3, index_count=3),
                    ],
                ),
                MdlMesh(
                    name="body_b",
                    material_path="mt_b",
                    vertices=[
                        MdlVertex(
                            (0.0, 0.0, 1.0),
                            (0.0, 0.0, 1.0),
                            bone_indices=(1, 2, 0, 0, 0, 0, 0, 0),
                            bone_weights=(
                                0.7,
                                0.3,
                                0.0,
                                0.0,
                                0.0,
                                0.0,
                                0.0,
                                0.0,
                            ),
                        ),
                        MdlVertex(
                            (1.0, 0.0, 1.0),
                            (0.0, 0.0, 1.0),
                            bone_indices=(1, 2, 0, 0, 0, 0, 0, 0),
                            bone_weights=(
                                0.6,
                                0.4,
                                0.0,
                                0.0,
                                0.0,
                                0.0,
                                0.0,
                                0.0,
                            ),
                        ),
                        MdlVertex(
                            (0.0, 1.0, 1.0),
                            (0.0, 0.0, 1.0),
                            bone_indices=(1, 2, 0, 0, 0, 0, 0, 0),
                            bone_weights=(
                                0.8,
                                0.2,
                                0.0,
                                0.0,
                                0.0,
                                0.0,
                                0.0,
                                0.0,
                            ),
                        ),
                    ],
                    indices=[0, 1, 2],
                    submeshes=[MdlSubmesh(start_index=0, index_count=3)],
                ),
            ]
        ],
        materials=["mt_a", "mt_b"],
        bones=["root", "spine", "chest"],
        shapekeys=[
            MdlShapeKey(
                name="shpx_test",
                mesh_deltas={
                    0: [MdlShapeDelta(vertex_index=0, delta=(0.05, 0.0, 0.0))],
                    1: [MdlShapeDelta(vertex_index=1, delta=(0.0, 0.04, 0.0))],
                },
            )
        ],
    )

    payload = model_to_bytes(model)

    parsed = XIVModel.from_bytes(payload)
    assert parsed.mesh_header.mesh_count == len(parsed.meshes)
    assert parsed.mesh_header.submesh_count == len(parsed.submeshes)
    assert parsed.mesh_header.shape_mesh_count == len(parsed.shape_meshes)

    index_mesh_num = {mesh.start_idx: i for i, mesh in enumerate(parsed.meshes)}

    for shape in parsed.shapes:
        start = shape.mesh_start_idx[0]
        count = shape.mesh_count[0]
        for idx in range(start, start + count):
            shape_mesh = parsed.shape_meshes[idx]
            assert shape_mesh.mesh_idx_offset in index_mesh_num
            mesh_idx = index_mesh_num[shape_mesh.mesh_idx_offset]
            mesh = parsed.meshes[mesh_idx]

            value_start = shape_mesh.shape_value_offset
            value_end = value_start + shape_mesh.shape_value_count
            values = parsed.shape_values[value_start:value_end]
            for value in values:
                assert int(value["base_indices_idx"]) < mesh.idx_count
                assert int(value["replace_vert_idx"]) < mesh.vertex_count

    for mesh in parsed.meshes:
        bone_table = parsed.bone_tables[mesh.bone_table_idx].bone_idx
        for sub_idx in range(
            mesh.submesh_index, mesh.submesh_index + mesh.submesh_count
        ):
            submesh = parsed.submeshes[sub_idx]
            start = submesh.bone_start_idx
            end = start + submesh.bone_count
            local_bones = parsed.submesh_bonemaps[start:end]
            for local_idx in local_bones:
                assert local_idx < len(bone_table)
