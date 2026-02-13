
import bpy
import os

from pathlib import Path
from bpy.types import Operator, Context
from ..properties.model_settings import get_model_props
from ..properties.model_settings import ModelSettings

from ..shared.export.modpack import update_live_modpack
from ..properties.export_properties import get_export_props
from ..shared.blender_typing import OperatorReturn


class MODKIT_OT_live_install(Operator):
    """Perform live install for the given collection using existing exported MDL files."""

    bl_idname: str = "modkit.live_install"
    bl_label: str = "Live Install Now"

    def execute(self, context: Context) -> set[OperatorReturn]:
        cfg = get_export_props()

        export_root = getattr(cfg, "export_root_dir", None) if cfg else None
        if not export_root or not os.path.isdir(export_root):
            self.report(
                {"ERROR"}, f"FBX export folder not found: {export_root}")
            return {"CANCELLED"}

        target_root = getattr(
            cfg, "live_install_target_dir", None) if cfg else None

        if not target_root:
            self.report({"ERROR"}, "Live install target folder not configured")
            return {"CANCELLED"}

        export_dir = Path(export_root)
        if not export_dir.exists() or not export_dir.is_dir():
            self.report(
                {"ERROR"}, f"Export folder for collection not found: {export_dir}"
            )
            return {"CANCELLED"}

        # Build mapping of collection name -> ModelSettings for the updater
        collections: dict[str, ModelSettings] = {}
        for col in bpy.data.collections:
            model = get_model_props(col)
            if not model or not model.is_enabled or not model.export_enabled:
                continue
            collections[col.name] = model

        try:
            summary = update_live_modpack(
                Path(target_root), Path(export_root), collections
            )
            orphans = summary.get("orphans", set())
            duplicates = summary.get("duplicates", set())
            self.report(
                {"INFO"},
                f"Live install completed. Orphans: {len(orphans)}, Duplicates: {len(duplicates)}",
            )
        except Exception as e:
            self.report({"ERROR"}, f"Live install update failed: {e}")
            return {"CANCELLED"}
        return {"FINISHED"}


CLASSES = [
    MODKIT_OT_live_install,
]
