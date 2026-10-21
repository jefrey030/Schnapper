import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "team"))
from runner import ROLES, choose_task, load_tasks


class TestSchnapper(unittest.TestCase):
    def test_four_roles(self):
        self.assertEqual(ROLES, ("LEAD", "BRAIN", "CHECK", "COMMAND"))

    def test_tasks_format(self):
        self.assertTrue(load_tasks())

    def test_priority(self):
        items = [{"id": "b", "priority": 2, "status": "open"},
                 {"id": "a", "priority": 1, "status": "open"}]
        self.assertEqual(choose_task(items)["id"], "a")

    def test_closed_task_ignored(self):
        self.assertIsNone(choose_task([{"id": "a", "priority": 1, "status": "done"}]))


if __name__ == "__main__":
    unittest.main()
