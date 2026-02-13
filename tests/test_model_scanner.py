from types import SimpleNamespace

from ..shared.model_scanner import ModelScanner, NAME_RE, PartNameInfo
from .helpers import Object, Collection


def test_parse_part_name_valid_and_invalid():
    valid = "BaseName 1.2"
    info = ModelScanner._parse_part_name(valid)
    assert isinstance(info, PartNameInfo)
    assert info.base_name == "BaseName"
    assert info.mesh_index == 1
    assert info.part_index == 2

    assert ModelScanner._parse_part_name("NoMatch") is None


def test_scan_collection_groups_by_mesh_index():
    # create objects with matching names and some non-mesh objects
    o1 = Object(type="MESH")
    o1.name = "Thing 0.1"
    o2 = Object(type="MESH")
    o2.name = "Thing 0.2"
    o3 = Object(type="MESH")
    o3.name = "Other 1.0"
    o4 = Object(type="EMPTY")
    o4.name = "Ignore"

    col = Collection(all_objects=[o1, o2, o3, o4], objects=[o1, o2, o3, o4])

    meshes = ModelScanner.scan_collection(col)
    assert 0 in meshes and 1 in meshes
    assert len(meshes[0]) == 2
    assert len(meshes[1]) == 1
    # check tuple contents
    obj, base, part = meshes[0][0]
    assert hasattr(obj, "name") and isinstance(
        base, str) and isinstance(part, int)
