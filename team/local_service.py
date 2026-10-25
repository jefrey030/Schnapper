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
        # Einzelbelege dürfen keine Symlinks auf fremde lokale Dateien sein.
        if datei.is_symlink():
            fehler.append(f"Agentendatei {rolle}.json ist ein unzulässiger symbolischer Link.")
        elif not datei.exists():
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
        if a.get("rolle") != rolle:
            fehler.append(f"Agentenbericht {rolle}: Rollenidentität fehlt oder ist falsch.")
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
    # Aggregierte Angaben müssen aus den tatsächlichen Einzelbelegen folgen,
    # nicht bloß eine positive Behauptung im Sammelbericht sein.
    if (bericht.get("aufgabe") != plan.get("aufgabe_id")
            or not isinstance(bericht.get("selected_task"), dict)
            or bericht["selected_task"].get("id") != plan.get("aufgabe_id")):
        fehler.append("Aufgaben-ID von LEAD, Rotation und Gesamtbericht widerspricht sich.")
    check_rolle = agenten.get("CHECK")
    check_rolle = check_rolle if isinstance(check_rolle, dict) else {}
    urteil = check_rolle.get("urteil")
    urteil = urteil if isinstance(urteil, dict) else {}
    werkzeuge = check_rolle.get("werkzeug")
    werkzeuge = werkzeuge if isinstance(werkzeuge, dict) else {}
    einzeltests = werkzeuge.get("tests")
    einzeltests = einzeltests if isinstance(einzeltests, dict) else {}
    if urteil.get("urteil") != bericht.get("check_urteil"):
        fehler.append("CHECK-Urteil und Gesamtbericht widersprechen sich.")
    if (einzeltests.get("ok") is not True
            or not isinstance(einzeltests.get("anzahl"), int)
            or isinstance(einzeltests.get("anzahl"), bool)
            or einzeltests.get("anzahl", 0) < 1
            or bericht.get("tests_ok") is not True
            or bericht.get("tests_anzahl") != einzeltests.get("anzahl")):
        fehler.append("CHECK-Testergebnisse und Gesamtbericht stimmen nicht überein.")
    if werkzeuge.get("geheimnis_funde") != []:
        fehler.append("CHECK-Geheimnisscan fehlt oder ist nicht leer.")
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
    if (bericht.get("tests_ok") is not True
            or type(bericht.get("tests_anzahl")) is not int
            or bericht["tests_anzahl"] < 1):
        fehler.append("Unit-Tests nicht erfolgreich nachgewiesen.")
    erwartet = (*ROLES, "BERICHT")
    if (len(schritte) != len(erwartet)
            or not all(
                isinstance(schritt, dict)
                and schritt.get("rolle") == rolle
                and type(schritt.get("exitcode")) is int
                and schritt["exitcode"] == 0
                for rolle, schritt in zip(erwartet, schritte)
            )):
        fehler.append("Prozessbelege unvollständig, vertauscht, doppelt oder fehlgeschlagen.")
    return fehler



