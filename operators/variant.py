
from typing import TYPE_CHECKING, Optional
from bpy.types import Operator, Context, OperatorProperties
from bpy.props import StringProperty

from ..shared.blender_typing import OperatorReturn


class MODKIT_OT_variant_info(Operator):
    """Display variant/shapekey information."""
    bl_idname: str = "modkit.variant_info"
    bl_label: str = "Variant Info"
    bl_description: str = "Display mapping between Blender shapekey and exported name"

    blender_name: StringProperty(  # type: ignore
        name="Blender Name",
        description="Shapekey name in Blender"
    )

    export_name: StringProperty(  # type: ignore
        name="Export Name",
        description="Name used when exporting"
    )

    @classmethod
    def description(
        cls,
        context: Optional[Context],
        properties: OperatorProperties
    ) -> str:
        """Generate tooltip showing mapping."""
        return (
            f"Blender shapekey: {properties.blender_name}\n"
            f"Exported as: {properties.export_name}"
        )

    def execute(self, context: Context) -> set[OperatorReturn]:
        """Execute variant info (no-op, info only)."""
        return {'FINISHED'}

    if TYPE_CHECKING:
        blender_name: str
        export_name: str


CLASSES = [
    MODKIT_OT_variant_info,
]
