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
                # Die positiven Artefakte werden ausdrücklich als MOCK erzeugt.
                # Der Prüfer muss ihre Inhalte mit dem Bericht vergleichen.
                agenten = json.loads(p.read_text(encoding="utf-8"))["agenten"]
                for r in rollen:
                    (lauf / (r + ".json")).write_text(
                        json.dumps({"rolle": r, **agenten[r]}), encoding="utf-8")
                # Im tatsächlichen Bericht steht kein separater "rolle"-Eintrag.
                # Darum denselben Eintrag auch im Bericht setzen.
                report = json.loads(p.read_text(encoding="utf-8"))
                report["agenten"] = {
                    r: {"rolle": r, **agenten[r]} for r in rollen
                }
                p.write_text(json.dumps(report), encoding="utf-8")
                (lauf / "ki_aufrufe.txt").write_text("4", encoding="utf-8")
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        with mock.patch.object(dienst.subprocess, "run", side_effect=fake):
            self.assertEqual(dienst.einmal(), 0)
        self.assertEqual(len(list((self.team / "work").glob("*/nachweise.json"))), 1)

    def _konsistenter_mock_nachweis(self):
        """Vollständiges lokales Testartefakt, KEIN realer KI-Lauf."""
        lauf = self.team / "work" / "mock-konsistent"
        lauf.mkdir(parents=True)
        rollen = ("LEAD", "BRAIN", "CHECK", "COMMAND")
        vorschlag = self.team / "proposals" / "fake.md"
        vorschlag.parent.mkdir(parents=True)
        vorschlag.write_text("Simuliertes Artefakt", encoding="utf-8")
        agenten = {}
        for r in rollen:
            eintrag = {
                "rolle": r, "status": "OK", "ki_echt": True,
                "plan": {"aufgabe_id": "S-000"} if r == "LEAD" else None,
                "vorschlag_datei": "team/proposals/fake.md" if r == "BRAIN" else None,
                "protokoll": {"freigabe": "ja", "naechster_schritt": "Manuell prüfen"}
                    if r == "COMMAND" else None,
                "ki": {"laufzeit": "Ollama lokal (keine bezahlte KI-API)",
                       "modell": "qwen2.5:1.5b",
                       "text": "SIMULIERTER Unit-Test",
                       "antwort_id": "lokal-mock-" + r.lower()},
            }
            agenten[r] = eintrag
            (lauf / (r + ".json")).write_text(json.dumps(eintrag), encoding="utf-8")
        (lauf / "ki_aufrufe.txt").write_text("4", encoding="utf-8")
        bericht = {
            "lauf": lauf.name, "team_einsatzbereit": True,
            "agenten_mit_echter_ki": list(rollen),
            "ki_aufrufe": 4, "check_urteil": "bestanden",
            "tests_ok": True, "tests_anzahl": 3,
            "agenten": agenten,
        }
        schritte = [{"rolle": r, "exitcode": 0} for r in (*rollen, "BERICHT")]
        return lauf, bericht, schritte

    def test_bericht_und_rollendatei_muessen_uebereinstimmen(self):
        lauf, bericht, schritte = self._konsistenter_mock_nachweis()
        self.assertEqual(dienst.pruefe_nachweise(bericht, lauf, schritte), [])
        # Positive Berichtsfelder durften vorher den tatsächlichen Rolleninhalt
        # ignorieren; der geänderte JSON-Inhalt muss nun zur Sperre führen.
        datei = lauf / "LEAD.json"
        daten = json.loads(datei.read_text(encoding="utf-8"))
        daten["ki"]["antwort_id"] = "lokal-manipuliert"
        datei.write_text(json.dumps(daten), encoding="utf-8")
        fehler = dienst.pruefe_nachweise(bericht, lauf, schritte)
        self.assertTrue(any("Abweichung zwischen Bericht und Agentendatei" in f
                            for f in fehler))

    def test_beschaedigte_rollendatei_blockiert(self):
        lauf, bericht, schritte = self._konsistenter_mock_nachweis()
        (lauf / "BRAIN.json").write_text("{ungültig", encoding="utf-8")
        fehler = dienst.pruefe_nachweise(bericht, lauf, schritte)
        self.assertTrue(any("beschädigt/nicht lesbar" in f for f in fehler))

    def test_lokaler_aufrufzaehler_darf_nicht_nur_im_bericht_stehen(self):
        lauf, bericht, schritte = self._konsistenter_mock_nachweis()
        self.assertEqual(dienst.pruefe_nachweise(bericht, lauf, schritte), [])
        (lauf / "ki_aufrufe.txt").unlink()
        fehler = dienst.pruefe_nachweise(bericht, lauf, schritte)
        self.assertTrue(any("KI-Aufrufzähler fehlt" in f for f in fehler))
        (lauf / "ki_aufrufe.txt").write_text("3", encoding="utf-8")
        fehler = dienst.pruefe_nachweise(bericht, lauf, schritte)
        self.assertTrue(any("KI-Aufrufzähler fehlt" in f for f in fehler))

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
