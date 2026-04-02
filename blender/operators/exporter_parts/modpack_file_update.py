from bpy.props import BoolProperty, StringProperty
from bpy.types import Context, Operator, UILayout

from .base import ExporterProtocol


class ModpackFileExporterPart(ExporterProtocol):

    update_modpack: BoolProperty(  # type: ignore
        name="Update Modpack",
        description="Automatically update modpack files after export",
        default=False,
    )
    modpack_path: StringProperty(  # type: ignore
        name="Modpack Path",
        description="Path to the modpack file to update after export",
        subtype="FILE_PATH",
        default="",
    )

    def draw_modpack_update_settings(self, layout: UILayout) -> None:
        header, body = layout.panel("Modpack Update", default_closed=True)
        header.enabled = self.is_mdl_export_enabled()
        header.prop(self, "update_modpack", text="Enable Modpack Update")

        if not body:
            return

        body.enabled = self.update_modpack
        body.prop(self, "modpack_path", text="Modpack File Path")
