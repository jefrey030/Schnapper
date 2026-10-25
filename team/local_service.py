"""SCHNAPPER: vier lokale KI-Rollen stündlich ohne Bezahl-API starten.

Einmaliger Pilot: python team/local_service.py --once
Stundenbetrieb:  python team/local_service.py --loop
Nur solange der eigene Rechner und Ollama laufen. Kein Remote-Server.
"""
import argparse
import datetime as dt
import fcntl
import hashlib
import json
import os
import pathlib
import stat
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
    if bericht.get("lauf") != lauf.name:
        fehler.append("Bericht gehört nicht zu diesem Lauf.")
    if bericht.get("team_einsatzbereit") is not True:
        fehler.append("Vier-Agenten-Team im Bericht nicht einsatzbereit.")
    gemeldete_rollen = bericht.get("agenten_mit_echter_ki")
    if (not isinstance(gemeldete_rollen, list)
            or len(gemeldete_rollen) != len(ROLES)
            or any(not isinstance(r, str) for r in gemeldete_rollen)
            or set(gemeldete_rollen) != set(ROLES)):
        fehler.append("KI-Nachweis für mindestens eine Rolle fehlt.")
    if bericht.get("ki_aufrufe") != 4:
        fehler.append("KI-Nachweis: erwartet genau vier lokale Modellaufrufe.")
    # Der Bericht ist keine eigene Quelle für den Modellaufrufzähler.
    zaehler = lauf / "ki_aufrufe.txt"
    try:
        if zaehler.is_symlink():
            raise ValueError("Symlink als Zähler nicht vertrauenswürdig")
        lokaler_zaehler = int(zaehler.read_text(encoding="utf-8").strip())
    except (OSError, UnicodeError, ValueError):
        lokaler_zaehler = None
    if lokaler_zaehler != 4:
        fehler.append("Lokaler KI-Aufrufzähler fehlt, ist ungültig oder nicht vier.")
    antwort_ids = []
    agenten = bericht.get("agenten") or {}
    if not isinstance(agenten, dict):
        fehler.append("Agentenbericht muss ein JSON-Objekt sein.")
        agenten = {}
    for rolle in ROLES:
        datei = lauf / (rolle + ".json")
        a = agenten.get(rolle) or {}
        if not isinstance(a, dict):
            fehler.append(f"Agentenbericht {rolle} ist kein Objekt.")
            a = {}
            agenten[rolle] = {}
        if datei.is_symlink():
            fehler.append(f"Agentendatei {rolle}.json darf kein Symlink sein.")
        elif not datei.is_file():
            fehler.append(f"Agentendatei fehlt: {rolle}.json")
        else:
            try:
                einzeln = json.loads(datei.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, ValueError):
                fehler.append(f"Agentendatei {rolle}.json unlesbar/ungültig.")
            else:
                # Ein aggregierter Bericht darf keinen anderen Inhalt als das
                # zugehörige einzelne Rollenprotokoll als Beleg ausgeben.
                if (not isinstance(einzeln, dict)
                        or einzeln.get("rolle") != rolle or einzeln != a):
                    fehler.append(f"Agentenbericht {rolle}: Datei und Gesamtbericht widersprechen sich.")
        info = a.get("ki") or {}
        if not isinstance(info, dict):
            fehler.append(f"KI-Metadaten {rolle} sind kein Objekt.")
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
    lead = agenten.get("LEAD") or {}
    plan = lead.get("plan") or {}
    if not isinstance(plan, dict):
        plan = {}
    if not isinstance(plan, dict) or not isinstance(
        plan.get("aufgabe_id"), str) or not plan.get("aufgabe_id"):
        fehler.append("LEAD hat keinen gültigen Aufgabenauftrag erstellt.")
    brain = agenten.get("BRAIN") or {}
    pfad = brain.get("vorschlag_datei")
    if not isinstance(pfad, str) or not pfad.startswith("team/proposals/"):
        fehler.append("BRAIN hat keine Vorschlagsdatei nachgewiesen.")
    else:
        datei = (ROOT / pfad).resolve()
        ordner = (TEAM / "proposals").resolve()
        if not datei.is_relative_to(ordner) or not datei.is_file():
            fehler.append("BRAIN-Vorschlag fehlt oder liegt außerhalb von team/proposals.")
    check = agenten.get("CHECK") or {}
    pruefurteil = check.get("urteil") or {}
    if not isinstance(pruefurteil, dict):
        pruefurteil = {}
    if (bericht.get("check_urteil") != "bestanden"
            or pruefurteil.get("urteil") != "bestanden"):
        fehler.append("CHECK hat nicht bestanden: keine positive Pilotabnahme.")
    werkzeug = check.get("werkzeug") or {}
    if not isinstance(werkzeug, dict):
        werkzeug = {}
    if werkzeug.get("geheimnis_funde") != []:
        fehler.append("CHECK-Geheimnisscan fehlt oder hat Funde.")
    tests = werkzeug.get("tests") or {}
    if not isinstance(tests, dict):
        tests = {}
    if (tests.get("ok") is not True
            or type(tests.get("anzahl")) is not int
            or tests["anzahl"] < 1
            or tests["anzahl"] != bericht.get("tests_anzahl")):
        fehler.append("CHECK-Tests fehlen, sind ungültig oder widersprechen dem Bericht.")
    command = (agenten.get("COMMAND") or {}).get("protokoll") or {}
    if not isinstance(command, dict):
        command = {}
    if command.get("freigabe") != "ja" or not (
        isinstance(command.get("naechster_schritt"), str) and
        command["naechster_schritt"].strip()
    ):
        fehler.append("COMMAND hat kein gültiges Abschlussprotokoll erstellt.")
    if bericht.get("tests_ok") is not True or type(
        bericht.get("tests_anzahl")) is not int or bericht["tests_anzahl"] < 1:
        fehler.append("Unit-Tests nicht erfolgreich nachgewiesen.")
    # Jeder erfolgreiche Prozessbeleg muss genau zur ausgefuehrten Rolle
    # passen. Nur fuenf Exitcodes=0 lassen auch duplizierte Rollen passieren.
    erwartet = (*ROLES, "BERICHT")
    if (not isinstance(schritte, list)
            or len(schritte) != len(erwartet)
            or any(not isinstance(s, dict) for s in schritte)
            or tuple(s.get("rolle") for s in schritte) != erwartet
            or any(type(s.get("exitcode")) is not int or s["exitcode"] != 0
                   for s in schritte)):
        fehler.append("Agentenprozessfolge unvollstaendig, vertauscht oder fehlgeschlagen.")
    return fehler


