"""MASTER 8: reproduzierbare Mehrinstanzen-/Symlink-Negativtests."""
import pathlib
import sys
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "app"))

from schnapper.mission import MissionsFehler, Missionsspeicher


class MissionConcurrentRegression(unittest.TestCase):
    def test_two_preloaded_instances_do_not_overwrite_each_other(self):
        with tempfile.TemporaryDirectory() as tmp:
            pfad = pathlib.Path(tmp, "missionen.json")
            a = Missionsspeicher.laden(pfad)
            b = Missionsspeicher.laden(pfad)
            a.erstellen(name="A", suche="A")
            b.erstellen(name="B", suche="B")
            self.assertEqual({m.name for m in Missionsspeicher.laden(pfad).alle()}, {"A", "B"})
            self.assertEqual({m.name for m in a.alle()}, {"A", "B"})

    def test_eight_parallel_independent_instances_preserve_all_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            pfad = pathlib.Path(tmp, "missionen.json")
            barrier = threading.Barrier(8)
            def worker(i):
                instance = Missionsspeicher.laden(pfad)
                barrier.wait(timeout=15)
                return instance.erstellen(name=f"Mission {i}", suche=f"Artikel {i}").id
            with ThreadPoolExecutor(max_workers=8) as pool:
                ids = list(pool.map(worker, range(8)))
            gespeicherte = Missionsspeicher.laden(pfad).alle()
            self.assertEqual(len(gespeicherte), 8)
            self.assertEqual({m.id for m in gespeicherte}, set(ids))

    def test_symlink_store_and_lock_are_rejected_without_touching_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            target = root / "fremd.json"
            target.write_text("UNVERÄNDERT", encoding="utf-8")
            link = root / "missionen.json"
            link.symlink_to(target)
            with self.assertRaises(MissionsFehler):
                Missionsspeicher.laden(link)
            self.assertEqual(target.read_text(encoding="utf-8"), "UNVERÄNDERT")
            link.unlink()
            sperr = root / "missionen.json.lock"
            sperr.symlink_to(target)
            with self.assertRaises(MissionsFehler):
                Missionsspeicher.laden(link).erstellen(name="Test", suche="Test")
            self.assertEqual(target.read_text(encoding="utf-8"), "UNVERÄNDERT")

    def test_corruption_after_load_blocks_mutation_and_preserves_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            pfad = pathlib.Path(tmp, "missionen.json")
            instance = Missionsspeicher.laden(pfad)
            instance.erstellen(name="vorher", suche="A")
            pfad.write_text("{KAPUTT", encoding="utf-8")
            with self.assertRaises(MissionsFehler):
                instance.erstellen(name="nachher", suche="B")
            self.assertEqual(pfad.read_text(encoding="utf-8"), "{KAPUTT")

    def test_directory_symlink_rejected_without_outside_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            outside = root / "outside"
            outside.mkdir()
            link = root / "linked"
            link.symlink_to(outside, target_is_directory=True)
            with self.assertRaises(MissionsFehler):
                Missionsspeicher.laden(link / "missionen.json")
            self.assertEqual(list(outside.iterdir()), [])

    def test_stored_file_is_private_and_roundtrips(self):
        import stat
        with tempfile.TemporaryDirectory() as tmp:
            pfad = pathlib.Path(tmp, "missionen.json")
            instance = Missionsspeicher.laden(pfad)
            m = instance.erstellen(name="gesichert", suche="Preis")
            self.assertEqual(stat.S_IMODE(pfad.stat().st_mode), 0o600)
            self.assertEqual(Missionsspeicher.laden(pfad).alle()[0].id, m.id)

    def test_failed_write_does_not_change_persisted_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            pfad = pathlib.Path(tmp, "missionen.json")
            store = Missionsspeicher.laden(pfad)
            m = store.erstellen(name="Test", suche="Lampe")
            with mock.patch.object(store, "_speichern", side_effect=OSError("disk full")):
                with self.assertRaises(OSError):
                    store.pausieren(m.id)
            self.assertEqual(Missionsspeicher.laden(pfad).alle()[0].status, "aktiv")


if __name__ == "__main__":
    unittest.main()
