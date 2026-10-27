"""Web-Oberfläche für SCHNAPPER – nur Python-Standardbibliothek, keine Kosten.

Start (aus dem Repo-Stamm):
    PYTHONPATH=app python -m schnapper.web app/beispiele/angebote.csv
Dann im Browser: http://127.0.0.1:8765

Standardmäßig nur auf diesem Gerät erreichbar. Mit --host 0.0.0.0 auch im
eigenen WLAN (z. B. vom Handy auf den PC) – dann ohne Passwort für alle im
WLAN sichtbar, daher nur im eigenen Heimnetz verwenden.
Hochgeladene Listen bleiben nur im Arbeitsspeicher. Nur mit --verlauf DATEI werden
die gesehenen Preise (URL, Zeitpunkt, Preis) lokal in DATEI festgehalten.
Missionen und BLITZ-Deduplizierung werden getrennt davon lokal unter
~/.local/share/schnapper gespeichert (mit --datenverzeichnis änderbar).
"""
from __future__ import annotations

import argparse
import datetime as dt
import ipaddress
import json
import pathlib
import sys
import threading
import uuid
from decimal import Decimal, InvalidOperation
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

from .adapter import finde_in
from .alarm import Wunsch
from .angebot import ZUSTAENDE, AngebotFehler, geld
from .blitz import Blitz, BlitzFehler, BlitzKonflikt
from .einlesen import Importergebnis, lies_datei, lies_text
from .mission import Mission, Missionsspeicher, MissionsFehler, MissionsKonflikt
from .quellen import QuellenFehler, Register
from .sicherer_speicher import dateien_wiederherstellen, dateisperre, lese_fd, missionslauf_sperre
from .suche import SORTIERUNGEN, Filter
from .verlauf import Verlauf, VerlaufFehler, warnung

STATISCH = pathlib.Path(__file__).resolve().parent / "web"
DATEIEN = {"/": ("index.html", "text/html; charset=utf-8"),
           "/app.js": ("app.js", "text/javascript; charset=utf-8"),
           "/app.css": ("app.css", "text/css; charset=utf-8"),
           "/manifest.webmanifest": ("manifest.webmanifest", "application/manifest+json; charset=utf-8"),
           "/icon-192.png": ("icon-192.png", "image/png"),
           "/icon-512.png": ("icon-512.png", "image/png"),
           "/icon-maskable-512.png": ("icon-maskable-512.png", "image/png"),
           "/sw.js": ("sw.js", "text/javascript; charset=utf-8")}
MAX_UPLOAD = 5 * 1024 * 1024
MAX_BACKUP_BYTES = 12 * 1024 * 1024
SICHERHEIT = {
    "Content-Security-Policy": "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; "
                               "img-src 'self' data:; manifest-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
}


def _lokaler_host(host_header: str | None, bind_host: str, port: int) -> tuple[str, int] | None:
    """Abwehr fremder Hostnames/DNS-Rebinding bei der lokalen, ungeschützten UI.

    Nur localhost/Loopback auf dem wirklich verwendeten Port. Die explizite
    WLAN-Freigabe (--host 0.0.0.0) erlaubt zusätzlich private IP-Literale,
    keine über DNS auf lokale IPs auflösenden Fremd-Hostnamen.
    """
    if not isinstance(host_header, str) or not host_header or any(
            x.isspace() or x in "/\\@" for x in host_header):
        return None
    try:
        teile = urlsplit("http://" + host_header)
        hostname = (teile.hostname or "").lower()
        angefragt_port = teile.port or 80
        if teile.username or teile.password or teile.path or teile.query or teile.fragment:
            return None
    except ValueError:
        return None
    if angefragt_port != port:
        return None
    if hostname == "localhost":
        return hostname, angefragt_port
    try:
        ip = ipaddress.ip_address(hostname)
    except ValueError:
        return None
    if ip.is_loopback:
        return hostname, angefragt_port
    if bind_host not in ("0.0.0.0", "::", "") and hostname != bind_host:
        return None
    if ip.is_unspecified or ip.is_multicast or ip.is_reserved:
        return None
    if ip.is_private or ip.is_link_local:
        return hostname, angefragt_port
    return None


