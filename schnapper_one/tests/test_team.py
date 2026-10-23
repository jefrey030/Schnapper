"""Isolierte Tests für SCHNAPPER ONE – Simulation ≠ echter KI-Nachweis."""
import json
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "team"))
import agent  # noqa
import ki  # noqa
import runner  # noqa


class AntwortSimulator:
    """Nur im Test: vier getrennte Antwortobjekte, kein KI-Netzaufruf."""
    def __init__(self):
        self.calls = []
    def frage(self, system, nutzer):
        self.calls.append(system)
        if "Rolle LEAD:" in system:
            text = json.dumps({
                "aufgabe_id": "ONE-001", "begruendung": "Test",
                "auftrag_brain": "Konzept", "auftrag_check": "Abnahme",
                "akzeptanzkriterien": ["Test"]})
        elif "Rolle BRAIN:" in system:
            text = "## Analyse\nTest\n## Vorschlag\nGeplanter Chat\n## Testfälle\nKeine Daten."
        elif "Rolle CHECK:" in system:
            text = json.dumps({"urteil": "bestanden", "erfuellt": ["Test"],
                               "maengel": [], "risiken": []})
        else:
            text = json.dumps({"zusammenfassung": "Testlauf", "freigabe": "ja",
                               "fehler": [], "naechster_schritt": "Manuell prüfen"})
        return {"text": text, "modell": "TEST-SIMULATOR", "antwort_id": "mock-" + str(len(self.calls)),
                "nutzung": {"total_tokens": 0}, "laufzeit": "TEST / KEINE ECHTE KI"}


class TeamTests(unittest.TestCase):
    def test_projekt_hat_eigene_aufgaben(self):
        tasks = runner.load_tasks()
        self.assertEqual([t["id"] for t in tasks],
                         ["ONE-001", "ONE-002", "ONE-003", "ONE-004", "ONE-005"])
        self.assertTrue(all(t["status"] == "open" for t in tasks))
        self.assertEqual(set(runner.ROLES), {"LEAD", "BRAIN", "CHECK", "COMMAND"})

    def test_ki_standardmaessig_deaktiviert(self):
        with mock.patch.dict(os.environ, {"SCHNAPPER_ONE_KI_ENABLED": "",
                                          "GITHUB_TOKEN": "nur-test"}):
            with self.assertRaises(ki.KINichtVerfuegbar):
                ki._token()

    def test_keine_unsichere_modell_url(self):
        for url in ("http://models.github.ai/x", "https://models.github.ai.evil.com/x",
                    "https://benutzer:passwort@models.github.ai/x",
                    "https://models.github.ai:8080/x"):
            with self.assertRaises(ki.KINichtVerfuegbar):
                ki._pruefe_url(url)

    def test_root_ist_isoliertes_teilprojekt(self):
        self.assertEqual(agent.ROOT, ROOT)
        self.assertEqual(runner.ROOT, ROOT)
        self.assertEqual(agent.TEAM, ROOT / "team")

    def test_vier_rollen_als_simulation_verdrahtet(self):
        fake = AntwortSimulator()
        with tempfile.TemporaryDirectory() as d:
            team = pathlib.Path(d)
            work = team / "work" / "probe"
            with mock.patch.object(agent, "TEAM", team), \
                 mock.patch.object(agent, "load_tasks", return_value=runner.load_tasks()), \
                 mock.patch.object(agent, "previous_task_id", return_value=None), \
                 mock.patch.object(agent, "tests_ausfuehren",
                                   return_value={"ok": True, "anzahl": 5, "ausgabe_ende": ""}), \
                 mock.patch.object(agent, "geheimnis_scan", return_value=[]):
                for role in runner.ROLES:
                    result = getattr(agent, role.lower())(work, fake)
                    self.assertEqual(result["status"], "OK", f"{role}: {result.get('fehler')}")
                    agent.schreibe(work, role, result)
                (work / "ki_aufrufe.txt").write_text("4", encoding="utf-8")
                agent.bericht(work)
            data = json.loads((team / "runs" / "probe.json").read_text(encoding="utf-8"))
            self.assertEqual(len(fake.calls), 4)
            self.assertTrue(data["team_einsatzbereit"])
            self.assertTrue(data["antwort_ids_eindeutig"])
            self.assertEqual(data["aufgabe"], "ONE-001")
            self.assertEqual(data["check_urteil"], "bestanden")
            self.assertEqual(data["modelle"], ["TEST-SIMULATOR"])

    def test_kein_kostenpflichtiger_live_aufruf_bei_gesperrtem_gate(self):
        with tempfile.TemporaryDirectory() as d:
            with mock.patch.dict(os.environ, {"SCHNAPPER_ONE_KI_ENABLED": "",
                                              "GITHUB_TOKEN": "nur-test"}), \
                 mock.patch.object(ki, "_http", side_effect=AssertionError("Kein Netz!")):
                with self.assertRaises(ki.KINichtVerfuegbar):
                    ki.KI(pathlib.Path(d) / "anzahl.txt").frage("System", "Prompt")


if __name__ == "__main__":
    unittest.main()
