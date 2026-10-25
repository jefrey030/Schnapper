"""MASTER 76: OS-basiertes Exklusivlock – kein Modell, kein Netzwerk."""
import fcntl
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "team"))
import local_service as dienst


class TestLokalerDienstLock(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = pathlib.Path(tmp.name)
        self.team = self.root / "team"
        self.lockfile = self.team / "work" / "local_runner.lock"
        self.lockfile.parent.mkdir(parents=True)
        for name, value in (("ROOT", self.root), ("TEAM", self.team)):
            patch = mock.patch.object(dienst, name, value)
            patch.start()
            self.addCleanup(patch.stop)

    def _start_once(self):
        with mock.patch.object(sys, "argv", ["local_service.py", "--once"]), \
             mock.patch.object(dienst, "einmal", return_value=0) as once:
            status = dienst.start()
        return status, once.call_count

    def test_stale_datei_vom_absturz_blockiert_keinen_neuen_lauf(self):
        self.lockfile.write_text("123456 (veraltete PID)", encoding="utf-8")
        status, calls = self._start_once()
        self.assertEqual((status, calls), (0, 1))
        self.assertTrue(self.lockfile.exists())

    def test_aktives_lock_verhindert_zweiten_lauf(self):
        fd = os.open(self.lockfile, os.O_RDWR | os.O_CREAT, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            status, calls = self._start_once()
            self.assertEqual((status, calls), (2, 0))
        finally:
            os.close(fd)
        status, calls = self._start_once()
        self.assertEqual((status, calls), (0, 1))

    def test_nach_zwei_erfolgreichen_laeufen_bleibt_lock_nutzbar(self):
        self.assertEqual(self._start_once(), (0, 1))
        self.assertEqual(self._start_once(), (0, 1))
        self.assertEqual(self.lockfile.read_text(encoding="utf-8"), str(os.getpid()))

    @unittest.skipUnless(hasattr(os, "O_NOFOLLOW"), "No O_NOFOLLOW on this platform")
    def test_symlink_als_lockdatei_wird_sicher_abgelehnt(self):
        target = self.root / "opfer.txt"
        target.write_text("unveraendert", encoding="utf-8")
        self.lockfile.symlink_to(target)
        status, calls = self._start_once()
        self.assertEqual((status, calls), (2, 0))
        self.assertEqual(target.read_text(encoding="utf-8"), "unveraendert")


if __name__ == "__main__":
    unittest.main()
