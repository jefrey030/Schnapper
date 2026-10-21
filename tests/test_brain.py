import pathlib
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "team"))
import brain


class TestLocalBrain(unittest.TestCase):
    def setUp(self):
        self.task = {"id": "S-000", "title": "Vier-Agenten-Test"}

    def test_private_local_endpoint(self):
        self.assertEqual(brain.BASE, "http://127.0.0.1:11434")
        self.assertNotIn("cloud", brain.MODEL)

    def test_three_lead_features(self):
        answer = {"features": [{"name": str(i), "reason": "Nutzen"} for i in range(3)]}
        self.assertTrue(brain.validate("LEAD", self.task, answer)[0])
        answer["features"].pop()
        self.assertFalse(brain.validate("LEAD", self.task, answer)[0])

    def test_listing_schema(self):
        schema = {key: "text" for key in (
            "id", "title", "price", "currency", "url", "source", "observed_at")}
        answer = {"input": ["Suchbegriff"], "output": ["Inserate"],
                  "steps": ["Aufnehmen", "Filtern", "Prüfen"], "listing_schema": schema}
        self.assertTrue(brain.validate("BRAIN", self.task, answer)[0])
        del schema["price"]
        self.assertFalse(brain.validate("BRAIN", self.task, answer)[0])

    def test_three_checks(self):
        answer = {"cases": [{"kind": k, "risk": "Risiko", "test": "Beispieltest"} for k in
                            ("stale_price", "duplicate_listing", "usage_rights")]}
        self.assertTrue(brain.validate("CHECK", self.task, answer)[0])
        answer["cases"].pop()
        self.assertFalse(brain.validate("CHECK", self.task, answer)[0])

    def test_command_report(self):
        answer = {"status": "blocked",
                  "evidence": ["LEAD: x", "BRAIN: y", "CHECK: z"],
                  "next_step": "Ergebnisse prüfen"}
        self.assertTrue(brain.validate("COMMAND", self.task, answer)[0])

    def test_absent_local_model_fails_closed(self):
        with patch.object(brain, "_request", return_value={"models": []}):
            with self.assertRaises(brain.LocalBrainError):
                brain.available()

    def test_model_is_separate_local_call(self):
        captured = []
        def fake(path, data=None, timeout=120):
            captured.append((path, data))
            return {"response": '{"features":[]}'}
        with patch.object(brain, "_request", side_effect=fake):
            self.assertEqual(brain.ask("LEAD", self.task, {}, True),
                             {"features": []})
        self.assertEqual(captured[0][0], "/api/generate")
        self.assertEqual(captured[0][1]["model"], brain.MODEL)
        self.assertEqual(captured[0][1]["stream"], False)


if __name__ == "__main__":
    unittest.main()
