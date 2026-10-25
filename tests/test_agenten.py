"""Tests für die vier Agenten und die KI-Kostenbremsen.

Der End-to-End-Test nutzt einen LOKALEN NACHAHMER von GitHub Models (kein
echtes Modell). Er beweist nur die Verdrahtung, nicht die KI-Qualität.
"""
import http.server
import json
import os
import pathlib
import sys
import tempfile
import threading
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "team"))
import agent  # noqa: E402
import ki  # noqa: E402
import runner as agent_runner  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]


class Nachahmer(http.server.BaseHTTPRequestHandler):
    aufrufe = []

    def log_message(self, *a):
        pass

    def _send(self, obj):
        body = json.dumps(obj).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._send([{"id": "meta/Llama-3.3-70B-Instruct", "rate_limit_tier": "high"},
                    {"id": "openai/gpt-4o-mini", "rate_limit_tier": "low"}])

    def do_POST(self):
        req = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        system = req["messages"][0]["content"]
        Nachahmer.aufrufe.append(req["model"])
        if "Rolle LEAD" in system:
            text = '```json\n{"aufgabe_id": "S-000", "begruendung": "b", "auftrag_brain": "x", "auftrag_check": "y", "akzeptanzkriterien": ["k1"]}\n```'
        elif "Rolle BRAIN" in system:
            text = "## Analyse\nA\n## Vorschlag\nV"
        elif "Rolle CHECK" in system:
            text = '{"urteil": "bestanden", "erfuellt": ["k1"], "maengel": [], "risiken": []}'
        else:
            text = '{"zusammenfassung": "z", "freigabe": "ja", "fehler": [], "naechster_schritt": "n"}'
        self._send({"id": f"resp-{len(Nachahmer.aufrufe)}", "model": req["model"],
                    "choices": [{"message": {"content": text}}], "usage": {"total_tokens": 10}})


class TestKostenbremsen(unittest.TestCase):
    def test_nur_github_models_erlaubt(self):
        for url in ("https://api.anthropic.com/v1/messages", "https://api.openai.com/v1/chat/completions",
                    "https://models.github.ai.evil.com/x"):
            with self.assertRaises(ki.KINichtVerfuegbar):
                ki._pruefe_url(url)
        ki._pruefe_url(ki.INFERENZ_URL)

    def test_kein_bezahlter_anbieter_im_code(self):
        for datei in ("team/ki.py", "team/agent.py", "team/runner.py", ".github/workflows/schnapper-hourly.yml"):
            text = (ROOT / datei).read_text(encoding="utf-8")
            for verboten in ("api.anthropic.com", "ANTHROPIC_API_KEY", "api.openai.com", "OPENAI_API_KEY"):
                self.assertNotIn(verboten, text, f"{verboten} in {datei}")

    def test_workflow_minimale_rechte(self):
        wf = (ROOT / ".github/workflows/schnapper-hourly.yml").read_text(encoding="utf-8")
        self.assertNotIn("models: read", wf)
        self.assertNotIn("schedule:", wf)
        self.assertIn("contents: read", wf)
        self.assertIn("false &&", wf)
        self.assertIn("SCHNAPPER_PAUSE", wf)
        self.assertNotIn("team/agent.py", wf)
        self.assertNotIn("GITHUB_TOKEN", wf)
        self.assertNotIn("git push", wf)
        self.assertNotIn("secrets.ANTHROPIC", wf)

    def test_kostenschutz_nur_oeffentlich(self):
        wf = (ROOT / ".github/workflows/schnapper-hourly.yml").read_text(encoding="utf-8")
        self.assertIn("toJSON(github.event.repository.private) == 'false'", wf)
        self.assertNotIn("github.event.repository.private == false", wf)
        self.assertIn("vars.SCHNAPPER_OEFFENTLICH == 'true'", wf)
        self.assertIn("false &&", wf)
        self.assertIn("contents: read", wf)
        tests_wf = (ROOT / ".github/workflows/tests.yml").read_text(encoding="utf-8")
        self.assertIn("github.event.repository.private == false", tests_wf)

    def test_aufrufbudget(self):
        with tempfile.TemporaryDirectory() as d:
            k = ki.KI(pathlib.Path(d) / "z.txt")
            with mock.patch.object(ki, "MAX_AUFRUFE", 2):
                k._zaehle()
                k._zaehle()
                with self.assertRaises(ki.KINichtVerfuegbar):
                    k._zaehle()

    def test_eingestellte_github_models_verursachen_keinen_netzaufruf(self):
        with tempfile.TemporaryDirectory() as d:
            zaehler = pathlib.Path(d) / "calls.txt"
            with (mock.patch.dict(os.environ, {"GITHUB_TOKEN": "nur-test-token"}),
                  mock.patch.object(ki, "_http") as http):
                with self.assertRaisesRegex(ki.KINichtVerfuegbar, "eingestellt"):
                    ki.KI(zaehler).frage("system", "nutzer")
                http.assert_not_called()
            self.assertFalse(zaehler.exists())

    def test_modellwahl_bevorzugt_open_weight(self):
        kat = [{"id": "openai/gpt-4o-mini", "rate_limit_tier": "low"},
               {"id": "microsoft/Phi-4", "rate_limit_tier": "low"}]
        self.assertEqual(ki.waehle_modell(kat), "microsoft/Phi-4")
        with self.assertRaises(ki.KINichtVerfuegbar):
            ki.waehle_modell(kat, "meta/gibtsnicht")
        with self.assertRaises(ki.KINichtVerfuegbar):
            ki.waehle_modell([{"id": "openai/gpt-4o-mini", "rate_limit_tier": "low"}])


