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
                            "protokoll": {"freigabe": "nein",
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
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        with mock.patch.object(dienst.subprocess, "run", side_effect=fake):
            self.assertEqual(dienst.einmal(), 0)
        self.assertEqual(len(list((self.team / "work").glob("*/nachweise.json"))), 1)

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

if __name__ == "__main__":
    unittest.main()
