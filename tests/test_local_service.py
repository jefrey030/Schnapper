"""Lokaler Scheduler: reine Unit-Tests, KEIN Modellaufruf."""
import hashlib
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
            # Older deterministic service tests exercise downstream reports, not consent.
            # The real approval function has its own fail-closed regression suite.
            mock.patch.object(dienst, "pruefe_freigabe", return_value="S-014"),
        ]
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)

    def _manifest_fixture(self, erfolgreich=True):
        """Synthetisches SHA-256-Manifest ohne reale KI oder Netzwerk."""
        lauf = self.team / "work" / "lauf-test"
        lauf.mkdir(parents=True, exist_ok=True)
        runs = self.team / "runs"
        runs.mkdir(exist_ok=True)
        dateien = [runs / (lauf.name + ".json"), lauf / "prozesse.json"]
        if erfolgreich:
            dateien += [lauf / (r + ".json") for r in dienst.ROLES]
        for i, datei in enumerate(dateien):
            datei.write_text(json.dumps({"test": i}), encoding="utf-8")
        manifest = {
            "lauf": lauf.name,
            "ergebnis": {
                "lauf": lauf.name,
                "status": "TECHNISCHER PILOT ERFOLGREICH" if erfolgreich else "BLOCKIERT",
                "vier_echte_ki_antworten": erfolgreich,
            },
            "dateien": {
                str(p.relative_to(self.root)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in dateien
            },
        }
        (lauf / "nachweise.json").write_text(json.dumps(manifest), encoding="utf-8")
        return lauf, manifest

    def test_manifest_gueltig_und_vollstaendig_pruefen(self):
        lauf, _ = self._manifest_fixture()
        resultat = dienst.pruefe_manifest(lauf)
        self.assertEqual(resultat["status"], "INTEGRITAET_OK")
        self.assertEqual(resultat["dateien_geprueft"], 6)
        self.assertEqual(resultat["fehler"], [])

    def test_manifest_blockierter_lauf_bleibt_blockiert_aber_nachvollziehbar(self):
        lauf, _ = self._manifest_fixture(erfolgreich=False)
        resultat = dienst.pruefe_manifest(lauf)
        self.assertEqual(resultat["status"], "INTEGRITAET_OK")
        self.assertEqual(resultat["dateien_geprueft"], 2)

    def test_manifest_entdeckt_nachtraeglich_geaenderte_ki_datei(self):
        lauf, _ = self._manifest_fixture()
        (lauf / "CHECK.json").write_text("nachtraeglich geaendert", encoding="utf-8")
        resultat = dienst.pruefe_manifest(lauf)
        self.assertEqual(resultat["status"], "BLOCKIERT")
        self.assertTrue(any("Prüfsummenabweichung" in e for e in resultat["fehler"]))

    def test_manifest_erkennt_geloeschten_beleg(self):
        lauf, _ = self._manifest_fixture()
        (lauf / "BRAIN.json").unlink()
        resultat = dienst.pruefe_manifest(lauf)
        self.assertEqual(resultat["status"], "BLOCKIERT")
        self.assertTrue(any("Dateiliste" in e for e in resultat["fehler"]))

    def test_manifest_blockiert_fremde_pfade_ohne_sie_zu_lesen(self):
        lauf, manifest = self._manifest_fixture()
        secret = self.root / "fremd.txt"
        secret.write_text("nicht-zum-lesen", encoding="utf-8")
        manifest["dateien"]["../../fremd.txt"] = hashlib.sha256(secret.read_bytes()).hexdigest()
        (lauf / "nachweise.json").write_text(json.dumps(manifest), encoding="utf-8")
        # Whitelist wird vor dem Hashing geprüft. Der fremde Pfad ist
        # kein zulässiges Dateimitglied, selbst mit korrekt geratenem Hash.
        status = dienst.pruefe_manifest(lauf)["status"]
        self.assertEqual(status, "BLOCKIERT")

    def test_manifest_symlink_beleg_und_symlink_lauf_sind_gesperrt(self):
        lauf, _ = self._manifest_fixture()
        outside = self.root / "fremd.json"
        outside.write_text('{"fremd":true}', encoding="utf-8")
        (lauf / "LEAD.json").unlink()
        try:
            (lauf / "LEAD.json").symlink_to(outside)
        except (OSError, NotImplementedError):
            self.skipTest("Symbolische Links auf diesem Host nicht verfügbar")
        resultat = dienst.pruefe_manifest(lauf)
        self.assertEqual(resultat["status"], "BLOCKIERT")
        self.assertTrue(any("verlinkt" in e for e in resultat["fehler"]))
        link = self.team / "work" / "anderer_lauf"
        link.symlink_to(lauf, target_is_directory=True)
        self.assertEqual(dienst.pruefe_manifest(link)["status"], "BLOCKIERT")

    def test_manifest_sperrt_falsche_sha256_und_widerspruch(self):
        lauf, manifest = self._manifest_fixture()
        key = next(iter(manifest["dateien"]))
        manifest["dateien"][key] = "kein-sha-256"
        manifest["ergebnis"]["vier_echte_ki_antworten"] = False
        (lauf / "nachweise.json").write_text(json.dumps(manifest), encoding="utf-8")
        fehler = dienst.pruefe_manifest(lauf)["fehler"]
        self.assertTrue(any("Fingerabdruck" in e for e in fehler))
        self.assertTrue(any("widersprechen" in e for e in fehler))

    def test_manifest_erfolgsbehauptung_ohne_vier_agenten_blockiert(self):
        lauf, manifest = self._manifest_fixture(erfolgreich=False)
        manifest["ergebnis"]["status"] = "TECHNISCHER PILOT ERFOLGREICH"
        manifest["ergebnis"]["vier_echte_ki_antworten"] = True
        (lauf / "nachweise.json").write_text(json.dumps(manifest), encoding="utf-8")
        result = dienst.pruefe_manifest(lauf)
        self.assertEqual(result["status"], "BLOCKIERT")
        self.assertTrue(any("Agentenbelege" in e for e in result["fehler"]))

    def test_manifest_abweichenden_laufordner_sicher_abweisen(self):
        lauf, _ = self._manifest_fixture()
        self.assertEqual(dienst.pruefe_manifest(self.root)["status"], "BLOCKIERT")
        self.assertEqual(dienst.pruefe_manifest(lauf / "..")["status"], "BLOCKIERT")
        self.assertEqual(dienst.pruefe_manifest(self.root / "nicht_da")["status"], "BLOCKIERT")

    def test_verify_cli_ist_lesend_und_startet_keine_agenten(self):
        lauf, _ = self._manifest_fixture()
        with (
            mock.patch.object(sys, "argv", ["local_service.py", "--verify", str(lauf)]),
            mock.patch.object(dienst.subprocess, "run") as run,
            mock.patch("builtins.print") as output,
        ):
            self.assertEqual(dienst.start(), 0)
        run.assert_not_called()
        self.assertFalse((self.team / "work" / "local_runner.lock").exists())
        self.assertEqual(json.loads(output.call_args.args[0])["status"], "INTEGRITAET_OK")

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
                    "selected_task": {"id": "S-000"},
                    "check_urteil": "bestanden",
                    "tests_ok": True,
                    "tests_anzahl": 3,
                    "agenten": {
                        r: {
                            "rolle": r, "status": "OK", "ki_echt": True,
                            "plan": {"aufgabe_id": "S-000"} if r == "LEAD" else None,
                            "vorschlag_datei": "team/proposals/fake.md" if r == "BRAIN" else None,
                            "urteil": {"urteil": "bestanden"} if r == "CHECK" else None,
                            "werkzeug": {"tests": {"ok": True, "anzahl": 3},
                                        "geheimnis_funde": []} if r == "CHECK" else None,
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
                # Positive Fixture: On-disk role files must match the aggregate
                # report; stand-in process logs alone are insufficient.
                belege = json.loads(p.read_text(encoding="utf-8"))["agenten"]
                for r in rollen:
                    (lauf / (r + ".json")).write_text(
                        json.dumps(belege[r]), encoding="utf-8")
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

    def test_kaputter_stundenbericht_stoppt_ohne_positive_antworten(self):
        for name, inhalt in (
            ("ungültig", "{kaputtes json"),
            ("liste", "[1, 2, 3]"),
            ("null", "null"),
        ):
            with self.subTest(fall=name):
                def fake(cmd, **kwargs):
                    if cmd[2] == "BERICHT":
                        lauf = pathlib.Path(cmd[3])
                        p = self.team / "runs" / (lauf.name + ".json")
                        p.parent.mkdir(parents=True, exist_ok=True)
                        p.write_text(inhalt, encoding="utf-8")
                    return SimpleNamespace(returncode=0, stdout="", stderr="")

                with mock.patch.object(dienst.subprocess, "run", side_effect=fake), \
                     mock.patch("builtins.print") as ausgabe:
                    self.assertEqual(dienst.einmal(), 1)
                self.assertIn("BLOCKIERT", str(ausgabe.call_args))

    def test_nachweispruefung_abweichende_json_typen_blockiert(self):
        lauf = self.team / "work" / "ungueltige-typen"
        lauf.mkdir(parents=True)
        tests = (
            None,
            [],
            {"lauf": lauf.name, "agenten": []},
            {"lauf": lauf.name, "agenten": {},
             "agenten_mit_echter_ki": [["LEAD"]]},
            {"lauf": lauf.name,
             "agenten": {"LEAD": ["statt", "objekt"], "BRAIN": {"ki": ["fake"]},
                         "COMMAND": {"protokoll": ["fake"]}},
             "agenten_mit_echter_ki": list(dienst.ROLES)},
        )
        for fall in tests:
            with self.subTest(fall=repr(fall)[:100]):
                fehler = dienst.pruefe_nachweise(fall, lauf, [])
                self.assertTrue(fehler)

    def test_agenten_start_oserror_stoppt_folgerollen_und_versteckt_details(self):
        anfragen = []
        def fake(cmd, **kwargs):
            anfragen.append(cmd[2])
            if cmd[2] == "LEAD":
                raise OSError("privates-temporäres-detail")
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        with mock.patch.object(dienst.subprocess, "run", side_effect=fake):
            self.assertEqual(dienst.einmal(), 1)
        self.assertEqual(anfragen, ["LEAD", "BERICHT"])
        lauf = next((self.team / "work").glob("*/"))
        prozesse = json.loads((lauf / "prozesse.json").read_text(encoding="utf-8"))
        self.assertEqual(prozesse[0]["exitcode"], -4)
        self.assertTrue(all(x["exitcode"] == -2 for x in prozesse[1:4]))
        self.assertNotIn("privates-temporäres-detail", json.dumps(prozesse))

    def test_strukturell_ungueltiger_bericht_hat_keinen_gruenen_piloten(self):
        def fake(cmd, **kwargs):
            if cmd[2] == "BERICHT":
                lauf = pathlib.Path(cmd[3])
                p = self.team / "runs" / (lauf.name + ".json")
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(json.dumps({"lauf": lauf.name, "agenten": []}),
                             encoding="utf-8")
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        with mock.patch.object(dienst.subprocess, "run", side_effect=fake), \
             mock.patch("builtins.print") as printed:
            self.assertEqual(dienst.einmal(), 1)
        ergebnis = json.loads(printed.call_args.args[0])
        self.assertEqual(ergebnis["status"], "BLOCKIERT")
        self.assertFalse(ergebnis["vier_echte_ki_antworten"])

    def test_prozesskette_exakt_einmal_und_in_richtiger_reihenfolge(self):
        lauf = self.team / "work" / "prozessketten"
        lauf.mkdir(parents=True)
        bericht = {"lauf": lauf.name, "agenten": {}}
        gueltig = [{"rolle": r, "exitcode": 0} for r in (*dienst.ROLES, "BERICHT")]
        fail_muster = [
            gueltig[:4],
            gueltig[:],
            [*gueltig[:2], gueltig[1], *gueltig[3:]],
            list(reversed(gueltig)),
            [*gueltig[:4], {"rolle": "BERICHT", "exitcode": False}],
            [*gueltig[:4], {"rolle": "BERICHT", "exitcode": "0"}],
        ]
        fail_muster[1][1] = {"rolle": "LEAD", "exitcode": 0}
        for schritte in fail_muster:
            with self.subTest(schritte=schritte):
                fehler = dienst.pruefe_nachweise(bericht, lauf, schritte)
                self.assertTrue(any("Prozessbelege" in e for e in fehler))
        ohne_prozessfehler = dienst.pruefe_nachweise(bericht, lauf, gueltig)
        self.assertFalse(any("Prozessbelege" in e for e in ohne_prozessfehler))

    def test_lead_aufgabe_muss_gesamtbericht_und_rotation_entsprechen(self):
        lauf = self.team / "work" / "aufgabe"
        lauf.mkdir(parents=True)
        bericht = {
            "lauf": lauf.name, "aufgabe": "S-002",
            "selected_task": {"id": "S-001"},
            "agenten": {"LEAD": {"rolle": "LEAD", "plan": {"aufgabe_id": "S-000"}}},
        }
        fehler = dienst.pruefe_nachweise(bericht, lauf, [])
        self.assertTrue(any("Aufgaben-ID" in e for e in fehler))
        bericht["aufgabe"] = "S-000"
        bericht["selected_task"] = {"id": "S-000"}
        fehler = dienst.pruefe_nachweise(bericht, lauf, [])
        self.assertFalse(any("Aufgaben-ID" in e for e in fehler))

    def test_check_urteil_und_testzahlen_widerspruch_blockiert(self):
        lauf = self.team / "work" / "check"
        lauf.mkdir(parents=True)
        bericht = {
            "lauf": lauf.name, "check_urteil": "bestanden",
            "tests_ok": True, "tests_anzahl": 99,
            "agenten": {"CHECK": {
                "rolle": "CHECK", "urteil": {"urteil": "abgelehnt"},
                "werkzeug": {"tests": {"ok": True, "anzahl": 3},
                             "geheimnis_funde": []},
            }},
        }
        fehler = dienst.pruefe_nachweise(bericht, lauf, [])
        self.assertTrue(any("CHECK-Urteil" in e for e in fehler))
        self.assertTrue(any("CHECK-Testergebnisse" in e for e in fehler))
        bericht["agenten"]["CHECK"]["urteil"]["urteil"] = "bestanden"
        bericht["tests_anzahl"] = 3
        fehler = dienst.pruefe_nachweise(bericht, lauf, [])
        self.assertFalse(any("CHECK-Urteil" in e or "CHECK-Testergebnisse" in e
                             for e in fehler))

    def test_check_geheimnisscan_darf_nicht_ausgelassen_werden(self):
        lauf = self.team / "work" / "check-scan"
        lauf.mkdir(parents=True)
        bericht = {
            "lauf": lauf.name, "agenten": {
                "CHECK": {"rolle": "CHECK", "urteil": {"urteil": "bestanden"},
                          "werkzeug": {"tests": {"ok": True, "anzahl": 2}}},
            }, "check_urteil": "bestanden", "tests_ok": True,
            "tests_anzahl": 2,
        }
        fehler = dienst.pruefe_nachweise(bericht, lauf, [])
        self.assertTrue(any("Geheimnisscan" in e for e in fehler))
        bericht["agenten"]["CHECK"]["werkzeug"]["geheimnis_funde"] = []
        fehler = dienst.pruefe_nachweise(bericht, lauf, [])
        self.assertFalse(any("Geheimnisscan" in e for e in fehler))

    def test_einzelrollen_identitaet_muss_zur_datei_passen(self):
        lauf = self.team / "work" / "rollen"
        lauf.mkdir(parents=True)
        falsch = {"rolle": "BRAIN", "status": "OK"}
        (lauf / "LEAD.json").write_text(json.dumps(falsch), encoding="utf-8")
        bericht = {"lauf": lauf.name, "agenten": {"LEAD": falsch}}
        fehler = dienst.pruefe_nachweise(bericht, lauf, [])
        self.assertTrue(any("Rollenidentität" in e for e in fehler))

    def test_symlink_zu_externer_agentendatei_ist_keine_evidenz(self):
        lauf = self.team / "work" / "symlink"
        lauf.mkdir(parents=True)
        fremd = self.root / "fremd.json"
        daten = {"rolle": "LEAD", "status": "OK"}
        fremd.write_text(json.dumps(daten), encoding="utf-8")
        try:
            (lauf / "LEAD.json").symlink_to(fremd)
        except (OSError, NotImplementedError):
            self.skipTest("Symbolische Links auf diesem Betriebssystem nicht erlaubt")
        fehler = dienst.pruefe_nachweise(
            {"lauf": lauf.name, "agenten": {"LEAD": daten}}, lauf, [])
        self.assertTrue(any("symbolischer Link" in x for x in fehler))

    def test_bool_zahl_ist_keine_gemessene_testanzahl(self):
        lauf = self.team / "work" / "boolzahl"
        lauf.mkdir(parents=True)
        bericht = {
            "lauf": lauf.name, "agenten": {}, "tests_ok": True,
            "tests_anzahl": True,
        }
        fehler = dienst.pruefe_nachweise(bericht, lauf, [])
        self.assertTrue(any("Unit-Tests nicht erfolgreich" in x for x in fehler))

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
