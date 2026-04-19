"""Pipeline: orchestrate benchmark run → filter → annotate → export."""
from typing import List, Optional, Dict
from batchmark.runner import BatchResult, benchmark_command
from batchmark.filter import FilterCriteria, filter_results
from batchmark.annotator import AnnotatedResult, annotate, build_index, AnnotationIndex
from batchmark.exporter import export


def run_pipeline(
    commands: List[str],
    iterations: int = 5,
    criteria: Optional[FilterCriteria] = None,
    notes_map: Optional[Dict[str, List[str]]] = None,
    export_path: Optional[str] = None,
    export_fmt: str = "json",
) -> AnnotationIndex:
    """
    Full pipeline:
      1. Benchmark each command.
      2. Optionally filter results.
      3. Annotate with notes.
      4. Optionally export.
      5. Return AnnotationIndex.
    """
    results: List[BatchResult] = [
        benchmark_command(cmd, iterations) for cmd in commands
    ]

    if criteria is not None:
        results = filter_results(results, criteria)

    notes_map = notes_map or {}
    annotated: List[AnnotatedResult] = [
        annotate(r, notes_map.get(r.label, [])) for r in results
    ]

    if export_path:
        export(results, export_path, fmt=export_fmt)

    return build_index(annotated)
