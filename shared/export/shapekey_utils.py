from dataclasses import dataclass
from typing import Iterable

from bpy.types import Mesh, Object, Collection

from ..profile import Profile


@dataclass
class ShapeKeyState:
    value: float
    mute: bool


def apply_variant_shapekeys(
    mesh: Mesh, profile: Profile, shapekeys: set[str]
) -> None:
    """Apply shape keys for a given variant on a mesh object."""

    profile_shapekeys = profile.get_shapekey_names()

    sk = mesh.shape_keys

    if not sk:
        return

    for key_name in profile_shapekeys:
        if key_name in sk.key_blocks:
            if key_name in shapekeys:
                sk.key_blocks[key_name].value = 1.0
                sk.key_blocks[key_name].mute = False
            else:
                sk.key_blocks[key_name].value = 0.0
                sk.key_blocks[key_name].mute = True


def apply_variant_shapekeys_to_objects(
    objects: Iterable[Object], profile: Profile, shapekeys: set[str]
) -> None:
    """Apply variant shape-key states to a set of objects."""
    for obj in objects:
        if not isinstance(obj.data, Mesh):
            continue

        apply_variant_shapekeys(obj.data, profile, shapekeys)


def save_shapekey_config(mesh: Object) -> dict[str, ShapeKeyState]:
    """Save the shape key configuration of a mesh object."""
    if not isinstance(mesh.data, Mesh):
        return {}
    sk = mesh.data.shape_keys
    if not sk:
        return {}

    config = dict[str, ShapeKeyState]()
    for kb in sk.key_blocks:
        config[kb.name] = ShapeKeyState(value=kb.value, mute=kb.mute)
    return config


def restore_shapekey_config(
    mesh: Object, config: dict[str, ShapeKeyState]
) -> None:
    """Restore a mesh object's shape-key configuration."""
    if not isinstance(mesh.data, Mesh):
        return

    sk = mesh.data.shape_keys
    if not sk:
        return

    for kb in sk.key_blocks:
        if kb.name in config:
            state = config[kb.name]
            kb.value = state.value
            kb.mute = state.mute




def collect_objects_shapekeys(objects: Iterable[Object]) -> set[str]:
    """Collect shape key names from a set of mesh objects."""
    existing_keys: set[str] = set()
    for obj in objects:
        data = getattr(obj, "data", None)
        if not isinstance(data, Mesh):
            continue

        obj_keys = collect_object_shapekeys(data)
        existing_keys.update(obj_keys)

    return existing_keys


def collect_object_shapekeys(mesh: Mesh) -> set[str]:
    """Collect shape key names from a mesh object."""
    existing_keys: set[str] = set()

    sk = mesh.shape_keys
    if not sk:
        return existing_keys

    for kb in sk.key_blocks:
        existing_keys.add(kb.name)

    return existing_keys


def collection_shapekeys(collection: Collection) -> set[str]:
    """Collect shape key names from all mesh objects in a collection."""
    return collect_objects_shapekeys(collection.objects)

