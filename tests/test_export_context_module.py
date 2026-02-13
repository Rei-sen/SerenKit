from types import SimpleNamespace


def make_obj_with_modkit(attrs=None):
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


def test_validate_export_readiness_and_context(monkeypatch):
    from ..shared import export_context as ec

    # fake collection
    collection = SimpleNamespace(name='C1')

    # Case: missing model
    monkeypatch.setattr(ec, 'get_modkit_collection_props', lambda c: None)
    ok, msg = ec.validate_export_readiness(collection)
    assert ok is False

    # Proper model
    model = SimpleNamespace(export_enabled=True,
                            game_path='/g', assigned_profile='P')
    monkeypatch.setattr(ec, 'get_modkit_collection_props',
                        lambda c: SimpleNamespace(model=model))

    # profile exists
    monkeypatch.setattr(ec, 'get_profile_data', lambda name: {'dummy': True})

    ok2, msg2 = ec.validate_export_readiness(collection)
    assert ok2 is True and msg2 is None

    # Test CollectionExportContext caching and properties
    ctx = ec.CollectionExportContext(collection, 'P')

    # monkeypatch profile data getter
    monkeypatch.setattr(ec, 'get_profile_data', lambda name: {'profile': True})

    # shapekeys -> support_map
    monkeypatch.setattr(ec, 'collect_collection_shapekeys',
                        lambda col: ['sk1'])
    monkeypatch.setattr(
        ec, 'summarize_variant_support_from_profile', lambda sk, p: ['group'])
    monkeypatch.setattr(ec, 'generate_variant_combinations',
                        lambda g: [['a'], ['b']])

    # scanned meshes
    monkeypatch.setattr(ec, 'ModelScanner', SimpleNamespace(
        scan_collection=lambda c: {1: [(make_obj_with_modkit(['x']), 'name', 0)]}))

    # material info via model meshes
    mesh = SimpleNamespace(id=1, material_name='mat')
    monkeypatch.setattr(ec, 'get_modkit_collection_props', lambda c: SimpleNamespace(
        model=SimpleNamespace(meshes=[mesh])))

    # access properties
    assert ctx.profile_data
    assert ctx.support_map
    assert ctx.variants and len(ctx.variants) == 2
    assert ctx.scanned_meshes and 1 in ctx.scanned_meshes
    assert ctx.material_info == {1: 'mat'}
    assert ctx.part_attrs == {(1, 0): ['x']}

    # total/count and clear
    assert ctx.total_variants == ctx.count_variants()
    ctx.clear()
    # after clear, cached attrs should be reset (accessing again regenerates)
    assert ctx._profile_data is None
