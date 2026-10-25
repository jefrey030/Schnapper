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

    def test_command_ohne_offene_aufgabe_vermeidet_ki_aufruf(self):
        self._schreibe("LEAD", status="KEINE AUFGABE", ki_echt=False,
                       fehler="Keine offenen Aufgaben in team/tasks.json.")
        fake = mock.Mock()
        fake.frage.side_effect = AssertionError("Unnötiger COMMAND-Modellaufruf")
        result = agent.command(self.lauf, fake)
        fake.frage.assert_not_called()
        self.assertEqual(result["status"], "ÜBERSPRUNGEN")
        self.assertFalse(result["ki_echt"])
        self.assertIn("Keine offene Aufgabe", result["fehler"])
        self.assertNotIn("protokoll", result)

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

    def test_secret_in_command_or_lead_reply_blocks_readiness(self):
        for rolle in ("LEAD", "COMMAND", "CHECK"):
            self._gueltige_antworten()
            self._schreibe(
                rolle,
                ki={"antwort_id": rolle.lower() + "-response", "text": "ghp_" + "A" * 25},
                **({"plan": {"aufgabe_id": "S-000"}} if rolle == "LEAD" else {}),
                **({"urteil": {"urteil": "bestanden"},
                    "werkzeug": {"tests": {"ok": True, "anzahl": 2},
                                 "geheimnis_funde": []}} if rolle == "CHECK" else {}),
                **({"protokoll": {"freigabe": "ja", "naechster_schritt": "Prüfen"}}
                   if rolle == "COMMAND" else {}),
            )
            (self.lauf / "ki_aufrufe.txt").write_text("4", encoding="utf-8")
            gespeichert = (self.lauf / (rolle + ".json")).read_text(encoding="utf-8")
            self.assertNotIn("ghp_" + "A" * 25, gespeichert)
            self.assertTrue(json.loads(gespeichert)["geheimnis_redigiert"])
            self.assertEqual(json.loads(gespeichert)["status"], "FEHLER")
            bericht = self._bereit()
            self.assertFalse(bericht["team_einsatzbereit"], rolle)
            self.assertIn(rolle, bericht["ki_geheimnis_rollen"])

    def test_git_scan_ausfall_muss_blockieren(self):
        from types import SimpleNamespace
        with mock.patch.object(agent.subprocess, "run",
                               return_value=SimpleNamespace(stdout="", returncode=1)):
            self.assertEqual(agent.geheimnis_scan(), ["git_scan_fehlgeschlagen"])
        with mock.patch.object(agent.subprocess, "run", side_effect=FileNotFoundError()):
            self.assertEqual(agent.geheimnis_scan(), ["git_scan_nicht_verfuegbar"])

    def test_git_scan_erfasst_dateinamen_mit_leerzeichen(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            filename = "datei mit leerzeichen.txt"
            (root / filename).write_text("ghp_" + "A" * 25, encoding="utf-8")
            from types import SimpleNamespace
            with mock.patch.object(agent, "ROOT", root), mock.patch.object(
                agent.subprocess, "run",
                return_value=SimpleNamespace(stdout=filename + "\0", returncode=0),
            ):
                self.assertEqual(agent.geheimnis_scan(), [filename])

    def test_ki_antwort_mit_token_wird_vor_weitergabe_verworfen(self):
        fake = mock.Mock()
        fake.frage.return_value = {
            "text": '{"aufgabe_id":"S-000"}',
            "modell": "ghp_" + "A" * 25,
            "antwort_id": "test-id",
        }
        antwort, fehler = agent.ki_teil(fake, "LEAD", "Testauftrag")
        self.assertIsNone(antwort)
        self.assertIn("Geheimnisindikator", fehler)
        self.assertNotIn("ghp_" + "A" * 25, fehler)

    def test_ki_eingabe_mit_token_wird_niemals_an_modell_gesendet(self):
        fake = mock.Mock()
        secret = "ghp_" + "A" * 25
        antwort, fehler = agent.ki_teil(fake, "LEAD", "Auftrag: " + secret)
        self.assertIsNone(antwort)
        self.assertIn("KI-Eingabe", fehler)
        self.assertNotIn(secret, fehler)
        fake.frage.assert_not_called()

    def test_ki_geheimnis_fund_macht_rollenprozess_rot(self):
        # Der API-Adapter wirft die verdächtige Antwort vor schreibe() weg.
        # Auch dann muss der Prozess non-zero zurückgeben.
        fake = mock.Mock()
        fake.frage.return_value = {
            "text": '{"aufgabe_id":"S-000"}',
            "modell": "ghp_" + "A" * 25,
            "antwort_id": "test-id",
        }
        class FakeKI:
            def __init__(self, _zaehler):
                self.frage = fake.frage

        with mock.patch.object(agent, "KI", FakeKI), mock.patch.object(
            agent, "load_tasks",
            return_value=[{"id": "S-000", "status": "open"}]
        ), mock.patch.object(agent, "choose_task", return_value={"id":"S-000"}), mock.patch.object(
            agent, "previous_task_id", return_value=None
        ):
            self.assertEqual(agent.main(["agent.py", "LEAD", str(self.lauf)]), 1)
        gespeichert = json.loads((self.lauf / "LEAD.json").read_text(encoding="utf-8"))
        self.assertEqual(gespeichert["status"], "NICHT EINSATZBEREIT")
        self.assertNotIn("ghp_" + "A" * 25, json.dumps(gespeichert))

    def test_git_scan_lesefehler_verhindert_positive_abnahme(self):
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            with mock.patch.object(agent, "ROOT", root), mock.patch.object(
                agent.subprocess, "run",
                return_value=SimpleNamespace(stdout="fehlt.txt\0", returncode=0),
            ):
                self.assertEqual(agent.geheimnis_scan(), ["datei_fehlt:fehlt.txt"])

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
