"""MASTER 85: lokale Runner-Lockdatei sicher öffnen; nur Offline-Tests.

Kein Ollama, kein Netzwerk, kein Deployment, keine bezahlte API.
"""
import fcntl
import os
import pathlib
import stat
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "team"))
import local_service as dienst


class TestMaster85SicheresRunnerLock(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = pathlib.Path(temp.name)
        self.team = self.root / "team"
        self.path = self.team / "work" / "local_runner.lock"
        self.path.parent.mkdir(parents=True)
        for name, value in (("ROOT", self.root), ("TEAM", self.team)):
            patch = mock.patch.object(dienst, name, value)
            patch.start()
            self.addCleanup(patch.stop)

    def _once(self):
        with mock.patch.object(sys, "argv", ["local_service.py", "--once"]), \
             mock.patch.object(dienst, "einmal", return_value=0) as einmal:
            status = dienst.start()
        return status, einmal.call_count

    def test_ungueltiger_symlink_keine_pid_ueberschreibung(self):
        extern = self.root / "externe_datei"
        extern.write_text("nicht veraendern", encoding="utf-8")
        self.path.symlink_to(extern)
        self.assertEqual(self._once(), (2, 0))
        self.assertEqual(extern.read_text(), "nicht veraendern")

    def test_defekter_symlink_fuehrt_zu_no_go(self):
        self.path.symlink_to(self.root / "nicht-da")
        self.assertEqual(self._once(), (2, 0))

    def test_hardlink_fuehrt_zu_no_go(self):
        original = self.root / "fremde_datei"
        original.write_text("nicht veraendern")
        os.link(original, self.path)
        self.assertEqual(self._once(), (2, 0))
        self.assertEqual(original.read_text(), "nicht veraendern")

    def test_directory_fuehrt_zu_no_go(self):
        self.path.mkdir()
        self.assertEqual(self._once(), (2, 0))

    @unittest.skipUnless(hasattr(os, "mkfifo"), "POSIX-FIFO erforderlich")
    def test_fifo_blockiert_ohne_haengen(self):
        os.mkfifo(self.path)
        self.assertEqual(self._once(), (2, 0))

    def test_regulaere_neue_datei_ist_nutzbar(self):
        self.assertEqual(self._once(), (0, 1))
        self.assertEqual(self.path.read_text(), str(os.getpid()))
        self.assertTrue(stat.S_ISREG(self.path.stat().st_mode))

    def test_stale_pid_datei_ist_wieder_nutzbar(self):
        self.path.write_text("alte PID")
        self.assertEqual(self._once(), (0, 1))
        self.assertEqual(self.path.read_text(), str(os.getpid()))

    def test_aktives_lock_blockiert_ohne_pid_mutation(self):
        self.path.write_text("reserviert")
        fd = os.open(self.path, os.O_RDWR)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.assertEqual(self._once(), (2, 0))
            self.assertEqual(self.path.read_text(), "reserviert")
        finally:
            os.close(fd)

    def test_nach_aktivem_lock_wieder_startbar(self):
        fd = os.open(self.path, os.O_RDWR | os.O_CREAT, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.assertEqual(self._once(), (2, 0))
        finally:
            os.close(fd)
        self.assertEqual(self._once(), (0, 1))

    def test_sicheres_fd_hat_nofollow_und_nonblock(self):
        fd = dienst._oeffne_runner_sperre(self.path)
        try:
            self.assertTrue(stat.S_ISREG(os.fstat(fd).st_mode))
            self.assertEqual(os.fstat(fd).st_nlink, 1)
        finally:
            os.close(fd)
        self.assertTrue(hasattr(os, "O_NOFOLLOW"))
        self.assertTrue(hasattr(os, "O_NONBLOCK"))

    def test_missing_nofollow_muss_blockieren(self):
        # patch.dict auf os.__dict__ simuliert fehlendes POSIX-Flag.
        previous = os.O_NOFOLLOW
        try:
            delattr(os, "O_NOFOLLOW")
            with self.assertRaisesRegex(OSError, "nicht abgesichert"):
                dienst._oeffne_runner_sperre(self.path)
        finally:
            os.O_NOFOLLOW = previous
        self.assertFalse(self.path.exists())

    def test_fstat_fehler_schliesst_fd(self):
        original_close = os.close
        original_open, original_fstat = os.open, os.fstat
        opened = []

        def track_open(path, *args, **kwargs):
            fd = original_open(path, *args, **kwargs)
            if path == self.path.name:
                opened.append(fd)
            return fd

        def fail_lock_fstat(fd):
            if fd in opened:
                raise OSError("fstat misslungen")
            return original_fstat(fd)

        with mock.patch.object(dienst.os, "open", side_effect=track_open), \
             mock.patch.object(dienst.os, "fstat", side_effect=fail_lock_fstat), \
             mock.patch.object(dienst.os, "close",
                               wraps=original_close) as close:
            with self.assertRaises(OSError):
                dienst._oeffne_runner_sperre(self.path)
            self.assertEqual(len(opened), 1)
            close.assert_any_call(opened[0])
            with self.assertRaises(OSError):
                original_fstat(opened[0])

    def test_nach_open_erzeugter_hardlink_blockiert_pid_schreiben(self):
        original = dienst._oeffne_runner_sperre
        extern = self.root / "link_zweite_kopie"
        def change(path):
            fd = original(path)
            os.link(path, extern)
            return fd
        with mock.patch.object(dienst, "_oeffne_runner_sperre",
                               side_effect=change):
            self.assertEqual(self._once(), (2, 0))
        self.assertEqual(self.path.stat().st_size, 0)

    def test_pid_write_oserror_blockiert_ohne_start(self):
        with mock.patch.object(dienst.os, "ftruncate",
                               side_effect=OSError("write refused")):
            self.assertEqual(self._once(), (2, 0))

    def test_pid_short_write_blockiert_ohne_start(self):
        with mock.patch.object(dienst.os, "write", return_value=0):
            self.assertEqual(self._once(), (2, 0))

    def test_pid_fsync_error_blockiert_ohne_start(self):
        with mock.patch.object(dienst.os, "fsync",
                               side_effect=OSError("disk full")):
            self.assertEqual(self._once(), (2, 0))

    def test_new_file_is_private_mode(self):
        self.assertEqual(self._once(), (0, 1))
        mode = self.path.stat().st_mode & 0o777
        self.assertEqual(mode & 0o077, 0)

    def test_no_subprocess_called_when_lock_invalid(self):
        extern = self.root / "external"
        extern.write_text("locked")
        self.path.symlink_to(extern)
        with mock.patch.object(dienst, "rolle_starten") as process:
            self.assertEqual(self._once(), (2, 0))
            process.assert_not_called()


if __name__ == "__main__":
    unittest.main()
