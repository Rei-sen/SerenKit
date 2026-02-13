from types import SimpleNamespace

from ..shared.export import shapekey_utils as sku
from ..shared.profile import VariantProfile, VariantGroup
from .helpers import Mesh, KeyBlock, ShapeKeys


def make_mesh_with_keys(names):
    m = Mesh(id=1, material_name="mat")
    # Create key blocks that support iteration, membership and indexing.

    class KeyBlockMapping:
        def __init__(self, names):
            self._d = {}
            for n in names:
                kb = KeyBlock(n)
                kb.value = 0.0
                kb.mute = False
                self._d[n] = kb

        def __iter__(self):
            return iter(self._d.values())

        def __contains__(self, item):
            return item in self._d

        def __getitem__(self, key):
            return self._d[key]

    m.shape_keys = SimpleNamespace(key_blocks=KeyBlockMapping(names))
    return m


def test_collect_object_and_objects_and_collection_shapekeys():
    m1 = make_mesh_with_keys(["A", "B"])
    m2 = make_mesh_with_keys(["C"])

    # collect_object_shapekeys
    s1 = sku.collect_object_shapekeys(m1)
    assert s1 == {"A", "B"}

    # collect_objects_shapekeys with a set of objects
    class HObj(SimpleNamespace):
        def __hash__(self):
            return id(self)

    o1 = HObj(data=m1)
    o2 = HObj(data=m2)
    s2 = sku.collect_objects_shapekeys({o1, o2})
    assert s2 == {"A", "B", "C"}

    # collect_collection_shapekeys expects collection with .objects
    coll = SimpleNamespace(objects=[o1, o2])
    s3 = sku.collect_collection_shapekeys(coll)
    assert s3 == {"A", "B", "C"}


def test_save_and_restore_shapekey_config():
    m = make_mesh_with_keys(["X"])
    kb = m.shape_keys.key_blocks["X"]
    kb.value = 0.5
    kb.mute = True

    cfg = sku.save_shapekey_config(m)
    assert "X" in cfg
    state = cfg["X"]
    assert state.value == 0.5 and state.mute is True

    # change and restore
    kb.value = 0.0
    kb.mute = False
    sku.restore_shapekey_config(m, cfg)
    assert kb.value == 0.5 and kb.mute is True


def test_apply_variant_shapekeys_to_mesh_and_collection():
    # Prepare profile with shapekey names
    vg = VariantGroup(group_name="G", mode="exclusive",
                      shapekeys=[("A", "A"), ("B", "B")])
    vp = VariantProfile(profile_name="P", groups=[vg])

    m = make_mesh_with_keys(["A", "B"])
    # apply A active only
    sku.apply_variant_shapekeys(m, vp, {"A"})
    assert m.shape_keys.key_blocks["A"].value == 1.0
    assert m.shape_keys.key_blocks["A"].mute is False
    assert m.shape_keys.key_blocks["B"].value == 0.0
    assert m.shape_keys.key_blocks["B"].mute is True

    # apply to collection: use a fresh mesh instance so previous state
    # doesn't affect the result
    m_coll = make_mesh_with_keys(["A", "B"])
    o = SimpleNamespace(data=m_coll)
    # mannequin is Mesh instance placed on model.mannequin_object
    model = SimpleNamespace(mannequin_object=SimpleNamespace(data=m_coll))
    col = SimpleNamespace(objects=[o])
    col.modkit = SimpleNamespace(model=model)

    sku.apply_variant_shapekeys_to_collection(col, vp, {"B"})
    assert m_coll.shape_keys.key_blocks["A"].value == 0.0
    assert m_coll.shape_keys.key_blocks["B"].value == 1.0
