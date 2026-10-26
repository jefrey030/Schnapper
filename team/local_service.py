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
import signal
import stat
import subprocess
import sys
import time
import uuid

from agent import GEHEIMNIS_MUSTER  # Dieselben Token-Indikatoren wie in Agentenberichten
from ki import KINichtVerfuegbar
from operator_approval import pruefe_freigabe

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEAM = ROOT / "team"
ROLES = ("LEAD", "BRAIN", "CHECK", "COMMAND")
STOP_DATEI = TEAM / "work" / "STOP"


def gestoppt():
    """Betreiber-Not-Aus: Flag-Datei blockiert den nächsten Prozess und Stundenlauf."""
    return (TEAM / "work" / "STOP").exists() or (TEAM / "work" / "STOP").is_symlink()


def pruefe_nachweise(bericht, lauf, schritte, beleg_hashes=None):
    """Strikter technischer Pilotnachweis, unabhängig von KI-Eigenbehauptungen.

    Die Ergebnisse gelten ausschließlich für lokale Agentenantworten, nicht
    als Freigabe von Patches oder als Beweis für echten Preisvergleich.
    """
    fehler = []
    if not isinstance(bericht, dict):
        return ["Stundenbericht ist kein JSON-Objekt."]
    if not isinstance(schritte, list):
        return ["Prozessbelege / Agentenprozessfolge sind keine Liste."]
    if not isinstance(bericht.get("agenten"), dict):
        return ["Agentenbericht muss ein JSON-Objekt sein."]
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
        zaehler_bytes = _lese_sicher(zaehler)
        lokaler_zaehler = int(zaehler_bytes.decode("utf-8").strip())
        if beleg_hashes is not None:
            beleg_hashes[str(zaehler.relative_to(ROOT))] = hashlib.sha256(
                zaehler_bytes).hexdigest()
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
            fehler.append(f"Agentendatei {rolle}.json darf kein Symlink sein (symbolischer Link).")
        elif not datei.is_file():
            fehler.append(f"Agentendatei fehlt: {rolle}.json")
        else:
            try:
                rollen_bytes = _lese_sicher(datei)
                einzeln = json.loads(rollen_bytes)
                if beleg_hashes is not None:
                    beleg_hashes[str(datei.relative_to(ROOT))] = hashlib.sha256(
                        rollen_bytes).hexdigest()
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
        # Ollama gibt hier keine signierte Job-ID zurück. Die UUID ist nur
        # eine lokal erzeugte Zuordnung; entscheidend ist die zuvor validierte
        # API-Abschlussmetadatenstruktur, separat von der lokalen Kennung.
        if info.get("antwort_id_typ") != "nur-lokale-kennung":
            fehler.append(f"Antwort-ID von {rolle} ist nicht als lokale Kennung ausgewiesen.")
        beleg = info.get("ollama_beleg")
        if not isinstance(beleg, dict):
            fehler.append(f"Ollama-Abschlussbeleg für {rolle} fehlt.")
        else:
            antwortzeit = beleg.get("created_at")
            try:
                zeit = dt.datetime.fromisoformat(
                    antwortzeit.replace("Z", "+00:00")
                ) if isinstance(antwortzeit, str) and len(antwortzeit) <= 80 else None
            except ValueError:
                zeit = None
            if (beleg.get("modell_antwort") != modell
                    or beleg.get("done") is not True
                    or beleg.get("done_reason") != "stop"
                    or beleg.get("rolle") != "assistant"
                    or type(beleg.get("prompt_eval_count")) is not int
                    or beleg["prompt_eval_count"] < 0
                    or type(beleg.get("eval_count")) is not int
                    or beleg["eval_count"] < 1
                    or zeit is None or zeit.tzinfo is None):
                fehler.append(f"Ollama-Abschlussbeleg für {rolle} ungültig.")
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
    if (bericht.get("aufgabe") != plan.get("aufgabe_id")
            or not isinstance(bericht.get("selected_task"), dict)
            or bericht["selected_task"].get("id") != plan.get("aufgabe_id")):
        fehler.append("Aufgaben-ID von LEAD und Gesamtbericht widerspricht sich.")
    check = agenten.get("CHECK") or {}
    pruefurteil = check.get("urteil") or {}
    if not isinstance(pruefurteil, dict):
        pruefurteil = {}
    if (bericht.get("check_urteil") != "bestanden"
            or pruefurteil.get("urteil") != "bestanden"):
        fehler.append("CHECK hat nicht bestanden: keine positive Pilotabnahme.")
    if pruefurteil.get("urteil") != bericht.get("check_urteil"):
        fehler.append("CHECK-Urteil und Gesamtbericht widersprechen sich.")
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
        fehler.append("CHECK-Testergebnisse / CHECK-Tests fehlen, sind ungültig oder widersprechen dem Bericht.")
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
        fehler.append("Prozessbelege / Agentenprozessfolge unvollstaendig, vertauscht oder fehlgeschlagen.")
    return fehler


