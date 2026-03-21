from __future__ import annotations
from pathlib import Path
from typing import Iterable, Literal, Optional

import bpy

from bpy.types import (
    Event,
    Object,
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
    PointerProperty,
)

from ..properties.collection_settings import get_collection_settings

from ..properties.object_settings import get_modkit_object_props

from .generate_shapekeys import MODKIT_OT_generate_shapekeys


from .materials import MODKIT_OT_mesh_material
from .shape_toggle import MODKIT_OT_shape_toggle

from ..properties.shapekey_state import (
    get_modkit_disabled_shapes,
    is_shapekey_disabled,
)

from ..preferences import get_addon_preferences
from ..shared.export.new_export_session import NewExportSession
from ..shared.export.settings import ExportSettings
from ..shared.export.shapekey_utils import collection_shapekeys
from ..shared.model_scanner import ModelScanner
from ..shared.modpack import update_live_modpack, update_packed_modpack
from ..shared.blender_typing import OperatorReturn
from ..shared.variants import generate_variant_combos_for_export
from ..shared.penumbra import PenumbraConnection
from ..shared.profile import (
    Group,
    NamePair,
    Profile,
    get_profile_data,
    get_profile_items,
)


class ExportFFXIV(Operator):
    bl_idname = "modkit.export_ffxiv"
    bl_label = "FFXIV Export (placeholder)"

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

    def _get_profile_items(
        self, context: Optional[Context] = None
    ) -> Iterable[tuple[str, str, str]]:
        return get_profile_items()

    # Batch export properties

    profile: EnumProperty(  # type: ignore
        name="Export Profile",
        description="Profile to use by this collection",
        items=_get_profile_items,
    )

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

    batch_export: BoolProperty(  # type: ignore
        name="Batch Export",
        description="Export all detected shapes from current profile",
        default=True,
    )

    # MDL Conversion properties

    convert_to_mdl: BoolProperty(  # type: ignore
        name="Convert to MDL",
        description="Convert exported data to MDL format",
        default=True,
    )

    mdl_export_mode: EnumProperty(  # type: ignore
        name="MDL Export Mode",
        description="Choose how MDL files are generated",
        items=(
            ("textools", "Textools", "Export FBX then convert via Textools"),
            (
                "direct",
                "Direct (WIP, broken)",
                "Build MDL directly from Blender mesh data",
            ),
        ),
        default="textools",
    )

    game_path: StringProperty(  # type: ignore
        name="Game Path",
        description="Path to in-game model file",
        default="",
    )

    # Live Install properties
    live_install: BoolProperty(  # type: ignore
        name="Live Install",
        description="Automatically install exported files to the mod directory",
        default=False,
    )

    live_install_target_dir: StringProperty(  # type: ignore
        name="Live Install Target Directory",
        description="Directory where model files will be installed",
        subtype="DIR_PATH",
        default="",
    )

    live_install_auto_reload: BoolProperty(  # type: ignore
        name="Auto Reload",
        description="Automatically trigger a reload in-game after live install",
        default=False,
    )

    live_install_auto_redraw: BoolProperty(  # type: ignore
        name="Auto Redraw",
        description="Automatically trigger a redraw in-game after live install.",
        default=False,
    )

    # Modpack update
    update_modpack: BoolProperty(  # type: ignore
        name="Update Modpack",
        description="Automatically update modpack files after export",
        default=False,
    )
    modpack_path: StringProperty(  # type: ignore
        name="Modpack Path",
        description="Path to the modpack file to update after export",
        subtype="FILE_PATH",
        default="",
    )

    # Modpack group settings
    target_group: StringProperty(  # type: ignore
        name="Target Group",
        description="Name of the group in the modpack to update with the exported files",
        default="",
    )

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
            self.draw_materials_settings(layout, context)
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

        needs_game_path = (
            self.convert_to_mdl
            and self.mdl_export_mode == "textools"
            and not self.game_path
        )
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
        if (
            self.convert_to_mdl
            and self.mdl_export_mode == "textools"
            and (pref is None or not pref.textools_path)
        ):
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
        if (
            not config
            and self.convert_to_mdl
            and self.mdl_export_mode == "textools"
        ):
            raise RuntimeError(
                "Addon preferences not found, required for MDL conversion"
            )

        textools_dir = (
            Path(config.textools_path)
            if config and self.mdl_export_mode == "textools"
            else None
        )

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
            mdl_export_mode=self.mdl_export_mode,
        )

    # Drawing methods for UI panels

    def draw_main_settings(
        self, layout: UILayout, collection: Collection
    ) -> None:

        row = layout.row()
        lcol = row.column(align=True)
        lcol.alignment = "CENTER"
        lcol.label(text="", icon="WARNING_LARGE")
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

    def draw_materials_settings(
        self, layout: UILayout, context: Context
    ) -> None:
        header, body = layout.panel("Materials", default_closed=True)
        header.label(text="Materials to Export", icon="MATERIAL")

        if not body:
            return

        if not context.collection:
            body.label(text="No collection in context")
            return

        scanned_ids = set(
            ModelScanner.scan_collection(context.collection).keys()
        )
        scanned_ids_list = sorted(scanned_ids)

        mats = getattr(context.collection, "modkit_materials", None)
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
            op.profile = self.profile
            op.id = mat_id
            op.material = cur_value

    def draw_mdl_conversion_settings(self, layout: UILayout) -> None:
        header, body = layout.panel("MDL Conversion", default_closed=True)
        header.prop(self, "convert_to_mdl", text="Convert to MDL after export")

        if not body:
            return

        body.enabled = self.convert_to_mdl
        body.prop(self, "mdl_export_mode", text="Mode")

        game_path_row = body.row()
        game_path_row.enabled = (
            self.mdl_export_mode == "textools"
            or self.live_install
            or self.update_modpack
        )
        game_path_row.prop(self, "game_path", text="In-Game Model Path")

    def draw_auto_live_install_settings(self, layout: UILayout) -> None:
        header, body = layout.panel("Live Install", default_closed=True)
        header.enabled = self.convert_to_mdl
        header.prop(self, "live_install", text="Enable Live Install")

        if not body:
            return

        body.enabled = self.live_install
        body.prop(self, "live_install_target_dir", text="Target Directory")
        body.prop(
            self, "live_install_auto_reload", text="Auto Reload After Install"
        )
        body.prop(
            self, "live_install_auto_redraw", text="Auto Redraw After Install"
        )

    def draw_modpack_update_settings(self, layout: UILayout) -> None:
        header, body = layout.panel("Modpack Update", default_closed=True)
        header.enabled = self.convert_to_mdl
        header.prop(self, "update_modpack", text="Enable Modpack Update")

        if not body:
            return

        body.enabled = self.update_modpack
        body.prop(self, "modpack_path", text="Modpack File Path")

    def draw_modpack_group_settings(self, layout: UILayout) -> None:
        header, body = layout.panel(
            "Modpack Group Settings", default_closed=True
        )
        header.label(text="Modpack Group Settings", icon="GROUP")
        if not body:
            return

        body.prop(self, "target_group", text="Target Group in Modpack")

    def draw_shapekey_item(
        self,
        layout: UILayout,
        collection: Collection,
        shapekey: NamePair,
        detected_shapekeys: set[str],
    ) -> None:
        cell = layout.row(align=True)

        blender_name, export_name = shapekey

        detected = blender_name in detected_shapekeys
        disabled_shapekeys = get_modkit_disabled_shapes(collection)
        disabled = is_shapekey_disabled(disabled_shapekeys, blender_name)

        cell.enabled = detected
        cell.alert = disabled and detected

        is_on = detected and not disabled

        icon: Literal["CHECKMARK", "X"] = "CHECKMARK" if is_on else "X"

        op = cell.operator(
            MODKIT_OT_shape_toggle.bl_idname,
            text=blender_name,
            emboss=True,
            depress=is_on,
            icon=icon,
        )
        op.collection = collection.name

        op.key = blender_name
        op.name = export_name

    def draw_group(
        self,
        layout: UILayout,
        collection: Collection,
        group: Group,
        detected_shapekeys: set[str],
    ) -> None:
        box = layout.box()
        name_label = box.row(align=True)
        # name_label.alignment = "CENTER"
        name = f"{group.group_name} ({group.mode.name.title()})"
        name_label.label(text=name, icon="FILEBROWSER")
        name_label.separator()

        generate_op = name_label.operator(
            MODKIT_OT_generate_shapekeys.bl_idname, text="", icon="FILE_NEW"
        )
        generate_op.profile = self.profile
        generate_op.group_name = group.group_name

        box.separator(type="LINE")

        flow = box.grid_flow(
            row_major=True,
            columns=0,
            even_columns=False,
            even_rows=False,
            align=True,
        )

        for shapekey in group.shapekeys:
            self.draw_shapekey_item(
                flow, collection, shapekey, detected_shapekeys
            )

    def draw_batch_export_settings(
        self, layout: UILayout, context: Context, profile: Profile
    ) -> None:

        header, body = layout.panel("Shapes", default_closed=False)
        # header.label(text="Shapes", icon="SHAPEKEY_DATA")
        header.prop(
            self,
            "batch_export",
            text="Batch Shape Export",
        )

        if not context.collection:
            return
        if not body:
            return

        body.enabled = self.batch_export
        shapekeys = collection_shapekeys(context.collection)
        for group in profile.groups:
            self.draw_group(body, context.collection, group, shapekeys)


class IO_FH_mdl(FileHandler):
    bl_idname: str = "IO_FH_mdl"
    bl_label: str = "FFXIV Mod"
    bl_export_operator = ExportFFXIV.bl_idname
    bl_file_extensions = ""


CLASSES = [ExportFFXIV, IO_FH_mdl]
