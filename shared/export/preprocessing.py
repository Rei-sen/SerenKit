from typing import Any
import bpy
from bpy.types import Object
from contextlib import contextmanager

from ...properties.object_settings import get_modkit_object_props


from .utils import select_objects_for_export

from ..logging import log_debug, log_error, log_warning
from ..ui_helpers import call_operator_in_3d_viewport
from ..export_context import CollectionExportInfo

from ...properties.model_settings import get_modkit_collection_props


@contextmanager
def _preserve_view_context():
    """Context manager to preserve the current view context, including mode,
    active object, and selection, restoring them upon exit.
    """
    prev_mode = bpy.context.mode
    view_layer = bpy.context.view_layer
    prev_active = None
    if view_layer:
        prev_active = view_layer.objects.active
    prev_selection = bpy.context.selected_objects

    try:
        yield
    finally:
        try:
            bpy.ops.object.mode_set(mode=prev_mode)
        except Exception as e:
            log_warning(f"postprocessing: could not restore mode: {e}")
        try:
            bpy.ops.object.select_all(action="DESELECT")
        except Exception:
            pass
        for o in prev_selection:
            try:
                o.select_set(True)
            except Exception:
                pass
        if view_layer:
            view_layer.objects.active = prev_active


def unwrap_uvs(obj: Object) -> None:
    """Run Blender's UV unwrap on `obj` while preserving selection/context."""
    with _preserve_view_context():
        try:
            # enter edit mode and select all geometry for unwrap
            bpy.ops.object.mode_set(mode="EDIT")
            try:
                bpy.ops.mesh.select_all(action="SELECT")
            except Exception as e:
                log_warning(f"postprocessing: mesh.select_all failed: {e}")

            bpy.ops.uv.unwrap(method="ANGLE_BASED", fill_holes=False)
        except Exception as exc:
            log_error(f"postprocessing: unwrap failed for {obj.name}: {exc}")


def robust_weight_transfer_setup_ffxiv() -> None:
    """Configure the robust weight transfer operator for FFXIV-specific
    settings, such as enforcing the 4-bone limit and setting
    the number of limit groups.
    """

    rwt_settings = getattr(
        bpy.context.scene, "robust_weight_transfer_settings", None
    )
    if rwt_settings is None:
        log_error(
            "postprocessing: robust_weight_transfer_settings not found in scene"
        )
        return

    rwt_settings.enforce_four_bone_limit = True
    rwt_settings.num_limit_groups = 7


def robust_weight_transfer(info: CollectionExportInfo, obj: Object) -> None:
    """Perform robust weight transfer on `obj` using the operator,
    with settings
    """

    rwt_op: Any = None
    try:
        rwt_op = bpy.ops.object.skin_weight_transfer  # type: ignore
    except AttributeError:
        log_error("postprocessing: skin_weight_transfer operator not found")
        return
    rwt_settings = getattr(
        bpy.context.scene, "robust_weight_transfer_settings", None
    )
    obj_rwt_settings = getattr(obj, "robust_weight_transfer_settings", None)

    if rwt_settings is None or rwt_op is None:
        log_error(
            "postprocessing: robust_weight_transfer_settings or operator not found"
        )
        return

    robust_weight_transfer_setup_ffxiv()

    obj_container = get_modkit_object_props(obj)
    if obj_container is None:
        log_error("postprocessing: object missing 'modkit' property group")
        return

    model = get_modkit_collection_props(info.collection)

    source_obj = model.model.mannequin_object if model else None

    old_source = rwt_settings.get("source_object", None)
    if source_obj:
        rwt_settings.source_object = source_obj

    old_mask = None
    if obj_rwt_settings is not None:
        old_mask = getattr(obj_rwt_settings, "vertex_group", None)

    props = obj_container.props
    if props.rwt_use_custom_mask and obj_rwt_settings:
        obj_rwt_settings.vertex_group = props.rwt_custom_mask_name

    try:
        with _preserve_view_context():
            try:
                bpy.ops.object.mode_set(mode="OBJECT")
            except Exception as e:
                log_warning(f"postprocessing: could not set OBJECT mode: {e}")

            sel_list = [obj]
            select_objects_for_export(sel_list)

            try:
                call_operator_in_3d_viewport(rwt_op, "INVOKE_DEFAULT")
            except Exception as exc:
                raise RuntimeError(f"robust weight transfer failed: {exc}")
    finally:
        rwt_settings.source_object = old_source
        if obj_rwt_settings is not None:
            obj_rwt_settings.vertex_group = old_mask


def run_preprocessing(
    info: CollectionExportInfo, objects: list[Object]
) -> None:
    """Run configured preprocessing operations on a list of objects."""
    for obj in objects:
        if obj.type != "MESH":
            continue

        # Per-object settings live under `obj.modkit.props`
        container = get_modkit_object_props(obj)
        if container is None:
            return

        props = container.props
        try:
            if props.postproc_unwrap_uvs:
                log_debug(f"preprocessing: unwrap_uvs for {obj.name}")
                unwrap_uvs(obj)
            if props.post_proc_robust_weight_transfer:
                log_debug(
                    f"preprocessing: robust_weight_transfer for {obj.name}"
                )
                robust_weight_transfer(info, obj)

        except Exception as exc:
            log_error(f"preprocessing: failed for {obj.name}: {exc}")
