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
                            "rolle": r, "status": "OK", "ki_echt": True,
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
                gespeicherter_bericht = json.loads(p.read_text(encoding="utf-8"))
                for r in rollen:
                    (lauf / (r + ".json")).write_text(
                        json.dumps(gespeicherter_bericht["agenten"][r]), encoding="utf-8")
                (lauf / "ki_aufrufe.txt").write_text("4", encoding="utf-8")
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        with mock.patch.object(dienst.subprocess, "run", side_effect=fake):
            self.assertEqual(dienst.einmal(), 0)
        self.assertEqual(len(list((self.team / "work").glob("*/nachweise.json"))), 1)

    def test_gesamtbericht_darf_abweichende_agentendatei_nicht_freigeben(self):
        lauf = self.team / "work" / "integritaetsprobe"
        lauf.mkdir(parents=True)
        (lauf / "ki_aufrufe.txt").write_text("4", encoding="utf-8")
        rollen = ("LEAD", "BRAIN", "CHECK", "COMMAND")
        agenten = {
            r: {"rolle": r, "status": "OK", "ki_echt": True,
                "ki": {"laufzeit": "Ollama lokal (keine bezahlte KI-API)",
                       "modell": "qwen2.5:1.5b", "text": "Test",
                       "antwort_id": "lokal-" + r}}
            for r in rollen
        }
        for r in rollen:
            datei = lauf / (r + ".json")
            content = dict(agenten[r])
            if r == "CHECK":
                content["status"] = "FEHLER"
            datei.write_text(json.dumps(content), encoding="utf-8")
        bericht = {
            "lauf": lauf.name, "team_einsatzbereit": True,
            "agenten_mit_echter_ki": list(rollen), "ki_aufrufe": 4,
            "tests_ok": True, "tests_anzahl": 5,
            "check_urteil": "bestanden", "agenten": agenten,
        }
        schritte = [{"rolle": r, "exitcode": 0} for r in (*rollen, "BERICHT")]
        fehler = dienst.pruefe_nachweise(bericht, lauf, schritte)
        self.assertTrue(any("widersprechen sich: CHECK.json" in x for x in fehler))

    def test_aufrufzaehler_muss_persistent_und_genau_vier_sein(self):
        lauf = self.team / "work" / "zaehlerprobe"
        lauf.mkdir(parents=True)
        bericht = {"lauf": lauf.name, "team_einsatzbereit": True,
                   "ki_aufrufe": 4}
        for wert in (None, "3", "5", "ungültig"):
            pfad = lauf / "ki_aufrufe.txt"
            if wert is None:
                pfad.unlink(missing_ok=True)
            else:
                pfad.write_text(wert, encoding="utf-8")
            fehler = dienst.pruefe_nachweise(bericht, lauf, [])
            self.assertTrue(any("Aufrufzähler fehlt" in x for x in fehler), wert)

    def test_kaputte_agenten_json_blockiert_ohne_ausnahme(self):
        lauf = self.team / "work" / "kaputtes_json"
        lauf.mkdir(parents=True)
        (lauf / "ki_aufrufe.txt").write_text("4", encoding="utf-8")
        (lauf / "LEAD.json").write_text("{", encoding="utf-8")
        fehler = dienst.pruefe_nachweise(
            {"lauf": lauf.name, "agenten": {"LEAD": {"rolle": "LEAD"}}},
            lauf, [])
        self.assertTrue(any("Agentendatei fehlt oder ungültig: LEAD.json" in x for x in fehler))

    def test_unlesbarer_stundenbericht_ist_blockiert(self):
        def fake(cmd, **kwargs):
            if cmd[2] == "BERICHT":
                lauf = pathlib.Path(cmd[3])
                pfad = self.team / "runs" / (lauf.name + ".json")
                pfad.parent.mkdir(parents=True, exist_ok=True)
                pfad.write_text("{defekt", encoding="utf-8")
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        with mock.patch.object(dienst.subprocess, "run", side_effect=fake):
            self.assertEqual(dienst.einmal(), 1)

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
