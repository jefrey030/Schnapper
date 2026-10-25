"""MASTER 87 – aktiver Not-Aus und sichere Prozessbehandlung.

Ausschließlich simulierte Popen-/Rollenprozesse, keine Modellaufrufe und
keine API-/Netzwerkrequests.
"""
import json
import pathlib
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "team"))
import local_service as dienst


class TestMaster87AktiverNotAus(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.root = pathlib.Path(t.name)
        self.team = self.root / "team"
        (self.team / "work").mkdir(parents=True)
        for name, path in (("ROOT", self.root), ("TEAM", self.team)):
            patch = mock.patch.object(dienst, name, path)
            patch.start()
            self.addCleanup(patch.stop)
        self.stop = self.team / "work" / "STOP"
        self.cmd = ["python", "fake-agent"]

    def _fake_process(self, *, returncode=0, communicate=("", "")):
        p = mock.MagicMock()
        p.__enter__.return_value = p
        p.poll.return_value = None
        p.returncode = returncode
        p.communicate.return_value = communicate
        return p

    def _start(self, *, timeout=10, stop_on_flag=True):
        return dienst.rolle_starten(
            self.cmd, cwd=self.root, env={},
            capture_output=True, text=True, check=False,
            timeout=timeout, stop_on_flag=stop_on_flag)

    def test_successful_process_keeps_logs_and_code(self):
        p = self._fake_process(communicate=("fertig", ""))
        with mock.patch.object(dienst.subprocess, "Popen", return_value=p):
            out = self._start()
        self.assertEqual((out.returncode, out.stdout, out.stderr), (0, "fertig", ""))
        p.kill.assert_not_called()
        p.terminate.assert_not_called()

    def test_negative_exitcode_is_returned_unchanged(self):
        p = self._fake_process(returncode=7, communicate=("", "fehler"))
        with mock.patch.object(dienst.subprocess, "Popen", return_value=p):
            result = self._start()
        self.assertEqual(result.returncode, 7)

    def test_stop_before_spawn_never_starts_subprocess(self):
        self.stop.write_text("STOP")
        with mock.patch.object(dienst.subprocess, "Popen") as popen:
            result = self._start()
        self.assertEqual((result.returncode, result.stdout), (-4, ""))
        popen.assert_not_called()

    def test_stop_during_running_process_terminates_child(self):
        p = self._fake_process()
        def fake_comm(*, timeout):
            if not self.stop.exists():
                self.stop.write_text("Betreiber-STOP")
                raise dienst.subprocess.TimeoutExpired(self.cmd, timeout)
            return ("partial secret", "partial stderr")
        p.communicate.side_effect = fake_comm
        with mock.patch.object(dienst.subprocess, "Popen", return_value=p):
            result = self._start()
        self.assertEqual((result.returncode, result.stdout, result.stderr), (-4, "", ""))
        p.terminate.assert_called_once()
        p.kill.assert_not_called()

    def test_stop_during_communicate_discards_partial_output(self):
        p = self._fake_process()
        def fake_comm(*, timeout):
            self.stop.write_text("STOP")
            return ("partielle Ausgabe", "ein Token")
        p.communicate.side_effect = fake_comm
        with mock.patch.object(dienst.subprocess, "Popen", return_value=p):
            result = self._start()
        self.assertEqual((result.returncode, result.stdout, result.stderr), (-4, "", ""))

    def test_stuck_child_after_stop_is_killed(self):
        p = self._fake_process()
        def fake_comm(*, timeout):
            if timeout == 2:
                raise dienst.subprocess.TimeoutExpired(self.cmd, timeout)
            if not self.stop.exists():
                self.stop.write_text("STOP")
                raise dienst.subprocess.TimeoutExpired(self.cmd, timeout)
            return ("", "")
        p.communicate.side_effect = fake_comm
        with mock.patch.object(dienst.subprocess, "Popen", return_value=p):
            result = self._start()
        self.assertEqual(result.returncode, -4)
        p.terminate.assert_called_once()
        p.kill.assert_called_once()

    def test_timeout_expires_and_kills_child(self):
        p = self._fake_process()
        with mock.patch.object(dienst.subprocess, "Popen", return_value=p):
            with self.assertRaises(dienst.subprocess.TimeoutExpired):
                self._start(timeout=0)
        p.kill.assert_called_once()

    def test_timeout_after_one_poll_expires(self):
        p = self._fake_process()
        p.communicate.side_effect = dienst.subprocess.TimeoutExpired(self.cmd, 0.5)
        with mock.patch.object(dienst.subprocess, "Popen", return_value=p), \
             mock.patch.object(dienst.time, "monotonic", side_effect=[0, 0, 1]):
            with self.assertRaises(dienst.subprocess.TimeoutExpired):
                self._start(timeout=0.5)
        p.kill.assert_called_once()

    def test_report_can_run_after_stop_when_explicitly_allowed(self):
        self.stop.write_text("STOP")
        p = self._fake_process(communicate=("bericht", ""))
        with mock.patch.object(dienst.subprocess, "Popen", return_value=p):
            result = self._start(stop_on_flag=False)
        self.assertEqual((result.returncode, result.stdout), (0, "bericht"))

    def test_report_stop_does_not_force_termination(self):
        p = self._fake_process(communicate=("bericht", ""))
        def fake_comm(*, timeout):
            self.stop.write_text("STOP")
            return ("bericht", "")
        p.communicate.side_effect = fake_comm
        with mock.patch.object(dienst.subprocess, "Popen", return_value=p):
            result = self._start(stop_on_flag=False)
        self.assertEqual(result.returncode, 0)
        p.terminate.assert_not_called()

    def test_bypass_capture_output_rejected(self):
        with self.assertRaises(ValueError):
            dienst.rolle_starten(self.cmd, cwd=self.root, env={},
                                 capture_output=False)
    def test_bypass_text_log_rejected(self):
        with self.assertRaises(ValueError):
            dienst.rolle_starten(self.cmd, cwd=self.root, env={},
                                 text=False)
    def test_bypass_check_mode_rejected(self):
        with self.assertRaises(ValueError):
            dienst.rolle_starten(self.cmd, cwd=self.root, env={},
                                 check=True)

    def test_start_failure_marks_blocked_and_still_calls_report(self):
        calls = []
        def fake(cmd, **kwargs):
            role = cmd[2]
            calls.append(role)
            if role == "LEAD":
                raise OSError("subprocess unavailable")
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        with mock.patch.object(dienst, "rolle_starten", side_effect=fake):
            status = dienst.einmal()
        self.assertEqual(status, 1)
        self.assertEqual(calls, ["LEAD", "BERICHT"])
        lauf = next((self.team / "work").glob("*/"))
        records = json.loads((lauf / "prozesse.json").read_text())
        self.assertEqual(records[0]["exitcode"], -5)
        self.assertTrue(all(x["exitcode"] == -2 for x in records[1:4]))

    def test_active_stop_marks_blocked_and_skips_other_roles(self):
        calls = []
        def fake(cmd, **kwargs):
            role = cmd[2]
            calls.append(role)
            if role == "LEAD":
                self.stop.write_text("STOP")
                return SimpleNamespace(returncode=-4, stdout="", stderr="")
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        with mock.patch.object(dienst, "rolle_starten", side_effect=fake):
            status = dienst.einmal()
        self.assertEqual(status, 1)
        self.assertEqual(calls, ["LEAD", "BERICHT"])
        lauf = next((self.team / "work").glob("*/"))
        records = json.loads((lauf / "prozesse.json").read_text())
        self.assertEqual(records[0]["exitcode"], -4)

    def test_no_shell_in_process_creation(self):
        p = self._fake_process()
        with mock.patch.object(dienst.subprocess, "Popen", return_value=p) as spawn:
            self._start()
        self.assertEqual(spawn.call_args.args[0], self.cmd)
        self.assertIs(spawn.call_args.kwargs["text"], True)
        self.assertNotIn("shell", spawn.call_args.kwargs)

    def test_unusable_report_process_is_not_positive(self):
        calls = []
        def fake(cmd, **kwargs):
            calls.append(cmd[2])
            if cmd[2] == "BERICHT":
                raise OSError("cannot start")
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        with mock.patch.object(dienst, "rolle_starten", side_effect=fake):
            code = dienst.einmal()
        self.assertEqual(code, 1)
        self.assertEqual(calls, ["LEAD", "BRAIN", "CHECK", "COMMAND", "BERICHT"])
        lauf = next((self.team / "work").glob("*/"))
        entries = json.loads((lauf / "prozesse.json").read_text())
        self.assertEqual(entries[-1]["exitcode"], -5)


if __name__ == "__main__":
    unittest.main()
