from bpy.types import Panel, Context, Mesh

from ..properties.object_settings import get_modkit_object_props


class MODKIT_PT_mesh_preprocessing(Panel):
    bl_label = "FFXIV Export Preprocessing"
    bl_idname = "MODKIT_PT_mesh_preprocessing"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context: Context):
        layout = self.layout
        obj = context.object

        if layout is None:
            return

        if not obj or not isinstance(obj.data, Mesh):
            layout.label(text="No mesh object selected.")
            return

        modkit = get_modkit_object_props(obj)
        if not modkit or not modkit.preprocess_settings:
            layout.label(text="No mesh preprocessing settings found.")
            return

        settings = modkit.preprocess_settings
        layout.prop(settings, "unwrap_uvs")

        header, body = layout.panel("", default_closed=True)

        header.prop(settings, "robust_weight_transfer")

        if not body:
            return

        body.enabled = settings.robust_weight_transfer
        body.prop(settings, "rwt_use_custom_mask")
        body.prop(settings, "rwt_custom_mask_name")


CLASSES = [
    MODKIT_PT_mesh_preprocessing,
]
