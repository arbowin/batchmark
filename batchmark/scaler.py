"""scaler.py — scale elapsed times in BatchResults by a numeric factor or unit conversion.

Useful for converting raw seconds to milliseconds, normalizing time units
across heterogeneous benchmark sources, or stress-testing analysis pipelines
with artificially inflated/deflated timings.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from batchmark.runner import BatchResult, RunResult

# ---------------------------------------------------------------------------
# Predefined unit multipliers (from seconds)
# ---------------------------------------------------------------------------

UNIT_MULTIPLIERS: dict[str, float] = {
    "s": 1.0,
    "ms": 1_000.0,
    "us": 1_000_000.0,
    "ns": 1_000_000_000.0,
    "min": 1.0 / 60.0,
}


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class ScaledBatch:
    """A BatchResult whose elapsed times have been multiplied by *factor*."""

    original: BatchResult
    scaled: BatchResult
    factor: float
    unit: Optional[str]  # None when an arbitrary factor was supplied

    @property
    def label(self) -> str:  # convenience passthrough
        return self.scaled.label


@dataclass
class ScaleResult:
    """Collection of ScaledBatch objects produced by a single scaling pass."""

    batches: List[ScaledBatch] = field(default_factory=list)
    factor: float = 1.0
    unit: Optional[str] = None

    @property
    def count(self) -> int:
        return len(self.batches)


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------

def _scale_run(run: RunResult, factor: float) -> RunResult:
    """Return a new RunResult with *elapsed* multiplied by *factor*."""
    return RunResult(
        elapsed=run.elapsed * factor,
        returncode=run.returncode,
        stdout=run.stdout,
        stderr=run.stderr,
    )


def scale_batch(batch: BatchResult, factor: float, unit: Optional[str] = None) -> ScaledBatch:
    """Scale every run in *batch* by *factor* and return a ScaledBatch.

    Args:
        batch:  The source BatchResult.
        factor: Multiplicative factor applied to each elapsed time.
        unit:   Optional human-readable unit label (e.g. ``"ms"``).  When
                supplied via :func:`scale_unit` this is set automatically.

    Returns:
        A :class:`ScaledBatch` containing both the original and scaled data.
    """
    if factor <= 0:
        raise ValueError(f"factor must be positive, got {factor}")

    scaled_runs = [_scale_run(r, factor) for r in batch.runs]
    scaled = BatchResult(label=batch.label, runs=scaled_runs)
    return ScaledBatch(original=batch, scaled=scaled, factor=factor, unit=unit)


def scale_all(
    batches: List[BatchResult],
    factor: float,
    unit: Optional[str] = None,
) -> ScaleResult:
    """Apply :func:`scale_batch` to every batch in *batches*.

    Args:
        batches: List of BatchResult objects to scale.
        factor:  Multiplicative factor.
        unit:    Optional unit label propagated to each :class:`ScaledBatch`.

    Returns:
        A :class:`ScaleResult` containing all scaled batches.
    """
    result = ScaleResult(factor=factor, unit=unit)
    for b in batches:
        result.batches.append(scale_batch(b, factor, unit))
    return result


def scale_unit(batches: List[BatchResult], unit: str) -> ScaleResult:
    """Convenience wrapper that looks up *unit* in :data:`UNIT_MULTIPLIERS`.

    Args:
        batches: List of BatchResult objects whose times are in **seconds**.
        unit:    Target unit string — one of ``"s"``, ``"ms"``, ``"us"``,
                 ``"ns"``, or ``"min"``.

    Returns:
        A :class:`ScaleResult` with times expressed in *unit*.

    Raises:
        KeyError: If *unit* is not a recognised multiplier key.
    """
    if unit not in UNIT_MULTIPLIERS:
        raise KeyError(
            f"Unknown unit {unit!r}. Choose from: {sorted(UNIT_MULTIPLIERS)}"
        )
    factor = UNIT_MULTIPLIERS[unit]
    return scale_all(batches, factor=factor, unit=unit)


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

def format_scale_result(result: ScaleResult) -> str:
    """Return a human-readable summary of a :class:`ScaleResult`."""
    unit_label = result.unit if result.unit else f"×{result.factor}"
    lines: List[str] = [
        f"Scaled {result.count} batch(es) — factor: {result.factor} ({unit_label})",
        "-" * 52,
    ]
    for sb in result.batches:
        orig_times = [r.elapsed for r in sb.original.runs]
        new_times = [r.elapsed for r in sb.scaled.runs]
        if orig_times:
            orig_mean = sum(orig_times) / len(orig_times)
            new_mean = sum(new_times) / len(new_times)
            lines.append(
                f"  {sb.label:<30}  {orig_mean:.4f} → {new_mean:.4f} {unit_label}"
            )
        else:
            lines.append(f"  {sb.label:<30}  (no runs)")
    return "\n".join(lines)
