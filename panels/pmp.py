"""PMP import and editing UI panels."""

from bpy.types import Panel, Context
from pathlib import Path

from ..properties.export_properties import get_pmp_props
from ..properties.export_properties import get_export_props
from ..xivpy.pmp.modpack import Modpack


class MODKIT_PT_pmp_import(Panel):
    """Panel for loading and managing PMP files."""
    bl_label: str = "PMP Import & Edit"
    bl_idname: str = "MODKIT_PT_pmp_import"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category: str = "Modkit"

    def draw(self, context: Context) -> None:
        layout = self.layout

        if not layout:
            return

        pmp_props = get_pmp_props()
        export_props = get_export_props()

        # Check if a PMP file is loaded
        pmp_path = pmp_props.pmp_path if pmp_props else None

        if not pmp_path:
            # No PMP loaded - show load button
            layout.label(text="No PMP file loaded", icon='FILE')
            layout.operator("modkit.load_pmp",
                            icon='FILE_ARCHIVE', text="Load PMP File")

        else:
            # PMP is loaded - show file info and editing options
            box = layout.box()

            # File info header
            row = box.row()
            row.label(text=f"PMP: {Path(pmp_path).name}", icon='FILE')
            row.operator("modkit.unload_pmp", text="", icon='X', emboss=True)

            box.separator(type='LINE')

            # Export directory section
            export_dir = export_props.export_root_dir if export_props else ""

            dir_box = box.box()
            dir_box.label(text="Export Directory", icon='FOLDER_REDIRECT')

            if not export_dir:
                dir_box.label(text="Not set", icon='ERROR')
                dir_box.operator("modkit.set_pmp_export_dir",
                                 icon='FILE_FOLDER', text="Select Export Dir")
            else:
                dir_box.label(text=export_dir, icon='CHECKMARK')
                dir_box.operator("modkit.set_pmp_export_dir",
                                 icon='FILE_FOLDER', text="Change Dir")

            box.separator(type='LINE')

            # Scan and add section
            scan_box = box.box()
            scan_box.label(text="Add MDL Files", icon='ADD')
            scan_box.operator("modkit.scan_and_add_mdl_files",
                              icon='FILE_3D', text="Scan & Add MDL Files")

            box.separator(type='LINE')

            # Groups info section
            groups_box = box.box()

            try:
                pmp_path_obj = Path(pmp_path)
                modpack = Modpack.from_archive(pmp_path_obj)

                # Show all groups
                group_count = len(modpack.groups)
                header_row = groups_box.row()
                header_row.label(text=f"Groups ({group_count})", icon='GROUP')

                # Display groups
                for group in modpack.groups:
                    option_count = len(group.Options) if group.Options else 0
                    group_row = groups_box.row()
                    group_row.label(
                        text=f"{group.Name} ({option_count})", icon='FOLDER_REDIRECT')

            except Exception as e:
                groups_box.label(text=f"Error: {str(e)}", icon='ERROR')

            box.separator(type='LINE')

            # Save section
            save_box = box.box()
            save_box.operator("modkit.save_pmp",
                              icon='FILE_TICK', text="Save PMP")


CLASSES = [
    MODKIT_PT_pmp_import,
]
