"""SCHNAPPER: stündlich vier getrennte lokale KI-Entwürfe erstellen und prüfen."""
import datetime as dt
import json
import pathlib
import subprocess
import sys

from brain import MODEL, ROLES, LocalBrainError, ask, available, validate

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEAM = ROOT / "team"


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


def choose_task(tasks):
    active = [t for t in tasks if t.get("status") == "open"]
    return min(active, key=lambda t: (t["priority"], t["id"])) if active else None


def test_result():
    p = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
                       cwd=ROOT, capture_output=True, text=True, timeout=90)
    output = (p.stdout + "\n" + p.stderr)[-3500:]
    return {"ok": p.returncode == 0, "details": output}


def save_report(data, timestamp):
    stamp = timestamp.strftime("%Y%m%dT%H%M%S%fZ")
    report = TEAM / "runs" / (stamp + ".json")
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")
    task = data.get("selected_task")
    rows = [
        "# SCHNAPPER – letzter wirklicher Stundenlauf", "",
        "- UTC: " + data["timestamp_utc"],
        "- Aufgabe: " + (task["id"] if task else "keine"),
        "- KI-Modell: " + (MODEL if data["local_model_available"] else "nicht erreichbar"),
        "- Lokale Python-Tests: " + ("bestanden" if data["tests"]["ok"] else "FEHLER"),
        "- Vier Rollen formal gültig: " + ("ja" if data["accepted"] else "NEIN"),
        "- WICHTIG: KI-Entwürfe sind kein Beleg für fertige App-Funktionen.", "",
        "| Rolle | Ergebnis | Strukturprüfung |",
        "| --- | --- | --- |"
    ]
    for role in ROLES:
        value = data["agents"][role]
        rows.append("| " + role + " | " + value["status"] + " | "
                    + value["check"] + " |")
    rows += ["", "Beleg: " + str(report.relative_to(ROOT)),
             "", "Keine automatischen Änderungen an App-Code, Aufgabenstatus oder Zahlungen."]
    (TEAM / "STATUS.md").write_text("\n".join(rows) + "\n", encoding="utf-8")
    return report


def run():
    timestamp = dt.datetime.now(dt.timezone.utc)
    selected = choose_task(load_tasks())
    checks = test_result()
    data = {
        "timestamp_utc": timestamp.isoformat(),
        "project": "SCHNAPPER",
        "selected_task": selected,
        "model": MODEL,
        "local_model_available": False,
        "tests": checks,
        "agents": {},
        "accepted": False,
    }
    availability_error = None
    try:
        available()
        data["local_model_available"] = True
    except LocalBrainError as exc:
        availability_error = str(exc)

    previous = {}
    for role in ROLES:
        if availability_error:
            data["agents"][role] = {"status": "blockiert", "check": "Kein Modell",
                                    "error": availability_error}
            continue
        if selected is None:
            data["agents"][role] = {"status": "blockiert", "check": "Keine offene Aufgabe"}
            continue
        try:
            answer = ask(role, selected, previous, checks["ok"])
            valid, check = validate(role, selected, answer)
            data["agents"][role] = {
                "status": "lokales_sprachmodell" if valid else "unvollständig",
                "check": check, "formally_valid": valid, "answer": answer,
            }
            previous[role] = answer
        except (LocalBrainError, ValueError) as exc:
            data["agents"][role] = {
                "status": "blockiert", "check": "Antwort fehlgeschlagen",
                "error": str(exc),
            }
    data["accepted"] = bool(
        selected and checks["ok"] and data["local_model_available"]
        and all(data["agents"][role].get("formally_valid") for role in ROLES)
    )
    report = save_report(data, timestamp)
    print(json.dumps({
        "report": str(report.relative_to(ROOT)),
        "model_available": data["local_model_available"],
        "tests_ok": checks["ok"],
        "accepted": data["accepted"],
    }, ensure_ascii=False))
    return 0 if data["accepted"] else 1


if __name__ == "__main__":
    sys.exit(run())
