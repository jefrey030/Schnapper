"""MASTER 77: Nur Offline-MOCKs; kein Ollama, kein Cloudflare und keine bezahlte API."""
import copy
import json
import pathlib
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "team"))
import local_service as dienst


class TestMaster77Nachweise(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = pathlib.Path(temp.name)
        self.team = self.root / "team"
        self.lauf = self.team / "work" / "mock77"
        self.lauf.mkdir(parents=True)
        for name, obj in (("ROOT", self.root), ("TEAM", self.team)):
            patcher = mock.patch.object(dienst, name, obj)
            patcher.start()
            self.addCleanup(patcher.stop)
        proposal = self.team / "proposals" / "mock77.md"
        proposal.parent.mkdir()
        proposal.write_text("FAKE-Proposal, nur Unit-Test", encoding="utf-8")
        self.roles = {}
        for role in dienst.ROLES:
            agent = {
                "rolle": role,
                "status": "OK",
                "ki_echt": True,
                "ki": {
                    "laufzeit": "Ollama lokal (keine bezahlte KI-API)",
                    "modell": "qwen2.5:1.5b",
                    "text": "Simulierte Antwort, KEINE echte KI",
                    "antwort_id": "lokal-mock77-" + role,
                    "antwort_id_typ": "nur-lokale-kennung",
                    "ollama_beleg": {
                        "modell_antwort": "qwen2.5:1.5b",
                        "done": True, "done_reason": "stop",
                        "rolle": "assistant",
                        "created_at": "2026-10-25T13:00:00Z",
                        "prompt_eval_count": 10, "eval_count": 2,
                    },
                },
                "plan": {"aufgabe_id": "S-000"} if role == "LEAD" else None,
                "vorschlag_datei": "team/proposals/mock77.md" if role == "BRAIN" else None,
                "urteil": {"urteil": "bestanden"} if role == "CHECK" else None,
                "werkzeug": {"tests": {"ok": True, "anzahl": 7},
                             "geheimnis_funde": []} if role == "CHECK" else {},
                "protokoll": {"freigabe": "ja", "naechster_schritt": "Manuell pruefen"}
                             if role == "COMMAND" else None,
            }
            self.roles[role] = agent
            (self.lauf / (role + ".json")).write_text(
                json.dumps(agent, ensure_ascii=False), encoding="utf-8")
        (self.lauf / "ki_aufrufe.txt").write_text("4", encoding="utf-8")
        self.report = {
            "lauf": self.lauf.name,
            "team_einsatzbereit": True,
            "agenten_mit_echter_ki": list(dienst.ROLES),
            "ki_aufrufe": 4,
            "tests_ok": True,
            "tests_anzahl": 7,
            "check_urteil": "bestanden",
            "agenten": copy.deepcopy(self.roles),
        }
        self.steps = [{"rolle": role, "exitcode": 0}
                      for role in (*dienst.ROLES, "BERICHT")]

    def check(self):
        return dienst.pruefe_nachweise(self.report, self.lauf, self.steps)

    def assert_blocked_by(self, phrase):
        self.assertTrue(any(phrase in f for f in self.check()), self.check())

    def test_mock_is_consistent_but_not_a_live_ai_proof(self):
        self.assertEqual(self.check(), [])

    def test_no_independent_counter_no_success(self):
        path = self.lauf / "ki_aufrufe.txt"
        for value in (None, "3", "5", "garbage", ""):
            with self.subTest(counter=value):
                if value is None:
                    path.unlink(missing_ok=True)
                else:
                    path.write_text(value, encoding="utf-8")
                self.assert_blocked_by("Lokaler KI-Aufrufzähler")

    def test_counter_symlink_is_not_evidence(self):
        path = self.lauf / "ki_aufrufe.txt"
        path.unlink()
        external = self.root / "counter.txt"
        external.write_text("4", encoding="utf-8")
        path.symlink_to(external)
        self.assert_blocked_by("Lokaler KI-Aufrufzähler")

    def test_check_denial_cannot_be_overruled_by_aggregate(self):
        self.report["agenten"]["CHECK"]["urteil"]["urteil"] = "abgelehnt"
        (self.lauf / "CHECK.json").write_text(
            json.dumps(self.report["agenten"]["CHECK"]), encoding="utf-8")
        self.assert_blocked_by("CHECK hat nicht bestanden")

    def test_missing_or_positive_secret_scan_blocks(self):
        for value in (None, ["test-fund"], "unbekannt"):
            with self.subTest(scan=value):
                check = self.report["agenten"]["CHECK"]
                if value is None:
                    check["werkzeug"].pop("geheimnis_funde", None)
                else:
                    check["werkzeug"]["geheimnis_funde"] = value
                (self.lauf / "CHECK.json").write_text(
                    json.dumps(check), encoding="utf-8")
                self.assert_blocked_by("CHECK-Geheimnisscan")

    def test_check_tests_must_match_aggregate(self):
        for ok, n in ((False, 7), (True, 0), (True, 6), (True, "7")):
            with self.subTest(ok=ok, n=n):
                check = self.report["agenten"]["CHECK"]
                check["werkzeug"]["tests"] = {"ok": ok, "anzahl": n}
                (self.lauf / "CHECK.json").write_text(
                    json.dumps(check), encoding="utf-8")
                self.assert_blocked_by("CHECK-Tests")

    def test_role_file_tamper_blocks(self):
        path = self.lauf / "LEAD.json"
        obj = json.loads(path.read_text(encoding="utf-8"))
        obj["ki"]["antwort_id"] = "lokal-tampered"
        path.write_text(json.dumps(obj), encoding="utf-8")
        self.assert_blocked_by("widersprechen sich")

    def test_role_symlink_blocks(self):
        path = self.lauf / "LEAD.json"
        external = self.root / "lead.json"
        external.write_bytes(path.read_bytes())
        path.unlink()
        path.symlink_to(external)
        self.assert_blocked_by("Symlink")

    def test_malformed_structures_fail_closed_without_crash(self):
        for bad in ([{"rolle": "LEAD"}], "not-an-object", 12):
            with self.subTest(bad=bad):
                self.report["agenten"] = bad
                self.assert_blocked_by("Agentenbericht muss ein JSON-Objekt sein")
        self.report["agenten"] = copy.deepcopy(self.roles)
        self.report["agenten"]["LEAD"] = ["not a role object"]
        self.assert_blocked_by("kein Objekt")

    def test_unreadable_json_report_is_blocked_without_ai(self):
        # Vollstaendig simulierter Unterprozess; kein Netzwerk/LLM.
        def run(cmd, **kwargs):
            if cmd[2] == "BERICHT":
                path = self.team / "runs" / (pathlib.Path(cmd[3]).name + ".json")
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("{not json", encoding="utf-8")
            return SimpleNamespace(stdout="", stderr="", returncode=0)
        with mock.patch.object(dienst, "rolle_starten", side_effect=run), \
             mock.patch("builtins.print") as printed:
            self.assertEqual(dienst.einmal(), 1)
            lines = "\n".join(str(x) for x in printed.call_args_list)
            self.assertIn("BLOCKIERT", lines)


if __name__ == "__main__":
    unittest.main()
