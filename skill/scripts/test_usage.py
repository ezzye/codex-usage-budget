import csv
import datetime as dt
import importlib.util
import json
import pathlib
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("collector", pathlib.Path(__file__).with_name("collect.py"))
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)


class UsageTests(unittest.TestCase):
    zone = dt.timezone.utc

    def event(self, kind, payload, timestamp="2026-09-02T10:00:00Z"):
        return {"timestamp": timestamp, "type": kind, "payload": payload}

    def usage(self, tokens):
        return {"input_tokens": tokens, "cached_input_tokens": tokens // 2, "output_tokens": 10,
                "reasoning_output_tokens": 3, "cache_write_input_tokens": 0, "total_tokens": tokens + 10}

    def parse(self, events, title="Sensitive first line\nprivate prompt"):
        with tempfile.TemporaryDirectory() as root:
            path = pathlib.Path(root) / "sample.jsonl"
            path.write_text("\n".join(json.dumps(event) for event in events), encoding="utf-8")
            return collector.parse_file(path, dt.datetime(2026, 9, 1, tzinfo=self.zone), self.zone,
                                        {"/private/Project": "Friendly project"}, title, True)[0]

    def base(self):
        return [self.event("session_meta", {"id": "private-thread", "cwd": "/private/Project"}),
                self.event("turn_context", {"turn_id": "turn", "model": "test-model", "effort": "low"})]

    def test_precise_usage_suppresses_same_turn_cumulative_delta(self):
        rows = self.parse(self.base() + [
            self.event("token_usage_record", {"turn_id": "turn", "usage": self.usage(100)}),
            self.event("event_msg", {"type": "token_count", "info": {"total_token_usage": self.usage(100)}})])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["total_tokens"], 110)

    def test_empty_title_is_safe(self):
        rows = self.parse(self.base() + [self.event("token_usage_record", {"turn_id": "turn", "usage": self.usage(2)})], "")
        self.assertEqual(rows[0]["task"], "Untitled task")

    def test_record_id_uses_local_date_at_utc_midnight(self):
        london = dt.timezone(dt.timedelta(hours=1))
        rows = self.parse(self.base() + [self.event("token_usage_record", {"turn_id": "turn", "usage": self.usage(2)}, "2026-09-01T23:30:00Z")])
        with tempfile.TemporaryDirectory() as root:
            path = pathlib.Path(root) / "one.jsonl"
            path.write_text("\n".join(json.dumps(event) for event in self.base() + [self.event("token_usage_record", {"turn_id": "turn", "usage": self.usage(2)}, "2026-09-01T23:30:00Z")]))
            local = collector.parse_file(path, dt.datetime(2026, 9, 1, tzinfo=london), london, {}, "", False)[0][0]
        self.assertEqual(local["date"], "2026-09-02")
        self.assertNotEqual(local["record_id"], rows[0]["record_id"])

    def test_project_map_and_optional_title_are_sanitized(self):
        rows = self.parse(self.base() + [self.event("token_usage_record", {"turn_id": "turn", "usage": self.usage(12)})])
        serialized = json.dumps(rows)
        self.assertEqual(rows[0]["project"], "Friendly project")
        self.assertEqual(rows[0]["task"], "Sensitive first line")
        self.assertNotIn("private prompt", serialized)
        self.assertNotIn("private-thread", serialized)
        self.assertNotIn("/private/Project", serialized)
        self.assertRegex(rows[0]["record_id"], r"^[0-9a-f]{20}$")

    def test_default_since_is_current_month_and_utc_works(self):
        now = dt.datetime(2026, 9, 19, tzinfo=dt.timezone.utc)
        original = collector.dt.datetime
        class FrozenDateTime(dt.datetime):
            @classmethod
            def now(cls, tz=None): return now.astimezone(tz) if tz else now.replace(tzinfo=None)
        collector.dt.datetime = FrozenDateTime
        try:
            self.assertEqual(collector.since_value(None, dt.timezone.utc), dt.datetime(2026, 9, 1, tzinfo=dt.timezone.utc))
        finally:
            collector.dt.datetime = original

    def test_exports_exclude_titles_without_opt_in(self):
        with tempfile.TemporaryDirectory() as root:
            home, data = pathlib.Path(root) / "codex", pathlib.Path(root) / "out"
            session = home / "sessions" / "one.jsonl"; session.parent.mkdir(parents=True)
            session.write_text("\n".join(json.dumps(event) for event in self.base() + [self.event("token_usage_record", {"turn_id": "turn", "usage": self.usage(5)})]))
            result = collector.collect(home, data, dt.datetime(2026, 9, 1, tzinfo=self.zone), self.zone, {}, False)
            self.assertEqual(result["rows"][0]["task"], "Task " + result["rows"][0]["record_id"][:8])
            with (data / "usage.csv").open() as handle:
                self.assertIn("task", next(csv.reader(handle)))
            self.assertNotIn("/private/Project", (data / "usage.json").read_text())

    def test_deduplicates_response_id_across_files_and_legacy_delta_uses_baseline(self):
        with tempfile.TemporaryDirectory() as root:
            home, data = pathlib.Path(root) / "codex", pathlib.Path(root) / "out"
            sessions = home / "sessions"; sessions.mkdir(parents=True)
            precise = self.base() + [self.event("token_usage_record", {"turn_id": "turn", "response_id": "same", "usage": self.usage(7)})]
            precise.append(self.event("event_msg", {"type": "token_count", "info": {"total_token_usage": self.usage(7)}}))
            for name in ("one.jsonl", "two.jsonl"):
                (sessions / name).write_text("\n".join(json.dumps(event) for event in precise))
            result = collector.collect(home, data, dt.datetime(2026, 9, 1, tzinfo=self.zone), self.zone, {}, False)
            self.assertEqual(result["rows"][0]["requests"], 1)
            legacy = self.base() + [
                self.event("event_msg", {"type": "token_count", "info": {"total_token_usage": self.usage(100)}}, "2026-08-31T10:00:00Z"),
                self.event("event_msg", {"type": "token_count", "info": {"total_token_usage": self.usage(130)}})]
            self.assertEqual(self.parse(legacy)[0]["total_tokens"], 30)

    def test_csv_neutralizes_formula_strings(self):
        with tempfile.TemporaryDirectory() as root:
            path = pathlib.Path(root) / "usage.csv"
            collector.write_csv(path, [{"record_id": "x", "date": "2026-09-01", "project": "=formula", "task": "+title", "model": "@model", "effort": "-low", "requests": 1, **self.usage(1), "basis": "Response usage", "computer": False, "image": False, "web": False, "agents": False}])
            with path.open() as handle:
                row = list(csv.DictReader(handle))[0]
            self.assertEqual(row["project"], "'=formula")
            self.assertEqual(row["task"], "'+title")


if __name__ == "__main__":
    unittest.main()
