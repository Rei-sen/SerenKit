from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Optional

from .progress import compute_total_progress


class ProgressSidecar:
    """Streams export progress to a dedicated console window via stdin pipe.

    On Windows a new console window is opened for the reader process.
    On other platforms progress falls back to stdout.

    - ``write(line)``                      - static line with newline
    - ``progress(line)``                   - in-place progress line
    - ``emit_progress(...)``               - primitive progress update
    - ``run_started(title, ...)``          - writes export header block
    - ``run_finished(summary)``            - writes summary and closes pipe
    - ``run_failed(message)``              - writes error and closes pipe
    - ``finish()`` / ``close()``           - close child stdin pipe
    """

    _proc: Optional[subprocess.Popen[bytes]]

    def __init__(self) -> None:
        self._proc = None

    def start(self, title: str = "SerenKit Export") -> None:
        """Launch the checked-in reader script and print an initial title line."""
        root = Path(__file__).resolve().parents[2]
        reader_path = root / "scripts" / "export_progress_sidecar_reader.py"

        if sys.platform == "win32":
            try:
                self._proc = subprocess.Popen(
                    [sys.executable, str(reader_path)],
                    stdin=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                )
            except OSError:
                self._proc = None

        self.write(f"=== {title} ===")

    @staticmethod
    def _pipe_write(
        proc: Optional[subprocess.Popen[bytes]],
        data: bytes,
        close: bool = False,
    ) -> None:
        if proc is None or proc.stdin is None or proc.poll() is not None:
            return
        try:
            proc.stdin.write(data)
            proc.stdin.flush()
            if close:
                proc.stdin.close()
        except OSError:
            pass

    def _send(self, kind: str, text: str) -> None:
        proc = self._proc
        encoded = f"{kind}:{text}\n".encode("utf-8")
        # No-op when the sidecar process is unavailable or has terminated.
        if proc is None:
            return
        self._pipe_write(proc, encoded)

    def write(self, line: str) -> None:
        """Print a static line with newline in the sidecar."""
        self._send("s", line)

    def progress(self, line: str) -> None:
        """Update the in-place progress line in the sidecar."""
        self._send("p", line)

    def finish(self) -> None:
        """Signal DONE and close the child stdin pipe."""
        proc = self._proc
        if proc is not None:
            self._pipe_write(proc, b"DONE\n", close=True)

    def run_started(
        self,
        title: str,
        collection: str,
        profile: str,
    ) -> None:
        """Emit standard export header lines."""
        self.start(title)
        self.write(f"Collection : {collection}")
        self.write(f"Profile    : {profile}")
        self.write("-" * 60)

    def emit_progress(
        self,
        variant_index: int,
        variant_total: int,
        stage_progress: float,
        message: str,
        elapsed_seconds: float | None = None,
        eta_seconds: float | None = None,
    ) -> None:
        """Render one progress update from primitive values."""
        progress = compute_total_progress(
            variant_index=variant_index,
            variant_total=variant_total,
            stage_progress=stage_progress,
        )
        bar = _render_bar(progress)
        percent = progress * 100
        timing_bits: list[str] = []
        if elapsed_seconds is not None:
            timing_bits.append(
                f"elapsed {self._format_duration(elapsed_seconds)}"
            )
        if eta_seconds is not None:
            timing_bits.append(f"eta {self._format_duration(eta_seconds)}")

        timing = ""
        if timing_bits:
            timing = "  [" + " | ".join(timing_bits) + "]"

        line = (
            f"[{variant_index + 1:>3}/{variant_total}]"
            f"  {bar} {percent:>3.1f}%"
            f"  {message}"
            f"{timing}"
        )
        self.progress(line)

    @staticmethod
    def _format_duration(seconds: float) -> str:
        """Format seconds as h:mm:ss or m:ss."""
        if seconds < 0.0:
            seconds = 0.0
        total = int(round(seconds))
        hours, rem = divmod(total, 3600)
        minutes, secs = divmod(rem, 60)
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes}:{secs:02d}"

    def run_finished(self, summary: str) -> None:
        """Emit summary and close the sidecar stream."""
        self.write("-" * 60)
        self.write(summary)
        self.finish()

    def run_failed(self, message: str) -> None:
        """Emit failure and close the sidecar stream."""
        self.write("")
        self.write(f"Export FAILED: {message}")
        self.finish()

    def close(self) -> None:
        """Alias for finish()."""
        self.finish()


def _render_bar(fraction: float, width: int = 20) -> str:
    filled = max(0, min(width, int(fraction * width)))
    return "[" + "#" * filled + "-" * (width - filled) + "]"
