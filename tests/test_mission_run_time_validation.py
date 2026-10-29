"""Regression: a completed run must never precede the mission's creation."""
import datetime as dt
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from schnapper.mission import MissionsFehler, Missionsspeicher  # noqa: E402


class MissionRunTimeValidation(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.path = pathlib.Path(self.tempdir.name, "missionen.json")
        self.created = dt.datetime(2026, 10, 29, 10, tzinfo=dt.timezone.utc)
        self.before = self.created - dt.timedelta(minutes=1)
        self.store = Missionsspeicher.laden(self.path)
        self.mission = self.store.erstellen(
            name="Kamera", suche="Kamera", jetzt=self.created
        )

    def test_reject_earlier_run_without_corrupting_persisted_mission(self):
        previous_bytes = self.path.read_bytes()
        with self.assertRaisesRegex(MissionsFehler, "vor der Erstellung"):
            self.store.lauf_abschliessen(self.mission.id, jetzt=self.before)
        self.assertEqual(self.path.read_bytes(), previous_bytes)
        self.assertIsNone(Missionsspeicher.laden(self.path).alle()[0].letzter_lauf_am)

    def test_forced_run_cannot_bypass_creation_time_check(self):
        previous_bytes = self.path.read_bytes()
        with self.assertRaisesRegex(MissionsFehler, "vor der Erstellung"):
            self.store.lauf_abschliessen(
                self.mission.id, jetzt=self.before, erzwingen=True
            )
        self.assertEqual(self.path.read_bytes(), previous_bytes)
        self.assertEqual(len(Missionsspeicher.laden(self.path).alle()), 1)

    def test_run_at_creation_time_remains_valid_and_reloadable(self):
        completed = self.store.lauf_abschliessen(
            self.mission.id, jetzt=self.created
        )
        self.assertEqual(completed.letzter_lauf_am, self.created)
        restored = Missionsspeicher.laden(self.path).alle()[0]
        self.assertEqual(restored.letzter_lauf_am, self.created)


if __name__ == "__main__":
    unittest.main()
