from __future__ import annotations
from pathlib import Path
import textwrap
from typing import Iterable, Literal, Optional

import bpy

from bpy.types import (
    Event,
    Operator,
    FileHandler,
    Context,
    UILayout,
    Collection,
)

from bpy.props import (
    StringProperty,
    EnumProperty,
    BoolProperty,
)

from .exporter_parts.modpack_file_update import ModpackFileExporterPart
from .exporter_parts.mdl_converter import MdlConverterExporterPart
from .exporter_parts.modpack_group import ModpackGroupExporterPart
from .exporter_parts.live_install import LiveInstallExporterPart
from .exporter_parts.materials import MaterialExporterPart
from .exporter_parts.batch import BatchExporterPart

from ..properties.collection_settings import get_collection_settings

from ..properties.object_settings import get_modkit_object_props

from ..properties.shapekey_state import (
    get_modkit_disabled_shapes,
    is_shapekey_disabled,
)

from ..preferences import get_addon_preferences
from .._shared.export.new_export_session import NewExportSession
from .._shared.export.settings import ExportSettings
from .._shared.export.shapekey_utils import collection_shapekeys
from .._shared.model_scanner import ModelScanner
from .._shared.modpack import update_live_modpack, update_packed_modpack
from .._shared.blender_typing import OperatorReturn
from .._shared.variants import generate_variant_combos_for_export
from .._shared.penumbra import PenumbraConnection
from .._shared.profile import (
    Group,
    NamePair,
    Profile,
    get_profile_data,
    get_profile_items,
)


