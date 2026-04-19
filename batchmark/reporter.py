"""HTML and text report generation for batchmark results."""

from dataclasses import dataclass
from typing import List, Optional
from batchmark.runner import BatchResult
from batchmark.stats import summarize
from batchmark.formatter import format_summary, format_table
from batchmark.comparator import compare, format_comparison


@dataclass
class Report:
    title: str
    sections: List[str]

    def to_text(self) -> str:
        divider = "=" * 60
        parts = [divider, self.title, divider]
        for section in self.sections:
            parts.append(section)
            parts.append("")
        return "\n".join(parts)

    def to_html(self) -> str:
        rows = "".join(f"<pre>{s}</pre>" for s in self.sections)
        return (
            f"<!DOCTYPE html><html><head><title>{self.title}</title>"
            f"<style>body{{font-family:monospace;padding:2em}}"
            f"pre{{background:#f4f4f4;padding:1em;border-radius:4px}}</style>"
            f"</head><body><h1>{self.title}</h1>{rows}</body></html>"
        )


def build_report(results: List[BatchResult], title: str = "Batchmark Report") -> Report:
    if not results:
        raise ValueError("No results to report")

    sections = []

    summaries = [summarize(r) for r in results]
    table = format_table(summaries)
    sections.append("## Summary Table\n" + table)

    for r in results:
        s = summarize(r)
        sections.append(format_summary(s))

    if len(results) > 1:
        comparison = compare(results)
        sections.append("## Comparison\n" + format_comparison(comparison))

    return Report(title=title, sections=sections)


def save_report(report: Report, path: str, fmt: str = "text") -> None:
    content = report.to_html() if fmt == "html" else report.to_text()
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
