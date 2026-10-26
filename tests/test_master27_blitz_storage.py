"""MASTER 27: echte POSIX-Speicher-, Neustart- und Multi-Instanzen-Regressionen.

Keine Netzwerkabfragen, Modelle, Deployments, Käufe oder fremden Dateizugriffe.
"""
import datetime as dt
import json
import os
import pathlib
import sys
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "app"))
from schnapper.alarm import Wunsch
from schnapper.blitz import Blitz, BlitzFehler
from schnapper.einlesen import lies_text

NOW = dt.datetime(2026, 10, 26, 12, 0, tzinfo=dt.timezone.utc)


def daten():
    raw = [{
        "id": "eins", "titel": "Kopfhörer kabellos", "preis": "49",
        "referenzpreis": "80", "url": "https://shop.example/offer/1",
        "quelle": "mock", "erfasst_am": NOW.isoformat(),
        "zustand": "gebraucht",
    }]
    erg = lies_text(json.dumps(raw), "json", jetzt=NOW)
    assert not erg.fehler, erg.fehler
    return erg


def wunsch():
    return [Wunsch.aus_dict({"name": "Kopfhörer", "suche": "kabellos",
                            "max_preis": "60", "zustaende": ["gebraucht"]})]


@unittest.skipUnless(os.name == "posix", "POSIX-Sperren erforderlich")
class BlitzPosixSecurity(unittest.TestCase):
    def test_preloaded_instances_cannot_emit_duplicate(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = pathlib.Path(tmp) / "blitz.json"
            a = Blitz.laden(p)
            b = Blitz.laden(p)
            first = a.pruefen(daten(), wunsch(), jetzt=NOW)
            second = b.pruefen(daten(), wunsch(), jetzt=NOW)
            self.assertEqual(len(first), 1)
            self.assertEqual(second, [])
            self.assertEqual(len(Blitz.laden(p)), 1)

    def test_parallel_independent_instances_emit_exactly_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = pathlib.Path(tmp) / "blitz.json"
            gate = threading.Barrier(6)
            def worker(_):
                queue = Blitz.laden(p)
                gate.wait(timeout=15)
                return queue.pruefen(daten(), wunsch(), jetzt=NOW)
            with ThreadPoolExecutor(max_workers=6) as pool:
                results = list(pool.map(worker, range(6)))
            self.assertEqual(sum(map(len, results)), 1)
            self.assertEqual(len(Blitz.laden(p)), 1)

    def test_symlink_parent_never_creates_external_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            outside = root / "outside"
            outside.mkdir()
            (root / "link").symlink_to(outside, target_is_directory=True)
            with self.assertRaises(BlitzFehler):
                Blitz.laden(root / "link" / "blitz.json")
            self.assertEqual(list(outside.iterdir()), [])

    def test_symlink_leaf_and_lock_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            target = root / "target.json"
            target.write_text("UNVERAENDERT", encoding="utf-8")
            p = root / "blitz.json"
            p.symlink_to(target)
            with self.assertRaises(BlitzFehler):
                Blitz.laden(p)
            self.assertEqual(target.read_text(), "UNVERAENDERT")
            p.unlink()
            lock = root / "blitz.json.lock"
            lock.unlink()
            lock.symlink_to(target)
            with self.assertRaises(BlitzFehler):
                Blitz.laden(p)
            self.assertEqual(target.read_text(), "UNVERAENDERT")

    def test_corruption_after_loading_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = pathlib.Path(tmp) / "blitz.json"
            old = Blitz.laden(p)
            old.pruefen(daten(), wunsch(), jetzt=NOW)
            p.write_text("{kaputt", encoding="utf-8")
            with self.assertRaises(BlitzFehler):
                old.pruefen(daten(), wunsch(), jetzt=NOW)
            self.assertEqual(p.read_text(), "{kaputt")

    def test_private_atomic_file_survives_reload(self):
        import stat
        with tempfile.TemporaryDirectory() as tmp:
            p = pathlib.Path(tmp) / "blitz.json"
            b = Blitz.laden(p)
            self.assertEqual(len(b.pruefen(daten(), wunsch(), jetzt=NOW)), 1)
            self.assertEqual(stat.S_IMODE(p.stat().st_mode), 0o600)
            self.assertEqual(len(Blitz.laden(p)), 1)


if __name__ == "__main__":
    unittest.main()
