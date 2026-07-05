import csv
import io
import json
import unittest

from app.services.exporter import PublishPlanExportRow, export_publish_plans_csv, export_publish_plans_json


class PublishPlanExporterTest(unittest.TestCase):
    def test_exports_publish_plans_as_csv_with_stable_columns(self):
        rows = [
            PublishPlanExportRow(
                clip_id="clip-1",
                platform="douyin",
                title="三步拆出高转化直播切片",
                description="从痛点、价值、行动建议拆解切片。",
                hashtags=["直播切片", "内容运营"],
                start_sec=12,
                end_sec=58,
                status="approved",
            )
        ]

        content = export_publish_plans_csv(rows)
        parsed = list(csv.DictReader(io.StringIO(content)))

        self.assertEqual(
            list(parsed[0].keys()),
            ["clip_id", "platform", "title", "description", "hashtags", "start_sec", "end_sec", "status"],
        )
        self.assertEqual(parsed[0]["hashtags"], "直播切片,内容运营")

    def test_exports_publish_plans_as_json(self):
        rows = [
            PublishPlanExportRow(
                clip_id="clip-1",
                platform="wechat_channels",
                title="直播复盘的切片方法",
                description="用时间轴定位高价值片段。",
                hashtags=["复盘"],
                start_sec=20,
                end_sec=70,
                status="approved",
            )
        ]

        content = export_publish_plans_json(rows)
        payload = json.loads(content)

        self.assertEqual(payload[0]["clip_id"], "clip-1")
        self.assertEqual(payload[0]["hashtags"], ["复盘"])


if __name__ == "__main__":
    unittest.main()
