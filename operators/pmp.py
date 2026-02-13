"""PMP file import and editing operators."""

import os
import bpy
from pathlib import Path
from typing import TYPE_CHECKING

from bpy.types import Operator, Context, Event
from bpy.props import StringProperty

from ..shared.export.modpack import add_file_to_option, find_or_create_group, find_or_create_option, pmp_work_context, save_modpack_versioned
from ..properties.model_settings import get_model_props
from ..properties.export_properties import get_pmp_props
from ..properties.export_properties import get_export_props
from ..xivpy.pmp.modpack import Modpack
from ..shared.export.modpack import collect_mdl_files_by_collection
from ..shared.logging import log_error
from ..shared.blender_typing import OperatorReturn


class MODKIT_OT_load_pmp(Operator):
    """Load a PMP file and display its contents."""
    bl_idname: str = "modkit.load_pmp"
    bl_label: str = "Load PMP File"
    bl_description: str = "Load a modpack (pmp) file to edit or update"

    filepath: StringProperty(  # type: ignore
        name="File Path",
        description="Path to the PMP file",
        subtype='FILE_PATH'
    )

    def execute(self, context: Context) -> set[OperatorReturn]:
        if not os.path.isfile(self.filepath):
            self.report({'ERROR'}, f"File not found: {self.filepath}")
            return {'CANCELLED'}

        try:
            pmp_path = Path(self.filepath)
            modpack = Modpack.from_archive(pmp_path)

            # Store the loaded modpack in PMP properties
            pmp_props = get_pmp_props()
            if not pmp_props:
                self.report({'ERROR'}, "PMP properties not found")
                return {'CANCELLED'}

            pmp_props.pmp_path = self.filepath

            self.report(
                {'INFO'}, f"Loaded PMP with {len(modpack.groups)} groups")
            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"Failed to load PMP file: {str(e)}")
            return {'CANCELLED'}

    def invoke(self, context: Context, event: Event) -> set[OperatorReturn]:
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    if TYPE_CHECKING:
        filepath: str


class MODKIT_OT_unload_pmp(Operator):
    """Unload the currently loaded PMP file."""
    bl_idname: str = "modkit.unload_pmp"
    bl_label: str = "Unload PMP"
    bl_description: str = "Unload the currently loaded PMP file"

    def execute(self, context: Context) -> set[OperatorReturn]:
        pmp_props = get_pmp_props()

        if not pmp_props:
            self.report({'ERROR'}, "PMP properties not found")
            return {'CANCELLED'}

        pmp_props.pmp_path = ""

        self.report({'INFO'}, "PMP file unloaded")
        return {'FINISHED'}


class MODKIT_OT_set_pmp_export_dir(Operator):
    """Set the export directory for scanning .mdl files."""
    bl_idname: str = "modkit.set_pmp_export_dir"
    bl_label: str = "Set Export Directory"
    bl_description: str = "Select the directory containing exported .mdl files"

    dirpath: StringProperty(  # type: ignore
        name="Directory Path",
        description="Path to the export directory",
        subtype='DIR_PATH'
    )

    def execute(self, context: Context) -> set[OperatorReturn]:
        if not os.path.isdir(self.dirpath):
            self.report({'ERROR'}, f"Directory not found: {self.dirpath}")
            return {'CANCELLED'}

        export_props = get_export_props()
        if not export_props:
            self.report({'ERROR'}, "Export properties not found")
            return {'CANCELLED'}
        export_props.export_root_dir = self.dirpath
        self.report({'INFO'}, f"Export directory set to: {self.dirpath}")
        return {'FINISHED'}

    def invoke(self, context: Context, event: Event) -> set[OperatorReturn]:
        wm = context.window_manager
        if not wm:
            self.report({'ERROR'}, "Window manager not found")
            return {'CANCELLED'}
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}

    if TYPE_CHECKING:
        dirpath: str


