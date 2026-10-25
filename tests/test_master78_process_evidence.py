"""MASTER 78: Rollenidentitaet und Manifest-Fehlersperren, ausschliesslich Offline-MOCKs."""
import copy
import json
import pathlib
import sys
import unittest
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import test_master77_proof as master77
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "team"))
import local_service as dienst


class TestMaster78Prozessbelege(unittest.TestCase):
    def setUp(self):
        # Bestehende isolierte MASTER-77-Fixture wiederverwenden, ohne
        # deren Testmethoden doppelt in unittest einzusammeln.
        self.fixture = master77.TestMaster77Nachweise(
            "test_mock_is_consistent_but_not_a_live_ai_proof")
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)

    def assert_blocked(self):
        fehler = self.fixture.check()
        self.assertTrue(
            any("Agentenprozessfolge" in e for e in fehler), fehler)

    def test_korrekte_fuenf_rollen_mock_ok(self):
        self.assertEqual(self.fixture.check(), [])

    def test_doppelte_rolle_anstelle_bericht_blockiert(self):
        self.fixture.steps[-1]["rolle"] = "LEAD"
        self.assert_blocked()

    def test_doppelte_rolle_anstelle_check_blockiert(self):
        self.fixture.steps[2]["rolle"] = "BRAIN"
        self.assert_blocked()

    def test_vertauchte_rolle_blockiert(self):
        self.fixture.steps[0], self.fixture.steps[1] = (
            self.fixture.steps[1], self.fixture.steps[0])
        self.assert_blocked()

    def test_fremde_rolle_blockiert(self):
        self.fixture.steps[0]["rolle"] = "ADMIN"
        self.assert_blocked()

    def test_leere_und_unvollstaendige_prozessliste_blockiert(self):
        for steps in ([], self.fixture.steps[:3]):
            with self.subTest(steps=steps):
                self.fixture.steps = steps
                self.assert_blocked()

    def test_nicht_objekt_in_prozessliste_blockiert_ohne_crash(self):
        self.fixture.steps[1] = "invalid"
        self.assert_blocked()

    def test_falscher_datentyp_prozessliste_blockiert(self):
        self.fixture.steps = tuple(self.fixture.steps)
        self.assert_blocked()

    def test_bool_exitcode_wird_nicht_als_null_akzeptiert(self):
        self.fixture.steps[0]["exitcode"] = False
        self.assert_blocked()

    def test_nicht_null_exitcode_blockiert(self):
        self.fixture.steps[0]["exitcode"] = 1
        self.assert_blocked()

    def _simulate_once(self, tamper_role=False, unreadable_hash=False):
        fixture = self.fixture
        extern = fixture.root / "external.json"
        extern.write_text("private fixture; kein Geheimnis", encoding="utf-8")
        report_dir = fixture.team / "runs"
        report_dir.mkdir(exist_ok=True)
        def fake(cmd, **kwargs):
            rolle, lauf = cmd[2], pathlib.Path(cmd[3])
            if rolle == "BERICHT":
                daten = copy.deepcopy(fixture.report)
                daten["lauf"] = lauf.name
                for r in dienst.ROLES:
                    pfad = lauf / (r + ".json")
                    if tamper_role and r == "LEAD":
                        pfad.symlink_to(extern)
                    else:
                        pfad.write_text(json.dumps(daten["agenten"][r]),
                                        encoding="utf-8")
                (lauf / "ki_aufrufe.txt").write_text("4", encoding="utf-8")
                (report_dir / (lauf.name + ".json")).write_text(
                    json.dumps(daten), encoding="utf-8")
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        # MASTER 79 liest ueber einen sicheren OS-Deskriptor, nicht mehr
        # ueber pathlib.Path.read_bytes. I/O-Fehler gezielt dort simulieren.
        hash_original = dienst._hash_sicher
        def guarded_hash(path):
            if unreadable_hash and path.name == "prozesse.json":
                raise OSError("MOCK: Dateizugriff verweigert")
            return hash_original(path)
        with mock.patch.object(dienst, "rolle_starten", side_effect=fake), \
             mock.patch.object(dienst, "_hash_sicher", side_effect=guarded_hash), \
             mock.patch("builtins.print") as printed:
            status = dienst.einmal()
        self.assertEqual(status, 1)
        self.assertEqual(extern.read_text(encoding="utf-8"),
                         "private fixture; kein Geheimnis")
        self.assertIn("BLOCKIERT", str(printed.call_args_list))

    def test_manifest_folgt_keinem_rollen_symlink(self):
        self._simulate_once(tamper_role=True)

    def test_unlesbare_manifestdatei_blockiert_kontrolliert(self):
        self._simulate_once(unreadable_hash=True)


if __name__ == "__main__":
    unittest.main()
