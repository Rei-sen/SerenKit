from pathlib import Path
from typing import Iterable

import bpy
from bpy.types import Collection, Mesh, Object

from .preprocessing import run_preprocessing
from .result import ExportResult

from .data import override_objects_data
from .shapekey_utils import (
    apply_variant_shapekeys,
    apply_variant_shapekeys_to_objects,
    restore_shapekey_config,
    save_shapekey_config,
)
from .settings import ExportSettings

from ..textools_adapter import TextoolsAdapter
from ..mdl.exporter import export_blender_objects_to_mdl
from ..profile import NamePair
from ..variants import detect_export_alias
from ..logging import log_error


class NewExportSession:

    export_settings: ExportSettings
    export_result: ExportResult

    def __init__(self, export_settings: ExportSettings):
        self.export_settings = export_settings
        self.export_result = ExportResult()

    def start(self) -> None:
        return

    def prepare_collection_for_export(self) -> None:
        dir = self.export_settings.export_root_dir

        dir.mkdir(parents=True, exist_ok=True)

    def export_mesh_variants(
        self, collection: Collection, variants: Iterable[Iterable[NamePair]]
    ) -> ExportResult:

        # TODO: Save mannequin shapekeys
        mannequin_state = dict()

        if self.export_settings.mannequin:
            mannequin_state = save_shapekey_config(
                self.export_settings.mannequin
            )

        try:
            for variant in variants:
                objs = [obj for obj in collection.objects if obj.type == "MESH"]

                with override_objects_data(objs):
                    self.export_variant(collection, variant)

        finally:
            if self.export_settings.mannequin:
                restore_shapekey_config(
                    self.export_settings.mannequin, mannequin_state
                )

        return self.export_result

    def export_variant(
        self, collection: Collection, variant: Iterable[NamePair]
    ) -> None:
        variant_shapekeys: set[str] = set()
        shapekeys_names: list[str] = []

        for shapekey, name in variant:
            variant_shapekeys.add(shapekey)
            shapekeys_names.append(name)

        if self.export_settings.mannequin and isinstance(
            self.export_settings.mannequin.data, Mesh
        ):
            apply_variant_shapekeys(
                self.export_settings.mannequin.data,
                self.export_settings.profile,
                variant_shapekeys,
            )

        apply_variant_shapekeys_to_objects(
            collection.objects, self.export_settings.profile, variant_shapekeys
        )

        self.run_preprocessing(collection)

        name = self.build_export_name(shapekeys_names)

        output_path = Path(self.export_settings.export_root_dir) / name

        if self.export_settings.mdl_export_mode == "direct":
            if self.export_settings.convert_to_mdl:
                mdl_file = self.convert_to_mdl(output_path, collection.objects)
                self.export_result.mdl_files.append(mdl_file)
            return

        fbx_file = self.export_fbx(collection.objects, output_path)
        self.export_result.fbx_files.append(fbx_file)

        if self.export_settings.convert_to_mdl:
            mdl_file = self.convert_to_mdl(output_path, collection.objects)
            self.export_result.mdl_files.append(mdl_file)

    def run_preprocessing(self, collection: Collection) -> None:
        run_preprocessing(self.export_settings, collection.objects)

    def build_export_name(
        self,
        variant_names: Iterable[str],
    ) -> str:
        alias, rest = detect_export_alias(
            list(variant_names), self.export_settings.profile
        )
        prefix = alias or self.export_settings.export_prefix

        variant_name = " - ".join(rest)

        result = prefix
        if variant_name:
            result += f" {variant_name}"

        return result.strip()

    @staticmethod
    def select_objects_for_export(objects: Iterable[Object]) -> None:
        bpy.ops.object.select_all(action="DESELECT")

        for o in objects:
            o.select_set(True)

        # view_layer = bpy.context.view_layer
        # if view_layer:
        #     view_layer.objects.active = objects[0]

    @staticmethod
    def make_objects_visible(objects: Iterable[Object]) -> None:
        for obj in objects:
            obj.hide_set(False)

    @staticmethod
    def export_fbx(objects: Iterable[Object], output_path: Path) -> Path:
        output_fbx = output_path.with_suffix(".fbx")
        NewExportSession.make_objects_visible(objects)
        NewExportSession.select_objects_for_export(objects)

        bpy.ops.export_scene.fbx(
            filepath=str(output_fbx),
            use_selection=True,
            apply_unit_scale=True,
            apply_scale_options="FBX_SCALE_ALL",
            add_leaf_bones=False,
            bake_anim=False,
            use_custom_props=True,
            object_types={"MESH", "ARMATURE"},
        )

        return output_fbx

    def convert_to_mdl(self, path: Path, objects: Iterable[Object]) -> Path:
        fbx_name = path.with_suffix(".fbx")
        mdl_name = path.with_suffix(".mdl")

        if self.export_settings.mdl_export_mode == "direct":
            return export_blender_objects_to_mdl(
                objects,
                mdl_name,
            )

        if not self.export_settings.textools_dir:
            raise RuntimeError(
                "Textools directory is required for MDL conversion"
            )

        adapter = TextoolsAdapter(self.export_settings.textools_dir)

        db_path = adapter.convert_fbx(fbx_name)

        mats = self.export_settings.materials_info
        attrs = self.export_settings.attributes

        adapter.apply_patches(db_path, mats, attrs)

        if self.export_settings.game_path is None:

            log_error("MDL build failed: export_settings.game_path is not set")
            raise RuntimeError("game_path is required for MDL build")

        adapter.build_mdl(db_path, mdl_name, self.export_settings.game_path)

        return mdl_name
