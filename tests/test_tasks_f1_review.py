"""F1 (#36): S-009 bis S-013 stehen auf "review" und werden nicht erneut vergeben.

Lauf 20261023-0529 hat die fünf Aufgaben bewusst auf "review" gesetzt, weil ihre
Umsetzung in eigenen Draft-PRs liegt. Diese Tests sichern ab, dass weder
team/runner.py:choose_task() noch die Auswahl für LEAD in team/agent.py
(status == "open") sie doppelt vergibt. lead() wird echt aufgerufen, mit einer
KI-Attrappe und einer Kopie der Aufgaben. Nur Standardbibliothek, kein Netz.
"""
import copy
import json
import pathlib
import re
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "team"))
from runner import choose_task, load_tasks
import agent  # noqa: E402

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


class FakeKI:
    """Attrappe für die KI: merkt sich die Anfrage und liefert eine feste Wahl."""

    def __init__(self, wahl):
        self.wahl = wahl
        self.aufrufe = 0
        self.nutzer = None

    def frage(self, system, nutzer):
        self.aufrufe += 1
        self.nutzer = json.loads(nutzer)
        return {"text": json.dumps({"aufgabe_id": self.wahl})}


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

    def _lead(self, wahl, aufgaben=None):
        """Ruft team/agent.py:lead() echt auf – mit KI-Attrappe, ohne Netz, ohne team/runs."""
        fake = FakeKI(wahl)
        with mock.patch.object(agent, "previous_task_id", return_value=None):
            if aufgaben is None:
                erg = agent.lead(None, fake)
            else:
                with mock.patch.object(agent, "load_tasks", return_value=aufgaben):
                    erg = agent.lead(None, fake)
        return erg, fake

    def _kopie_mit_s011_offen(self):
        kopie = copy.deepcopy(self.tasks)
        next(t for t in kopie if t["id"] == "S-011")["status"] = "open"
        return kopie

    def test_c_lead_bietet_review_nicht_an_und_lehnt_review_wahl_ab(self):
        # Fall A: KI wählt S-009 (review) -> FEHLER; angebotene Liste ohne review-Aufgaben.
        kopie = self._kopie_mit_s011_offen()
        kopie_vorher = copy.deepcopy(kopie)
        erg, fake = self._lead("S-009", kopie)
        self.assertEqual(erg["status"], "FEHLER")
        self.assertIn("ungültige Aufgabe", erg["fehler"])
        self.assertEqual(erg["werkzeug"]["offene_aufgaben"], ["S-011"])
        angeboten = {t["id"] for t in fake.nutzer["offene_aufgaben"]}
        self.assertEqual(angeboten & set(ERWARTET), {"S-011"})
        self.assertEqual(kopie, kopie_vorher)
        self.assertEqual(load_tasks(), self.tasks)

    def test_c2_selbstpruefung_lead_nimmt_offene_kopie_an(self):
        # Fall B: S-011 in der Kopie offen und gewählt -> OK.
        kopie = self._kopie_mit_s011_offen()
        kopie_vorher = copy.deepcopy(kopie)
        erg, fake = self._lead("S-011", kopie)
        self.assertEqual(erg["status"], "OK")
        self.assertEqual(erg["plan"]["aufgabe_id"], "S-011")
        self.assertEqual(kopie, kopie_vorher)
        self.assertEqual(load_tasks(), self.tasks)

    def test_c3_lead_mit_echten_aufgaben_ohne_ki_frage(self):
        # Fall C: echtes team/tasks.json -> KEINE AUFGABE, KI wird nicht befragt.
        erg, fake = self._lead("S-009")
        self.assertEqual(erg["status"], "KEINE AUFGABE")
        self.assertEqual(erg["werkzeug"]["offene_aufgaben"], [])
        self.assertEqual(fake.aufrufe, 0)
        self.assertEqual(load_tasks(), self.tasks)

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
