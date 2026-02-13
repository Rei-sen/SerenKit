
from pathlib import Path

import bpy
from bpy.types import Object

from .runner import ExportRunner
from .utils import select_objects_for_export


class FBXExportRunner(ExportRunner):
    """Export runner that handles exporting a collection to FBX using 
    Blender's built-in FBX exporter."""

    def export(self, fbx_path: Path, objects: list[Object]) -> None:
        self.export_fbx_file(fbx_path, objects)

    @staticmethod
    def export_fbx_file(filepath: Path, objects: list[Object]) -> None:
        """Export the given objects to an FBX file at the specified
        filepath using Blender's FBX exporter.
        """
        select_objects_for_export(objects)

        bpy.ops.export_scene.fbx(
            filepath=str(filepath),
            use_selection=True,
            apply_unit_scale=True,
            apply_scale_options='FBX_SCALE_ALL',
            add_leaf_bones=False,
            bake_anim=False,
            use_custom_props=True,
            object_types={'MESH', 'ARMATURE'},
        )
