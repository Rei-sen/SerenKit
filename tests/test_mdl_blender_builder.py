from shared.mdl.blender_builder import (
    _build_baked_base_positions,
    _collect_object_shapekeys,
    _is_export_shapekey_name,
)
from shared.mdl.structures import MdlMesh, MdlModel, MdlSubmesh, MdlVertex


class _Vec:
    def __init__(self, x: float, y: float, z: float) -> None:
        self.x = x
        self.y = y
        self.z = z


class _Point:
    def __init__(self, co: _Vec) -> None:
        self.co = co


class _KeyBlock:
    def __init__(
        self,
        name: str,
        coords: list[tuple[float, float, float]],
        value: float = 0.0,
        mute: bool = False,
    ) -> None:
        self.name = name
        self.value = value
        self.mute = mute
        self.data = [_Point(_Vec(*co)) for co in coords]


class _ShapeKeys:
    def __init__(self, key_blocks: list[_KeyBlock]) -> None:
        self.key_blocks = key_blocks


class _MeshData:
    def __init__(self, shape_keys: _ShapeKeys) -> None:
        self.shape_keys = shape_keys


class _Obj:
    def __init__(self, shape_keys: _ShapeKeys) -> None:
        self.data = _MeshData(shape_keys)


def test_export_shapekey_prefix_filter() -> None:
    assert _is_export_shapekey_name("shp_smile")
    assert _is_export_shapekey_name("SHP_X_test")
    assert not _is_export_shapekey_name("Smile")


def test_bake_base_positions_applies_only_non_export_keys() -> None:
    basis = _KeyBlock("Basis", [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0)])
    regular = _KeyBlock(
        "jaw_open",
        [(0.2, 0.0, 0.0), (1.2, 0.0, 0.0)],
        value=0.5,
        mute=False,
    )
    export_key = _KeyBlock(
        "shp_smile",
        [(0.8, 0.0, 0.0), (1.8, 0.0, 0.0)],
        value=1.0,
        mute=False,
    )
    muted_regular = _KeyBlock(
        "brow_raise",
        [(0.5, 0.0, 0.0), (1.5, 0.0, 0.0)],
        value=1.0,
        mute=True,
    )

    mesh_data = _MeshData(
        _ShapeKeys([basis, regular, export_key, muted_regular])
    )
    baked = _build_baked_base_positions(mesh_data)

    assert baked is not None
    assert baked[0] == (0.1, 0.0, 0.0)
    assert baked[1] == (1.1, 0.0, 0.0)


def test_collect_object_shapekeys_only_collects_export_prefixed() -> None:
    basis = _KeyBlock("Basis", [(0.0, 0.0, 0.0)])
    export_key = _KeyBlock("shp_smile", [(1.0, 0.0, 0.0)])
    regular = _KeyBlock("jaw_open", [(0.5, 0.0, 0.0)])
    obj = _Obj(_ShapeKeys([basis, export_key, regular]))

    model = MdlModel(
        lod_meshes=[
            [
                MdlMesh(
                    name="mesh",
                    material_path="",
                    vertices=[
                        MdlVertex(
                            position=(0.0, 0.0, 0.0),
                            normal=(0.0, 0.0, 1.0),
                            source_vertex_index=0,
                        )
                    ],
                    indices=[0],
                    submeshes=[MdlSubmesh(start_index=0, index_count=1)],
                )
            ]
        ]
    )

    _collect_object_shapekeys(obj, [0], model)

    assert len(model.shapekeys) == 1
    assert model.shapekeys[0].name == "shp_smile"
