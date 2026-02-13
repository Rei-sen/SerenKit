"""Export collection operators."""

import os
from typing import TYPE_CHECKING, Optional, Any
from pathlib import Path

import bpy
from bpy.types import Operator, Context, Timer, Collection
from bpy.props import StringProperty

from ..shared.export.export_progress import ExportProgress
from ..shared.export.utils import collect_enabled_collections
from ..shared.cancel import Cancelled

from ..properties.export_properties import get_export_props
from ..preferences import get_addon_preferences
from ..shared.export.progress import ProgressStage
from ..shared.logging import log_warning
from ..shared.export.session import ExportSession
from ..shared.blender_typing import OperatorReturn


class MODKIT_OT_export_models(Operator):
    """Export enabled collections."""

    bl_idname: str = "modkit.export_models"
    bl_label: str = "Export All Enabled Collections"

    collection_name: StringProperty(  # type: ignore
        name="Collection Name",
        description="Name of the collection to export"
    )
    # Explicitly define runtime attributes to avoid dynamic setattr/getattr.
    _timer: Optional[Timer] = None
    _session: Optional[ExportSession] = None
    _progress_reporter: Optional[ExportProgress] = None

    def execute(self, context: Context) -> set[OperatorReturn]:
        cfg = get_export_props()
        if not cfg:
            self.report({"ERROR"}, "Export properties not found")
            return {"CANCELLED"}

        export_root = cfg.export_root_dir

        if not export_root or not os.path.isdir(export_root):
            self.report(
                {"ERROR"}, f"FBX export folder not found: {export_root}")
            return {"CANCELLED"}

        export_root = Path(export_root)

        # Create an ExportSession and reporter to orchestrate exports
        addon_pref = get_addon_preferences()
        if not addon_pref:
            self.report({"ERROR"}, "Addon preferences not found")
            return {"CANCELLED"}

        textools_path = addon_pref.textools_path
        textools_dir = Path(textools_path) if textools_path else None

        reporter = ExportProgress()

        self._progress_reporter = reporter

        self._session = ExportSession(
            export_root, cfg, progress_reporter=reporter)
        self._session.textools_dir = textools_dir

        cols: set[Collection] = set()

        if self.collection_name and self.collection_name != "":
            assert bpy.data.collections
            collection = bpy.data.collections.get(self.collection_name)

            if not collection:
                self.report(
                    {"ERROR"}, f"Collection '{self.collection_name}' not found")
                return {"CANCELLED"}

            cols = {collection}
        else:
            cols = set(collect_enabled_collections())

        self._progress_reporter.clear()
        self._session.start(cols)

        # total_variants = reporter.total_variant_count if reporter else 0
        # if total_variants > 0:
        self._begin_progress_ui(context)
        wm = context.window_manager
        assert wm
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        return {"RUNNING_MODAL"}

        # nothing to do
        self.report({"INFO"}, "No variants to export")
        return {"CANCELLED"}

    def modal(self, context: Context, event: Any) -> set[OperatorReturn]:
        # Cancel requested by user
        if event.type == 'ESC' and event.value == 'PRESS':
            self._handle_cancel(context)
            return {"CANCELLED"}

        if event.type == 'TIMER':
            session = self._session

            if not session or not getattr(session, '_current_gen', None):
                # session finished
                self._end_progress_ui(context)
                was_cancelled = session.is_cancelled() if session else False
                if was_cancelled:
                    self.report({"INFO"}, "Export cancelled")
                    return {"CANCELLED"}
                return {"FINISHED"}

            try:
                stage = session.next()
            except StopIteration:
                # session finished
                self._end_progress_ui(context)
                return {"FINISHED"}
            except Cancelled:
                # cancelled during generator
                self._end_progress_ui(context)
                self.report({"INFO"}, "Export cancelled")
                return {"CANCELLED"}
            except Exception as e:
                log_warning(f"Export session step failed: {e}")
                return {"CANCELLED"}
            if stage:
                self._update_ui(stage, context)

        return {"RUNNING_MODAL"}

    def _begin_progress_ui(self, context: Context) -> None:
        wm = context.window_manager
        assert wm
        total = 0
        if self._progress_reporter:
            total = self._progress_reporter.total_variant_count

        if total > 0:
            wm.progress_begin(0, total)

    def _end_progress_ui(self, context: Context) -> None:
        wm = context.window_manager
        assert wm is not None
        if self._timer:
            wm.event_timer_remove(self._timer)
        wm.progress_end()

        area = context.area
        assert area is not None
        area.header_text_set(None)

    def _handle_cancel(self, context: Context) -> None:
        # Ask session to cancel and clean up UI timer/progress
        try:
            if self._session:
                self._session.cancel()
        except Exception as e:
            log_warning(f"Session cancel request failed: {e}")

        self._end_progress_ui(context)

    def _build_header_text(
        self,
        reporter: Optional[ExportProgress],
        stage: Optional[ProgressStage] = None,
    ) -> str:
        # Build a concise header like: "Exporting NAME (2/5): 3/10 [stage] - msg"
        if reporter is None:
            return "Exporting..."

        idx_part = f"({reporter.collection_index}/{reporter.collection_count})"

        local_part = f"{reporter.local_idx}/{reporter.local_variant_count}"
        parts = [
            f"Exporting {reporter.collection_name}",
            f"{idx_part}:",
            local_part
        ]
        if stage:
            parts.append(f"[{stage.value}]")

        first_line = " ".join(parts)
        second_line = "Hold ESC to cancel"
        return f"{first_line}\n {second_line}"

    def _update_ui(
        self,
        stage: ProgressStage,
        context: Context
    ) -> None:
        """Update progress UI."""
        rep = self._progress_reporter

        if stage == ProgressStage.VARIANT and context.window_manager:
            wm = context.window_manager
            assert wm
            progress = rep.processed_variants if rep else 0
            wm.progress_update(progress)

        header_text = self._build_header_text(rep, stage)
        area = context.area
        assert area
        area.header_text_set(header_text)

    if TYPE_CHECKING:
        collection_name: Optional[str]


CLASSES = [
    MODKIT_OT_export_models,
]
