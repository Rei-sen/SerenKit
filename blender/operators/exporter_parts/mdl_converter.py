from typing import override

from bpy.props import BoolProperty, StringProperty
from bpy.types import Context, Operator, UILayout


from .base import ExporterProtocol


class MdlConverterExporterPart(ExporterProtocol):
    convert_to_mdl: BoolProperty(  # type: ignore
        name="Convert to MDL",
        description="Convert exported data to MDL format",
        default=True,
    )

    game_path: StringProperty(  # type: ignore
        name="Game Path",
        description="Path to in-game model file",
        default="",
    )

    @override
    def is_mdl_export_enabled(self) -> bool:
        return self.convert_to_mdl

    def is_mdl_conversion_setup_complete(self) -> bool:
        return self.convert_to_mdl and self.game_path.strip() != ""

    def draw_mdl_conversion_settings(self, layout: UILayout) -> None:
        header, body = layout.panel("MDL Conversion", default_closed=True)
        header.prop(self, "convert_to_mdl", text="Convert to MDL after export")

        if not body:
            return

        body.enabled = self.is_mdl_export_enabled()
        body.prop(self, "game_path", text="In-Game Model Path")