def _origin_erlaubt(origin: str | None, hostname: str, port: int) -> bool:
    """Fremde Browser-Origin bei schreibenden POST-Anfragen blockieren.

    Ohne Origin dürfen lokale Skripte weiter POST senden; hierfür ist noch
    immer X-Schnapper erforderlich. Kein Ersatz für ein WLAN-Passwort/Auth.
    """
    if origin is None:
        return True
    if not isinstance(origin, str) or not origin or any(x.isspace() for x in origin):
        return False
    try:
        teile = urlsplit(origin)
        return (teile.scheme == "http" and (teile.hostname or "").lower() == hostname
                and (teile.port or 80) == port and not teile.path
                and not teile.query and not teile.fragment
                and not teile.username and not teile.password)
    except ValueError:
        return False


class Zustand:
    """Aktuell geladene Angebotsliste, threadsicher austauschbar."""

    def __init__(self, register: Register, geladen: Importergebnis, name: str, beispiel: bool,
                 verlauf: Verlauf | None = None, datenverzeichnis: pathlib.Path | str | None = None):
        self.register = register
        self.verlauf = verlauf
        self._lock = threading.Lock()
        self._import_lock = threading.Lock()  # komplette Import-/Verlaufstransaktion serialisieren
        self._openprices_lock = threading.Lock()  # höchstens ein externer API-Abruf gleichzeitig
        self._mission_locks: dict[str, threading.Lock] = {}
        self._mission_locks_lock = threading.Lock()
        self.datenverzeichnis = None if datenverzeichnis is None else pathlib.Path(datenverzeichnis)
        self.missionen = None
        self.blitz = None
        if self.datenverzeichnis is not None:
            missionen_pfad = self.datenverzeichnis / "missionen.json"
            blitz_pfad = self.datenverzeichnis / "blitz.json"
            self.missionen = Missionsspeicher.laden(missionen_pfad)
            self.blitz = Blitz.laden(blitz_pfad)
        self._daten = (geladen, name, beispiel)

    def mission_sperre(self, mission_id: str) -> threading.Lock:
        with self._mission_locks_lock:
            return self._mission_locks.setdefault(mission_id, threading.Lock())

    def lesen(self):
        with self._lock:
            return self._daten

    def ersetzen(self, geladen: Importergebnis, name: str):
        # Immer nur ein Import zur Zeit: Ein langsamer Verlaufsschreibvorgang darf
        # nicht von einem zweiten Import überholt werden.
        with self._import_lock:
            # Bei einem Speicherfehler bleibt die bislang aktive Liste unverändert.
            self.preise_merken(geladen)
            with self._lock:
                self._daten = (geladen, name, False)

    def preise_merken(self, geladen: Importergebnis):
        if self.verlauf is not None:
            # Atomarer Verlauf: keine ungespeicherten/verworfenen Beobachtungen
            # im RAM belassen; das Angebot wird erst danach aktiviert.
            self.verlauf.importiere(geladen.angebote)


