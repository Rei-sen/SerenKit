"""Model management operators."""


from typing import TYPE_CHECKING

from bpy.types import Operator, Context, Event
from bpy.props import IntProperty, StringProperty

from ..shared.logging import log_error
from ..properties.model_settings import MeshSettings, get_modkit_collection_props
from ..shared.blender_typing import OperatorReturn


class MODKIT_OT_mesh_material(Operator):
    """Operator to assign materials to mesh objects."""
    bl_idname: str = "modkit.mesh_material"
    bl_label: str = "Assign Material to Mesh"

    id: IntProperty(  # type: ignore
        name="Mesh ID",
        default=0
    )

    material: StringProperty()  # type: ignore

    def _get_current_material(self, context: Context) -> MeshSettings:
        if not context.collection:
            log_error("No collection in context")
            raise ValueError("No collection in context")

        col_props = get_modkit_collection_props(context.collection)
        model = col_props.model if col_props else None
        if not model:
            log_error("No model properties found for collection")
            raise ValueError("No model properties found for collection")
        if self.id >= len(model.meshes):
            raise IndexError("Mesh ID out of range")
        return model.meshes[self.id]

    def invoke(self, context: Context, event: Event) -> set[OperatorReturn]:

        wm = context.window_manager
        if not wm:
            self.report({'ERROR'}, "Window manager not available")
            return {'CANCELLED'}

        if not context or not context.collection:
            self.report({"ERROR"}, "No collection in context")
            return {'CANCELLED'}

        col_props = get_modkit_collection_props(context.collection)
        model = col_props.model if col_props else None

        if not model:
            self.report({"ERROR"}, "No model properties found for collection")
            return {'CANCELLED'}

        meshes = model.meshes
        while self.id >= len(meshes):
            id = len(meshes)
            mesh = meshes.add()

            mesh.id = id
            mesh.material_name = ""
            mesh.profile = model.assigned_profile

        return wm.invoke_props_dialog(self)

    def draw(self, context: Context) -> None:
        layout = self.layout
        if layout is None:
            return
        mat = self._get_current_material(context)
        layout.prop(mat, "material_name")

    def execute(self, context: Context) -> set[OperatorReturn]:
        return {'FINISHED'}

    if TYPE_CHECKING:
        id: int
        material: str


CLASSES = [
    MODKIT_OT_mesh_material,
]
