from __future__ import annotations

import csv
import io
import json
from dataclasses import asdict, dataclass


CSV_COLUMNS = ["clip_id", "platform", "title", "description", "hashtags", "start_sec", "end_sec", "status"]


@dataclass(frozen=True)
class PublishPlanExportRow:
    clip_id: str
    platform: str
    title: str
    description: str
    hashtags: list[str]
    start_sec: float
    end_sec: float
    status: str


def export_publish_plans_csv(rows: list[PublishPlanExportRow]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=CSV_COLUMNS, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        payload = asdict(row)
        payload["hashtags"] = ",".join(row.hashtags)
        writer.writerow(payload)
    return output.getvalue()


def export_publish_plans_json(rows: list[PublishPlanExportRow]) -> str:
    return json.dumps([asdict(row) for row in rows], ensure_ascii=False, indent=2)
