"""MASTER 82: Manipulierte Prozessdatei darf trotz grüner Exitcodes kein PASS liefern.

Nur synthetische Offline-MOCKs. Keine echten Modell-, Netzwerk- oder Preisabrufe.
"""
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


class TestMaster82Prozessbindung(unittest.TestCase):
    def setUp(self):
        self.fixture = master77.TestMaster77Nachweise(
            "test_mock_is_consistent_but_not_a_live_ai_proof")
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.team = self.fixture.team

    def _run(self, tamper=None):
        # Rollen- und KI-Antworten sind Testdaten, keine echten Inferenzbelege.
        def fake(cmd, **kwargs):
            role, lauf = cmd[2], pathlib.Path(cmd[3])
            if role == "BERICHT":
                source = copy.deepcopy(self.fixture.report)
                source["lauf"] = lauf.name
                for r in dienst.ROLES:
                    (lauf / (r + ".json")).write_text(
                        json.dumps(source["agenten"][r]), encoding="utf-8")
                (lauf / "ki_aufrufe.txt").write_text("4", encoding="utf-8")
                report_dir = self.team / "runs"
                report_dir.mkdir(parents=True, exist_ok=True)
                (report_dir / (lauf.name + ".json")).write_text(
                    json.dumps(source), encoding="utf-8")
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        # Der Dienst schreibt prozesse.json erst NACH allen subprocess.run-
        # Aufrufen, auch nach BERICHT. Der Angriff erfolgt daher am
        # Pruef->Manifest-Uebergang (und nicht schon im BERICHT-Fake).
        original_pruefung = dienst.pruefe_nachweise
        def pruefung_mit_angriff(bericht, lauf, schritte, **kwargs):
            result = original_pruefung(bericht, lauf, schritte, **kwargs)
            if tamper is not None:
                target = lauf / "prozesse.json"
                raw = target.read_text(encoding="utf-8")
                target.write_text(tamper(raw), encoding="utf-8")
            return result

        with mock.patch.object(dienst, "rolle_starten", side_effect=fake), \
             mock.patch.object(dienst, "pruefe_nachweise",
                               side_effect=pruefung_mit_angriff), \
             mock.patch("builtins.print") as printed:
            status = dienst.einmal()
        msg = str(printed.call_args.args[0])
        return status, msg

    def test_unchanged_process_evidence_still_accepts_mock(self):
        code, message = self._run()
        self.assertEqual(code, 0)
        self.assertIn("TECHNISCHER PILOT ERFOLGREICH", message)

    def test_process_role_swapped_after_written_blocks(self):
        def alter(text):
            data = json.loads(text)
            data[0]["rolle"] = "FAKE"
            return json.dumps(data)
        code, text = self._run(alter)
        self.assertEqual(code, 1)
        self.assertIn("BLOCKIERT", text)
        self.assertIn('"vier_echte_ki_antworten": false', text)

    def test_process_exitcode_changed_after_written_blocks(self):
        def alter(text):
            data = json.loads(text)
            data[1]["exitcode"] = 99
            return json.dumps(data)
        code, text = self._run(alter)
        self.assertEqual(code, 1)
        self.assertIn("BLOCKIERT", text)

    def test_process_extra_field_inserted_after_written_blocks(self):
        def alter(text):
            data = json.loads(text)
            data[0]["extra_feld"] = "untrusted"
            return json.dumps(data)
        code, _ = self._run(alter)
        self.assertEqual(code, 1)

    def test_process_reformatted_without_semantic_change_blocks(self):
        code, _ = self._run(lambda text: json.dumps(json.loads(text)))
        self.assertEqual(code, 1)

    def test_process_replaced_with_empty_json_blocks(self):
        code, _ = self._run(lambda text: "{}")
        self.assertEqual(code, 1)

    def test_process_replaced_with_invalid_json_blocks(self):
        code, _ = self._run(lambda text: "{broken")
        self.assertEqual(code, 1)

    def test_process_empty_file_blocks(self):
        code, _ = self._run(lambda text: "")
        self.assertEqual(code, 1)

    def test_process_added_newline_blocks(self):
        code, _ = self._run(lambda text: text + "\n")
        self.assertEqual(code, 1)

    def test_process_trailing_string_blocks(self):
        code, _ = self._run(lambda text: text + "untrusted")
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