def _lese_sicher(p):
    """Nachweisbytes ueber einen einzigen sicheren Dateideskriptor lesen.

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
    return daten


def _hash_sicher(p):
    """SHA256 ueber genau die Bytes der sicheren, begrenzten Datei-Oeffnung."""
    return hashlib.sha256(_lese_sicher(p)).hexdigest()



def rolle_starten(cmd, *, cwd, env, capture_output=True, text=True,
                  timeout=240, check=False, stop_on_flag=True):
    """Agentenprozess mit regelmäßigem Betreiber-STOP-Check.

    Der lokale Kindprozess wird beendet, wenn STOP während des Laufs erscheint.
    Ein bereits an Ollama übermittelter Request kann dadurch nicht rückwirkend
    zurückgerufen werden. BERICHT darf mit stop_on_flag=False noch protokollieren.
    """
    if not capture_output or not text or check:
        raise ValueError("Lokaler Agent verlangt erfasste Textlogs ohne check=True")
    if stop_on_flag and gestoppt():
        return subprocess.CompletedProcess(cmd, -4, "", "")

    if os.name != "posix":
        raise OSError("Sichere Prozessgruppen benötigen POSIX")
    with subprocess.Popen(
        cmd, cwd=cwd, env=env, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True, start_new_session=True,
    ) as proc:
        def gruppe_beenden(sig):
            # Nur eine echte PID verwenden; Testdoubles bleiben isoliert.
            if type(proc.pid) is int:
                try:
                    os.killpg(proc.pid, sig)
                except ProcessLookupError:
                    pass
            elif sig == signal.SIGTERM:
                proc.terminate()
            else:
                proc.kill()

        def abbrechen(sofort=False):
            gruppe_beenden(signal.SIGKILL if sofort else signal.SIGTERM)
            # Ein Rollenabbruch verwirft Ausgaben; Nachkommen brauchen keine
            # Schonfrist und dürfen auch ohne offene Pipes nicht weiterlaufen.
            if type(proc.pid) is int:
                gruppe_beenden(signal.SIGKILL)
            try:
                proc.communicate(timeout=2)
            except subprocess.TimeoutExpired:
                if not sofort or type(proc.pid) is int:
                    gruppe_beenden(signal.SIGKILL)
                try:
                    proc.communicate(timeout=1)
                except subprocess.TimeoutExpired:
                    for stream in (proc.stdout, proc.stderr):
                        if stream is not None:
                            stream.close()
                    proc.wait(timeout=2)

        ende = time.monotonic() + timeout
        while True:
            if stop_on_flag and gestoppt():
                abbrechen()
                return subprocess.CompletedProcess(cmd, -4, "", "")
            rest = ende - time.monotonic()
            if rest <= 0:
                abbrechen(sofort=True)
                raise subprocess.TimeoutExpired(cmd, timeout)
            try:
                stdout, stderr = proc.communicate(timeout=min(0.5, rest))
            except subprocess.TimeoutExpired:
                continue
            if stop_on_flag and gestoppt():
                abbrechen()
                return subprocess.CompletedProcess(cmd, -4, "", "")
            # Rollen dürfen keine unbeaufsichtigten Hintergrundprozesse hinterlassen.
            if type(proc.pid) is int:
                gruppe_beenden(signal.SIGKILL)
            return subprocess.CompletedProcess(cmd, proc.returncode, stdout, stderr)

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
        manifest = json.loads(_lese_sicher(manifest_pfad))
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
    counter = lauf_real / "ki_aufrufe.txt"
    if status == "TECHNISCHER PILOT ERFOLGREICH" or counter.exists() or counter.is_symlink():
        pfade.append(counter)
    if status == "TECHNISCHER PILOT ERFOLGREICH" and len(pfade) != 7:
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
            calculated = _hash_sicher(p)
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
    try:
        # Refuse even a local subprocess if explicit scoped approval is absent.
        pruefe_freigabe()
    except KINichtVerfuegbar:
        print("BLOCKIERT: Lokale Betreiberfreigabe oder passende offene Aufgabe fehlt.")
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
            proc = rolle_starten(
                [sys.executable, str(TEAM / "agent.py"), rolle, str(lauf)],
                cwd=ROOT, env=env, capture_output=True, text=True,
                timeout=240, check=False, stop_on_flag=(rolle != "BERICHT"),
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
            sperre_fehler = True
            schritte.append({"rolle": rolle, "exitcode": -5,
                             "fehler": "Agentenprozess nicht startbar"})
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
        bericht_bytes = _lese_sicher(report_path)
        bericht = json.loads(bericht_bytes)
        if not isinstance(bericht, dict):
            raise ValueError("Bericht muss ein JSON-Objekt sein")
    except (OSError, UnicodeError, ValueError):
        print("BLOCKIERT: Stundenbericht ungültig oder nicht lesbar.")
        return 1
    # Exakte Bytes der fachlich geprueften Belege mit den spaeteren
    # Manifest-Hashes vergleichen; niemand darf nach der fachlichen
    # Pruefung eine andere Datei als erfolgreich belegen lassen.
    beleg_hashes = {
        str(report_path.relative_to(ROOT)):
            hashlib.sha256(bericht_bytes).hexdigest(),
    }
    fehler = pruefe_nachweise(bericht, lauf, schritte,
                             beleg_hashes=beleg_hashes)
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
        # Bericht + vier Rollenprotokolle + Zaehler muessen *alle*
        # bereits bei der fachlichen Pruefung als Bytes gesehen worden
        # sein, und ihr finaler Manifest-Inhalt muss identisch bleiben.
        if len(beleg_hashes) != len(dateien) - 1 or any(
                hashes.get(name) != expected
                for name, expected in beleg_hashes.items()):
            raise OSError("Manifestbeleg weicht vom geprueften Inhalt ab")
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


def _oeffne_runner_sperre(p):
    """Runner-Sperre nur ueber sicheren Dateideskriptor akzeptieren.

    Kein vorheriges exists()/is_symlink(), das nachtraeglich ungueltig
    werden koennte. Anders als der KI-Aufrufzaehler bleibt die Lockdatei
    nach normalem Lauf und Crash bestehen (stabile Inode fuer flock).
    """
    if not hasattr(os, "O_NOFOLLOW"):
        raise OSError("Runner-Lock auf dieser Plattform nicht abgesichert")
    flags = (os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW
             | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_CLOEXEC", 0))
    fd = os.open(str(p), flags, 0o600)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise OSError("Runner-Sperre ist keine eigene regulaere Datei")
        return fd
    except BaseException:
        os.close(fd)
        raise


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
    # Unix/Termux/macOS: kernel-seitige, nicht blockierende Sperre.
    # O_EXCL-Lockdateien bleiben nach Absturz liegen und verhindern jeden Neustart.
    # Das Lockfile bleibt absichtlich bestehen: unlink() waere eine Race-Condition
    # gegen einen bereits gestarteten zweiten Prozess.
    try:
        fd = _oeffne_runner_sperre(sperre)
    except OSError:
        print("BLOCKIERT: Sperrdatei kann nicht sicher geoeffnet werden.")
        return 2
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            print("BLOCKIERT: Ein anderer lokaler SCHNAPPER-Dienst ist aktiv.")
            return 2
        # Ein nach der Oeffnung angelegter Hardlink darf niemals zu
        # einem Schreibzugriff auf fremde gleichnamige Inodes fuehren.
        # Inode-/Verzeichnis-Austausch durch privilegierte lokale Angreifer
        # bleibt ausserhalb der unabhaengigen Attestierung.
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            print("BLOCKIERT: Runner-Sperre ist keine eigene regulaere Datei.")
            return 2
        # PID nur zur Diagnose, nie als Freigabe- oder Authentizitaetsbeweis.
        try:
            os.ftruncate(fd, 0)
            pid = str(os.getpid()).encode("ascii")
            if os.write(fd, pid) != len(pid):
                raise OSError("Unvollstaendiges Runner-PID-Protokoll")
            os.fsync(fd)
        except OSError:
            print("BLOCKIERT: Runner-PID-Protokoll konnte nicht sicher geschrieben werden.")
            return 2
        if args.once:
            return einmal()
        while True:
            if gestoppt():
                print("STOP: Betreiber-Not-Aus aktiv. Kein weiterer Stundenlauf.")
                return 2
            ergebnis_code = einmal()
            if ergebnis_code != 0:
                return ergebnis_code  # Never retry until explicit new operator start.
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
