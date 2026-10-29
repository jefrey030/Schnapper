"""F1 (#36): S-009 bis S-013 stehen auf "review" und werden nicht erneut vergeben.

Lauf 20261023-0529 hat die fünf Aufgaben bewusst auf "review" gesetzt, weil ihre
Umsetzung in eigenen Draft-PRs liegt. Diese Tests sichern ab, dass weder
team/runner.py:choose_task() noch die Auswahl für LEAD in team/agent.py
(status == "open") sie doppelt vergibt. Nur Standardbibliothek, kein Netz.
"""
import copy
import pathlib
import re
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "team"))
from runner import choose_task, load_tasks

ERWARTET = {
    "S-009": ("#39", "agent/master/20261022-21"),
    "S-010": ("#40", "agent/master/20261022-22"),
    "S-011": ("#41", "agent/master/20261022-2238"),
    "S-012": ("#44", "agent/master/20261022-23"),
    "S-013": ("#45", "agent/master/20261023-01"),
}


def _enthaelt(text, token):
    """Token als ganzes Wort (z. B. "#4" passt nicht auf "#44", "-23" nicht auf "-2338")."""
    return re.search(r"(?<![\w/-])" + re.escape(token) + r"(?![\w-])", text) is not None


class TestF1ReviewStatus(unittest.TestCase):
    def setUp(self):
        self.tasks = load_tasks()
        self.by_id = {t["id"]: t for t in self.tasks}

    def test_a_status_review_und_hinweis_mit_pr_und_branch(self):
        for task_id, (pr, branch) in ERWARTET.items():
            with self.subTest(task=task_id):
                self.assertIn(task_id, self.by_id)
                task = self.by_id[task_id]
                self.assertEqual(task["status"], "review")
                hinweis = task.get("hinweis", "")
                self.assertTrue(_enthaelt(hinweis, pr), f"{pr} fehlt im Hinweis von {task_id}")
                self.assertTrue(_enthaelt(hinweis, branch), f"{branch} fehlt im Hinweis von {task_id}")

    def test_b_choose_task_vergibt_keine_review_aufgabe(self):
        for previous in [None] + [t["id"] for t in self.tasks]:
            with self.subTest(previous_id=previous):
                chosen = choose_task(self.tasks, previous_id=previous)
                if chosen is not None:
                    self.assertNotIn(chosen["id"], ERWARTET)

    def test_c_lead_liste_enthaelt_keine_review_aufgabe(self):
        # Nachbildung der Auswahl in team/agent.py lead(): nur status == "open".
        offen = [t for t in self.tasks if t.get("status") == "open"]
        self.assertFalse({t["id"] for t in offen} & set(ERWARTET))

    def test_d_selbstpruefung_offene_kopie_wird_gewaehlt(self):
        kopie = copy.deepcopy(self.tasks)
        next(t for t in kopie if t["id"] == "S-011")["status"] = "open"
        gewaehlt = {(choose_task(kopie, previous_id=p) or {}).get("id")
                    for p in [None] + [t["id"] for t in kopie]}
        self.assertIn("S-011", gewaehlt)
        # Original unverändert
        self.assertEqual(self.by_id["S-011"]["status"], "review")
        self.assertEqual(load_tasks(), self.tasks)


if __name__ == "__main__":
    unittest.main()
