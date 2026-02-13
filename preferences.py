"""Addon preferences and configuration."""

import os
import platform
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import bpy

from bpy.types import AddonPreferences, Operator, Context
from bpy.props import StringProperty

from .shared.blender_typing import OperatorReturn
from .shared.logging import log_debug
from .shared.profile import (
    get_builtin_profiles_dir,
    get_loaded_profiles,
    reload_profiles
)

_PACKAGE_NAME = str(__package__)


class MODKIT_OT_reload_profiles(Operator):
    """Reload variant profiles from built-in directory."""
    bl_idname = "modkit.reload_profiles"
    bl_label = "Reload Profiles"
    bl_description = "Reload variant profiles from built-in directory"

    def execute(self, context: Context) -> set[OperatorReturn]:
        """Execute profile reloading."""
        try:
            count: int = reload_profiles()
            self.report({'INFO'}, f"Reloaded {count} variant profiles")
            if count > 0:
                log_debug(
                    "[PROFILES] Loaded profiles: "
                    f"{list(get_loaded_profiles().keys())}")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Failed to reload profiles: {str(e)}")
            return {'CANCELLED'}


class MODKIT_OT_open_profiles_folder(Operator):
    """Open profiles folder in file explorer."""
    bl_idname = "modkit.open_profiles_folder"
    bl_label = "Open Profiles Folder"
    bl_description = "Open the profiles directory in file explorer"

    def execute(self, context: Context) -> set[OperatorReturn]:
        """Execute opening profiles folder."""

        try:
            profiles_dir: Path = get_builtin_profiles_dir()
            profiles_dir.mkdir(parents=True, exist_ok=True)

            if platform.system() == 'Windows':
                os.startfile(str(profiles_dir))
            elif platform.system() == 'Darwin':
                subprocess.Popen(['open', str(profiles_dir)])
            else:  # Linux
                subprocess.Popen(['xdg-open', str(profiles_dir)])

            self.report({'INFO'}, f"Opened: {profiles_dir}")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Failed to open folder: {str(e)}")
            return {'CANCELLED'}


class ModkitAddonPreferences(AddonPreferences):
    """Addon preferences."""
    bl_idname = _PACKAGE_NAME

    textools_path: StringProperty(  # type: ignore
        name="TexTools Path",
        description="Path to TexTools directory containing ConsoleTools.exe",
        subtype='DIR_PATH',
    )

    def draw(self, context: Context) -> None:
        layout = self.layout
        layout.prop(self, "textools_path")
        row = layout.row()
        row.operator("modkit.open_profiles_folder",
                     text="Open Profiles Folder", icon='FILE_FOLDER')
        row.operator("modkit.reload_profiles",
                     text="Reload Profiles", icon='FILE_REFRESH')

    if TYPE_CHECKING:
        textools_path: str


def get_addon_preferences() -> Optional[ModkitAddonPreferences]:
    """Get addon preferences."""
    pref = bpy.context.preferences
    addons = pref.addons if pref else None
    addon = addons[_PACKAGE_NAME] if addons else None

    return getattr(addon, "preferences", None)


CLASSES: list[type] = [
    MODKIT_OT_reload_profiles,
    MODKIT_OT_open_profiles_folder,
    ModkitAddonPreferences,
]
