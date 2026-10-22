import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "team"))
from runner import ROLES, choose_task, load_tasks, previous_task_id


class TestSchnapper(unittest.TestCase):
    def test_four_roles(self):
        self.assertEqual(ROLES, ("LEAD", "BRAIN", "CHECK", "COMMAND"))

    def test_tasks_format(self):
        self.assertTrue(load_tasks())

    def test_offene_aufgaben_werden_waehlbar(self):
        # Ein abgearbeiteter Backlog darf später legal leer werden.
        tasks = load_tasks()
        aktive = [t for t in tasks if t.get("status") == "open"]
        ausgewaehlt = choose_task(tasks)
        if aktive:
            self.assertIsNotNone(ausgewaehlt)
            self.assertIn(ausgewaehlt["id"], {t["id"] for t in aktive})
        else:
            self.assertIsNone(ausgewaehlt)

    def test_priority(self):
        items = [{"id": "b", "priority": 2, "status": "open"},
                 {"id": "a", "priority": 1, "status": "open"}]
        self.assertEqual(choose_task(items)["id"], "a")

    def test_closed_task_ignored(self):
        self.assertIsNone(choose_task([{"id": "a", "priority": 1, "status": "done"}]))

    def test_no_paid_api_in_runner(self):
        runner = (pathlib.Path(__file__).resolve().parents[1] / "team" / "runner.py").read_text(encoding="utf-8")
        self.assertNotIn("api.anthropic.com", runner)
        self.assertNotIn("ANTHROPIC_API_KEY", runner)

    def test_rotation_across_open_tasks(self):
        items = [{"id": "b", "priority": 2, "status": "open"},
                 {"id": "a", "priority": 1, "status": "open"},
                 {"id": "closed", "priority": 0, "status": "done"}]
        self.assertEqual(choose_task(items)["id"], "a")
        self.assertEqual(choose_task(items, "a")["id"], "b")
        self.assertEqual(choose_task(items, "b")["id"], "a")
        self.assertEqual(choose_task(items, "unknown")["id"], "a")

    def test_last_task_recovered_from_report(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = pathlib.Path(directory)
            self.assertIsNone(previous_task_id(folder))
            (folder / "20261021T130000Z.json").write_text(
                json.dumps({"selected_task": {"id": "S-000"}}), encoding="utf-8")
            self.assertEqual(previous_task_id(folder), "S-000")

    def test_malformed_report_is_safe(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = pathlib.Path(directory)
            (folder / "20261021T130000Z.json").write_text(
                "{", encoding="utf-8")
            self.assertIsNone(previous_task_id(folder))

    def test_rotation_ignoriert_defekten_neusten_bericht(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = pathlib.Path(directory)
            (folder / "20261021T130000Z.json").write_text(
                json.dumps({"selected_task": {"id": "S-005"}}), encoding="utf-8")
            (folder / "20261021T140000Z.json").write_text("{", encoding="utf-8")
            self.assertEqual(previous_task_id(folder), "S-005")

    def test_rotation_ignoriert_berichte_ohne_ausgewaehlte_aufgabe(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = pathlib.Path(directory)
            (folder / "20261021T130000Z.json").write_text(
                json.dumps({"selected_task": {"id": "S-004"}}), encoding="utf-8")
            (folder / "20261021T140000Z.json").write_text(
                json.dumps({"selected_task": None}), encoding="utf-8")
            (folder / "20261021T150000Z.json").write_text(
                json.dumps({"selected_task": {"id": 123}}), encoding="utf-8")
            (folder / "20261021T160000Z.json").write_text(
                json.dumps(["kein Bericht"]), encoding="utf-8")
            self.assertEqual(previous_task_id(folder), "S-004")


if __name__ == "__main__":
    unittest.main()
