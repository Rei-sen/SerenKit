from pathlib import Path
from typing import Generator, Optional
from bpy.types import Object, Collection, Mesh


from .naming import build_export_name
from .preprocessing import run_preprocessing
from .shapekey_utils import (
    apply_variant_shapekeys_to_collection,
    restore_shapekey_config,
    save_shapekey_config,
)
from .utils import cleanup_duplicate_collection, duplicate_collection
from .progress import ProgressStage
from .export_progress import ProgressReporter

from ..profile import NamePair
from ..cancel import CancelToken, Cancelled
from ..export_context import CollectionExportInfo

from ...properties.export_properties import ExportSettings
from ...properties.model_settings import get_modkit_collection_props


class ExportRunner:
    """Base class for export runners handling the export of a single collection across its variants."""

    collection_info: CollectionExportInfo
    textools_dir: Optional[Path]
    export_settings: ExportSettings
    cancel_token: CancelToken
    generator: Optional[Generator[ProgressStage, None, None]]
    progress_reporter: Optional[ProgressReporter]

    def __init__(
        self,
        collection_info: CollectionExportInfo,
        export_settings: ExportSettings,
        cancel_token: CancelToken,
        progress_reporter: Optional[ProgressReporter],
        textools_dir: Optional[Path] = None,
    ) -> None:
        self.collection_info = collection_info
        self.textools_dir = textools_dir
        self.export_settings = export_settings
        self.cancel_token = cancel_token
        self.progress_reporter = progress_reporter

    def export(self, fbx_path: Path, objects: list[Object]) -> None: ...

    def start(
        self,
        info: CollectionExportInfo,
        export_root: Path,
    ) -> None:
        """Prepare the runner for exporting a collection by initializing the internal generator."""
        if not self.export_settings:
            raise RuntimeError("ExportRunner missing config or context")

        self.generator = self._iterate_variants(info, export_root)

    def step(self) -> Generator[ProgressStage, None, None]:
        """Advance the internally-stored generator by one yield and return the stage."""
        if not self.generator:
            raise RuntimeError(
                "Runner not started; call `start()` or use `run_generator()`"
            )
        yield from self.generator

    def next(self) -> ProgressStage:
        """Advance the internally-stored generator by one yield and return the stage."""
        if not self.generator:
            raise RuntimeError(
                "Runner not started; call `start()` or use `run_generator()`"
            )
        return next(self.generator)

    def stop(self) -> None:
        """Stop the internal generator if present and clear stored state."""
        if self.generator:
            self.generator.close()
            self.generator = None

    def _iterate_variants(
        self,
        info: CollectionExportInfo,
        export_dir: Path,
    ) -> Generator[ProgressStage, None, None]:
        """Generator iterating through the export process for each variant of a collection, yielding stage events."""

        mannequin = None
        # ensure collection props are loaded
        props = get_modkit_collection_props(info.collection)
        if props:
            mannequin = props.model.mannequin_object

        original_shape_keys = None
        if mannequin and isinstance(mannequin.data, Mesh):
            original_shape_keys = save_shapekey_config(mannequin.data)

        try:
            for variant in info.variants:
                for stage in self._process_single_variant(
                    info, export_dir, variant
                ):
                    yield stage

        finally:
            if (
                original_shape_keys
                and mannequin
                and isinstance(mannequin.data, Mesh)
            ):
                restore_shapekey_config(mannequin.data, original_shape_keys)

    def is_ready(self) -> tuple[bool, Optional[str]]:
        """Check if the runner is ready to start the export process,
        validating necessary conditions and returning an error message if not.
        """
        return True, None

    def requires_game_path(self) -> bool:
        """Whether this export runner requires a game path to be set."""
        return False

    def _process_single_variant(
        self,
        info: CollectionExportInfo,
        export_dir: Path,
        variant: list[NamePair],
    ) -> Generator[ProgressStage, None, None]:
        """Process a single variant of a collection, performing duplication,
        shape-key application, preprocessing and export steps,
        while yielding progress stages.
        """

        if self.progress_reporter:
            self.progress_reporter.increment_variant_index()

        yield ProgressStage.DUPLICATE
        dup = duplicate_collection(info.collection)

        self._check_cancel()

        try:
            yield from self._run_variant_steps(
                dup,
                info,
                export_dir,
                variant,
            )
        finally:
            cleanup_duplicate_collection(dup)

    def _run_variant_steps(
        self,
        dup: Collection,
        info: CollectionExportInfo,
        export_dir: Path,
        variant: list[NamePair],
    ) -> Generator[ProgressStage, None, None]:
        """Run the steps for processing a single variant,
        yielding progress stages between steps.
        """
        variant_shapekeys: set[str] = set()
        shapekeys_names: list[str] = []
        for shapekey, name in variant:
            variant_shapekeys.add(shapekey)
            shapekeys_names.append(name)

        # Apply shapekeys
        yield ProgressStage.APPLY_SHAPEKEYS

        profile_data = info.profile
        if profile_data is None:
            raise RuntimeError(
                "Variant profile data is required for applying shape keys"
            )

        apply_variant_shapekeys_to_collection(
            dup, profile_data, variant_shapekeys
        )

        self._check_cancel()

        yield ProgressStage.PREPROCESS

        run_preprocessing(info, list(dup.objects))

        self._check_cancel()

        # Export
        name = build_export_name(self.export_settings, info, shapekeys_names)
        fbx_path: Path = Path(export_dir) / name

        yield ProgressStage.EXPORT

        self.export(fbx_path, list(dup.objects))

        yield ProgressStage.VARIANT

    def _check_cancel(self) -> None:
        """Raise `Cancelled` if a cancel has been requested on the token."""

        if self.cancel_token.requested:
            raise Cancelled()
