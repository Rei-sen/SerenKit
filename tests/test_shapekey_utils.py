from ..shared.export import shapekey_utils
from .helpers import (
    Mesh,
    ShapeKeys,
    KeyBlock,
    Collection as TestCollection,
    Object,
)


def test_collect_object_shapekeys():
    mesh = Mesh(1, "mat")
    mesh.shape_keys = ShapeKeys([KeyBlock("A"), KeyBlock("B")])

    names = shapekey_utils.collect_object_shapekeys(mesh)
    assert names == {"A", "B"}


def test_collect_objects_and_collection_shapekeys():
    mesh = Mesh(2, "mat2")
    mesh.shape_keys = ShapeKeys([KeyBlock("X")])

    # use the provided Object shim and attach the mesh as its `data`
    obj = Object(key_names=None)
    obj.data = mesh

    # ensure the module-local Mesh type matches our test Mesh class
    shapekey_utils.Mesh = Mesh

    coll = TestCollection(objects=[obj])

    names_objs = shapekey_utils.collect_objects_shapekeys([obj])
    assert names_objs == {"X"}

    names_coll = shapekey_utils.collection_shapekeys(coll)
    assert names_coll == {"X"}


def test_apply_and_save_restore_shapekeys():
    from ..shared.profile import Profile, Group

    # prepare mesh with key blocks and attach runtime `value`
    mesh = Mesh(3, "m")
    kb1 = KeyBlock("A")
    kb2 = KeyBlock("B")
    kb1.value = 0.0
    kb2.value = 0.0
    # create a key_blocks container that supports both iteration (for collectors)
    # and name-based lookup (for apply_variant_shapekeys)
    class KeyBlockMap:
        def __init__(self, blocks):
            self._map = {b.name: b for b in blocks}

        def __iter__(self):
            return iter(self._map.values())

        def __contains__(self, name):
            return name in self._map

        def __getitem__(self, name):
            return self._map[name]

        @property
        def key_blocks(self):
            return list(self._map.values())

    mesh.shape_keys = type("SK", (), {"key_blocks": KeyBlockMap([kb1, kb2])})()

    # ensure isinstance checks inside module pass
    shapekey_utils.Mesh = Mesh

    profile = Profile(
        profile_name="P",
        groups=[Group(group_name="G", shapekeys=[("A", "A"), ("B", "B")])],
    )

    # apply variant that selects only A
    shapekey_utils.apply_variant_shapekeys(mesh, profile, {"A"})

    # verify state: A enabled, B disabled
    # normalize to name->KeyBlock mapping for assertions
    kb_names = {kb.name: kb for kb in mesh.shape_keys.key_blocks}
    assert kb_names["A"].value == 1.0
    assert kb_names["A"].mute is False
    assert kb_names["B"].value == 0.0
    assert kb_names["B"].mute is True

    # save state and then change values (save expects an Object with `.data`)
    obj = Object(key_names=None)
    obj.data = mesh
    # `save_shapekey_config` accesses `mesh.shape_keys` on the passed object
    obj.shape_keys = mesh.shape_keys
    cfg = shapekey_utils.save_shapekey_config(obj)
    kb_names["A"].value = 0.0
    kb_names["A"].mute = True

    # restore and verify (restore expects the same Object)
    shapekey_utils.restore_shapekey_config(obj, cfg)
    assert kb_names["A"].value == 1.0
    assert kb_names["A"].mute is False
