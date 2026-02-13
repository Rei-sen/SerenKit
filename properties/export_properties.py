
from typing import TYPE_CHECKING, Optional

import bpy

from bpy.types import PropertyGroup
from bpy.props import PointerProperty, StringProperty, EnumProperty


class ExportSettings(PropertyGroup):

    export_root_dir: StringProperty(  # type: ignore
        name="Export Folder",
        description="Root folder where FBX files will be exported",
        subtype='DIR_PATH',
        default=""
    )

    export_prefix_mode: EnumProperty(  # type: ignore
        name="Name Prefix Mode",
        description="How to prepend a prefix to exported files",
        items=[
            ('NONE', "None", "No prefix"),
            ('PROFILE', "Profile", "Use variant profile name"),
            ('CUSTOM', "Custom", "Use custom string")
        ],
        default='PROFILE',
    )

    export_custom_prefix: StringProperty(  # type: ignore
        name="Custom Prefix",
        description="Custom string to prepend to "
        "exported files if mode is CUSTOM",
        default=""
    )

    export_mode: EnumProperty(  # type: ignore
        name="Exporter",
        description="Which export pipeline to run",
        items=[
            ('FBX_ONLY', "FBX Only", "Export FBX files only"),
            ('FBX_TO_MDL', "FBX -> MDL",
             "Export FBX and convert to MDL using Textools")
        ],
        default='FBX_TO_MDL',
    )

    live_install_target_dir: StringProperty(  # type: ignore
        name="Live Mod Folder",
        description="Path to the installed mod folder "
        "where MDL files will be written",
        subtype='DIR_PATH',
        default="",
    )

    if TYPE_CHECKING:
        export_root_dir: str
        export_prefix_mode: str
        export_custom_prefix: str
        export_mode: str
        live_install_target_dir: str


class PMPImportSettings(PropertyGroup):
    """Properties for PMP file import and management."""

    pmp_path: StringProperty(  # type: ignore
        name="PMP File Path",
        description="Path to the currently loaded PMP file",
        default=""
    )

    if TYPE_CHECKING:
        pmp_path: str


class ModkitSceneProps(PropertyGroup):
    """Top-level container for Modkit scene-scoped properties."""

    export: PointerProperty(  # type: ignore
        name="Export Config",
        type=ExportSettings
    )

    pmp: PointerProperty(  # type: ignore
        name="PMP Import",
        type=PMPImportSettings
    )

    if TYPE_CHECKING:
        export: ExportSettings
        pmp: PMPImportSettings


def get_modkit_scene_props() -> Optional[ModkitSceneProps]:
    """Get the Modkit scene properties from the current scene."""
    return getattr(bpy.context.scene, "modkit", None)


def get_export_props() -> Optional[ExportSettings]:
    """Get the export configuration from the current scene.

    NOTE: This function returns the new `scene.modkit.export` container only
    (breaking change).
    """
    modkit = get_modkit_scene_props()

    return modkit.export if modkit else None


def get_pmp_props() -> Optional[PMPImportSettings]:
    """Get the PMP import properties from the current scene.

    NOTE: This returns `scene.modkit.pmp` only (breaking change).
    """
    modkit = get_modkit_scene_props()
    return modkit.pmp if modkit else None


CLASSES: list[type] = [
    ExportSettings,
    PMPImportSettings,
    ModkitSceneProps,
]
