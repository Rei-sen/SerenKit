from types import SimpleNamespace, Any
from pytest import Monkeypatch

from ..shared import export_context as ec


def make_obj_with_modkit(attrs: Any = None) -> SimpleNamespace:
    o = SimpleNamespace()
    if attrs:

        class C:
            pass

        c = C()
        c.attributes = [SimpleNamespace(value=v) for v in attrs]
        o.modkit = c
    else:
        o.modkit = None
    return o


def test_validate_export_readiness_and_context(
    monkeypatch: Monkeypatch,
) -> None:
    from ..shared import export_context as ec

    # fake collection
    collection = SimpleNamespace(name="C1")

    # Case: missing model
    monkeypatch.setattr(ec, "get_modkit_collection_props", lambda c: None)
    ok, msg = ec.validate_export_readiness(collection)
    assert ok is False

    # Proper model
    model = SimpleNamespace(
        export_enabled=True, game_path="/g", assigned_profile="P"
    )
    monkeypatch.setattr(
        ec,
        "get_modkit_collection_props",
        lambda c: SimpleNamespace(model=model),
    )

    # profile exists
    monkeypatch.setattr(ec, "is_profile_loaded", lambda name: True)

    ok2, msg2 = ec.validate_export_readiness(collection)
    assert ok2 is True and msg2 is None

    # Test CollectionExportInfo properties
    p = ec.Profile(profile_name="P", groups=[])
    monkeypatch.setattr(ec, "get_profile_data", lambda name: p)
    monkeypatch.setattr(ec, "collect_collection_shapekeys", lambda col: {"sk1"})
    monkeypatch.setattr(ec, "filter_profile_shapekeys", lambda sk, prof: [])
    monkeypatch.setattr(
        ec, "generate_variant_combinations", lambda g, inc: [["a"], ["b"]]
    )

    # scanned meshes
    monkeypatch.setattr(
        ec,
        "ModelScanner",
        SimpleNamespace(
            scan_collection=lambda c: {
                1: [(make_obj_with_modkit(["x"]), "name", 0)]
            }
        ),
    )

    # material info via model meshes and collection props
    mesh = SimpleNamespace(id=1, material_name="mat")
    monkeypatch.setattr(
        ec,
        "get_modkit_collection_props",
        lambda c: SimpleNamespace(
            model=SimpleNamespace(
                meshes=[mesh],
                assigned_profile="P",
                game_path="gp",
                mannequin_object=None,
            )
        ),
    )

    ctx = ec.CollectionExportInfo(collection)

    assert ctx.profile_name == "P"
    assert ctx.variants and len(ctx.variants) == 2
    assert ctx.materials_info == {1: "mat"}
    assert ctx.part_attrs == {(1, 0): ["x"]}
