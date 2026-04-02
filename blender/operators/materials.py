"""Model management operators."""

from __future__ import annotations
from typing import TYPE_CHECKING

from bpy.types import Operator, Context, Event
from bpy.props import IntProperty, StringProperty


from .._shared.blender_typing import OperatorReturn
from .._shared.profile import Material, get_profile_data


class MODKIT_OT_mesh_material(Operator):
    """Operator to assign materials to mesh objects."""

    bl_idname: str = "modkit.mesh_material"
    bl_label: str = "Assign Material to Mesh"

    profile: StringProperty(options={"HIDDEN"})  # type: ignore

    id: IntProperty(name="Mesh ID", default=0, options={"HIDDEN"})  # type: ignore

    def _search(self, context: Context, edit_text: str) -> list[str]:
        prof_data = get_profile_data(self.profile)
        if prof_data is None:
            return []

        mats = prof_data.standard_materials
        mat_names = [mat.name for mat in mats]

        return mat_names

    material: StringProperty(  # type: ignore
        name="Material Path",
        description="",
        default="",
        search=_search,
        search_options={"SUGGESTION"},
    )

    def _get_profile_materials(self) -> list[Material]:
        prof_data = get_profile_data(self.profile)
        if prof_data is None:
            return []
        return prof_data.standard_materials

    def _is_known_name(self, name: str) -> bool:
        materials = self._get_profile_materials()

        return any(mat.name.lower() == name.lower() for mat in materials)

    def _to_known_name(self, name: str) -> str:
        materials = self._get_profile_materials()
        for mat in materials:
            if mat.path.lower() == name.lower():
                return mat.name
        return name

    def _known_name_to_path(self, name: str) -> str:
        materials = self._get_profile_materials()
        for mat in materials:
            if mat.name.lower() == name.lower():
                return mat.path
        return name

    def invoke(self, context: Context, event: Event) -> set[OperatorReturn]:

        wm = context.window_manager
        if not wm:
            self.report({"ERROR"}, "Window manager not available")
            return {"CANCELLED"}

        if not context or not context.collection:
            self.report({"ERROR"}, "No collection in context")
            return {"CANCELLED"}

        mats = getattr(context.collection, "modkit_materials", None)

        if mats is None:
            self.report(
                {"ERROR"},
                f"No material properties found for collection {context.collection.name}",
            )
            return {"CANCELLED"}

        while self.id >= len(mats):
            mat = mats.add()
            mat.name = ""
            mat.path = ""

        self.material = self._to_known_name(mats[self.id].name)

        return wm.invoke_props_dialog(self)

    def draw(self, context: Context) -> None:
        layout = self.layout
        if layout is None:
            return

        layout.prop(self, "material", text="Material", icon="MATERIAL")

    def execute(self, context: Context) -> set[OperatorReturn]:

        collection = context.collection
        if not collection:
            self.report({"ERROR"}, "No collection in context")
            return {"CANCELLED"}
        mats = getattr(collection, "modkit_materials", None)
        if mats is None:
            self.report(
                {"ERROR"},
                f"No material properties found for collection {collection.name}",
            )
            return {"CANCELLED"}

        if self.id >= len(mats):
            self.report({"ERROR"}, "Mesh ID out of range")
            return {"CANCELLED"}

        mat = mats[self.id]
        if self._is_known_name(self.material):
            mat.name = self.material
            mat.path = self._known_name_to_path(self.material)
        else:
            sanitized = _sanitize_material_name(self.material)
            mat.name = sanitized
            mat.path = sanitized

        return {"FINISHED"}

    if TYPE_CHECKING:
        id: int  # type: ignore
        material: str  # type: ignore


def _sanitize_material_name(name: str) -> str:
    if not name:
        return ""

    s = name.strip()
    s = "/" + s.lstrip("/")

    if not s.lower().endswith(".mtrl"):
        s = s + ".mtrl"
    return s


CLASSES = [
    MODKIT_OT_mesh_material,
]
