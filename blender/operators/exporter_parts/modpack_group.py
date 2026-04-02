from bpy.types import Context, Operator, UILayout
from bpy.props import StringProperty

from .base import ExporterProtocol


class ModpackGroupExporterPart(ExporterProtocol):

    target_group: StringProperty(  # type: ignore
        name="Target Group",
        description="Name of the group in the modpack to update with the exported files",
        default="",
    )

    def draw_modpack_group_settings(self, layout: UILayout) -> None:
        header, body = layout.panel(
            "Modpack Group Settings", default_closed=True
        )
        header.label(text="Modpack Group Settings", icon="GROUP")
        if not body:
            return

        body.prop(self, "target_group", text="Target Group in Modpack")
