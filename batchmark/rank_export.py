import json
import csv
import io
from typing import List
from batchmark.ranker import RankingResult, RankedResult


def to_dict(entry: RankedResult) -> dict:
    return {
        "rank": entry.rank,
        "label": entry.label,
        "mean": entry.mean,
        "success_rate": entry.success_rate,
        "score": entry.score,
    }


def export_ranking_json(result: RankingResult) -> str:
    data = {
        "ranking": [to_dict(e) for e in result.entries],
        "best": result.best().label if result.best() else None,
        "worst": result.worst().label if result.worst() else None,
    }
    return json.dumps(data, indent=2)


def export_ranking_csv(result: RankingResult) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(
        buf, fieldnames=["rank", "label", "mean", "success_rate", "score"]
    )
    writer.writeheader()
    for entry in result.entries:
        writer.writerow(to_dict(entry))
    return buf.getvalue()


def save_ranking(result: RankingResult, path: str, fmt: str = "json") -> None:
    if fmt == "json":
        content = export_ranking_json(result)
    elif fmt == "csv":
        content = export_ranking_csv(result)
    else:
        raise ValueError(f"Unsupported format: {fmt}")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