def _hash_sicher(p):
    """Dateihash nur ueber einen einzigen sicheren Dateideskriptor.

    Auf POSIX keine Symlink-Folgeverfolgung (auch nicht bei einem Austausch
    zwischen Vorabpruefung und open). Nur regulaere Dateien bis 2 MB; ein
    FIFO/Device darf niemals einen unendlichen Lesezugriff ausloesen.
    Integritaet, aber keine unabhaengige Modell-Attestierung.
    """
    if not hasattr(os, "O_NOFOLLOW"):
        raise OSError("O_NOFOLLOW fehlt: Artefaktnachweis nicht abgesichert")
    flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NONBLOCK", 0)
    fd = os.open(str(p), flags)
    with os.fdopen(fd, "rb") as datei:
        if not stat.S_ISREG(os.fstat(datei.fileno()).st_mode):
            raise OSError("Nachweisartefakt ist keine regulaere Datei")
        daten = datei.read(2_000_001)
        if len(daten) > 2_000_000:
            raise OSError("Nachweisartefakt ueberschreitet 2 MB")
    return hashlib.sha256(daten).hexdigest()


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
    # Prozessbeleg ist aus den beobachteten Exitcodes und Rollen entstanden.
    # Den Byte-Hash vor dem Schreiben merken: das spaetere Manifest darf
    # nicht unbemerkt eine manipulierte Ersatzdatei belegen.
    prozess_pfad = lauf / "prozesse.json"
    prozess_roh = json.dumps(schritte, ensure_ascii=False, indent=2).encode("utf-8")
    prozess_hash_erwartet = hashlib.sha256(prozess_roh).hexdigest()
    prozess_pfad.write_bytes(prozess_roh)
    report_path = TEAM / "runs" / (lauf.name + ".json")
    if not report_path.exists():
        print(f"BLOCKIERT: Stundenbericht fehlt. Details: {lauf}/prozesse.json")
        return 1
    try:
        if report_path.is_symlink():
            raise ValueError("Symlinkbericht")
        bericht = json.loads(report_path.read_text(encoding="utf-8"))
        if not isinstance(bericht, dict):
            raise ValueError("Bericht muss ein JSON-Objekt sein")
    except (OSError, UnicodeError, ValueError):
        print("BLOCKIERT: Stundenbericht ungültig oder nicht lesbar.")
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
    # Kein optionaler Rollen-/Zaehlerbeleg: die Manifestliste ist vollstaendig.
    # Die O_NOFOLLOW-Oeffnung und fstat-Pruefung erfolgen am *selben* FD.
    # Ein Path.is_symlink()-Vortest waere anfaellig fuer Austausch-Rennen.
    dateien = ([report_path, lauf / "prozesse.json"]
               + [lauf / (rolle + ".json") for rolle in ROLES]
               + [lauf / "ki_aufrufe.txt"])
    hashes = {}
    try:
        for p in dateien:
            hashes[str(p.relative_to(ROOT))] = _hash_sicher(p)
        # MASTER 82: In-memory-Rollenpruefung und On-Disk-Manifest muessen
        # dieselben Prozessdaten betreffen. Keine rein selbstbehauptete
        # Ersatzdatei darf als technische Pilotevidenz zaehlen.
        if hashes[str(prozess_pfad.relative_to(ROOT))] != prozess_hash_erwartet:
            raise OSError("Prozessnachweis wurde nach dem Schreiben veraendert")
    except OSError:
        # Fehlende Pflichtartefakte duerfen weder einen Erfolg noch eine
        # Ausnahme ausgeben. Auch bei einem ansonsten positiven MOCK-Bericht
        # bleibt das strukturierte Ergebnis eindeutig BLOCKIERT.
        ergebnis["vier_echte_ki_antworten"] = False
        ergebnis["status"] = "BLOCKIERT"
        ergebnis["fehler"].append(
            "Pflichtnachweis fehlt, ist unsicher oder nicht lesbar.")
        print(json.dumps(ergebnis, ensure_ascii=False))
        return 1
    manifest = {
        "lauf": lauf.name, "zeit_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "dateien": hashes,
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
    # Unix/Termux/macOS: kernel-seitige, nicht blockierende Sperre.
    # O_EXCL-Lockdateien bleiben nach Absturz liegen und verhindern jeden Neustart.
    # Das Lockfile bleibt absichtlich bestehen: unlink() waere eine Race-Condition
    # gegen einen bereits gestarteten zweiten Prozess.
    flags = os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(str(sperre), flags, 0o600)
    except OSError:
        print("BLOCKIERT: Sperrdatei kann nicht sicher geoeffnet werden.")
        return 2
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            print("BLOCKIERT: Ein anderer lokaler SCHNAPPER-Dienst ist aktiv.")
            return 2
        # PID nur zur Diagnose, nie als Freigabe- oder Authentizitaetsbeweis.
        os.ftruncate(fd, 0)
        os.write(fd, str(os.getpid()).encode("ascii"))
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
        # close() gibt flock auch nach Exception/KeyboardInterrupt frei.
        # Nicht loeschen: die Inode muss fuer alle Prozesse dieselbe bleiben.
        os.close(fd)


if __name__ == "__main__":
    sys.exit(start())