class ModExport(
    Operator,
    BatchExporterPart,
    LiveInstallExporterPart,
    MaterialExporterPart,
    MdlConverterExporterPart,
    ModpackFileExporterPart,
    ModpackGroupExporterPart,
):
    bl_idname = "modkit.export_ffxiv"
    bl_label = "FF Mod Export"

    # Unused, required for compatibility with 4.2
    filepath: StringProperty(  # type: ignore
        name="File Path",
        options={"HIDDEN", "SKIP_SAVE"},
    )

    # Set by blender during export
    collection: StringProperty(  # type: ignore
        name="Source Collection",
        description="Name of the collection to export",
        default="",
    )

    output_path: StringProperty(  # type: ignore
        name="Output Path",
        description="Directory to export files to (should be a folder, not a file)",
        default="",
        subtype="DIR_PATH",
    )

    # Batch export properties

    use_custom_prefix: BoolProperty(  # type: ignore
        name="Use Custom Export Prefix",
        description="Use a custom string as prefix for exported files instead of the profile name",
        default=False,
    )

    custom_prefix: StringProperty(  # type: ignore
        name="Custom Export Prefix",
        description="Custom string to use as prefix for exported files when enabled",
        default="",
    )

    # MDL Conversion properties

    # Live Install properties

    # Modpack update

    # Modpack group settings

    def invoke(self, context: Context, event: Event) -> set[OperatorReturn]:
        return {"RUNNING_MODAL"}

    def execute(self, context: Context) -> set[OperatorReturn]:

        valid, error_message = self._check_valid(context)
        if not valid:
            assert error_message is not None
            self.report({"ERROR"}, error_message)
            return {"CANCELLED"}

        collection = bpy.data.collections.get(self.collection)
        if not collection:
            self.report({"ERROR"}, f"Collection not found: {self.collection}")
            return {"CANCELLED"}

        export_settings = self._create_export_settings(collection)

        variants: Iterable[Iterable[NamePair] | tuple[()]] = [()]

        if self.batch_export:

            detected_shapekeys = collection_shapekeys(collection)
            disabled_shapes = {
                sk.name for sk in get_modkit_disabled_shapes(collection)
            }

            variants = generate_variant_combos_for_export(
                export_settings.profile, detected_shapekeys, disabled_shapes
            )

        session = NewExportSession(export_settings)
        session.start(self.collection)

        try:
            session.prepare_collection_for_export()

            result = session.export_mesh_variants(collection, variants)
        except Exception as exc:
            session.fail(str(exc))
            self.report({"ERROR"}, f"Export failed: {exc}")
            return {"CANCELLED"}

        if self.live_install:

            update_live_modpack(
                modpack_root=Path(self.live_install_target_dir),
                mdl_files=result.mdl_files,
                target_group_name=self.target_group,
                game_path=self.game_path,
            )
            if self.live_install_auto_reload or self.live_install_auto_redraw:
                penumbra = PenumbraConnection()

                if self.live_install_auto_reload:
                    penumbra.reload(path=self.live_install_target_dir)
                if self.live_install_auto_redraw:
                    penumbra.redraw()

        if self.update_modpack:
            update_packed_modpack(
                pmp_path=Path(self.modpack_path),
                mdl_files=result.mdl_files,
                target_group_name=self.target_group,
                game_path=self.game_path,
            )

        mdl_count = len(result.mdl_files)
        fbx_count = len(result.fbx_files)
        summary = (
            f"Done - {mdl_count} MDL file(s)"
            if mdl_count
            else f"Done - {fbx_count} FBX file(s)"
        )
        session.complete()

        self.report({"INFO"}, f"Export complete: {summary}")
        return {"FINISHED"}

    def draw(self, context: Context) -> None:
        layout = self.layout
        if not layout:
            return

        profile_data = get_profile_data(self.profile)
        collection = context.collection

        if collection:
            self.draw_main_settings(layout, collection)
            if profile_data and profile_data.profile_info:
                self.draw_profile_info(layout, profile_data)
            self.draw_materials_settings(layout, collection)
        self.draw_mdl_conversion_settings(layout)
        self.draw_auto_live_install_settings(layout)
        self.draw_modpack_update_settings(layout)
        self.draw_modpack_group_settings(layout)

        if profile_data:
            self.draw_batch_export_settings(layout, context, profile_data)

    def _check_valid(self, context: Context) -> tuple[bool, Optional[str]]:
        if not self.collection:
            return False, "No collection specified for export"

        if not self.output_path:
            return False, "No output path specified for export"

        if self.use_custom_prefix and not self.custom_prefix:
            return False, "Custom prefix enabled but no prefix provided"

        needs_game_path = self.convert_to_mdl and not self.game_path
        if needs_game_path:
            return False, "MDL conversion enabled but no game path provided"

        if (self.live_install or self.update_modpack) and not self.game_path:
            return (
                False,
                "Game path is required for live install or modpack update",
            )

        if self.live_install and not self.live_install_target_dir:
            return (
                False,
                "Live install enabled but no target directory provided",
            )

        pref = get_addon_preferences()
        if self.convert_to_mdl and (pref is None or not pref.textools_path):
            return False, "Textools path not set in addon preferences"

        return True, None

    def _create_export_settings(self, collection: Collection) -> ExportSettings:
        prefix = self.custom_prefix if self.use_custom_prefix else self.profile
        game_path = self.game_path if self.convert_to_mdl else None
        live_install_dir = (
            self.live_install_target_dir if self.live_install else None
        )
        profile = get_profile_data(self.profile)
        if not profile:
            raise ValueError(f"Invalid profile selected: {self.profile}")

        config = get_addon_preferences()
        if not config and self.convert_to_mdl:
            raise RuntimeError(
                "Addon preferences not found, required for MDL conversion"
            )

        textools_dir = Path(config.textools_path) if config else None
        if self.convert_to_mdl and not textools_dir:
            raise ValueError("Textools path is required for MDL conversion")

        mats = dict()
        col_mats = getattr(collection, "modkit_materials", None)
        if col_mats is not None:
            for i, mat in enumerate(col_mats):
                mats[i] = mat.path

        scan = ModelScanner.scan_collection(collection)
        attrs = dict()
        for mesh_index, parts in scan.items():
            for obj, _, part_index in parts:
                modkit = get_modkit_object_props(obj)
                if not modkit or not modkit.attribute_settings:
                    continue

                attributes = [
                    a.value for a in modkit.attribute_settings.attributes
                ]
                attrs[(mesh_index, part_index)] = attributes

        col_props = get_collection_settings(collection)
        mannequin = None
        if (
            col_props
            and col_props.mannequin_object
            and col_props.mannequin_object.type == "MESH"
        ):
            mannequin = col_props.mannequin_object

        return ExportSettings(
            textools_dir=textools_dir,
            profile=profile,
            export_root_dir=Path(self.output_path),
            export_prefix=prefix,
            game_path=game_path,
            live_install_target_dir=live_install_dir,
            mannequin=mannequin,
            attributes=attrs,
            materials_info=mats,
            convert_to_mdl=self.convert_to_mdl,
        )

    # Drawing methods for UI panels

    def draw_main_settings(
        self, layout: UILayout, collection: Collection
    ) -> None:

        preferences = get_addon_preferences()
        if preferences and preferences.update_available:
            layout.label(text="Update Available!", icon="ERROR")

        row = layout.row()
        lcol = row.column(align=True)
        lcol.alignment = "CENTER"
        lcol.label(text="", icon="ERROR")
        rcol = row.column(align=True)
        rcol.alignment = "CENTER"
        rcol.label(text="The filepath property is hardcoded in blender.")
        rcol.label(text="Just ignore it and use the field below")

        layout.prop(self, "output_path", text="Output Path")

        layout.separator()
        layout.prop(self, "profile")
        layout.prop(self, "use_custom_prefix")
        if self.use_custom_prefix:
            layout.prop(self, "custom_prefix")

        col_props = get_collection_settings(collection)
        layout.prop(col_props, "mannequin_object")


class IO_FH_ffmod(FileHandler):
    bl_idname: str = "IO_FH_ffmod"
    bl_label: str = "FFXIV Mod"
    bl_export_operator = ModExport.bl_idname
    bl_file_extensions = ""


def register():
    bpy.utils.register_class(ModExport)
    bpy.utils.register_class(IO_FH_ffmod)


def unregister():
    bpy.utils.unregister_class(IO_FH_ffmod)
    bpy.utils.unregister_class(ModExport)
