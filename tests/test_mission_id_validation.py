"""Regression: persisted mission IDs must never be silently regenerated."""
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from schnapper.mission import Mission, MissionsFehler  # noqa: E402


class MissionIdValidation(unittest.TestCase):
    def test_explicit_falsy_ids_are_rejected(self):
        for invalid_id in ("", False, 0):
            with self.subTest(mission_id=repr(invalid_id)):
                with self.assertRaises(MissionsFehler):
                    Mission.erstellen(name="Kamera", suche="Kamera", mission_id=invalid_id)

    def test_persisted_empty_id_is_not_silently_regenerated(self):
        record = Mission.erstellen(name="Kamera", suche="Kamera").als_dict()
        record["id"] = ""
        with self.assertRaises(MissionsFehler):
            Mission.aus_dict(record)

    def test_omitted_id_still_generates_a_valid_id(self):
        mission = Mission.erstellen(name="Kamera", suche="Kamera")
        self.assertRegex(mission.id, r"^[A-Za-z0-9_-]{1,64}$")

    def test_explicit_valid_id_is_preserved(self):
        mission = Mission.erstellen(
            name="Kamera", suche="Kamera", mission_id="known-mission-id"
        )
        self.assertEqual(mission.id, "known-mission-id")


if __name__ == "__main__":
    unittest.main()