def filter_aus_query(q: dict) -> tuple[Filter, str]:
    def eins(name, standard=""):
        return (q.get(name) or [standard])[0].strip()

    try:
        max_preis = geld(eins("max_preis")) if eins("max_preis") else None
        if max_preis is not None and max_preis <= 0:
            raise ValueError("Höchstpreis muss größer als 0 sein")
        min_rabatt = Decimal(eins("min_rabatt").replace(",", ".")) if eins("min_rabatt") else None
        if min_rabatt is not None and (not min_rabatt.is_finite() or not 0 <= min_rabatt <= 100):
            raise ValueError("Mindestrabatt muss zwischen 0 und 100 Prozent liegen")
        entfernung = Decimal(eins("entfernung_km").replace(",", ".")) if eins("entfernung_km") else None
        if entfernung is not None and (not entfernung.is_finite() or not 0 <= entfernung <= 500):
            raise ValueError("Entfernung muss zwischen 0 und 500 km liegen")
    except (AngebotFehler, InvalidOperation) as exc:
        raise ValueError("Höchstpreis oder Mindestrabatt ist keine Zahl") from exc
    zustand = eins("zustand")
    if zustand and zustand not in ZUSTAENDE:
        raise ValueError("Unbekannter Zustand")
    sortierung = eins("sortierung", "rabatt")
    if sortierung not in SORTIERUNGEN:
        raise ValueError("Unbekannte Sortierung")
    f = Filter(text=eins("text")[:200], max_preis=max_preis, min_rabatt=min_rabatt,
               zustaende={zustand} if zustand else set(),
               region=eins("region")[:100], entfernung_km=entfernung,
               ohne_veraltet=eins("ohne_veraltet") == "1", ohne_verdacht=eins("mit_verdacht") != "1")
    return f, sortierung


def als_json(ergebnis, name: str, beispiel: bool, verlauf: Verlauf | None = None) -> dict:
    infos = {t.angebot.id: (verlauf.info(t.angebot) if verlauf is not None else None) for t in ergebnis.treffer}
    return {
        "verlauf_aktiv": verlauf is not None,
        "liste": name, "beispieldaten": beispiel,
        "enthaelt_testdaten": any(t.angebot.quelle == "mock" for t in ergebnis.treffer),
        "eingelesen": ergebnis.eingelesen,
        "ungueltig": ergebnis.fehler,
        "dubletten": [{"entfernt": a.id, "behalten": b.id, "titel": a.titel} for a, b in ergebnis.dubletten],
        "treffer": [{
            "id": t.angebot.id, "titel": t.angebot.titel, "preis": str(t.angebot.preis),
            "versand": str(t.angebot.versand), "gesamtpreis": str(t.angebot.gesamtpreis),
            "referenzpreis": None if t.angebot.referenzpreis is None else str(t.angebot.referenzpreis),
            "rabatt_prozent": None if t.angebot.rabatt_prozent is None else str(t.angebot.rabatt_prozent),
            "zustand": t.angebot.zustand, "quelle": t.angebot.quelle, "kategorie": t.angebot.kategorie,
            "region": t.angebot.extra.get("region") if isinstance(t.angebot.extra.get("region"), str) else None,
            "entfernung_km": t.angebot.extra.get("entfernung_km"),
            "url": t.angebot.url, "erfasst_am": t.angebot.erfasst_am.isoformat(),
            "warnungen": list(t.warnungen) + [w for w in (warnung(infos[t.angebot.id]),) if w],
            "verlauf": None if infos[t.angebot.id] is None else infos[t.angebot.id].als_dict(),
        } for t in ergebnis.treffer],
    }


