from shared.export.progress import compute_total_progress, estimate_eta_seconds
from shared.export.progress_sidecar import _render_bar, ProgressSidecar


# ---------------------------------------------------------------------------
# compute_total_progress
# ---------------------------------------------------------------------------


def test_total_progress_zero_variants():
    total = compute_total_progress(
        variant_index=0,
        variant_total=0,
        stage_progress=0.5,
    )
    assert total == 0.0


def test_total_progress_first_variant_midway():
    # variant 0 of 4, halfway through the stage → 0/4 + 0.5/4 = 0.125
    total = compute_total_progress(
        variant_index=0,
        variant_total=4,
        stage_progress=0.5,
    )
    assert total == 0.125


def test_total_progress_last_variant_complete():
    # variant 3 of 4, stage done → 3/4 + 1.0/4 = 1.0
    total = compute_total_progress(
        variant_index=3,
        variant_total=4,
        stage_progress=1.0,
    )
    assert total == 1.0


def test_total_progress_clamps_to_one():
    # Overrun should be clamped.
    total = compute_total_progress(
        variant_index=5,
        variant_total=4,
        stage_progress=1.0,
    )
    assert total == 1.0


def test_total_progress_single_variant():
    # 1 variant, stage 50% → total 0.0 + 0.5/1 = 0.5
    total = compute_total_progress(
        variant_index=0,
        variant_total=1,
        stage_progress=0.5,
    )
    assert total == 0.5


def test_total_progress_clamps_negative():
    total = compute_total_progress(
        variant_index=0,
        variant_total=4,
        stage_progress=-3.0,
    )
    assert total == 0.0


# ---------------------------------------------------------------------------
# estimate_eta_seconds
# ---------------------------------------------------------------------------


def test_eta_none_at_zero_progress():
    eta = estimate_eta_seconds(total_progress=0.0, elapsed_seconds=10.0)
    assert eta is None


def test_eta_zero_when_complete():
    eta = estimate_eta_seconds(total_progress=1.0, elapsed_seconds=10.0)
    assert eta == 0.0


def test_eta_estimation_midway():
    # 25% complete after 20s => total 80s => remaining 60s
    eta = estimate_eta_seconds(total_progress=0.25, elapsed_seconds=20.0)
    assert eta == 60.0


# ---------------------------------------------------------------------------
# _render_bar
# ---------------------------------------------------------------------------


def test_render_bar_empty():
    assert _render_bar(0.0, width=10) == "[----------]"


def test_render_bar_full():
    assert _render_bar(1.0, width=10) == "[##########]"


def test_render_bar_half():
    assert _render_bar(0.5, width=10) == "[#####-----]"


def test_render_bar_clamps_overflow():
    assert _render_bar(2.0, width=5) == "[#####]"


def test_render_bar_clamps_negative():
    assert _render_bar(-1.0, width=5) == "[-----]"


# ---------------------------------------------------------------------------
# sidecar formatting behavior
# ---------------------------------------------------------------------------


class _CaptureSidecar(ProgressSidecar):
    """Capture writes/progress lines without launching a real process."""

    def __init__(self):
        super().__init__()
        self.progress_lines: list[str] = []
        self.static_lines: list[str] = []

    def start(self, title: str = "") -> None:
        self.write(f"=== {title} ===")

    def progress(self, line: str) -> None:
        self.progress_lines.append(line)

    def write(self, line: str) -> None:
        self.static_lines.append(line)

    def finish(self) -> None:
        pass


def test_emit_progress_uses_progress_not_write():
    cap = _CaptureSidecar()
    cap.emit_progress(
        variant_index=1,
        variant_total=3,
        stage_progress=0.0,
        message="Preprocessing...",
    )

    assert len(cap.progress_lines) == 1
    assert len(cap.static_lines) == 0


def test_emit_progress_formats_line():
    cap = _CaptureSidecar()
    cap.emit_progress(
        variant_index=1,
        variant_total=3,
        stage_progress=0.0,
        message="Preprocessing...",
    )

    line = cap.progress_lines[0]
    assert "2/3" in line
    assert "preprocessing..." in line.lower()
    assert "Preprocessing..." in line
    assert "[" in line and "]" in line


def test_emit_progress_pct_shown():
    cap = _CaptureSidecar()
    cap.emit_progress(
        variant_index=0,
        variant_total=1,
        stage_progress=0.0,
        message="Exporting FBX...",
    )

    assert "0%" in cap.progress_lines[0]


def test_emit_progress_includes_elapsed_and_eta():
    cap = _CaptureSidecar()
    cap.emit_progress(
        variant_index=0,
        variant_total=2,
        stage_progress=0.5,
        message="Exporting FBX...",
        elapsed_seconds=12.0,
        eta_seconds=30.0,
    )

    line = cap.progress_lines[0]
    assert "elapsed 0:12" in line
    assert "eta 0:30" in line


def test_format_duration_hours():
    assert _CaptureSidecar._format_duration(3661.0) == "1:01:01"


def test_run_started_writes_header_block():
    cap = _CaptureSidecar()
    cap.run_started(
        title="SerenKit Export - TestCollection",
        collection="TestCollection",
        profile="Bibo",
    )

    assert cap.static_lines[0] == "=== SerenKit Export - TestCollection ==="
    assert "Collection : TestCollection" in cap.static_lines
    assert "Profile    : Bibo" in cap.static_lines


def test_run_finished_writes_summary():
    cap = _CaptureSidecar()
    cap.run_finished("Done - 1 MDL file(s)")

    assert cap.static_lines[-2] == "-" * 60
    assert cap.static_lines[-1] == "Done - 1 MDL file(s)"
