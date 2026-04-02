from bpy.types import Context, Collection, Mesh, UILayout

from .base import ExporterProtocol

from ..materials import MODKIT_OT_mesh_material


class MaterialExporterPart(ExporterProtocol):

    def draw_materials_settings(
        self, layout: UILayout, collection: Collection
    ) -> None:
        header, body = layout.panel("Materials", default_closed=True)
        header.label(text="Materials to Export", icon="MATERIAL")

        if not body:
            return

        scanned_ids = set(
            ModelScanner.scan_collection(collection).keys()
        )
        scanned_ids_list = sorted(scanned_ids)

        mats = getattr(collection, "modkit_materials", None)
        if mats is None:
            mats = []

        for mat_id in scanned_ids_list:
            row = body.row()
            row.label(text=f"Mesh #{mat_id}")

            cur_value = ""
            if mat_id < len(mats):
                cur_value = mats[mat_id].name

            label = cur_value if cur_value else "Material Missing"

            op = row.operator(MODKIT_OT_mesh_material.bl_idname, text=label)
            op.profile = self.current_profile_name()
            op.id = mat_id
            op.material = cur_value
