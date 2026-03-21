def compute_total_progress(
    variant_index: int,
    variant_total: int,
    stage_progress: float,
) -> float:
    """Compute normalized overall progress in range [0.0, 1.0]."""
    if variant_total <= 0:
        return 0.0

    raw = variant_index / variant_total + stage_progress / variant_total
    if raw < 0.0:
        return 0.0
    if raw > 1.0:
        return 1.0
    return raw


def estimate_eta_seconds(
    total_progress: float,
    elapsed_seconds: float,
) -> float | None:
    """Estimate remaining seconds from elapsed time and normalized progress.

    Returns None when there is insufficient information (progress <= 0) or
    when progress is already complete.
    """
    if elapsed_seconds < 0.0:
        elapsed_seconds = 0.0

    if total_progress <= 0.0:
        return None
    if total_progress >= 1.0:
        return 0.0

    remaining_ratio = (1.0 - total_progress) / total_progress
    return elapsed_seconds * remaining_ratio
