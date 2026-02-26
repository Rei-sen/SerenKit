"""Model panel for displaying model information."""

from types import SimpleNamespace
from typing import Any, List, Optional, Tuple, Union
from bpy.types import Panel, Collection, UILayout, Object, Context

from ..shared.model_scanner import ModelScanner

from ..properties.object_settings import get_modkit_object_props
from ..properties.model_settings import (
    MeshSettings,
    get_model_props,
    get_modkit_collection_props,
)
from ..shared.export.shapekey_utils import collect_collection_shapekeys
from ..shared.variants import filter_profile_shapekeys
from ..shared.profile import GroupMode, NamePair, get_profile_data
from ..shared.ui_helpers import (
    draw_info_box,
    draw_grid_flow,
    draw_toggle_with_field,
    draw_collapsible_section,
)


def draw_model_meshes(layout: UILayout, collection: Collection) -> None:
    """Render meshes with material selectors and part attributes."""
    box = draw_info_box(
        layout, f"Model: {collection.name}", icon="OUTLINER_OB_MESH"
    )

    model = get_model_props(collection)
    if not model:
        box.label(text="No model properties found for collection")
        return
    profile_id = model.assigned_profile
    if not profile_id:
        box.label(text="No assigned profile", icon="ERROR")
        return

    scanned_meshes = ModelScanner.scan_collection(collection)

    # Ensure stable ordering: meshes ascending, parts ascending
    for mesh_id, parts in sorted(scanned_meshes.items()):
        parts_sorted = sorted(parts, key=lambda p: p[2])

        # Find or create a stored mesh entry for UI state
        mesh_prop = None
        for m in model.meshes:
            if m.id == mesh_id:
                mesh_prop = m
                break
        if mesh_prop is None:
            mesh_prop = SimpleNamespace(
                profile=model.assigned_profile, material_name="", id=mesh_id
            )
        _draw_single_mesh(box, mesh_prop, parts_sorted, collection)


def _draw_single_mesh(
    layout: UILayout,
    mesh_prop: Union[MeshSettings, SimpleNamespace],
    parts: List[Tuple[Object, str, int]],
    collection: Collection,
) -> None:
    """Render one mesh row with material and its parts."""
    box = layout.box()

    def _mesh_extra(row: UILayout) -> None:
        # material operator placed at the end of the header row

        mat_name = getattr(mesh_prop, "material_name", "")
        label = "No material assigned" if mat_name == "" else mat_name

        if isinstance(mesh_prop, MeshSettings):
            standard_mats = mesh_prop.get_standard_materials()

            for key, value in standard_mats.items():
                if label == value:
                    label = key
                    break

        op = row.operator(
            "modkit.mesh_material",
            text=label,
            icon="MATERIAL",
        )
        op.id = mesh_prop.id

    # Use transient state keyed by mesh id on the model (collection.modkit.model)
    # Use a simple string key for transient state
    expanded = draw_collapsible_section(
        box,
        f"#{mesh_prop.id}",
        state_key=f"collection:{collection.name}:mesh:{mesh_prop.id}",
        extra=_mesh_extra,
        icon="OUTLINER_OB_MESH",
    )
    if not expanded:
        return

    box.separator(type="LINE")

    # Draw each part (submesh) with its attributes
    for part_info in parts:
        _draw_part(box, part_info)


def _draw_part(layout: UILayout, part_info: Tuple[Object, str, int]) -> None:
    """Render a single part entry with attribute controls."""
    obj, name, part_id = part_info

    box = layout.box()
    container = get_modkit_object_props(obj)

    def _part_extra(row: UILayout) -> None:
        # add attribute button into the header row
        add = row.operator(
            "modkit.handle_attribute", text="", icon="ADD", emboss=True
        )
        add.obj = obj.name
        add.is_new = True

    # Use transient state keyed by object name (prefer the object's PropertyGroup)
    expanded = draw_collapsible_section(
        box,
        f"#{part_id} {name}",
        state_key=f"object:{obj.name}:part:{part_id}",
        extra=_part_extra,
        icon="MESH_DATA",
    )
    if not expanded:
        return

    # Draw existing attributes using shared grid helper
    if container:
        items = [(attr.value, attr) for attr in container.attributes]

        def _draw_attr(cell_layout: UILayout, label: str, value: Any) -> None:
            op = cell_layout.operator(
                "modkit.handle_attribute", text=label, icon="X", emboss=True
            )
            op.obj = obj.name
            op.attribute_name = label
            op.is_new = False

        draw_grid_flow(box, items, _draw_attr)

        # Postprocessing toggle: unwrap on export (registered BoolProperty on Object)
        try:
            props = getattr(container, "props", None)
            if props is not None:
                box.prop(props, "postproc_unwrap_uvs", text="Unwrap on export")
                box.prop(
                    props,
                    "post_proc_robust_weight_transfer",
                    text="Robust Weight Transfer on export",
                )
                if getattr(props, "post_proc_robust_weight_transfer", False):
                    rwt_box = box.box()
                    draw_toggle_with_field(
                        rwt_box,
                        props,
                        "rwt_use_custom_mask",
                        "rwt_custom_mask_name",
                        label="Custom Mask Name",
                    )
        except Exception:
            pass