def baue_handler(zustand: Zustand):
    class Handler(BaseHTTPRequestHandler):
        server_version = "SCHNAPPER"
        sys_version = ""

        def log_message(self, fmt, *args):  # keine Suchbegriffe/IPs ins Protokoll
            pass

        def _senden(self, status, inhalt: bytes, typ: str):
            self.send_response(status)
            self.send_header("Content-Type", typ)
            self.send_header("Content-Length", str(len(inhalt)))
            for k, v in SICHERHEIT.items():
                self.send_header(k, v)
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(inhalt)

        def _json(self, status, obj):
            self._senden(status, json.dumps(obj, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

        def _json_eingabe(self, max_bytes=16 * 1024):
            try:
                laenge = int(self.headers.get("Content-Length", ""))
            except ValueError:
                return None, "Länge fehlt", HTTPStatus.LENGTH_REQUIRED
            if not 1 <= laenge <= max_bytes:
                return None, "JSON fehlt oder ist zu groß", HTTPStatus.REQUEST_ENTITY_TOO_LARGE
            if self.headers.get_content_type() != "application/json":
                return None, "Content-Type muss application/json sein", HTTPStatus.UNSUPPORTED_MEDIA_TYPE
            try:
                daten = json.loads(self.rfile.read(laenge))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return None, "Ungültiges JSON", HTTPStatus.BAD_REQUEST
            if not isinstance(daten, dict):
                return None, "JSON muss ein Objekt sein", HTTPStatus.BAD_REQUEST
            return daten, None, None

        def _mission_lauf_ausfuehren(self, mission_id: str, automatisch: bool):
            mission = next((m for m in zustand.missionen.alle() if m.id == mission_id), None)
            if mission is None:
                return self._json(HTTPStatus.NOT_FOUND, {"fehler": "Mission nicht gefunden"})
            jetzt = dt.datetime.now(dt.timezone.utc)
            if mission.status != "aktiv":
                return self._json(HTTPStatus.CONFLICT, {"fehler": "Mission ist pausiert oder beendet"})
            if automatisch and (not mission.automatisch or not mission.ist_faellig(jetzt)):
                return self._json(HTTPStatus.CONFLICT, {"fehler": "Mission ist nicht automatisch fällig"})
            geladen, name, beispiel = zustand.lesen()
            ergebnis = finde_in(geladen, mission.filter(), "preis", jetzt=jetzt)
            try:
                zustand.missionen.lauf_abschliessen(mission_id, jetzt=jetzt, erzwingen=True)
            except (MissionsFehler, OSError):
                return self._json(HTTPStatus.CONFLICT,
                                  {"fehler": "Missionslauf konnte nicht sicher gespeichert werden; bitte neu laden"})
            meldungen = []
            blitz_fehler = None
            wunsch = Wunsch(
                name=mission.name, suche=mission.suche, max_preis=mission.max_preis,
                min_rabatt=mission.min_rabatt, zustaende=mission.zustaende,
                region=mission.region, entfernung_km=mission.entfernung_km)
            try:
                meldungen = [m.als_dict() for m in zustand.blitz.pruefen(geladen, [wunsch], jetzt)]
            except BlitzKonflikt as exc:
                return self._json(HTTPStatus.CONFLICT, {"fehler": str(exc), "aktualisieren": True})
            except (BlitzFehler, OSError):
                blitz_fehler = "BLITZ-Deduplizierung konnte nicht gespeichert werden; kein Versand bestätigt"
            antwort = als_json(ergebnis, name, beispiel, zustand.verlauf)
            antwort.update({
                "job_id": uuid.uuid4().hex,
                "mission_id": mission_id,
                "gestartet_am": jetzt.isoformat(),
                "abgeschlossen_am": dt.datetime.now(dt.timezone.utc).isoformat(),
                "meldungen": meldungen,
                "blitz_fehler": blitz_fehler,
                "benachrichtigung": "lokale_queue" if meldungen else "keine_neue_meldung",
            })
            return self._json(HTTPStatus.OK, antwort)

        def _host_erlaubt(self):
            bind_host, port = self.server.server_address[:2]
            return _lokaler_host(self.headers.get("Host"), bind_host, port)

        def do_HEAD(self):
            self.do_GET()

        def do_GET(self):
            if self._host_erlaubt() is None:
                return self._json(HTTPStatus.FORBIDDEN, {"fehler": "Host nicht erlaubt"})
            teile = urlsplit(self.path)
            if teile.path in DATEIEN:
                datei, typ = DATEIEN[teile.path]
                return self._senden(HTTPStatus.OK, (STATISCH / datei).read_bytes(), typ)
            if teile.path == "/api/suche":
                try:
                    f, sortierung = filter_aus_query(parse_qs(teile.query))
                except ValueError as exc:
                    return self._json(HTTPStatus.BAD_REQUEST, {"fehler": str(exc)})
                geladen, name, beispiel = zustand.lesen()
                return self._json(HTTPStatus.OK, als_json(finde_in(geladen, f, sortierung), name, beispiel,
                                                         zustand.verlauf))
            if teile.path == "/api/quellen":
                return self._json(HTTPStatus.OK, {"quellen": [
                    {"kennung": q.kennung, "name": q.name, "entscheidung": q.entscheidung, "hinweis": q.hinweis}
                    for q in zustand.register]})
            if teile.path == "/api/missionen":
                if zustand.missionen is None:
                    return self._json(HTTPStatus.SERVICE_UNAVAILABLE,
                                      {"fehler": "Lokale Missionsspeicherung ist nicht konfiguriert"})
                return self._json(HTTPStatus.OK, {
                    "missionen": [m.als_dict() for m in zustand.missionen.alle()],
                    "speicher": "lokal",
                    "automatik": "nur während die App geöffnet und sichtbar ist",
                })
            if teile.path == "/api/backup":
                if zustand.missionen is None or zustand.blitz is None:
                    return self._json(HTTPStatus.SERVICE_UNAVAILABLE,
                                      {"fehler": "Lokale Sicherung ist nicht konfiguriert"})
                try:
                    # MISSION and BLITZ share one directory-wide lock. Read and
                    # validate both raw files under one acquisition; calling
                    # either store's public export method here would acquire a
                    # second blocking lock and could deadlock.
                    with dateisperre(zustand.datenverzeichnis / "missionen.json") as (directory, _name):
                        missionen, _mission_revision = Missionsspeicher.dekodiere_snapshot(
                            lese_fd(directory, "missionen.json"))
                        blitz_gesehen, _blitz_revision = Blitz.dekodiere_snapshot(
                            lese_fd(directory, "blitz.json"))
                    return self._json(HTTPStatus.OK, {
                        "format": "schnapper-server-backup",
                        "version": 1,
                        "missionen": [m.als_dict() for m in missionen],
                        "blitz_gesehen": blitz_gesehen,
                    })
                except (MissionsFehler, BlitzFehler, OSError):
                    return self._json(HTTPStatus.INTERNAL_SERVER_ERROR,
                                      {"fehler": "Lokaler Datenbestand ist beschädigt; Sicherung abgebrochen"})
            return self._json(HTTPStatus.NOT_FOUND, {"fehler": "Nicht gefunden"})

        def do_POST(self):
            ziel = urlsplit(self.path).path
            host = self._host_erlaubt()
            if host is None:
                return self._json(HTTPStatus.FORBIDDEN, {"fehler": "Host nicht erlaubt"})
            if not _origin_erlaubt(self.headers.get("Origin"), *host):
                return self._json(HTTPStatus.FORBIDDEN, {"fehler": "Fremde Webseite nicht erlaubt"})
            if ziel not in ("/api/import", "/api/openprices", "/api/missionen", "/api/backup") \
                    and not ziel.startswith("/api/missionen/"):
                return self._json(HTTPStatus.NOT_FOUND, {"fehler": "Nicht gefunden"})
            # Schutz gegen fremde Webseiten, die im Hintergrund Daten hochladen wollen
            if self.headers.get("X-Schnapper") != "1":
                return self._json(HTTPStatus.FORBIDDEN, {"fehler": "Anfrage nicht erlaubt"})
            if ziel == "/api/backup":
                if zustand.missionen is None or zustand.blitz is None or zustand.datenverzeichnis is None:
                    return self._json(HTTPStatus.SERVICE_UNAVAILABLE,
                                      {"fehler": "Lokale Wiederherstellung ist nicht konfiguriert"})
                daten, fehler, status = self._json_eingabe(MAX_BACKUP_BYTES)
                if fehler:
                    return self._json(status, {"fehler": fehler})
                if (daten.get("format") != "schnapper-server-backup"
                        or type(daten.get("version")) is not int or daten.get("version") != 1
                        or not isinstance(daten.get("missionen"), list)
                        or not isinstance(daten.get("blitz_gesehen"), dict)):
                    return self._json(HTTPStatus.BAD_REQUEST, {"fehler": "Sicherungsformat ist ungültig"})
                try:
                    missionen = [Mission.aus_dict(item) for item in daten["missionen"]]
                    Missionsspeicher._pruefe_gesamt(missionen)
                    mission_raw = json.dumps(
                        {"version": 2, "missionen": [m.als_dict() for m in missionen]},
                        ensure_ascii=False, separators=(",", ":"),
                    ).encode("utf-8")
                    blitz_raw = json.dumps(
                        {"version": 2, "gesehen": daten["blitz_gesehen"]},
                        ensure_ascii=False, separators=(",", ":"),
                    ).encode("utf-8")
                    Missionsspeicher._dekodiere(mission_raw, "missionen.json")
                    Blitz._dekodiere(blitz_raw, "blitz.json")
                    dateien_wiederherstellen(
                        zustand.datenverzeichnis / "missionen.json",
                        {"missionen.json": mission_raw, "blitz.json": blitz_raw},
                    )
                    # Refresh both in-memory snapshots and their conflict tokens.
                    zustand.missionen.alle()
                    zustand.blitz.exportdaten()
                    return self._json(HTTPStatus.OK, {
                        "wiederhergestellt": True,
                        "missionen": len(missionen),
                        "blitz_eintraege": len(daten["blitz_gesehen"]),
                    })
                except (MissionsFehler, BlitzFehler, ValueError, TypeError):
                    return self._json(HTTPStatus.BAD_REQUEST, {"fehler": "Sicherung ist ungültig"})
                except OSError:
                    return self._json(HTTPStatus.INTERNAL_SERVER_ERROR,
                                      {"fehler": "Wiederherstellung konnte nicht sicher abgeschlossen werden; Originaldatei behalten"})
            if ziel == "/api/missionen":
                if zustand.missionen is None:
                    return self._json(HTTPStatus.SERVICE_UNAVAILABLE,
                                      {"fehler": "Lokale Missionsspeicherung ist nicht konfiguriert"})
                daten, fehler, status = self._json_eingabe()
                if fehler:
                    return self._json(status, {"fehler": fehler})
                aktion = daten.get("aktion")
                mission_id = daten.get("id")
                try:
                    if aktion == "erstellen":
                        mission = zustand.missionen.erstellen(
                            name=daten.get("name"), suche=daten.get("suche"),
                            max_preis=daten.get("max_preis"), min_rabatt=daten.get("min_rabatt"),
                            zustaende=daten.get("zustaende", []),
                            intervall_minuten=daten.get("intervall_minuten", 60),
                            region=daten.get("region", ""),
                            entfernung_km=daten.get("entfernung_km"),
                            automatisch=daten.get("automatisch", False))
                        return self._json(HTTPStatus.CREATED, {"mission": mission.als_dict()})
                    if not isinstance(mission_id, str):
                        return self._json(HTTPStatus.BAD_REQUEST, {"fehler": "Missions-ID fehlt"})
                    if aktion == "bearbeiten":
                        felder = ("name", "suche", "max_preis", "min_rabatt", "zustaende",
                                  "intervall_minuten", "region", "entfernung_km", "automatisch")
                        aenderungen = {feld: daten[feld] for feld in felder if feld in daten}
                        mission = zustand.missionen.bearbeiten(mission_id, **aenderungen)
                        return self._json(HTTPStatus.OK, {"mission": mission.als_dict()})
                    if aktion == "pausieren":
                        mission = zustand.missionen.pausieren(mission_id)
                    elif aktion == "fortsetzen":
                        mission = zustand.missionen.fortsetzen(mission_id)
                    elif aktion == "loeschen":
                        zustand.missionen.loeschen(mission_id)
                        return self._json(HTTPStatus.OK, {"geloescht": mission_id})
                    else:
                        return self._json(HTTPStatus.BAD_REQUEST, {"fehler": "Unbekannte Mission-Aktion"})
                    return self._json(HTTPStatus.OK, {"mission": mission.als_dict()})
                except MissionsKonflikt as exc:
                    return self._json(HTTPStatus.CONFLICT, {"fehler": str(exc), "aktualisieren": True})
                except MissionsFehler as exc:
                    return self._json(HTTPStatus.BAD_REQUEST, {"fehler": str(exc)})
                except OSError:
                    return self._json(HTTPStatus.INTERNAL_SERVER_ERROR,
                                      {"fehler": "Mission konnte lokal nicht sicher gespeichert werden"})
            if ziel.startswith("/api/missionen/") and ziel.endswith("/lauf"):
                if zustand.missionen is None or zustand.blitz is None:
                    return self._json(HTTPStatus.SERVICE_UNAVAILABLE,
                                      {"fehler": "Lokaler Missions- und Blitzspeicher ist nicht konfiguriert"})
                teile = ziel.split("/")
                if len(teile) != 5 or not teile[3] or teile[4] != "lauf":
                    return self._json(HTTPStatus.NOT_FOUND, {"fehler": "Mission nicht gefunden"})
                mission_id = teile[3]
                daten, fehler, status = self._json_eingabe(1024)
                if fehler:
                    return self._json(status, {"fehler": fehler})
                automatisch = daten.get("automatisch", False)
                if not isinstance(automatisch, bool):
                    return self._json(HTTPStatus.BAD_REQUEST, {"fehler": "Automatik-Flag ungültig"})
                sperre = zustand.mission_sperre(mission_id)
                if not sperre.acquire(blocking=False):
                    return self._json(HTTPStatus.CONFLICT,
                                      {"fehler": "Für diese Mission läuft bereits eine Prüfung"})
                try:
                    try:
                        with missionslauf_sperre(
                                zustand.datenverzeichnis / "missionen.json", mission_id) as laeuft:
                            if not laeuft:
                                return self._json(HTTPStatus.CONFLICT,
                                                  {"fehler": "Für diese Mission läuft bereits eine Prüfung"})
                            return self._mission_lauf_ausfuehren(mission_id, automatisch)
                    except OSError:
                        return self._json(HTTPStatus.SERVICE_UNAVAILABLE,
                                          {"fehler": "Sichere Missionslauf-Sperre nicht verfügbar"})
                finally:
                    sperre.release()
            if ziel == "/api/openprices":
                from .openprices import (LIZENZ, OpenPricesAdapter,
                                         OpenPricesFehler, OpenPricesGesperrt)
                try:
                    laenge = int(self.headers.get("Content-Length", ""))
                except ValueError:
                    return self._json(HTTPStatus.LENGTH_REQUIRED, {"fehler": "Länge fehlt"})
                if not 1 <= laenge <= 256:
                    return self._json(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"fehler": "Barcode-Anfrage zu groß oder leer"})
                try:
                    eingabe = json.loads(self.rfile.read(laenge))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    return self._json(HTTPStatus.BAD_REQUEST, {"fehler": "Ungültiges JSON"})
                if not isinstance(eingabe, dict) or not isinstance(eingabe.get("ean"), str):
                    return self._json(HTTPStatus.BAD_REQUEST, {"fehler": "Barcode fehlt"})
                try:
                    adapter = OpenPricesAdapter(eingabe["ean"], register=zustand.register)
                except ValueError as exc:
                    return self._json(HTTPStatus.BAD_REQUEST, {"fehler": str(exc)})
                grund = adapter.sperrgrund()
                if grund:
                    return self._json(HTTPStatus.FORBIDDEN, {"fehler": grund})
                if not zustand._openprices_lock.acquire(blocking=False):
                    return self._json(HTTPStatus.TOO_MANY_REQUESTS,
                                      {"fehler": "Es läuft bereits eine Barcode-Abfrage. Bitte danach erneut versuchen."})
                try:
                    geladen = adapter.lade()
                except OpenPricesGesperrt as exc:
                    return self._json(HTTPStatus.FORBIDDEN, {"fehler": str(exc)})
                except OpenPricesFehler as exc:
                    return self._json(HTTPStatus.SERVICE_UNAVAILABLE, {"fehler": str(exc)})
                finally:
                    zustand._openprices_lock.release()
                daten = als_json(finde_in(geladen, Filter(), "preis"), "Open Prices", False)
                daten["lizenz"] = LIZENZ
                daten["hinweise"] = adapter.hinweise[:50]
                daten["begrenzung"] = "Nur die bis zu 50 neuesten gemeldeten Preise; keine Vollständigkeitsgarantie."
                return self._json(HTTPStatus.OK, daten)
            try:
                laenge = int(self.headers.get("Content-Length", ""))
            except ValueError:
                return self._json(HTTPStatus.LENGTH_REQUIRED, {"fehler": "Länge fehlt"})
            if laenge <= 0 or laenge > MAX_UPLOAD:
                return self._json(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"fehler": "Datei leer oder größer als 5 MB"})
            name = pathlib.PurePath(self.headers.get("X-Dateiname", "liste.csv")).name[:100]
            endung = pathlib.PurePath(name).suffix.lower()
            if endung not in (".csv", ".json"):
                return self._json(HTTPStatus.BAD_REQUEST, {"fehler": "Nur .csv oder .json"})
            try:
                text = self.rfile.read(laenge).decode("utf-8-sig")
            except UnicodeDecodeError:
                return self._json(HTTPStatus.BAD_REQUEST, {"fehler": "Datei ist nicht UTF-8"})
            geladen = lies_text(text, endung[1:], zustand.register)
            if not geladen.angebote:
                return self._json(HTTPStatus.UNPROCESSABLE_ENTITY,
                                  {"fehler": "Keine gültigen Angebote in der Datei", "ungueltig": geladen.fehler[:50]})
            try:
                zustand.ersetzen(geladen, name)
            except OSError:
                return self._json(HTTPStatus.INTERNAL_SERVER_ERROR,
                                  {"fehler": "Liste nicht übernommen: Preisverlauf konnte nicht gespeichert werden"})
            return self._json(HTTPStatus.OK, {"eingelesen": len(geladen.angebote), "ungueltig": geladen.fehler})

    return Handler


