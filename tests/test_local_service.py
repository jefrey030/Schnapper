"""Lokaler Scheduler: reine Unit-Tests, KEIN Modellaufruf."""
import json
import pathlib
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "team"))
import local_service as dienst


class TestDienst(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        self.team = self.root / "team"
        self.team.mkdir()
        self.patches = [
            mock.patch.object(dienst, "ROOT", self.root),
            mock.patch.object(dienst, "TEAM", self.team),
        ]
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)

    def test_fehlender_bericht_ist_blockiert(self):
        with mock.patch.object(dienst.subprocess, "run",
                               return_value=SimpleNamespace(returncode=0,
                                                            stdout="", stderr="")) as run:
            self.assertEqual(dienst.einmal(), 1)
        self.assertEqual(run.call_count, 5)
        for call in run.call_args_list:
            self.assertEqual(call.kwargs["env"]["SCHNAPPER_KI_BACKEND"], "ollama")
            self.assertFalse(call.kwargs["check"])

    def test_ausfall_eines_agenten_wird_nicht_als_erfolg_gewertet(self):
        def fake(cmd, **kwargs):
            if cmd[2] == "BERICHT":
                lauf = pathlib.Path(cmd[3])
                p = self.team / "runs" / (lauf.name + ".json")
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(json.dumps({
                    "team_einsatzbereit": False,
                    "agenten_mit_echter_ki": ["LEAD", "BRAIN", "CHECK"],
                    "tests_ok": True,
                }), encoding="utf-8")
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        with mock.patch.object(dienst.subprocess, "run", side_effect=fake):
            self.assertEqual(dienst.einmal(), 1)

    def test_vier_antworten_allein_genuegen_nicht_ohne_tests(self):
        def fake(cmd, **kwargs):
            if cmd[2] == "BERICHT":
                lauf = pathlib.Path(cmd[3])
                p = self.team / "runs" / (lauf.name + ".json")
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(json.dumps({
                    "team_einsatzbereit": True,
                    "agenten_mit_echter_ki": ["LEAD", "BRAIN", "CHECK", "COMMAND"],
                    "tests_ok": False,
                }), encoding="utf-8")
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        with mock.patch.object(dienst.subprocess, "run", side_effect=fake):
            self.assertEqual(dienst.einmal(), 1)



    def test_vier_fake_antworten_und_gruene_tests_im_unit_test(self):
        # Reine Simulation! Beweist die Logik, nicht Ollama-Verfügbarkeit.
        rollen = ("LEAD", "BRAIN", "CHECK", "COMMAND")

        def fake(cmd, **kwargs):
            lauf = pathlib.Path(cmd[3])
            rolle = cmd[2]
            if rolle in rollen:
                (lauf / (rolle + ".json")).write_text(
                    json.dumps({"rolle": rolle}), encoding="utf-8")
            if rolle == "BRAIN":
                p = self.team / "proposals" / "fake.md"
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text("Nur simuliertes Testartefakt", encoding="utf-8")
            if rolle == "BERICHT":
                p = self.team / "runs" / (lauf.name + ".json")
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(json.dumps({
                    "lauf": lauf.name,
                    "team_einsatzbereit": True,
                    "agenten_mit_echter_ki": list(rollen),
                    "ki_aufrufe": 4,
                    "aufgabe": "S-000",
                    "check_urteil": "bestanden",
                    "tests_ok": True,
                    "tests_anzahl": 3,
                    "agenten": {
                        r: {
                            "status": "OK", "ki_echt": True,
                            "plan": {"aufgabe_id": "S-000"} if r == "LEAD" else None,
                            "vorschlag_datei": "team/proposals/fake.md" if r == "BRAIN" else None,
                            "protokoll": {"freigabe": "ja",
                                          "naechster_schritt": "manuell pruefen"}
                                          if r == "COMMAND" else None,
                            "ki": {"laufzeit": "Ollama lokal (keine bezahlte KI-API)",
                                   "modell": "qwen2.5:1.5b",
                                   "text": "simulierte Antwort (nur im Unit Test)",
                                   "antwort_id": "lokal-" + r.lower()},
                        }
                        for r in rollen
                    },
                }), encoding="utf-8")
                # Positive Fixture: Nur MOCK-Daten; keine Modellantwort.
                # Der lokale Abschlusspruefer verlangt auch CHECK-Tests,
                # leeren Geheimnisscan und separaten persistenten Zaehler.
                gesamt = json.loads(p.read_text(encoding="utf-8"))
                belege = gesamt["agenten"]
                for r in rollen:
                    belege[r]["rolle"] = r
                    if r == "CHECK":
                        belege[r]["urteil"] = {"urteil": "bestanden"}
                        belege[r]["werkzeug"] = {
                            "tests": {"ok": True, "anzahl": 3},
                            "geheimnis_funde": [],
                        }
                    (lauf / (r + ".json")).write_text(
                        json.dumps(belege[r]), encoding="utf-8")
                (lauf / "ki_aufrufe.txt").write_text("4", encoding="utf-8")
                p.write_text(json.dumps(gesamt), encoding="utf-8")
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        with mock.patch.object(dienst.subprocess, "run", side_effect=fake):
            self.assertEqual(dienst.einmal(), 0)
        self.assertEqual(len(list((self.team / "work").glob("*/nachweise.json"))), 1)

    def test_agentenbericht_und_einzeldatei_muessen_uebereinstimmen(self):
        lauf = self.team / "work" / "inkonsistent"
        lauf.mkdir(parents=True)
        (lauf / "LEAD.json").write_text(
            json.dumps({"rolle": "LEAD", "status": "FEHLER"}), encoding="utf-8")
        bericht = {
            "lauf": lauf.name,
            "agenten": {"LEAD": {"rolle": "LEAD", "status": "OK"}},
        }
        fehler = dienst.pruefe_nachweise(bericht, lauf, [])
        self.assertTrue(any("widersprechen" in e for e in fehler))

    def test_ungueltige_agentendatei_ist_keine_freigabe(self):
        lauf = self.team / "work" / "unlesbar"
        lauf.mkdir(parents=True)
        (lauf / "LEAD.json").write_text("{nicht-json", encoding="utf-8")
        fehler = dienst.pruefe_nachweise(
            {"lauf": lauf.name, "agenten": {"LEAD": {"status": "OK"}}},
            lauf, []
        )
        self.assertTrue(any("unlesbar/ungültig" in e for e in fehler))

    def test_vier_antworten_falsch_bei_anderem_freigabefehler(self):
        # Ein fehlendes CHECK-GO muss vier_echte_ki_antworten=False setzen,
        # selbst wenn der gefälschte Sammelbericht vier Rollen behauptet.
        def fake(cmd, **kwargs):
            if cmd[2] == "BERICHT":
                lauf = pathlib.Path(cmd[3])
                p = self.team / "runs" / (lauf.name + ".json")
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(json.dumps({
                    "lauf": lauf.name,
                    "team_einsatzbereit": True,
                    "agenten_mit_echter_ki": list(dienst.ROLES),
                    "ki_aufrufe": 4,
                    "tests_ok": True,
                }), encoding="utf-8")
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        with mock.patch.object(dienst.subprocess, "run", side_effect=fake), \
             mock.patch.object(dienst, "pruefe_nachweise",
                               return_value=["CHECK hat nicht bestanden"]), \
             mock.patch("builtins.print") as printed:
            self.assertEqual(dienst.einmal(), 1)
        ergebnis = json.loads(printed.call_args.args[0])
        self.assertEqual(ergebnis["status"], "BLOCKIERT")
        self.assertFalse(ergebnis["vier_echte_ki_antworten"])

    def test_falsche_laufzeit_oder_doppelte_ids_blockieren(self):
        lauf = self.team / "work" / "fake"
        lauf.mkdir(parents=True)
        rollen = ("LEAD", "BRAIN", "CHECK", "COMMAND")
        for r in rollen:
            (lauf / (r + ".json")).write_text("{}", encoding="utf-8")
        bericht = {
            "lauf": lauf.name,
            "team_einsatzbereit": True,
            "agenten_mit_echter_ki": list(rollen),
            "ki_aufrufe": 4,
            "tests_ok": True,
            "tests_anzahl": 5,
            "agenten": {
                r: {"status": "OK", "ki_echt": True,
                    "ki": {"laufzeit": "GitHub Models",
                           "modell": "qwen2.5:1.5b", "text": "x",
                           "antwort_id": "lokal-dieselbe"}}
                for r in rollen
            },
        }
        schritte = [{"rolle": r, "exitcode": 0} for r in (*rollen, "BERICHT")]
        fehler = dienst.pruefe_nachweise(bericht, lauf, schritte)
        self.assertTrue(any("keine bestätigte lokale Laufzeit" in e for e in fehler))
        self.assertTrue(any("nicht viermal eindeutig" in e for e in fehler))

    def test_geheimnis_im_prozesslog_wird_redigiert_und_stoppt_folgerollen(self):
        geheimnis = "ghp_" + "A" * 25
        aufrufe = []

        def fake(cmd, **kwargs):
            aufrufe.append(cmd[2])
            return SimpleNamespace(returncode=0,
                                   stdout="Debug: " + geheimnis if cmd[2] == "LEAD" else "",
                                   stderr="")

        with mock.patch.object(dienst.subprocess, "run", side_effect=fake):
            self.assertEqual(dienst.einmal(), 1)
        self.assertEqual(aufrufe, ["LEAD", "BERICHT"])
        lauf = next((self.team / "work").glob("*/"))
        protokoll = (lauf / "prozesse.json").read_text(encoding="utf-8")
        self.assertNotIn(geheimnis, protokoll)
        eintraege = json.loads(protokoll)
        self.assertEqual(eintraege[0]["exitcode"], -3)
        self.assertTrue(all(x["exitcode"] == -2 for x in eintraege[1:4]))

    def test_agentenfehler_stoppt_naechste_kostenrelevante_rollen(self):
        aufrufe = []

        def fake(cmd, **kwargs):
            aufrufe.append(cmd[2])
            return SimpleNamespace(returncode=1 if cmd[2] == "LEAD" else 0,
                                   stdout="", stderr="")

        with mock.patch.object(dienst.subprocess, "run", side_effect=fake):
            self.assertEqual(dienst.einmal(), 1)
        self.assertEqual(aufrufe, ["LEAD", "BERICHT"])

    def test_betreiber_not_aus_verhindert_neuen_lauf(self):
        stop = self.team / "work" / "STOP"
        stop.parent.mkdir(parents=True)
        stop.write_text("Stopp angeordnet", encoding="utf-8")
        with mock.patch.object(dienst.subprocess, "run") as run:
            self.assertEqual(dienst.einmal(), 2)
            run.assert_not_called()

    def test_abgelehntes_check_und_command_nein_koennen_nicht_abnehmen(self):
        lauf = self.team / "work" / "20261022_test"
        lauf.mkdir(parents=True)
        report = {"lauf": lauf.name, "team_einsatzbereit": True,
                  "check_urteil": "abgelehnt",
                  "agenten": {"COMMAND": {"protokoll": {"freigabe": "nein",
                                                  "naechster_schritt": "Nachprüfen"}}}}
        fehler = dienst.pruefe_nachweise(report, lauf, [])
        self.assertTrue(any("CHECK hat nicht bestanden" in x for x in fehler))
        self.assertTrue(any("kein gültiges Abschlussprotokoll" in x for x in fehler))


if __name__ == "__main__":
    unittest.main()
