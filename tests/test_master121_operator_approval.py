"""Pure offline negative and positive tests. Never call local or remote models."""
import datetime as dt
import json
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "team"))
from ki import KINichtVerfuegbar
import operator_approval as approval

UTC = dt.timezone.utc
NOW = dt.datetime(2026, 10, 25, 16, 0, tzinfo=UTC)


class TestOperatorApproval(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.team = pathlib.Path(self.tmp.name) / "team"
        self.work = self.team / "work"
        self.work.mkdir(parents=True)
        self.file = self.work / "operator_approval.json"
        self.tasks = self.team / "tasks.json"
        for key, val in (("TEAM", self.team), ("WORK", self.work),
                         ("APPROVAL", self.file), ("TASKS", self.tasks),
                         ("STOP", self.work / "STOP")):
            p = mock.patch.object(approval, key, val)
            p.start()
            self.addCleanup(p.stop)
        self.set_tasks([{"id": "S-014", "status": "open"}])
        self.set_approval()

    def set_tasks(self, items):
        self.tasks.write_text(json.dumps({"tasks": items}), encoding="utf-8")

    def set_approval(self, **overrides):
        entry = {"approved": True, "scope": "LOCAL_OLLAMA_ONLY", "task_id": "S-014",
                 "expires_at_utc": (NOW + dt.timedelta(minutes=30)).isoformat()}
        entry.update(overrides)
        self.file.write_text(json.dumps(entry), encoding="utf-8")
        os.chmod(self.file, 0o600)

    def denied(self):
        with self.assertRaises(KINichtVerfuegbar):
            approval.pruefe_freigabe(NOW)

    def test_positive_single_open_task_short_approval(self):
        self.assertEqual(approval.pruefe_freigabe(NOW), "S-014")

    def test_missing_approval_is_blocked(self):
        self.file.unlink()
        self.denied()

    def test_env_backend_does_not_count_as_consent(self):
        self.file.unlink()
        with mock.patch.dict(os.environ, {"SCHNAPPER_KI_BACKEND": "ollama"}):
            self.denied()

    def test_wrong_scope_or_false_approval(self):
        self.set_approval(scope="LOCAL_OLLAMA_OR_CLOUD")
        self.denied()
        self.set_approval(approved="true")
        self.denied()

    def test_expired_future_or_timezone_naive(self):
        for expires in ((NOW - dt.timedelta(seconds=1)).isoformat(),
                        (NOW + dt.timedelta(hours=2)).isoformat(),
                        "2026-10-25T16:30:00"):
            self.set_approval(expires_at_utc=expires)
            self.denied()

    def test_zero_or_multiple_open_tasks(self):
        self.set_tasks([])
        self.denied()
        self.set_tasks([{"id": "S-014", "status": "open"},
                        {"id": "S-015", "status": "open"}])
        self.denied()

    def test_mismatched_task_denied(self):
        self.set_tasks([{"id": "S-003", "status": "open"}])
        self.denied()

    def test_operator_stop_file_denied(self):
        (self.work / "STOP").write_text("STOP", encoding="utf-8")
        self.denied()

    def test_bad_permissions_denied(self):
        os.chmod(self.file, 0o644)
        self.denied()

    def test_symlink_approval_denied(self):
        external = self.team / "external.json"
        external.write_bytes(self.file.read_bytes())
        self.file.unlink()
        self.file.symlink_to(external)
        self.denied()

    def test_tampered_or_oversize_file_denied(self):
        self.file.write_text("{broken", encoding="utf-8")
        self.denied()
        self.file.write_text("x" * 5000, encoding="utf-8")
        self.denied()

    def test_check_is_live_not_cached(self):
        self.assertEqual(approval.pruefe_freigabe(NOW), "S-014")
        self.file.unlink()
        self.denied()

    def test_task_file_symlink_denied(self):
        target = self.team / "other.json"
        target.write_bytes(self.tasks.read_bytes())
        self.tasks.unlink()
        self.tasks.symlink_to(target)
        self.denied()


if __name__ == "__main__":
    unittest.main()
