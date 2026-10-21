"""SCHNAPPER: vier lokale KI-Rollen stündlich ohne Bezahl-API starten.

Einmaliger Pilot: python team/local_service.py --once
Stundenbetrieb:  python team/local_service.py --loop
Nur solange der eigene Rechner und Ollama laufen. Kein Remote-Server.
"""
import argparse
import datetime as dt
import json
import os
import pathlib
import subprocess
import sys
import time
import uuid

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEAM = ROOT / "team"
ROLES = ("LEAD", "BRAIN", "CHECK", "COMMAND")


def einmal():
    stempel = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lauf = TEAM / "work" / (stempel + "-" + uuid.uuid4().hex[:6])
    lauf.mkdir(parents=True, exist_ok=False)
    env = os.environ.copy()
    # Kein Rückfall auf GitHub Models, Cloudflare oder andere KI-Anbieter.
    env["SCHNAPPER_KI_BACKEND"] = "ollama"
    schritte = []
    for rolle in (*ROLES, "BERICHT"):
        try:
            proc = subprocess.run(
                [sys.executable, str(TEAM / "agent.py"), rolle, str(lauf)],
                cwd=ROOT, env=env, capture_output=True, text=True,
                timeout=240, check=False,
            )
            schritte.append({"rolle": rolle, "exitcode": proc.returncode,
                             "stdout": proc.stdout[-1500:], "stderr": proc.stderr[-1500:]})
        except subprocess.TimeoutExpired:
            schritte.append({"rolle": rolle, "exitcode": -1,
                             "fehler": "Zeitlimit 240 Sekunden überschritten"})
    (lauf / "prozesse.json").write_text(
        json.dumps(schritte, ensure_ascii=False, indent=2), encoding="utf-8")
    report_path = TEAM / "runs" / (lauf.name + ".json")
    if not report_path.exists():
        print(f"BLOCKIERT: Stundenbericht fehlt. Details: {lauf}/prozesse.json")
        return 1
    bericht = json.loads(report_path.read_text(encoding="utf-8"))
    agenten_ok = (bericht.get("team_einsatzbereit") is True
                  and len(bericht.get("agenten_mit_echter_ki", [])) == 4)
    # KI-Antwort ist noch keine Freigabe: echte Unit-Tests müssen bestanden sein.
    tests_ok = bericht.get("tests_ok") is True
    prozesse_ok = all(s["exitcode"] == 0 for s in schritte)
    print(json.dumps({
        "lauf": lauf.name, "vier_echte_ki_antworten": agenten_ok,
        "tests_bestanden": tests_ok, "prozesse_ok": prozesse_ok,
        "status": "ERFOLGREICHER PILOT" if (agenten_ok and tests_ok and prozesse_ok)
                  else "BLOCKIERT",
        "protokoll": str(report_path.relative_to(ROOT)),
    }, ensure_ascii=False))
    return 0 if (agenten_ok and tests_ok and prozesse_ok) else 1


def start():
    p = argparse.ArgumentParser(description=__doc__)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--once", action="store_true", help="jetzt einen überprüften Pilotlauf starten")
    g.add_argument("--loop", action="store_true", help="einmal sofort, danach zu jeder vollen UTC-Stunde")
    args = p.parse_args()
    sperre = TEAM / "work" / "local_runner.lock"
    sperre.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(str(sperre), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        print(f"BLOCKIERT: Ein Lauf könnte bereits aktiv sein ({sperre}).")
        return 2
    try:
        with os.fdopen(fd, "w") as f:
            f.write(str(os.getpid()))
        if args.once:
            return einmal()
        while True:
            einmal()
            jetzt = dt.datetime.now(dt.timezone.utc)
            naechste = (jetzt.replace(minute=0, second=0, microsecond=0)
                        + dt.timedelta(hours=1))
            print(f"Nächster Start (UTC): {naechste.isoformat()}", flush=True)
            while (naechste - dt.datetime.now(dt.timezone.utc)).total_seconds() > 0:
                zeit = (naechste - dt.datetime.now(dt.timezone.utc)).total_seconds()
                time.sleep(max(0.1, min(zeit, 30)))
    except KeyboardInterrupt:
        return 0
    finally:
        sperre.unlink(missing_ok=True)


if __name__ == "__main__":
    sys.exit(start())
