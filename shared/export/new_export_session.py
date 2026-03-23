from pathlib import Path
import time
from typing import Iterable, Optional

import bpy
from bpy.types import Collection, Mesh, Object

from .preprocessing import run_preprocessing
from .result import ExportResult
from .progress import compute_total_progress, estimate_eta_seconds
from .progress_sidecar import ProgressSidecar
from .data import override_objects_data
from .shapekey_utils import (
    apply_variant_shapekeys,
    apply_variant_shapekeys_to_objects,
    restore_shapekey_config,
    save_shapekey_config,
)
from .settings import ExportSettings

from ..textools_adapter import TextoolsAdapter
from ..profile import NamePair
from ..variants import detect_export_alias
from ..logging import log_error


class NewExportSession:

    export_settings: ExportSettings
    export_result: ExportResult
    _sidecar: ProgressSidecar
    _start_time: Optional[float]

    def __init__(self, export_settings: ExportSettings) -> None:
        self.export_settings = export_settings
        self.export_result = ExportResult()
        self._sidecar = ProgressSidecar()
        self._start_time = None

    def _emit(
        self,
        variant_index: int,
        variant_total: int,
        stage_progress: float,
        message: str,
    ) -> None:
        total_progress = compute_total_progress(
            variant_index=variant_index,
            variant_total=variant_total,
            stage_progress=stage_progress,
        )
        elapsed = self._elapsed_seconds()
        eta = estimate_eta_seconds(
            total_progress=total_progress,
            elapsed_seconds=elapsed,
        )

        self._sidecar.emit_progress(
            variant_index=variant_index,
            variant_total=variant_total,
            stage_progress=stage_progress,
            message=message,
            elapsed_seconds=elapsed,
            eta_seconds=eta,
        )

    def start(self, collection_name: str) -> None:
        self._start_time = time.monotonic()
        self._sidecar.run_started(
            title=f"SerenKit Export - {collection_name}",
            collection=collection_name,
            profile=self.export_settings.profile.profile_name,
        )

    def _elapsed_seconds(self) -> float:
        if self._start_time is None:
            return 0.0
        elapsed = time.monotonic() - self._start_time
        if elapsed < 0.0:
            return 0.0
        return elapsed

    def fail(self, message: str) -> None:
        self._sidecar.run_failed(message)

    def complete(self) -> None:
        mdl_count = len(self.export_result.mdl_files)
        fbx_count = len(self.export_result.fbx_files)
        summary = (
            f"Done - {mdl_count} MDL file(s)"
            if mdl_count
            else f"Done - {fbx_count} FBX file(s)"
        )
        self._sidecar.run_finished(summary)

    def prepare_collection_for_export(self) -> None:
        dir = self.export_settings.export_root_dir

        dir.mkdir(parents=True, exist_ok=True)

    def export_mesh_variants(
        self, collection: Collection, variants: Iterable[Iterable[NamePair]]
    ) -> ExportResult:

        variant_list = list(variants)
        total = len(variant_list)

        mannequin_state = dict()

        if self.export_settings.mannequin:
            mannequin_state = save_shapekey_config(
                self.export_settings.mannequin
            )

        try:
            for idx, variant in enumerate(variant_list):
                self.export_variant(collection, variant, idx, total)

        finally:
            if self.export_settings.mannequin:
                restore_shapekey_config(
                    self.export_settings.mannequin, mannequin_state
                )

        return self.export_result

    def export_variant(
        self,
        collection: Collection,
        variant: Iterable[NamePair],
        variant_index: int = 0,
        variant_total: int = 1,
    ) -> None:
        def emit(stage_progress: float, message: str) -> None:
            self._emit(variant_index, variant_total, stage_progress, message)

        variant_shapekeys: set[str] = set()
        shapekeys_names: list[str] = []

        emit(0.0, "Applying shapekeys...")
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

        name = self.build_export_name(shapekeys_names)
        output_path = Path(self.export_settings.export_root_dir) / name

        # Duplicate mesh data only for the preprocessing/export window.

        mesh_objects = [obj for obj in collection.objects if obj.type == "MESH"]

        with override_objects_data(mesh_objects):
            emit(0.1, "Preprocessing...")
            self.run_preprocessing(collection)

            emit(0.2, f"Exporting FBX: {name}...")
            fbx_file = self.export_fbx(collection.objects, output_path)
            self.export_result.fbx_files.append(fbx_file)

            if self.export_settings.convert_to_mdl:
                emit(0.3, f"Converting to MDL: {name}...")
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
            use_custom_props=False,
            object_types={"MESH", "ARMATURE"},
        )

        return output_fbx

    def convert_to_mdl(self, path: Path, objects: Iterable[Object]) -> Path:
        fbx_name = path.with_suffix(".fbx")
        mdl_name = path.with_suffix(".mdl")

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