def pruefe_manifest(lauf):
    """Offline-Nachweise prüfen: lesend, ohne KI, Shell, Netzwerk oder Änderungen.

    SHA-256 entdeckt nachträgliche Dateiveränderungen. Es ist keine Signatur:
    Wer auch das Manifest schreiben darf, kann alle Hashes neu erzeugen.
    """
    fehler = []
    geprueft = 0
    lauf_pfad = pathlib.Path(lauf)
    # Niemals untrusted Pfade aus dem Manifest selbst für den Dateizugriff
    # verwenden. Stattdessen die exakten erwarteten Namen selbst bilden.
    try:
        work = TEAM / "work"
        if (work.is_symlink() or ".." in lauf_pfad.parts
                or lauf_pfad.is_symlink() or not lauf_pfad.is_dir()):
            raise ValueError("Unzulässiger Laufordner")
        work_real = work.resolve(strict=True)
        lauf_real = lauf_pfad.resolve(strict=True)
        root_real = ROOT.resolve(strict=True)
        if (lauf_real.parent != work_real
                or not work_real.is_relative_to(root_real)
                or not (TEAM / "runs").resolve().is_relative_to(root_real)):
            raise ValueError("Lauf außerhalb von team/work")
    except (OSError, RuntimeError, ValueError):
        return {"status": "BLOCKIERT", "lauf": None, "dateien_geprueft": 0,
                "fehler": ["Unzulässiger oder fehlender Laufordner."]}

    manifest_pfad = lauf_real / "nachweise.json"
    try:
        if manifest_pfad.is_symlink() or not manifest_pfad.is_file():
            raise ValueError("Nachweis fehlt oder ist ein Link")
        if manifest_pfad.stat().st_size > 100_000:
            raise ValueError("Nachweis über Größenlimit")
        manifest = json.loads(manifest_pfad.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return {"status": "BLOCKIERT", "lauf": lauf_real.name,
                "dateien_geprueft": 0,
                "fehler": ["Nachweisdatei fehlt, ist ungültig oder zu groß."]}
    if not isinstance(manifest, dict):
        return {"status": "BLOCKIERT", "lauf": lauf_real.name,
                "dateien_geprueft": 0,
                "fehler": ["Nachweis ist kein JSON-Objekt."]}

    result = manifest.get("ergebnis")
    hashes = manifest.get("dateien")
    if not isinstance(result, dict) or not isinstance(hashes, dict):
        fehler.append("Nachweisstruktur unvollständig.")
        result = result if isinstance(result, dict) else {}
        hashes = hashes if isinstance(hashes, dict) else {}
    if manifest.get("lauf") != lauf_real.name or result.get("lauf") != lauf_real.name:
        fehler.append("Laufkennung widerspricht dem Manifest.")
    status = result.get("status")
    if status not in ("BLOCKIERT", "TECHNISCHER PILOT ERFOLGREICH"):
        fehler.append("Ergebnisstatus fehlt oder ist ungültig.")
    if result.get("vier_echte_ki_antworten") is not (
            status == "TECHNISCHER PILOT ERFOLGREICH"):
        fehler.append("Nachweisstatus und KI-Kennzahl widersprechen sich.")

    pfade = [TEAM / "runs" / (lauf_real.name + ".json"),
             lauf_real / "prozesse.json"]
    rollendateien = [lauf_real / (rolle + ".json") for rolle in ROLES]
    pfade += [p for p in rollendateien if p.is_file() or p.is_symlink()]
    if status == "TECHNISCHER PILOT ERFOLGREICH" and len(pfade) != 6:
        fehler.append("Agentenbelege für erfolgreichen Lauf unvollständig.")

    erlaubt = {str(p.relative_to(ROOT)): p for p in pfade}
    if set(hashes) != set(erlaubt):
        fehler.append("Dateiliste weicht von den erwarteten Nachweisen ab.")
    for name, p in erlaubt.items():
        expected = hashes.get(name)
        if (not isinstance(expected, str)
                or len(expected) != 64
                or any(c not in "0123456789abcdef" for c in expected)):
            fehler.append("SHA-256-Fingerabdruck fehlt oder ist ungültig: " + p.name)
            continue
        try:
            if p.is_symlink() or not p.is_file() or p.stat().st_size > 1_000_000:
                raise ValueError("Ungültige Nachweisdatei")
            calculated = hashlib.sha256(p.read_bytes()).hexdigest()
        except (OSError, ValueError):
            fehler.append("Datei fehlt, ist verlinkt oder zu groß: " + p.name)
            continue
        geprueft += 1
        if calculated != expected:
            fehler.append("Prüfsummenabweichung: " + p.name)
    return {"status": "INTEGRITAET_OK" if not fehler else "BLOCKIERT",
            "lauf": lauf_real.name, "dateien_geprueft": geprueft,
            "fehler": fehler}


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
    integritaet = pruefe_manifest(lauf)
    if integritaet["status"] != "INTEGRITAET_OK":
        # Auch ein vorher positiver Agentenbericht zählt dann nicht als
        # technischer Erfolg. Der Prüfer verändert keine Nachweisdatei.
        print(json.dumps({"lauf": lauf.name, "status": "BLOCKIERT",
                          "vier_echte_ki_antworten": False,
                          "fehler": ["Integritätsprüfung der Nachweise fehlgeschlagen."]},
                         ensure_ascii=False))
        return 1
    print(json.dumps(ergebnis, ensure_ascii=False))
    return 0 if erfolgreich else 1


def start():
    p = argparse.ArgumentParser(description=__doc__)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--once", action="store_true", help="jetzt einen überprüften Pilotlauf starten")
    g.add_argument("--loop", action="store_true", help="einmal sofort, danach zu jeder vollen UTC-Stunde")
    g.add_argument("--verify", metavar="LAUFORDNER",
                   help="lokalen SHA-256-Nachweis offline prüfen (keine KI)")
    args = p.parse_args()
    if args.verify is not None:
        # Read-only: weder Scheduler-Lock noch subprocess/Ollama benötigen.
        pruefung = pruefe_manifest(pathlib.Path(args.verify))
        print(json.dumps(pruefung, ensure_ascii=False))
        return 0 if pruefung["status"] == "INTEGRITAET_OK" else 1
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