class MODKIT_OT_scan_and_add_mdl_files(Operator):
    """Scan export directory for .mdl files and add them to PMP."""
    bl_idname: str = "modkit.scan_and_add_mdl_files"
    bl_label: str = "Scan & Add MDL Files"
    bl_description: str = "Scan export directory for .mdl files and add to PMP"

    def execute(self, context: Context) -> set[OperatorReturn]:
        pmp_props = get_pmp_props()
        export_props = get_export_props()

        if not pmp_props or not export_props:
            self.report({'ERROR'}, "PMP or export properties not found")
            return {'CANCELLED'}

        pmp_path = pmp_props.pmp_path
        export_dir = export_props.export_root_dir

        if not pmp_path or not os.path.isfile(pmp_path):
            self.report({'ERROR'}, "No PMP file currently loaded")
            return {'CANCELLED'}

        if not export_dir or not os.path.isdir(export_dir):
            self.report({'ERROR'}, "No export directory set")
            return {'CANCELLED'}

        try:
            pmp_path_obj = Path(pmp_path)
            export_path = Path(export_dir)

            # Collect MDL files organized by collection
            groups_to_create = collect_mdl_files_by_collection(export_path)

            with pmp_work_context(pmp_path_obj) as (modpack, temp_work):
                files_to_copy: dict[Path, str] = {}

                # Process each collection's MDL files
                for collection_name, mdl_files in groups_to_create.items():
                    col = bpy.data.collections.get(collection_name)
                    model_props = get_model_props(col) if col else None

                    if model_props is None:
                        log_error(f"Skipping PMP add for unknown collection: {collection_name}")
                        continue

                    if not model_props.export_enabled:
                        log_error(f"Skipping PMP add for disabled export collection: {collection_name}")
                        continue

                    if model_props.use_custom_export_name and not model_props.export_name:
                        log_error(f"Skipping PMP add for collection with custom name enabled but no name set: {collection_name}")
                        continue

                    group_name = model_props.export_name if model_props.use_custom_export_name else collection_name
                    group = find_or_create_group(modpack, group_name)

                    for mdl_file in mdl_files:
                        option_name = mdl_file.stem
                        option = find_or_create_option(group, option_name, mdl_file.name)

                        game_path = model_props.game_path
                        rel_path = Path(group_name) / mdl_file.name

                        entry = add_file_to_option(option, game_path, mdl_file.resolve(), rel_path)
                        files_to_copy[entry[0]] = entry[1]

                # Save with versioning
                new_pmp_path = save_modpack_versioned(
                    modpack, pmp_path_obj, temp_work, files_to_copy)
                pmp_props.pmp_path = str(new_pmp_path)

                self.report({'INFO'}, f"Saved to: {new_pmp_path.name}")
                return {'FINISHED'}

        except ValueError as e:
            self.report({'WARNING'}, str(e))
            return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"Failed to scan and add files: {str(e)}")
            log_error(f"scan_and_add_mdl_files error: {e}")
            import traceback
            traceback.print_exc()
            return {'CANCELLED'}


class MODKIT_OT_save_pmp(Operator):
    """Save the currently loaded PMP file."""
    bl_idname: str = "modkit.save_pmp"
    bl_label: str = "Save PMP"
    bl_description: str = "Save changes to the currently loaded PMP file"

    def execute(self, context: Context) -> set[OperatorReturn]:
        pmp_props = get_pmp_props()
        if not pmp_props:
            self.report({'ERROR'}, "PMP properties not found")
            return {'CANCELLED'}

        pmp_path = pmp_props.pmp_path

        if not pmp_path or not os.path.isfile(pmp_path):
            self.report({'ERROR'}, "No PMP file currently loaded")
            return {'CANCELLED'}

        try:
            pmp_path_obj = Path(pmp_path)

            with pmp_work_context(pmp_path_obj) as (modpack, temp_work):
                # Save with versioning
                new_pmp_path = save_modpack_versioned(
                    modpack, pmp_path_obj, temp_work)
                pmp_props.pmp_path = str(new_pmp_path)

                self.report({'INFO'}, f"PMP saved to: {new_pmp_path.name}")
                return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"Failed to save PMP: {str(e)}")
            log_error(f"save_pmp error: {e}")
            return {'CANCELLED'}


CLASSES: list[type] = [
    MODKIT_OT_load_pmp,
    MODKIT_OT_unload_pmp,
    MODKIT_OT_set_pmp_export_dir,
    MODKIT_OT_scan_and_add_mdl_files,
    MODKIT_OT_save_pmp,
]
