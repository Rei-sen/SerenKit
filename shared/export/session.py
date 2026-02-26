from collections.abc import Generator
from typing import Iterable, Optional, Any, Union
from pathlib import Path

from bpy.types import Collection


from .fbx_exporter import FBXExportRunner
from .mdl_converter import MDLExportRunner
from .runner import ExportRunner
from .progress import ProgressStage
from .export_progress import ProgressReporter

from ..cancel import CancelToken, Cancelled
from ..export_context import CollectionExportInfo

from ...properties.export_properties import ExportSettings


class ExportSession:
    """Manages the state and execution of an export process across multiple collections."""

    export_root: Path
    cfg: ExportSettings
    progress_reporter: Optional[ProgressReporter]
    _current_gen: Optional[Generator[ProgressStage, None, None]]
    cancel_token: CancelToken
    textools_dir: Optional[Path]

    def __init__(
        self,
        export_root: Path,
        cfg: ExportSettings,
        progress_reporter: Optional[ProgressReporter] = None,
    ) -> None:
        self.export_root: Path = export_root
        self.cfg: ExportSettings = cfg
        self.progress_reporter = progress_reporter

        self.cancel_token: CancelToken = CancelToken()

        self._current_gen = None

        self.textools_dir: Optional[Path] = None

    def _create_runner(self, collection: Collection) -> ExportRunner:
        runner_cls = create_runner(self.cfg)
        return runner_cls(
            collection_info=CollectionExportInfo(collection),
            export_settings=self.cfg,
            cancel_token=self.cancel_token,
            progress_reporter=self.progress_reporter,
            textools_dir=self.textools_dir,
        )

    def start(self, collections: Iterable[Collection]) -> None:
        self._current_gen = self._iterate_collections(collections)

    def _iterate_collections(
        self, collections: Iterable[Collection]
    ) -> Generator[ProgressStage, None, None]:
        if not self.progress_reporter:
            raise RuntimeError("ExportSession requires a ProgressReporter")

        infos = [CollectionExportInfo(c) for c in collections]
        total = 0
        for info in infos:
            total += info.variant_count

        self.progress_reporter.set_total_variant_count(total)
        self.progress_reporter.set_total_collection_count(len(infos))

        for info in infos:
            try:
                self.progress_reporter.start_new_collection(
                    info.collection.name, info.variant_count
                )

                yield from self._process_single_collection(info)
            except Cancelled:
                return
            except StopIteration:
                pass

    def _process_single_collection(
        self,
        info: CollectionExportInfo,
    ) -> Generator[ProgressStage, None, None]:
        runner = self._create_runner(info.collection)

        collection_export_dir = self.export_root / info.collection.name

        collection_export_dir.mkdir(parents=True, exist_ok=True)

        runner.start(info, collection_export_dir)

        try:
            yield from runner.step()
        except StopIteration:
            pass
        finally:
            runner.stop()
            self._current_runner = None

    def step(self) -> Generator[ProgressStage, None, None]:
        if not self._current_gen:
            raise RuntimeError(
                "Session not started; call `start()` before stepping"
            )

        return self._current_gen

    def next(self) -> ProgressStage:
        """Advance the session by one step and return the current stage."""
        if not self._current_gen:
            raise RuntimeError(
                "Session not started; call `start()` before stepping"
            )
        return next(self._current_gen)

    def cancel(self) -> None:
        self.cancel_token.request()
        if self._current_gen:
            self._current_gen.close()
        self._current_gen = None
        self._current_runner = None

    def is_cancelled(self) -> bool:
        return self.cancel_token.requested


def create_runner(cfg_or_mode: Union[str, Any]) -> type[ExportRunner]:
    """Factory function to create an ExportRunner based on the export mode specified in cfg_or_mode."""
    mode = None
    if isinstance(cfg_or_mode, str):
        mode = cfg_or_mode
    else:
        mode = getattr(cfg_or_mode, "export_mode", None)

    if mode == "FBX_ONLY":
        return FBXExportRunner
    return MDLExportRunner
