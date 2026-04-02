from typing import Literal

from bpy.props import BoolProperty
from bpy.types import Collection, UILayout, Context


from .base import ExporterProtocol

from ..generate_shapekeys import MODKIT_OT_generate_shapekeys

from ..._shared.profile import Profile
from ..._shared.export.shapekey_utils import collection_shapekeys


class BatchExporterPart(ExporterProtocol):

    batch_export: BoolProperty(  # type: ignore
        name="Batch Export",
        description="Export all detected shapes from current profile",
        default=True,
    )

    def draw_shapekey_item(
        self,
        layout: UILayout,
        collection: Collection,
        shapekey: NamePair,
        detected_shapekeys: set[str],
    ) -> None:
        cell = layout.row(align=True)

        blender_name, export_name = shapekey

        detected = blender_name in detected_shapekeys
        disabled_shapekeys = get_modkit_disabled_shapes(collection)
        disabled = is_shapekey_disabled(disabled_shapekeys, blender_name)

        cell.enabled = detected
        cell.alert = disabled and detected

        is_on = detected and not disabled

        icon: Literal["CHECKMARK", "X"] = "CHECKMARK" if is_on else "X"

        op = cell.operator(
            MODKIT_OT_shape_toggle.bl_idname,
            text=blender_name,
            emboss=True,
            depress=is_on,
            icon=icon,
        )
        op.collection = collection.name

        op.key = blender_name
        op.name = export_name

    def draw_group(
        self,
        layout: UILayout,
        collection: Collection,
        group: Group,
        detected_shapekeys: set[str],
    ) -> None:
        box = layout.box()
        name_label = box.row(align=True)
        name = f"{group.group_name} ({group.mode.name.title()})"
        name_label.label(text=name, icon="FILEBROWSER")
        name_label.separator()

        generate_op = name_label.operator(
            MODKIT_OT_generate_shapekeys.bl_idname, text="", icon="FILE_NEW"
        )
        generate_op.profile = self.profile
        generate_op.group_name = group.group_name

        box.separator(type="LINE")

        flow = box.grid_flow(
            row_major=True,
            columns=0,
            even_columns=False,
            even_rows=False,
            align=True,
        )

        for shapekey in group.shapekeys:
            self.draw_shapekey_item(
                flow, collection, shapekey, detected_shapekeys
            )

    def draw_batch_export_settings(
        self, layout: UILayout, context: Context, profile: Profile
    ) -> None:

        header, body = layout.panel("Shapes", default_closed=False)
        # header.label(text="Shapes", icon="SHAPEKEY_DATA")
        header.prop(
            self,
            "batch_export",
            text="Batch Shape Export",
        )

        if not context.collection:
            return
        if not body:
            return

        body.enabled = self.batch_export
        shapekeys = collection_shapekeys(context.collection)
        for group in profile.groups:
            self.draw_group(body, context.collection, group, shapekeys)
