"""P3: defekte KI-Rollenbelege blockieren – ausschließlich Offline-/Mock-Tests."""
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "team"))
import agent  # noqa: E402
import local_service as dienst  # noqa: E402


class TestP3RollenBelege(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        self.team = self.root / "team"
        self.lauf = self.team / "work" / "fake-run"
        self.lauf.mkdir(parents=True)
        p = mock.patch.object(agent, "TEAM", self.team)
        p.start()
        self.addCleanup(p.stop)

    def write(self, rolle, content):
        (self.lauf / f"{rolle}.json").write_text(content, encoding="utf-8")

    def test_lies_nimmt_nur_kleine_json_objekte(self):
        self.assertIsNone(agent.lies(self.lauf, "LEAD"))
        for text in ("{kaputt", "[]", "42", '"string"', "null", " " * 128_010):
            with self.subTest(text=text[:18]):
                self.write("LEAD", text)
                self.assertIsNone(agent.lies(self.lauf, "LEAD"))
        self.write("LEAD", '{"status":"OK"}')
        self.assertEqual(agent.lies(self.lauf, "LEAD")["status"], "OK")

    def test_brain_ungueltiger_lead_plan_spart_ki_aufruf(self):
        fake = mock.Mock()
        for plan in (None, {}, {"aufgabe_id": "../ausserhalb"},
                     {"aufgabe_id": "x/y"}, {"aufgabe_id": 123},
                     {"aufgabe_id": "x" * 80}):
            with self.subTest(plan=plan):
                self.write("LEAD", json.dumps({"status": "OK", "plan": plan}))
                with mock.patch.object(agent, "repo_ueberblick",
                                       side_effect=AssertionError("kein Repo-Zugriff")):
                    result = agent.brain(self.lauf, fake)
                self.assertEqual(result["status"], "ÜBERSPRUNGEN")
                fake.frage.assert_not_called()
        self.assertFalse((self.team / "proposals").exists())

    def test_check_fehlende_vorrollen_oder_ki_text_keine_inferenz(self):
        fake = mock.Mock()
        with mock.patch.object(agent, "tests_ausfuehren",
                               return_value={"ok": True, "anzahl": 2, "ausgabe_ende": ""}), \
             mock.patch.object(agent, "geheimnis_scan", return_value=[]):
            self.write("BRAIN", '{"status":"OK","ki":{"text":"Vorschlag"}}')
            for lead in (None, '{"status":"OK"}', '{"status":"OK","plan":"text"}',
                         '{"status":"FEHLER","plan":{}}'):
                if lead is None:
                    (self.lauf / "LEAD.json").unlink(missing_ok=True)
                else:
                    self.write("LEAD", lead)
                result = agent.check(self.lauf, fake)
                self.assertEqual(result["status"], "ÜBERSPRUNGEN")
                fake.frage.assert_not_called()

            self.write("LEAD", '{"status":"OK","plan":{"aufgabe_id":"S-000"}}')
            for ki in ("kaputt", [], {}, None):
                with self.subTest(ki=ki):
                    self.write("BRAIN", json.dumps({"status": "OK", "ki": ki}))
                    result = agent.check(self.lauf, fake)
                    self.assertEqual(result["status"], "ÜBERSPRUNGEN")
                    fake.frage.assert_not_called()

    def test_check_defekte_tests_oder_scan_sperren_vor_inferenz(self):
        self.write("LEAD", '{"status":"OK","plan":{"aufgabe_id":"S-000"}}')
        self.write("BRAIN", '{"status":"OK","ki":{"text":"Vorschlag"}}')
        fake = mock.Mock()
        for tests, funde in (
            ({"ok": False, "anzahl": 2}, []),
            ({"ok": True, "anzahl": 0}, []),
            ({"ok": True}, []),
            ({"ok": True, "anzahl": 2}, ["sicherheitsbefund"]),
        ):
            with self.subTest(tests=tests, funde=funde), \
                 mock.patch.object(agent, "tests_ausfuehren", return_value=tests), \
                 mock.patch.object(agent, "geheimnis_scan", return_value=funde):
                result = agent.check(self.lauf, fake)
                self.assertEqual(result["status"], "ÜBERSPRUNGEN")
                fake.frage.assert_not_called()

    def test_unit_tests_bei_timeout_oder_prozessfehler_niemals_ok(self):
        for fehler in (subprocess.TimeoutExpired(cmd="python", timeout=120),
                       FileNotFoundError("python fehlt")):
            with self.subTest(fehler=type(fehler).__name__), \
                 mock.patch.object(agent.subprocess, "run", side_effect=fehler):
                result = agent.tests_ausfuehren()
                self.assertFalse(result["ok"])
                self.assertEqual(result["anzahl"], 0)


class TestP3LokalerBericht(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        self.team = self.root / "team"
        self.team.mkdir()
        for name, value in (("ROOT", self.root), ("TEAM", self.team)):
            p = mock.patch.object(dienst, name, value)
            p.start()
            self.addCleanup(p.stop)

    def test_pilot_mit_korruptem_oder_uebergrossem_bericht_blockiert(self):
        for raw in ("{defekt", "[]", "0", " " * 1_000_010):
            with self.subTest(raw=raw[:12]):
                def fake(cmd, **_kwargs):
                    if cmd[2] == "BERICHT":
                        lauf = pathlib.Path(cmd[3])
                        path = self.team / "runs" / f"{lauf.name}.json"
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_text(raw, encoding="utf-8")
                    return SimpleNamespace(returncode=0, stdout="", stderr="")

                with mock.patch.object(dienst.subprocess, "run", side_effect=fake), \
                     mock.patch("builtins.print") as printed:
                    self.assertEqual(dienst.einmal(), 1)
                    self.assertTrue(any("BLOCKIERT" in str(c) for c in printed.call_args_list))


if __name__ == "__main__":
    unittest.main()
