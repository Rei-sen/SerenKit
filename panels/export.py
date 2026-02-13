"""Export panel for FBX export settings and per-collection export."""

import bpy

from bpy.types import Panel, Context

from ..properties.export_properties import get_export_props
from ..shared.ui_helpers import draw_info_box, draw_toggle_with_field
from ..properties.model_settings import get_modkit_collection_props


class MODKIT_PT_export(Panel):
    """Panel for FBX export settings and per-collection export."""
    bl_label: str = "Export"
    bl_idname: str = "MODKIT_PT_export"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category: str = "Modkit"

    def draw(self, context: Context) -> None:
        layout = self.layout

        assert layout

        cfg = get_export_props()

        if not cfg:
            layout.label(text="Export configuration not found.")
            return

        box = layout
        box.prop(cfg, "export_root_dir")
        box.prop(cfg, "live_install_target_dir")
        box.operator("modkit.live_install", text="Live Install Now")

        row = layout.row()
        row.prop(cfg, "export_mode")
        layout.operator("modkit.export_models", icon='EXPORT')
        layout.separator()

        # Prefix options
        box = layout.box()
        box.label(text="Output Name Prefix")
        box.prop(cfg, "export_prefix_mode")
        if cfg.export_prefix_mode == 'CUSTOM':
            box.prop(cfg, "export_custom_prefix")

        layout.separator()

        for col in bpy.data.collections:
            col_props = get_modkit_collection_props(col)
            model = col_props.model if col_props else None
            if not model or not model.is_enabled:
                continue

            box = draw_info_box(layout, col.name, icon='OUTLINER_COLLECTION')

            box.prop(model, "export_enabled")
            box.prop(model, "game_path")

            draw_toggle_with_field(
                box, model, "use_custom_export_name", "export_name")
            op = box.operator("modkit.export_models", text="Export This")
            if col.name:
                op.collection_name = col.name


CLASSES = [
    MODKIT_PT_export,
]
