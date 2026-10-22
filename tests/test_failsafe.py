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


    def _gueltige_antworten(self):
        self._schreibe("LEAD", ki={"antwort_id": "lead-1"}, plan={"aufgabe_id": "S-000"})
        self._schreibe("BRAIN", ki={"antwort_id": "brain-2"})
        self._schreibe("CHECK", ki={"antwort_id": "check-3"},
                       urteil={"urteil": "bestanden"},
                       werkzeug={"tests": {"ok": True, "anzahl": 2}, "geheimnis_funde": []})
        self._schreibe("COMMAND", ki={"antwort_id": "command-4"},
                       protokoll={"freigabe": "ja", "naechster_schritt": "Prüfen"})

    def _bereit(self):
        agent.bericht(self.lauf)
        return json.loads((self.team / "runs" / (self.lauf.name + ".json")).read_text())

    def test_four_unique_response_ids_and_four_calls_allow_readiness(self):
        self._gueltige_antworten()
        (self.lauf / "ki_aufrufe.txt").write_text("4", encoding="utf-8")
        bericht = self._bereit()
        self.assertTrue(bericht["team_einsatzbereit"])
        self.assertTrue(bericht["antwort_ids_eindeutig"])

    def test_duplicate_response_id_blocks_false_readiness(self):
        self._gueltige_antworten()
        self._schreibe("COMMAND", ki={"antwort_id": "check-3"},
                       protokoll={"freigabe": "ja", "naechster_schritt": "Prüfen"})
        (self.lauf / "ki_aufrufe.txt").write_text("4", encoding="utf-8")
        bericht = self._bereit()
        self.assertFalse(bericht["team_einsatzbereit"])
        self.assertFalse(bericht["antwort_ids_eindeutig"])

    def test_missing_or_corrupt_call_counter_blocks_readiness(self):
        self._gueltige_antworten()
        self.assertFalse(self._bereit()["team_einsatzbereit"])
        (self.lauf / "ki_aufrufe.txt").write_text("kaputt", encoding="utf-8")
        bericht = self._bereit()
        self.assertEqual(bericht["ki_aufrufe"], 0)
        self.assertFalse(bericht["team_einsatzbereit"])


    def test_rejected_or_revision_check_is_not_ready(self):
        for verdict in ("abgelehnt", "nachbessern"):
            self._gueltige_antworten()
            self._schreibe("CHECK", ki={"antwort_id": "check-3"},
                           urteil={"urteil": verdict},
                           werkzeug={"tests": {"ok": True, "anzahl": 2},
                                      "geheimnis_funde": []})
            (self.lauf / "ki_aufrufe.txt").write_text("4", encoding="utf-8")
            bericht = self._bereit()
            self.assertFalse(bericht["team_einsatzbereit"], verdict)

    def test_command_denial_blocks_readiness(self):
        self._gueltige_antworten()
        self._schreibe("COMMAND", ki={"antwort_id": "command-4"},
                       protokoll={"freigabe": "nein", "naechster_schritt": "Prüfen"})
        (self.lauf / "ki_aufrufe.txt").write_text("4", encoding="utf-8")
        self.assertFalse(self._bereit()["team_einsatzbereit"])

    def test_missing_or_positive_secret_scan_blocks_readiness(self):
        self._gueltige_antworten()
        (self.lauf / "ki_aufrufe.txt").write_text("4", encoding="utf-8")
        self._schreibe("CHECK", ki={"antwort_id": "check-3"},
                       urteil={"urteil": "bestanden"},
                       werkzeug={"tests": {"ok": True, "anzahl": 2}})
        self.assertFalse(self._bereit()["team_einsatzbereit"])
        self._schreibe("CHECK", ki={"antwort_id": "check-3"},
                       urteil={"urteil": "bestanden"},
                       werkzeug={"tests": {"ok": True, "anzahl": 2},
                                  "geheimnis_funde": ["agentenausgabe[0]"]})
        self.assertFalse(self._bereit()["team_einsatzbereit"])


if __name__ == "__main__":
    unittest.main()
