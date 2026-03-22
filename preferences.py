"""Addon preferences and configuration."""

from __future__ import annotations
import os
import platform
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Optional
from urllib.error import HTTPError, URLError

import bpy

from bpy.types import AddonPreferences, Operator, Context
from bpy.props import StringProperty, BoolProperty

from .shared.blender_typing import OperatorReturn
from .shared.logging import log_debug, log_warning
from .shared.github.updates import (
    check_for_updates,
    format_datetime_iso,
    get_current_timestamp,
    should_check_for_updates,
)
from .shared.profile import (
    get_profiles_dir,
    get_loaded_profiles,
    load_profiles,
)

_PACKAGE_NAME = __package__ or ""


def _format_update_check_error(error: Exception) -> str:
    """Return a user-facing message for update check failures."""
    if isinstance(error, HTTPError):
        return f"Update check failed: GitHub returned HTTP {error.code}"
    if isinstance(error, URLError):
        return f"Update check failed: could not reach GitHub ({str(error)})"
    return f"Update check failed: {error}"


def _run_update_check(
    preferences: ModkitAddonPreferences,
) -> tuple[bool, Optional[str]]:
    now = get_current_timestamp()
    preferences.last_update_check = format_datetime_iso(now)

    try:
        result = check_for_updates()
    except Exception as error:
        preferences.update_available = False
        message = _format_update_check_error(error)
        log_warning(f"[UPDATES] {message}")
        return False, message

    preferences.update_available = result.is_update_available

    if result.is_update_available:
        log_debug(
            f"[UPDATES] Update available: {result.current_version} -> "
            f"{result.latest_version}"
        )
    else:
        log_debug(f"[UPDATES] Up to date: {result.current_version}")

    return result.is_update_available, None


def check_for_updates_on_startup() -> None:
    """Perform a one-shot startup update check if the throttle allows it."""
    preferences = get_addon_preferences()
    if preferences is None:
        return

    if not should_check_for_updates(preferences.last_update_check):
        return

    _run_update_check(preferences)


class MODKIT_OT_reload_profiles(Operator):
    """Reload variant profiles from built-in directory."""

    bl_idname = "modkit.reload_profiles"
    bl_label = "Reload Profiles"
    bl_description = "Reload variant profiles from built-in directory"

    def execute(self, context: Context) -> set[OperatorReturn]:
        """Execute profile reloading."""
        try:
            load_profiles()
            count: int = len(get_loaded_profiles())
            self.report({"INFO"}, f"Reloaded {count} variant profiles")
            if count > 0:
                log_debug(
                    "[PROFILES] Loaded profiles: "
                    f"{list(get_loaded_profiles().keys())}"
                )
            return {"FINISHED"}
        except Exception as e:
            self.report({"ERROR"}, f"Failed to reload profiles: {str(e)}")
            return {"CANCELLED"}


class MODKIT_OT_open_profiles_folder(Operator):
    """Open profiles folder in file explorer."""

    bl_idname = "modkit.open_profiles_folder"
    bl_label = "Open Profiles Folder"
    bl_description = "Open the profiles directory in file explorer"

    def execute(self, context: Context) -> set[OperatorReturn]:
        """Execute opening profiles folder."""

        try:
            profiles_dir: Path = get_profiles_dir()
            profiles_dir.mkdir(parents=True, exist_ok=True)

            if platform.system() == "Windows":
                os.startfile(str(profiles_dir))
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", str(profiles_dir)])
            else:  # Linux
                subprocess.Popen(["xdg-open", str(profiles_dir)])

            self.report({"INFO"}, f"Opened: {profiles_dir}")
            return {"FINISHED"}
        except Exception as e:
            self.report({"ERROR"}, f"Failed to open folder: {str(e)}")
            return {"CANCELLED"}


class MODKIT_OT_check_for_updates(Operator):
    """Check GitHub releases for a newer version of the add-on."""

    bl_idname = "modkit.check_for_updates"
    bl_label = "Check for Updates"
    bl_description = (
        "Check the latest GitHub release against this add-on version"
    )

    def execute(self, context: Context) -> set[OperatorReturn]:
        preferences = get_addon_preferences()
        if preferences is None:
            self.report({"ERROR"}, "Addon preferences not available")
            return {"CANCELLED"}

        update_available, error_message = _run_update_check(preferences)
        if error_message:
            self.report({"ERROR"}, error_message)
            return {"CANCELLED"}

        if update_available:
            self.report({"INFO"}, "A new SerenKit version is available")
        else:
            self.report({"INFO"}, "SerenKit is up to date")
        return {"FINISHED"}


class ModkitAddonPreferences(AddonPreferences):
    """Addon preferences."""

    bl_idname = _PACKAGE_NAME

    textools_path: StringProperty(  # type: ignore
        name="TexTools Path",
        description="Path to TexTools directory containing ConsoleTools.exe",
        subtype="DIR_PATH",
    )

    last_update_check: StringProperty(  # type: ignore
        name="Last Update Check",
        description="Timestamp of the most recent automatic or manual update check",
        default="",
    )

    update_available: BoolProperty(  # type: ignore
        name="Update Available",
        description="Whether a newer GitHub release is available",
        default=False,
        options={"SKIP_SAVE"},
    )

    def draw(self, context: Context) -> None:
        layout = self.layout
        layout.prop(self, "textools_path")

        row = layout.row()
        row.operator(
            MODKIT_OT_open_profiles_folder.bl_idname,
            text="Open Profiles Folder",
            icon="FILE_FOLDER",
        )
        row.operator(
            MODKIT_OT_reload_profiles.bl_idname,
            text="Reload Profiles",
            icon="FILE_REFRESH",
        )

        layout.separator()

        row = layout.row()
        row.label(text="Updates: ")

        if self.update_available:
            row.label(text="Update available", icon="ERROR")
        elif self.last_update_check:
            row.label(text=f"Last checked: {self.last_update_check}")

        row.operator(
            MODKIT_OT_check_for_updates.bl_idname,
            text="Check for Updates",
            icon="FILE_REFRESH",
        )

    if TYPE_CHECKING:
        textools_path: str  # type: ignore
        last_update_check: str  # type: ignore
        update_available: bool  # type: ignore


def get_addon_preferences() -> Optional[ModkitAddonPreferences]:
    """Get addon preferences."""
    pref = bpy.context.preferences
    addons = pref.addons if pref else None
    if not _PACKAGE_NAME:
        return None
    addon = addons[_PACKAGE_NAME] if addons else None

    return getattr(addon, "preferences", None)


CLASSES: list[type] = [
    MODKIT_OT_reload_profiles,
    MODKIT_OT_open_profiles_folder,
    MODKIT_OT_check_for_updates,
    ModkitAddonPreferences,
]
