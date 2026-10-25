"""SCHNAPPER: vier lokale KI-Rollen stündlich ohne Bezahl-API starten.

Einmaliger Pilot: python team/local_service.py --once
Stundenbetrieb:  python team/local_service.py --loop
Nur solange der eigene Rechner und Ollama laufen. Kein Remote-Server.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import time
import uuid

from agent import GEHEIMNIS_MUSTER  # Dieselben Token-Indikatoren wie in Agentenberichten

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEAM = ROOT / "team"
ROLES = ("LEAD", "BRAIN", "CHECK", "COMMAND")
STOP_DATEI = TEAM / "work" / "STOP"


def gestoppt():
    """Betreiber-Not-Aus: Flag-Datei blockiert den nächsten Prozess und Stundenlauf."""
    return (TEAM / "work" / "STOP").exists()


def pruefe_nachweise(bericht, lauf, schritte):
    """Strikter technischer Pilotnachweis, unabhängig von KI-Eigenbehauptungen.

    Die Ergebnisse gelten ausschließlich für lokale Agentenantworten, nicht
    als Freigabe von Patches oder als Beweis für echten Preisvergleich.
    """
    fehler = []
    if not isinstance(bericht, dict):
        return ["Stundenbericht ist kein JSON-Objekt."]
    if not isinstance(schritte, list):
        return ["Prozessnachweise sind keine Liste."]
    if not isinstance(bericht.get("agenten"), dict):
        return ["Agentendaten im Gesamtbericht sind kein JSON-Objekt."]
    if bericht.get("lauf") != lauf.name:
        fehler.append("Bericht gehört nicht zu diesem Lauf.")
    if bericht.get("team_einsatzbereit") is not True:
        fehler.append("Vier-Agenten-Team im Bericht nicht einsatzbereit.")
    rollen_belegt = bericht.get("agenten_mit_echter_ki")
    if (not isinstance(rollen_belegt, list)
            or not all(isinstance(x, str) for x in rollen_belegt)
            or sorted(rollen_belegt) != sorted(ROLES)):
        fehler.append("KI-Nachweis für mindestens eine Rolle fehlt.")
    if bericht.get("ki_aufrufe") != 4:
        fehler.append("KI-Nachweis: erwartet genau vier lokale Modellaufrufe.")
    antwort_ids = []
    agenten = bericht.get("agenten") or {}
    for rolle in ROLES:
        datei = lauf / (rolle + ".json")
        a = agenten.get(rolle)
        if not isinstance(a, dict):
            fehler.append(f"Agentendaten {rolle}: kein JSON-Objekt.")
            a = {}
        if not datei.exists():
            fehler.append(f"Agentendatei fehlt: {rolle}.json")
        else:
            try:
                einzeln = json.loads(datei.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, ValueError):
                fehler.append(f"Agentendatei {rolle}.json unlesbar/ungültig.")
            else:
                # Ein aggregierter Bericht darf keinen anderen Inhalt als das
                # zugehörige einzelne Rollenprotokoll als Beleg ausgeben.
                if not isinstance(einzeln, dict) or einzeln != a:
                    fehler.append(f"Agentenbericht {rolle}: Datei und Gesamtbericht widersprechen sich.")
        info = a.get("ki")
        if not isinstance(info, dict):
            info = {}
        if a.get("ki_echt") is not True or a.get("status") != "OK":
            fehler.append(f"KI-Nachweis {rolle}: kein bestätigter OK-Lauf.")
        if info.get("laufzeit") != "Ollama lokal (keine bezahlte KI-API)":
            fehler.append(f"KI-Nachweis {rolle}: keine bestätigte lokale Laufzeit.")
        if not isinstance(info.get("text"), str) or not info["text"].strip():
            fehler.append(f"KI-Nachweis {rolle}: leere KI-Antwort.")
        modell = info.get("modell")
        if not isinstance(modell, str) or not modell or modell.lower().endswith(":cloud"):
            fehler.append(f"KI-Nachweis {rolle}: Modell ungültig/Cloud.")
        identifier = info.get("antwort_id")
        if not isinstance(identifier, str) or not identifier.startswith("lokal-"):
            fehler.append(f"Antwort-ID von {rolle} fehlt oder ist unzulässig.")
        else:
            antwort_ids.append(identifier)
    if len(set(antwort_ids)) != len(ROLES):
        fehler.append("Antwort-IDs sind nicht viermal eindeutig.")
    # Vier lesbare KI-Antworten genügen nicht: Rollen müssen sinnvolle
    # strukturierte Übergaben erzeugen, sonst dreht die Rotation ins Leere.
    lead = agenten.get("LEAD")
    lead = lead if isinstance(lead, dict) else {}
    plan = lead.get("plan")
    plan = plan if isinstance(plan, dict) else {}
    if not isinstance(plan, dict) or not isinstance(
        plan.get("aufgabe_id"), str) or not plan.get("aufgabe_id"):
        fehler.append("LEAD hat keinen gültigen Aufgabenauftrag erstellt.")
    brain = agenten.get("BRAIN")
    brain = brain if isinstance(brain, dict) else {}
    pfad = brain.get("vorschlag_datei")
    if not isinstance(pfad, str) or not pfad.startswith("team/proposals/"):
        fehler.append("BRAIN hat keine Vorschlagsdatei nachgewiesen.")
    else:
        datei = (ROOT / pfad).resolve()
        ordner = (TEAM / "proposals").resolve()
        if not datei.is_relative_to(ordner) or not datei.is_file():
            fehler.append("BRAIN-Vorschlag fehlt oder liegt außerhalb von team/proposals.")
    if bericht.get("check_urteil") != "bestanden":
        fehler.append("CHECK hat nicht bestanden: keine positive Pilotabnahme.")
    command_rolle = agenten.get("COMMAND")
    command_rolle = command_rolle if isinstance(command_rolle, dict) else {}
    command = command_rolle.get("protokoll")
    command = command if isinstance(command, dict) else {}
    if not isinstance(command, dict) or command.get("freigabe") != "ja" or not (
        isinstance(command.get("naechster_schritt"), str) and
        command["naechster_schritt"].strip()
    ):
        fehler.append("COMMAND hat kein gültiges Abschlussprotokoll erstellt.")
    if bericht.get("tests_ok") is not True or not isinstance(
        bericht.get("tests_anzahl"), int) or bericht["tests_anzahl"] < 1:
        fehler.append("Unit-Tests nicht erfolgreich nachgewiesen.")
    if len(schritte) != len(ROLES) + 1 or not all(
        isinstance(x, dict) and x.get("exitcode") == 0 for x in schritte):
        fehler.append("Mindestens ein Agentenprozess/der Bericht ist fehlgeschlagen.")
    return fehler


def einmal():
    if gestoppt():
        print("BLOCKIERT: Betreiber-Not-Aus team/work/STOP ist aktiv.")
        return 2
    stempel = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lauf = TEAM / "work" / (stempel + "-" + uuid.uuid4().hex[:6])
    lauf.mkdir(parents=True, exist_ok=False)
    env = os.environ.copy()
    # Kein Rückfall auf GitHub Models, Cloudflare oder andere KI-Anbieter.
    env["SCHNAPPER_KI_BACKEND"] = "ollama"
    schritte = []
    sperre_fehler = False
    for rolle in (*ROLES, "BERICHT"):
        if rolle != "BERICHT" and (gestoppt() or sperre_fehler):
            schritte.append({"rolle": rolle, "exitcode": -2,
                             "fehler": "Not-Aus oder vorheriger Agent gescheitert; Agent nicht gestartet"})
            continue
        try:
            proc = subprocess.run(
                [sys.executable, str(TEAM / "agent.py"), rolle, str(lauf)],
                cwd=ROOT, env=env, capture_output=True, text=True,
                timeout=240, check=False,
            )
            ausgabe = (proc.stdout or "")[-1500:]
            fehlerausgabe = (proc.stderr or "")[-1500:]
            geheimnis = bool(GEHEIMNIS_MUSTER.search(ausgabe + fehlerausgabe))
            schritte.append({"rolle": rolle, "exitcode": -3 if geheimnis else proc.returncode,
                             "stdout": GEHEIMNIS_MUSTER.sub("[REDACTED]", ausgabe),
                             "stderr": GEHEIMNIS_MUSTER.sub("[REDACTED]", fehlerausgabe),
                             "fehler": "Geheimnisindikator in Prozesslog – Pilot gestoppt"
                                       if geheimnis else None})
            if geheimnis or proc.returncode != 0:
                sperre_fehler = True
        except subprocess.TimeoutExpired:
            sperre_fehler = True
            schritte.append({"rolle": rolle, "exitcode": -1,
                             "fehler": "Zeitlimit 240 Sekunden überschritten"})
        except OSError:
            # Fehlerdetails können Dateipfade oder sensitive Umgebungsdaten
            # enthalten. Keine Roh-Exception in Berichten oder Logs speichern.
            sperre_fehler = True
            schritte.append({"rolle": rolle, "exitcode": -4,
                             "fehler": "Agentenprozess konnte nicht gestartet werden."})
    (lauf / "prozesse.json").write_text(
        json.dumps(schritte, ensure_ascii=False, indent=2), encoding="utf-8")
    report_path = TEAM / "runs" / (lauf.name + ".json")
    if not report_path.exists():
        print(f"BLOCKIERT: Stundenbericht fehlt. Details: {lauf}/prozesse.json")
        return 1
    try:
        if report_path.stat().st_size > 1_000_000:
            raise ValueError("Bericht über Größenlimit")
        bericht = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        print("BLOCKIERT: Stundenbericht fehlt, ist unlesbar oder enthält ungültiges JSON.")
        return 1
    if not isinstance(bericht, dict):
        print("BLOCKIERT: Stundenbericht muss ein JSON-Objekt sein.")
        return 1
    fehler = pruefe_nachweise(bericht, lauf, schritte)
    erfolgreich = not fehler
    ergebnis = {
        "lauf": lauf.name,
        # Einzelne Fehlertext-Stichworte dürfen nicht als Beweis für vier
        # gültige Antworten dienen. Nur die vollständig geprüfte lokale
        # Pilotevidenz erlaubt diese positive technische Kennzahl.
        "vier_echte_ki_antworten": erfolgreich,
        "tests_bestanden": bericht.get("tests_ok") is True,
        "prozesse_ok": all(s["exitcode"] == 0 for s in schritte),
        "status": "TECHNISCHER PILOT ERFOLGREICH" if erfolgreich else "BLOCKIERT",
        "hinweis": "Technischer KI-Nachweis ist keine Freigabe für App-Änderungen.",
        "fehler": fehler,
        "protokoll": str(report_path.relative_to(ROOT)),
    }
    # Beleg-Hashes erlauben die spätere Prüfung der tatsächlich erzeugten Dateien.
    dateien = [report_path, lauf / "prozesse.json"]
    dateien += [lauf / (rolle + ".json") for rolle in ROLES if (lauf / (rolle + ".json")).exists()]
    manifest = {
        "lauf": lauf.name, "zeit_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "dateien": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in dateien},
        "ergebnis": ergebnis,
    }
    (lauf / "nachweise.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(ergebnis, ensure_ascii=False))
    return 0 if erfolgreich else 1


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
            if gestoppt():
                print("STOP: Betreiber-Not-Aus aktiv. Kein weiterer Stundenlauf.")
                return 2
            einmal()
            jetzt = dt.datetime.now(dt.timezone.utc)
            naechste = (jetzt.replace(minute=0, second=0, microsecond=0)
                        + dt.timedelta(hours=1))
            print(f"Nächster Start (UTC): {naechste.isoformat()}", flush=True)
            while (naechste - dt.datetime.now(dt.timezone.utc)).total_seconds() > 0:
                if gestoppt():
                    print("STOP: Betreiber-Not-Aus aktiv.")
                    return 2
                zeit = (naechste - dt.datetime.now(dt.timezone.utc)).total_seconds()
                time.sleep(max(0.1, min(zeit, 30)))
    except KeyboardInterrupt:
        return 0
    finally:
        sperre.unlink(missing_ok=True)


if __name__ == "__main__":
    sys.exit(start())