class TestAgenten(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.team = pathlib.Path(self.tmp.name) / "team"
        self.lauf = self.team / "work" / "20261021T190000Z"
        self.p = mock.patch.object(agent, "TEAM", self.team)
        self.p.start()
        # Eigene Aufgaben-Fixture, damit der Test nicht vom echten Aufgabenstatus abhängt.
        self.team.mkdir(parents=True, exist_ok=True)
        aufgaben = self.team / "tasks.json"
        aufgaben.write_text(json.dumps({"tasks": [
            {"id": "S-000", "priority": 0, "status": "open", "title": "Testaufgabe",
             "acceptance": ["k1"]}]}), encoding="utf-8")
        self.p_aufgaben = mock.patch.object(agent, "load_tasks", lambda: agent_runner.load_tasks(aufgaben))
        self.p_vorige = mock.patch.object(agent, "previous_task_id",
                                          lambda: agent_runner.previous_task_id(self.team / "runs"))
        self.p_aufgaben.start()
        self.p_vorige.start()

    def tearDown(self):
        self.p_vorige.stop()
        self.p_aufgaben.stop()
        self.p.stop()
        self.tmp.cleanup()

    def alle(self):
        for rolle in ("LEAD", "BRAIN", "CHECK", "COMMAND", "BERICHT"):
            self.assertEqual(agent.main(["agent.py", rolle, str(self.lauf)]), 0)
        return json.loads((self.team / "runs" / f"{self.lauf.name}.json").read_text())

    def test_ohne_ki_ehrlich_nicht_einsatzbereit(self):
        with mock.patch.dict(os.environ, {"GITHUB_TOKEN": ""}), \
             mock.patch.object(agent, "tests_ausfuehren", return_value={"ok": True, "anzahl": 1, "ausgabe_ende": ""}):
            bericht = self.alle()
        self.assertFalse(bericht["team_einsatzbereit"])
        self.assertEqual(bericht["agenten_mit_echter_ki"], [])
        for rolle in ("LEAD", "BRAIN", "CHECK", "COMMAND"):
            self.assertFalse(bericht["agenten"][rolle]["ki_echt"])
            self.assertIsNone(bericht["agenten"][rolle]["ki"])
        self.assertIn("NICHT EINSATZBEREIT", (self.team / "STATUS.md").read_text())

    def test_s003_jeder_agent_berichtet_und_fehlende_ki_ist_blocker(self):
        with mock.patch.dict(os.environ, {"GITHUB_TOKEN": ""}), \
             mock.patch.object(agent, "tests_ausfuehren", return_value={"ok": True, "anzahl": 1, "ausgabe_ende": ""}):
            bericht = self.alle()
        for rolle in ("LEAD", "BRAIN", "CHECK", "COMMAND"):
            daten = json.loads((self.lauf / f"{rolle}.json").read_text(encoding="utf-8"))
            self.assertEqual(daten["rolle"], rolle)
            self.assertTrue(daten["status"])
        self.assertEqual(len(bericht["blocker"]), 1)
        b = bericht["blocker"][0]
        self.assertEqual(b["art"], "KI-Anbindung fehlt")
        self.assertIn("GITHUB_TOKEN", b["detail"])
        self.assertEqual(b["rollen"], ["LEAD", "COMMAND"])
        md = (self.team / "runs" / f"{self.lauf.name}.md").read_text(encoding="utf-8")
        self.assertIn("## Blocker", md)
        self.assertIn("KI-Anbindung fehlt", md)

    def test_vier_getrennte_ki_aufrufe_mit_nachahmer(self):
        Nachahmer.aufrufe = []
        server = http.server.HTTPServer(("127.0.0.1", 0), Nachahmer)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        basis_url = f"http://127.0.0.1:{server.server_port}"
        try:
            with mock.patch.dict(os.environ, {"GITHUB_TOKEN": "test", "SCHNAPPER_MODELL": ""}), \
                 mock.patch.object(ki, "_pruefe_url", return_value=None), \
                 mock.patch.object(ki, "INFERENZ_URL", basis_url + "/inference"), \
                 mock.patch.object(ki, "KATALOG_URL", basis_url + "/catalog"), \
                 mock.patch.object(ki.KI, "modell", return_value="meta/Llama-3.3-70B-Instruct"), \
                 mock.patch.object(ki.KI.__init__, "__defaults__", (None, basis_url + "/inference", basis_url + "/catalog")), \
                 mock.patch.object(agent, "tests_ausfuehren", return_value={"ok": True, "anzahl": 3, "ausgabe_ende": ""}):
                bericht = self.alle()
        finally:
            server.shutdown()
            server.server_close()
        self.assertEqual(len(Nachahmer.aufrufe), 4)
        self.assertEqual(set(Nachahmer.aufrufe), {"meta/Llama-3.3-70B-Instruct"})
        self.assertTrue(bericht["team_einsatzbereit"])
        self.assertEqual(bericht["aufgabe"], "S-000")
        self.assertEqual(bericht["check_urteil"], "bestanden")
        self.assertEqual(bericht["ki_aufrufe"], 4)
        self.assertEqual(bericht["blocker"], [])
        ids = {bericht["agenten"][r]["ki"]["antwort_id"] for r in ("LEAD", "BRAIN", "CHECK", "COMMAND")}
        self.assertEqual(len(ids), 4)
        self.assertTrue(list((self.team / "proposals").glob("*S-000.md")))

    def test_werkzeugbefund_schlaegt_ki_urteil(self):
        with mock.patch.object(agent, "tests_ausfuehren", return_value={"ok": False, "anzahl": 1, "ausgabe_ende": ""}):
            agent.schreibe(self.lauf, "LEAD", {"status": "OK", "plan": {"aufgabe": {}, "akzeptanzkriterien": []}})
            agent.schreibe(self.lauf, "BRAIN", {"status": "OK", "ki": {"text": "x"}})
            fake = mock.Mock()
            fake.frage.return_value = {"text": '{"urteil": "bestanden"}', "modell": "m", "antwort_id": "1"}
            erg = agent.check(self.lauf, fake)
        self.assertEqual(erg["urteil"]["urteil"], "abgelehnt")

    def test_ungueltige_aufgabe_wird_abgelehnt(self):
        fake = mock.Mock()
        fake.frage.return_value = {"text": '{"aufgabe_id": "ERFUNDEN"}', "modell": "m", "antwort_id": "1"}
        erg = agent.lead(self.lauf, fake)
        self.assertEqual(erg["status"], "FEHLER")


if __name__ == "__main__":
    unittest.main()
