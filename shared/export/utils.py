
from typing import Optional

import bpy
from bpy.types import Object, Collection

from ...properties.object_settings import get_modkit_object_props

from ..logging import log_warning
from ...properties.model_settings import get_modkit_collection_props


def collect_enabled_collections() -> set[Collection]:
    """Collect collections that are enabled for export based on their properties.
    """
    cols: set[Collection] = set()
    for col in bpy.data.collections:
        col_props = get_modkit_collection_props(col)
        model = col_props.model if col_props else None
        if not model or not model.is_enabled or not model.export_enabled:
            continue

        cols.add(col)

    return cols


def get_export_armature(collection: Collection) -> Optional[Object]:
    """Get the export armature for a collection if set and valid.
    """
    col_props = get_modkit_collection_props(collection)
    model = col_props.model if col_props else None
    arm = model.export_armature if model else None
    if arm and arm.type == 'ARMATURE':
        return arm
    return None


def adjust_modifier_object_references(
    copied_objects: dict[Object, Object]
) -> None:
    """Remap object-pointer properties on modifiers to their duplicated targets.
    """

    for copy in copied_objects.values():
        for mod in copy.modifiers:
            try:
                for prop in mod.bl_rna.properties:
                    if prop.type != 'POINTER':
                        continue

                    fixed_type = getattr(prop, 'fixed_type', None)
                    if getattr(fixed_type, 'name', None) != 'Object':
                        continue

                    ident = prop.identifier
                    try:
                        target_obj = getattr(mod, ident)
                    except Exception as e:
                        log_warning(
                            f"adjust_modifier_object_references: could not get {ident} on modifier {mod.name}: {e}")
                        target_obj = None

                    replacement = None
                    if target_obj:
                        replacement = copied_objects.get(target_obj, None)

                    if replacement:
                        try:
                            setattr(mod, ident, replacement)
                        except Exception as e:
                            log_warning(
                                f"adjust_modifier_object_references: failed to set {ident} on {copy.name} modifier {mod.name}: {e}")
            except Exception as e:
                log_warning(
                    f"adjust_modifier_object_references: skipping modifier {getattr(mod, 'name', '<unknown>')} due to RNA access error: {e}")
                continue


def duplicate_collection(source_collection: Collection) -> Collection:
    """Duplicate a collection and its mesh objects for export, linking an armature if set.
    """
    scene = bpy.context.scene

    if scene is None:
        raise RuntimeError(
            "duplicate_collection: no active scene to link export collection to")

    dup = bpy.data.collections.new(name=f"{source_collection.name}__EXPORT")
    scene.collection.children.link(dup)

    dup_props = get_modkit_collection_props(dup)
    src_props = get_modkit_collection_props(source_collection)
    if dup_props and src_props:
        dup_props.model.copy_from(src_props.model)

    arm = get_export_armature(source_collection)
    if arm:
        dup.objects.link(arm)

    copied_objects: dict[Object, Object] = {}
    for obj in source_collection.objects:
        if obj.type != "MESH":
            continue
        obj_copy = _duplicate_mesh_for_export(obj, arm)
        copied_objects[obj] = obj_copy
        dup.objects.link(obj_copy)

    adjust_modifier_object_references(copied_objects)

    return dup


def _set_armature_for_object(obj: Object, arm: Object) -> None:
    """Set the armature modifier on `obj` to reference `arm`, creating one if needed."""

    if arm.type != 'ARMATURE':
        log_warning(
            f"_set_armature_for_object: provided arm {arm.name} is not of type ARMATURE")
        return

    obj.parent = arm
    if not any(m.type == 'ARMATURE' for m in obj.modifiers):
        mod = obj.modifiers.new(name="Armature", type='ARMATURE')
        setattr(mod, "object", arm)
    else:
        for mod in obj.modifiers:
            if mod.type == 'ARMATURE':
                setattr(mod, "object", arm)
                return


def _duplicate_mesh_for_export(obj: Object, arm: Optional[Object]) -> Object:
    """Duplicate a mesh object for export, copying Modkit properties and linking to `arm` if provided.
    """
    orig_modkit = get_modkit_object_props(obj)
    if not orig_modkit:
        raise RuntimeError(
            "_duplicate_mesh_for_export: source object missing 'modkit' property group")
    obj_copy = obj.copy()
    copy_modkit = get_modkit_object_props(obj_copy)
    if not copy_modkit:
        raise RuntimeError(
            "_duplicate_mesh_for_export: duplicated object missing 'modkit' property group")
    copy_modkit.props.copy_from(orig_modkit.props)
    obj_copy.data = obj.data.copy() if obj.data else None
    obj_copy.name = f"export_{obj.name}"

    if arm:
        _set_armature_for_object(obj_copy, arm)

    return obj_copy


def cleanup_duplicate_collection(dup_col: Collection) -> None:
    """Remove the duplicated collection and its objects after export.
    """

    for obj in list(dup_col.objects):
        if obj.type != 'ARMATURE':
            bpy.data.objects.remove(obj, do_unlink=True)

    scene = bpy.context.scene
    if scene:
        scene.collection.children.unlink(dup_col)
    bpy.data.collections.remove(dup_col)


def select_objects_for_export(objects: list[Object]) -> None:
    """Select the given objects in the viewport, making the first one active.
    """

    bpy.ops.object.select_all(action='DESELECT')

    if not objects:
        return

    for o in objects:
        o.select_set(True)

    view_layer = bpy.context.view_layer
    if view_layer:
        view_layer.objects.active = objects[0]