def draw_variant_shapekeys(layout: UILayout, collection: Collection) -> None:
    """Show shape key support for the collection's variant profile."""
    mainbox = layout.box()
    row = mainbox.row()
    row.alignment = "CENTER"
    row.label(text="Shape Variants", icon="SHAPEKEY_DATA")

    mainbox.separator(type="LINE")

    col_props = get_modkit_collection_props(collection)
    model_props = col_props.model if col_props else None
    profile_id = model_props.assigned_profile if model_props else None

    if not profile_id:
        mainbox.label(text="No assigned profile", icon="ERROR")
        return

    profile = get_profile_data(profile_id)
    if not profile:
        mainbox.label(text="Profile not loaded", icon="ERROR")
        return

    shapekeys = collect_collection_shapekeys(collection)

    support_groups = filter_profile_shapekeys(shapekeys, profile)

    model_props = col_props.model if col_props else None
    for group in profile.groups:
        group_name = group.group_name
        mode = group.mode
        sks = group.shapekeys

        matching_group = next(
            (g for g in support_groups if g.group_name == group_name), None
        )
        detected_keys: set[str] = set()
        if matching_group:
            detected_keys = {bname for bname, _ in matching_group.shapekeys}

            # Retrieve saved expansion state
            # Use transient handling in the helper: pass the collection and
            # group_name so the helper can obtain/manage transient state.
            _draw_variant_group(
                mainbox,
                collection,
                group_name,
                mode,
                sks,
                detected_keys,
                state_key=f"collection:{collection.name}:group:{group_name}",
            )


def _draw_variant_group(
    layout: UILayout,
    collection: Collection,
    group_name: str,
    mode: GroupMode,
    shapekeys: list[NamePair],
    detected_keys: set[str],
    state_key: Optional[str] = None,
) -> None:
    """Render a variant group with shape key status indicators."""
    box = layout.box()

    # Use the shared header helper; when state is transient the header will
    # render a clickable operator to flip state.
    expanded = draw_collapsible_section(
        box,
        f"{group_name} ({mode.name})",
        state_key=state_key,
        extra=None,
        icon="FILEBROWSER",
    )

    if not expanded:
        return

    flow = box.grid_flow(
        row_major=True,
        columns=0,
        even_columns=False,
        even_rows=False,
        align=True,
    )
    flow.scale_x = 0.6

    for sk_name, export_name in shapekeys:
        detected = sk_name in detected_keys

        cell = flow.row(align=True)
        cell.enabled = detected

        op = cell.operator(
            "modkit.variant_info",
            text=sk_name,
            emboss=True,
            depress=detected,
            icon="CHECKMARK" if detected else "X",
        )
        op.blender_name = sk_name
        op.export_name = export_name


class MODKIT_PT_model_panel(Panel):
    """UI panel showing model meshes, materials, and variants."""

    bl_label: str = "Model"
    bl_idname: str = "MODKIT_PT_model_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category: str = "Modkit"

    def draw(self, context: Context) -> None:
        layout = self.layout
        assert layout
        col = context.collection

        if not col:
            layout.label(text="No collection selected.")
            return

        col_props = get_modkit_collection_props(col)
        model_props = col_props.model if col_props else None

        if not model_props:
            layout.label(text="No model properties found.")
            return

        layout.prop(model_props, "is_enabled")

        if not model_props.is_enabled:
            return

        # Model mesh display with materials and attributes
        draw_model_meshes(layout, col)

        # Model configuration
        box = layout.box()

        box.prop(model_props, "export_armature", icon="ARMATURE_DATA")
        box.prop(model_props, "mannequin_object", icon="OUTLINER_OB_MESH")

        # Variant profile assignment
        box = layout.box()
        box.label(text="Variant Profiles:")
        box.prop(model_props, "assigned_profile")

        # Shape variant support visualization
        draw_variant_shapekeys(layout, col)


CLASSES = [
    MODKIT_PT_model_panel,
]
