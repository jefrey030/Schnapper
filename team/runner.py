"""SCHNAPPER: Aufgabenverwaltung (Laden, Rotation) für das Vier-Agenten-Team.

Die Agenten selbst laufen in team/agent.py. Dieses Modul enthält bewusst
keinen Regelmodus mehr, der sich als KI ausgeben könnte."""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEAM = ROOT / "team"
ROLES = ("LEAD", "BRAIN", "CHECK", "COMMAND")


def load_tasks(path=TEAM / "tasks.json"):
    obj = json.loads(path.read_text(encoding="utf-8"))
    tasks = obj.get("tasks", [])
    if not isinstance(tasks, list):
        raise ValueError("tasks muss eine Liste sein")
    ids = set()
    for task in tasks:
        if not isinstance(task, dict) or not all(k in task for k in ("id", "title", "priority", "status")):
            raise ValueError("Ungültiges Aufgabenformat")
        if task["id"] in ids:
            raise ValueError("Doppelte Aufgabe")
        ids.add(task["id"])
        if not isinstance(task["priority"], int):
            raise ValueError("Ungültige Priorität")
    return tasks


def choose_task(tasks, previous_id=None):
    """Choose open tasks in priority order, cycling between hourly runs."""
    active = sorted((t for t in tasks if t.get("status") == "open"),
                    key=lambda t: (t["priority"], t["id"]))
    if not active:
        return None
    last_index = next((i for i, task in enumerate(active) if task["id"] == previous_id), None)
    return active[(last_index + 1) % len(active)] if last_index is not None else active[0]


def previous_task_id(runs_dir=TEAM / "runs"):
    """Read the most recent persisted report, without altering task status."""
    # Fehlgeschlagene oder unvollständige Stundenberichte dürfen die
    # Aufgabenrotation nicht auf die erste Aufgabe zurücksetzen.
    # Suche deshalb rückwärts den letzten Bericht mit gültiger Aufgaben-ID.
    for bericht in reversed(sorted(runs_dir.glob("*.json"))):
        try:
            data = json.loads(bericht.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(data, dict):
            continue
        selected = data.get("selected_task")
        aufgabe = selected.get("id") if isinstance(selected, dict) else None
        if isinstance(aufgabe, str) and aufgabe.strip():
            return aufgabe
    return None


if __name__ == "__main__":
    print("Der Regelmodus wurde entfernt. Agenten starten mit: python team/agent.py <ROLLE> <laufordner>")
    sys.exit(2)
