"""Vorgeschlagene Aufgaben (status "proposed") brauchen Jefreys Freigabe.

Weder die Aufgabenrotation noch der LEAD-Agent dürfen sie automatisch wählen."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "team"))
from runner import choose_task, load_tasks

ERLAUBTE_STATUS = {"open", "in_progress", "review", "proposed", "done"}


class TestVorschlaege(unittest.TestCase):
    def test_proposed_wird_nie_gewaehlt(self):
        items = [{"id": "S-9", "priority": 0, "status": "proposed", "title": "x"}]
        self.assertIsNone(choose_task(items))

    def test_open_hat_vorrang_vor_proposed_mit_hoeherer_prioritaet(self):
        items = [{"id": "P", "priority": 0, "status": "proposed", "title": "x"},
                 {"id": "O", "priority": 9, "status": "open", "title": "y"}]
        self.assertEqual(choose_task(items)["id"], "O")

    def test_lead_agent_filtert_nur_open(self):
        quelle = (pathlib.Path(__file__).resolve().parents[1] / "team" / "agent.py").read_text(encoding="utf-8")
        self.assertIn('t.get("status") == "open"', quelle)

    def test_echte_aufgaben_haben_gueltigen_status(self):
        for t in load_tasks():
            self.assertIn(t["status"], ERLAUBTE_STATUS, t["id"])

    def test_vorschlaege_haben_akzeptanzkriterien(self):
        vorschlaege = [t for t in load_tasks() if t["status"] == "proposed"]
        for t in vorschlaege:
            self.assertIsInstance(t.get("acceptance"), list, t["id"])
            self.assertGreaterEqual(len(t["acceptance"]), 2, t["id"])

    def test_hinweis_ist_nichtleerer_text_und_aendert_status_nicht(self):
        for t in load_tasks():
            if "hinweis" in t:
                self.assertIsInstance(t["hinweis"], str, t["id"])
                self.assertTrue(t["hinweis"].strip(), t["id"])
        mit_hinweis = [{"id": "P", "priority": 0, "status": "proposed", "title": "x", "hinweis": "PR #10"}]
        self.assertIsNone(choose_task(mit_hinweis))


if __name__ == "__main__":
    unittest.main()
