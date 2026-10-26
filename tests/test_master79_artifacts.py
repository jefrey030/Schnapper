"""MASTER 79: sichere Pflichtartefakte; vollstaendig ohne LLM, Netz oder Deploy."""
import hashlib
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "team"))
import local_service as dienst
import safe_artifacts  # noqa: E402


class TestMaster79SicheresManifest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = pathlib.Path(tmp.name)
        self.file = self.root / "evidence.json"
        self.file.write_bytes(b'{"mock": true}')

    def test_regulaere_datei_hash_ist_korrekt(self):
        self.assertEqual(dienst._hash_sicher(self.file),
                         hashlib.sha256(b'{"mock": true}').hexdigest())

    def test_symlink_auf_regulaere_datei_blockiert(self):
        link = self.root / "agent.json"
        link.symlink_to(self.file)
        with self.assertRaises(OSError):
            dienst._hash_sicher(link)

    def test_defekter_symlink_blockiert(self):
        link = self.root / "agent.json"
        link.symlink_to(self.root / "does-not-exist.json")
        with self.assertRaises(OSError):
            dienst._hash_sicher(link)

    def test_datei_austausch_waehrend_open_blockiert(self):
        ziel = self.root / "fremder_bericht.json"
        ziel.write_bytes(b'{"untrusted": true}')
        echt_open = safe_artifacts.os.open
        def getauscht(path, flags, *args, **kwargs):
            if path == self.file.name and kwargs.get("dir_fd") is not None:
                self.file.unlink()
                self.file.symlink_to(ziel)
            return echt_open(path, flags, *args, **kwargs)
        # Austausch unmittelbar vor dem openat auf dem verankerten Verzeichnis.
        with mock.patch.object(safe_artifacts.os, "open", side_effect=getauscht):
            with self.assertRaises(OSError):
                dienst._hash_sicher(self.file)

    def test_elternordner_symlink_ist_gesperrt(self):
        ausserhalb = self.root / "ausserhalb"
        ausserhalb.mkdir()
        (ausserhalb / "evidence.json").write_bytes(b"private")
        link = self.root / "parent-link"
        link.symlink_to(ausserhalb, target_is_directory=True)
        with self.assertRaises(OSError):
            dienst._hash_sicher(link / "evidence.json")

    def test_hardlink_ausserhalb_der_artefaktstruktur_wird_abgewiesen(self):
        source = self.root / "original.json"
        source.write_text('{"secret":"not an artifact"}', encoding="utf-8")
        link = self.root / "team" / "runs" / "run-1" / "manifest.json"
        link.parent.mkdir(parents=True)
        os.link(source, link)
        with self.assertRaises(OSError):
            safe_artifacts.read_text(link)

    def test_sicheres_verzeichnis_anlegen_folgt_keinem_elternlink(self):
        outside = self.root / "outside"
        outside.mkdir()
        parent = self.root / "parent-link"
        parent.symlink_to(outside, target_is_directory=True)
        with self.assertRaises(OSError):
            safe_artifacts.create_directory(parent / "new-run")
        self.assertFalse((outside / "new-run").exists())

    def test_falsche_path_symlink_auskunft_ist_egal(self):
        link = self.root / "agent.json"
        link.symlink_to(self.file)
        with mock.patch.object(pathlib.Path, "is_symlink", return_value=False):
            with self.assertRaises(OSError):
                dienst._hash_sicher(link)

    def test_verzeichnisaustausch_waehrend_lesen_wird_erkannt(self):
        ausserhalb = self.root / "replacement"
        ausserhalb.mkdir()
        (ausserhalb / "evidence.json").write_bytes(b"outside")
        ordner = self.root / "anchored"
        ordner.mkdir()
        (ordner / "evidence.json").write_bytes(b"inside")
        verschoben = self.root / "anchored-original"
        echt_open = safe_artifacts.os.open
        ausgetauscht = False

        def tauschen(path, flags, *args, **kwargs):
            nonlocal ausgetauscht
            fd = echt_open(path, flags, *args, **kwargs)
            if (not ausgetauscht and path == ordner.name
                    and kwargs.get("dir_fd") is not None):
                ausgetauscht = True
                ordner.rename(verschoben)
                ordner.symlink_to(ausserhalb, target_is_directory=True)
            return fd

        with mock.patch.object(safe_artifacts.os, "open", side_effect=tauschen):
            with self.assertRaises(OSError):
                dienst._hash_sicher(ordner / "evidence.json")
        self.assertTrue(ausgetauscht)
        self.assertEqual((ausserhalb / "evidence.json").read_bytes(), b"outside")

    def test_fehlende_datei_blockiert(self):
        with self.assertRaises(OSError):
            dienst._hash_sicher(self.root / "missing.json")

    def test_verzeichnis_ist_keine_artefaktdatei(self):
        with self.assertRaises(OSError):
            dienst._hash_sicher(self.root)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "POSIX-FIFO nicht verfuegbar")
    def test_fifo_kann_nicht_als_datei_gelten(self):
        fifo = self.root / "evidence.fifo"
        os.mkfifo(fifo)
        with self.assertRaises(OSError):
            dienst._hash_sicher(fifo)

    def test_ueber_2mb_ist_nicht_erlaubt(self):
        self.file.write_bytes(b"x" * 2_000_001)
        with self.assertRaises(OSError):
            dienst._hash_sicher(self.file)

    def test_genau_2mb_ist_erlaubt(self):
        self.file.write_bytes(b"x" * 2_000_000)
        self.assertEqual(dienst._hash_sicher(self.file),
                         hashlib.sha256(b"x" * 2_000_000).hexdigest())

    def test_os_open_enthaelt_no_follow(self):
        echt_open = os.open
        flags_gesehen = []
        def pruefe_flags(path, flags, *args, **kwargs):
            flags_gesehen.append(flags)
            return echt_open(path, flags, *args, **kwargs)
        with mock.patch.object(dienst.os, "open", side_effect=pruefe_flags):
            dienst._hash_sicher(self.file)
        self.assertTrue(flags_gesehen)
        self.assertTrue(flags_gesehen[0] & os.O_NOFOLLOW)



if __name__ == "__main__":
    unittest.main()
