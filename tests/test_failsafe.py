"""Zero-cost regression tests: agent results must fail closed, never claim readiness on broken output."""
import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "team"))
import agent  # noqa: E402


class TestFailClosedAgentReports(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.team = pathlib.Path(self.tmp.name) / "team"
        self.lauf = self.team / "work" / "20261022T020000Z"
        patch = mock.patch.object(agent, "TEAM", self.team)
        patch.start()
        self.addCleanup(patch.stop)

    def _schreibe(self, rolle, **fields):
        agent.schreibe(self.lauf, rolle, {"rolle": rolle, "ki_echt": True, "status": "OK", **fields})

    def test_json_parser_finds_first_complete_object(self):
        sample = 'Text ```json\n{"aufgabe_id":"S-000"}\n``` und {"beispiel":2}'
        self.assertEqual(agent.json_aus_text(sample), {"aufgabe_id": "S-000"})
        self.assertIsNone(agent.json_aus_text("keine JSON-Antwort"))
        self.assertIsNone(agent.json_aus_text(None))

    def test_check_rejects_unparseable_ai_verdict(self):
        self._schreibe("LEAD", plan={"aufgabe": {"acceptance": ["beleg"]}})
        self._schreibe("BRAIN", ki={"text": "Vorschlag"})
        fake = mock.Mock()
        fake.frage.return_value = {"text": "Alles gut – kein JSON", "modell": "test"}
        with mock.patch.object(agent, "tests_ausfuehren",
                               return_value={"ok": True, "anzahl": 3, "ausgabe_ende": ""}), \
             mock.patch.object(agent, "geheimnis_scan", return_value=[]):
            result = agent.check(self.lauf, fake)
        self.assertEqual(result["status"], "FEHLER")
        self.assertTrue(result["ki_echt"])
        self.assertNotIn("urteil", result)

    def test_command_rejects_missing_required_fields(self):
        fake = mock.Mock()
        fake.frage.return_value = {"text": '{"zusammenfassung":"ok"}', "modell": "test"}
        result = agent.command(self.lauf, fake)
        self.assertEqual(result["status"], "FEHLER")
        self.assertNotIn("protokoll", result)

    def test_command_cannot_override_failed_check(self):
        self._schreibe("CHECK", urteil={"urteil": "abgelehnt"},
                       werkzeug={"tests": {"ok": False, "anzahl": 2}, "geheimnis_funde": []})
        fake = mock.Mock()
        fake.frage.return_value = {
            "text": json.dumps({"zusammenfassung": "Vorschlag", "freigabe": "ja",
                                "fehler": [], "naechster_schritt": "Zuerst Tests reparieren"}),
            "modell": "test",
        }
        result = agent.command(self.lauf, fake)
        self.assertEqual(result["status"], "OK")
        self.assertEqual(result["protokoll"]["freigabe"], "nein")

    def test_four_model_replies_not_sufficient_when_one_agent_failed(self):
        self._schreibe("LEAD", plan={"aufgabe_id": "S-000"})
        self._schreibe("BRAIN", ki={"modell": "dummy"})
        self._schreibe("CHECK", status="FEHLER", urteil={"urteil": "bestanden"},
                       werkzeug={"tests": {"ok": True, "anzahl": 3}})
        self._schreibe("COMMAND", protokoll={"naechster_schritt": "Prüfen"})
        self.assertEqual(agent.bericht(self.lauf), 0)
        report = json.loads((self.team / "runs" / (self.lauf.name + ".json")).read_text())
        self.assertFalse(report["team_einsatzbereit"])

    def test_zero_executed_tests_not_ready(self):
        self._schreibe("LEAD", plan={"aufgabe_id": "S-000"})
        self._schreibe("BRAIN")
        self._schreibe("CHECK", urteil={"urteil": "bestanden"},
                       werkzeug={"tests": {"ok": True, "anzahl": 0}})
        self._schreibe("COMMAND", protokoll={"naechster_schritt": "Prüfen"})
        agent.bericht(self.lauf)
        report = json.loads((self.team / "runs" / (self.lauf.name + ".json")).read_text())
        self.assertFalse(report["team_einsatzbereit"])


if __name__ == "__main__":
    unittest.main()
