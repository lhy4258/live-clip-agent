import unittest

from app.db.init_sql import build_init_sql, split_sql_statements


class DatabaseInitSqlTest(unittest.TestCase):
    def test_build_init_sql_contains_all_runtime_tables(self):
        sql = build_init_sql()

        for table_name in [
            "source_videos",
            "transcript_segments",
            "video_clips",
            "clip_reviews",
            "publish_plans",
            "agent_tasks",
            "ai_call_logs",
            "chain_runs",
        ]:
            self.assertIn(f"CREATE TABLE IF NOT EXISTS {table_name}", sql)

        self.assertIn("CREATE INDEX IF NOT EXISTS ix_transcript_segments_video_time", sql)
        self.assertIn("error_json JSONB NOT NULL DEFAULT '{}'::jsonb", sql)
        self.assertIn("ALTER TABLE agent_tasks", sql)
        self.assertIn("export_status TEXT NOT NULL DEFAULT 'not_started'", sql)
        self.assertIn("is_editable BOOLEAN NOT NULL DEFAULT false", sql)
        self.assertIn("edit_suggestion TEXT NOT NULL DEFAULT ''", sql)
        self.assertIn("edit_reason TEXT NOT NULL DEFAULT ''", sql)
        self.assertIn("WHERE status = 'needs_edit'", sql)
        self.assertIn("clip_file_uri TEXT", sql)
        self.assertIn("export_error TEXT", sql)
        self.assertIn("exported_at TIMESTAMPTZ", sql)
        self.assertIn("ALTER TABLE video_clips", sql)
        self.assertNotIn("__", sql)

    def test_split_sql_statements_returns_executable_statements(self):
        statements = split_sql_statements("CREATE TABLE a(id TEXT); \n\n CREATE INDEX b ON a(id);")

        self.assertEqual(statements, ["CREATE TABLE a(id TEXT)", "CREATE INDEX b ON a(id)"])


if __name__ == "__main__":
    unittest.main()
