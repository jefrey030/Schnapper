"""MASTER 83 – alle sieben Belege nur fuer die tatsaechlich geprueften Bytes.

Synthetische Offline-Proben: niemals echte Ollama- oder Cloud-Modellaufrufe.
"""
import copy
import hashlib
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


class TestMaster83AllePflichtbelege(unittest.TestCase):
    def setUp(self):
        self.fixture = master77.TestMaster77Nachweise(
            "test_mock_is_consistent_but_not_a_live_ai_proof")
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.team = self.fixture.team

    def _pilot(self, name=None, mutation=None, symlink=False):
        def fake(cmd, **kwargs):
            rolle, lauf = cmd[2], pathlib.Path(cmd[3])
            if rolle == "BERICHT":
                data = copy.deepcopy(self.fixture.report)
                data["lauf"] = lauf.name
                for r in dienst.ROLES:
                    (lauf / (r + ".json")).write_text(
                        json.dumps(data["agenten"][r]), encoding="utf-8")
                (lauf / "ki_aufrufe.txt").write_text("4", encoding="utf-8")
                reports = self.team / "runs"
                reports.mkdir(parents=True, exist_ok=True)
                (reports / (lauf.name + ".json")).write_text(
                    json.dumps(data), encoding="utf-8")
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        original = dienst.pruefe_nachweise
        captured = {}
        def inject(report, lauf, steps, **kwargs):
            errors = original(report, lauf, steps, **kwargs)
            captured["run"] = lauf
            captured["snapshots"] = dict(kwargs.get("beleg_hashes") or {})
            if name is not None:
                if name == "bericht.json":
                    path = self.team / "runs" / (lauf.name + ".json")
                else:
                    path = lauf / name
                raw = path.read_bytes()
                if symlink:
                    outside = self.fixture.root / ("external-" + name)
                    outside.write_bytes(raw)
                    path.unlink()
                    path.symlink_to(outside)
                else:
                    path.write_bytes(mutation(raw))
            return errors

        with mock.patch.object(dienst, "rolle_starten", side_effect=fake), \
             mock.patch.object(dienst, "pruefe_nachweise",
                               side_effect=inject), \
             mock.patch("builtins.print") as out:
            code = dienst.einmal()
        result = json.loads(out.call_args.args[0])
        return code, result, captured

    def assert_blocked(self, filename, operation=lambda b: b + b"\n",
                       symlink=False):
        code, report, capture = self._pilot(filename, operation, symlink)
        self.assertEqual(code, 1)
        self.assertEqual(report["status"], "BLOCKIERT")
        self.assertIs(report["vier_echte_ki_antworten"], False)
        self.assertFalse((capture["run"] / "nachweise.json").exists())

    def test_positive_mock_creates_seven_consistent_file_hashes(self):
        code, result, capture = self._pilot()
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "TECHNISCHER PILOT ERFOLGREICH")
        manifest = json.loads((capture["run"] / "nachweise.json").read_text())
        self.assertEqual(len(manifest["dateien"]), 7)
        self.assertEqual(len(capture["snapshots"]), 6)
        for path, digest in capture["snapshots"].items():
            self.assertEqual(manifest["dateien"][path], digest)

    def test_each_agent_role_mutated_after_validation_is_blocked(self):
        for role in dienst.ROLES:
            with self.subTest(role=role):
                self.assert_blocked(role + ".json")

    def test_hourly_report_mutated_after_validation_is_blocked(self):
        self.assert_blocked("bericht.json")

    def test_call_counter_mutated_after_validation_is_blocked(self):
        self.assert_blocked("ki_aufrufe.txt")

    def test_counter_equivalent_number_different_bytes_is_blocked(self):
        self.assert_blocked("ki_aufrufe.txt", lambda _: b"00000004")

    def test_report_semantically_same_new_format_is_blocked(self):
        self.assert_blocked(
            "bericht.json", lambda b: json.dumps(
                json.loads(b), indent=2).encode("utf-8"))

    def test_role_schema_same_new_format_is_blocked(self):
        self.assert_blocked(
            "LEAD.json", lambda b: json.dumps(
                json.loads(b), indent=2).encode("utf-8"))

    def test_report_replaced_with_symlink_after_validation_is_blocked(self):
        self.assert_blocked("bericht.json", symlink=True)

    def test_role_replaced_with_symlink_after_validation_is_blocked(self):
        self.assert_blocked("CHECK.json", symlink=True)

    def test_counter_replaced_with_symlink_after_validation_is_blocked(self):
        self.assert_blocked("ki_aufrufe.txt", symlink=True)

    def test_changed_role_text_after_validation_is_blocked(self):
        def mutate(raw):
            obj = json.loads(raw)
            obj["ki"]["text"] += " MANIPULIERT"
            return json.dumps(obj).encode("utf-8")
        self.assert_blocked("BRAIN.json", mutate)

    def test_checked_role_and_counter_snapshots_are_byte_hashes(self):
        hashes = {}
        err = dienst.pruefe_nachweise(
            self.fixture.report, self.fixture.lauf,
            self.fixture.steps, beleg_hashes=hashes)
        self.assertEqual(err, [])
        self.assertEqual(len(hashes), 5)
        paths = [self.fixture.lauf / (r + ".json") for r in dienst.ROLES]
        paths.append(self.fixture.lauf / "ki_aufrufe.txt")
        for path in paths:
            key = str(path.relative_to(self.fixture.root))
            self.assertEqual(hashes[key],
                             hashlib.sha256(path.read_bytes()).hexdigest())

    def test_missing_counter_never_produces_full_snapshot(self):
        (self.fixture.lauf / "ki_aufrufe.txt").unlink()
        hashes = {}
        err = dienst.pruefe_nachweise(
            self.fixture.report, self.fixture.lauf,
            self.fixture.steps, beleg_hashes=hashes)
        self.assertTrue(any("Lokaler KI-Aufrufzähler" in e for e in err))
        self.assertEqual(len(hashes), 4)

    def test_corrupt_role_never_produces_complete_snapshot(self):
        (self.fixture.lauf / "LEAD.json").write_text("{BROKEN")
        hashes = {}
        err = dienst.pruefe_nachweise(
            self.fixture.report, self.fixture.lauf,
            self.fixture.steps, beleg_hashes=hashes)
        self.assertTrue(any("unlesbar/ungültig" in e for e in err))
        self.assertEqual(len(hashes), 4)


if __name__ == "__main__":
    unittest.main()