def erstelle_server(datei, host="127.0.0.1", port=8765, quellen=None, verlauf=None,
                    datenverzeichnis=None) -> ThreadingHTTPServer:
    datei = pathlib.Path(datei)
    quellen_datei = pathlib.Path(quellen) if quellen else datei.parent / "quellen.json"
    register = Register.mit_datei(quellen_datei) if quellen_datei.is_file() else Register()
    geladen = lies_datei(datei, register)
    v = Verlauf.laden(verlauf) if verlauf else None
    zustand = Zustand(register, geladen, datei.name, beispiel=datei.parent.name == "beispiele",
                      verlauf=v, datenverzeichnis=datenverzeichnis)
    zustand.preise_merken(geladen)
    return ThreadingHTTPServer((host, port), baue_handler(zustand))


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="schnapper.web", description="SCHNAPPER im Browser")
    p.add_argument("datei", help="Start-Liste (.csv/.json)")
    p.add_argument("--host", default="127.0.0.1", help="0.0.0.0 = im eigenen WLAN erreichbar")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--quellen", help="quellen.json mit zusätzlichen Freigaben")
    p.add_argument("--verlauf", help="Datei für den Preisverlauf, z. B. verlauf.json (wird angelegt)")
    p.add_argument("--datenverzeichnis", help="Lokaler Speicher für Missionen und BLITZ-Deduplizierung")
    a = p.parse_args(argv)
    try:
        datenverzeichnis = a.datenverzeichnis or str(pathlib.Path.home() / ".local" / "share" / "schnapper")
        server = erstelle_server(a.datei, a.host, a.port, a.quellen, a.verlauf, datenverzeichnis)
    except (OSError, QuellenFehler, VerlaufFehler, ValueError) as exc:
        print("Start fehlgeschlagen:", exc, file=sys.stderr)
        return 1
    if a.host not in ("127.0.0.1", "localhost"):
        print("Achtung: im Netzwerk ohne Passwort erreichbar – nur im eigenen WLAN nutzen.", file=sys.stderr)
    print(f"SCHNAPPER läuft: http://{'127.0.0.1' if a.host == '0.0.0.0' else a.host}:{a.port}  (Beenden: Strg+C)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
