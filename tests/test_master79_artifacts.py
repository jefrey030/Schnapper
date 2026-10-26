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
        echt_open = os.open
        def getauscht(path, flags, *args, **kwargs):
            if str(path) == str(self.file):
                self.file.unlink()
                self.file.symlink_to(ziel)
            return echt_open(path, flags, *args, **kwargs)
        # Das Austauschen erfolgt unmittelbar vor dem echten Betriebssystem-open.
        # Ein reiner is_symlink()-Vorcheck waere hier nicht ausreichend.
        with mock.patch.object(dienst.os, "open", side_effect=getauscht):
            with self.assertRaises(OSError):
                dienst._hash_sicher(self.file)

    def test_falsche_path_symlink_auskunft_ist_egal(self):
        link = self.root / "agent.json"
        link.symlink_to(self.file)
        with mock.patch.object(pathlib.Path, "is_symlink", return_value=False):
            with self.assertRaises(OSError):
                dienst._hash_sicher(link)

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
