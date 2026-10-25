"""Web-Oberfläche für SCHNAPPER – nur Python-Standardbibliothek, keine Kosten.

Start (aus dem Repo-Stamm):
    PYTHONPATH=app python -m schnapper.web app/beispiele/angebote.csv
Dann im Browser: http://127.0.0.1:8765

Standardmäßig nur auf diesem Gerät erreichbar. Mit --host 0.0.0.0 auch im
eigenen WLAN (z. B. vom Handy auf den PC) – dann ohne Passwort für alle im
WLAN sichtbar, daher nur im eigenen Heimnetz verwenden.
Hochgeladene Listen bleiben nur im Arbeitsspeicher. Nur mit --verlauf DATEI werden
die gesehenen Preise (URL, Zeitpunkt, Preis) lokal in DATEI festgehalten.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import pathlib
import re
import sys
import threading
from decimal import Decimal, InvalidOperation
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

from .adapter import finde_in
from .angebot import ZUSTAENDE, AngebotFehler, geld
from .einlesen import Importergebnis, lies_datei, lies_text
from .quellen import QuellenFehler, Register
from .suche import SORTIERUNGEN, Filter
from .verlauf import Verlauf, VerlaufFehler, warnung

STATISCH = pathlib.Path(__file__).resolve().parent / "web"
DATEIEN = {"/": ("index.html", "text/html; charset=utf-8"),
           "/app.js": ("app.js", "text/javascript; charset=utf-8"),
           "/app.css": ("app.css", "text/css; charset=utf-8"),
           "/manifest.webmanifest": ("manifest.webmanifest", "application/manifest+json; charset=utf-8"),
           "/icon-192.png": ("icon-192.png", "image/png"),
           "/icon-512.png": ("icon-512.png", "image/png"),
           "/icon-maskable-512.png": ("icon-maskable-512.png", "image/png")}
MAX_UPLOAD = 5 * 1024 * 1024
SICHERHEIT = {
    "Content-Security-Policy": "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; "
                               "img-src 'self' data:; manifest-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
}


class Zustand:
    """Aktuell geladene Angebotsliste, threadsicher austauschbar."""

    def __init__(self, register: Register, geladen: Importergebnis, name: str, beispiel: bool,
                 verlauf: Verlauf | None = None):
        self.register = register
        self.verlauf = verlauf
        self._lock = threading.Lock()
        self._import_lock = threading.Lock()  # komplette Import-/Verlaufstransaktion serialisieren
        self._openprices_lock = threading.Lock()  # höchstens ein externer API-Abruf gleichzeitig
        self._daten = (geladen, name, beispiel)

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
            "url": t.angebot.url, "erfasst_am": t.angebot.erfasst_am.isoformat(),
            "warnungen": list(t.warnungen) + [w for w in (warnung(infos[t.angebot.id]),) if w],
            "verlauf": None if infos[t.angebot.id] is None else infos[t.angebot.id].als_dict(),
        } for t in ergebnis.treffer],
    }


CSV_FELDER = (
    "id", "titel", "gesamtpreis", "preis", "versand", "referenzpreis",
    "rabatt_prozent", "zustand", "quelle", "kategorie", "url", "erfasst_am",
    "warnungen",
)


def exportiere_csv(daten: dict) -> bytes:
    """Gefilterte Treffer als sicheres, Excel-kompatibles UTF-8-CSV.

    Fremde Freitextfelder nie als Tabellenformel interpretieren lassen.
    Es werden nur geprüfte Treffer und feste Spaltennamen exportiert.
    """
    ausgabe = io.StringIO(newline="")
    schreiber = csv.writer(ausgabe, delimiter=";", lineterminator="\r\n")
    schreiber.writerow(CSV_FELDER)
    for treffer in daten["treffer"]:
        zellen = []
        for feld in CSV_FELDER:
            wert = treffer.get(feld)
            if feld == "warnungen":
                wert = " | ".join(wert or [])
            text = "" if wert is None else str(wert)
            # Alle ASCII-Steuerzeichen und Unicode-Zeilentrenner entfernen:
            # ungepruefte Feldinhalte duerfen keine Zeilen injizieren.
            text = "".join(
                " " if ord(zeichen) < 32 or zeichen in "\u2028\u2029"
                else zeichen for zeichen in text
            )
            # Spreadsheetprogramme duerfen untrusted Zellen nicht als
            # Formeln ausfuehren – auch nach Unicode-Leerzeichen/BOM nicht.
            if re.match(r"^[\s\ufeff\u200b]*[=+\-@]", text):
                text = "'" + text
            zellen.append(text)
        schreiber.writerow(zellen)
    return ("\ufeff" + ausgabe.getvalue()).encode("utf-8")


def baue_handler(zustand: Zustand):
    class Handler(BaseHTTPRequestHandler):
        server_version = "SCHNAPPER"
        sys_version = ""

        def log_message(self, fmt, *args):  # keine Suchbegriffe/IPs ins Protokoll
            pass

        def _senden(self, status, inhalt: bytes, typ: str, download=None):
            self.send_response(status)
            self.send_header("Content-Type", typ)
            self.send_header("Content-Length", str(len(inhalt)))
            if download is not None:
                # Nur feste, von SCHNAPPER definierte Dateinamen.
                self.send_header("Content-Disposition", f'attachment; filename="{download}"')
            for k, v in SICHERHEIT.items():
                self.send_header(k, v)
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(inhalt)

        def _json(self, status, obj):
            self._senden(status, json.dumps(obj, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

        def do_HEAD(self):
            self.do_GET()

        def do_GET(self):
            teile = urlsplit(self.path)
            if teile.path in DATEIEN:
                datei, typ = DATEIEN[teile.path]
                return self._senden(HTTPStatus.OK, (STATISCH / datei).read_bytes(), typ)
            if teile.path in ("/api/suche", "/api/export.csv", "/api/export.json"):
                try:
                    f, sortierung = filter_aus_query(parse_qs(teile.query))
                except ValueError as exc:
                    return self._json(HTTPStatus.BAD_REQUEST, {"fehler": str(exc)})
                geladen, name, beispiel = zustand.lesen()
                daten = als_json(finde_in(geladen, f, sortierung), name, beispiel,
                                 zustand.verlauf)
                if teile.path == "/api/export.csv":
                    return self._senden(
                        HTTPStatus.OK, exportiere_csv(daten),
                        "text/csv; charset=utf-8", "schnapper-treffer.csv")
                if teile.path == "/api/export.json":
                    roh = (json.dumps(daten, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
                    return self._senden(
                        HTTPStatus.OK, roh, "application/json; charset=utf-8",
                        "schnapper-treffer.json")
                return self._json(HTTPStatus.OK, daten)
            if teile.path == "/api/quellen":
                return self._json(HTTPStatus.OK, {"quellen": [
                    {"kennung": q.kennung, "name": q.name, "entscheidung": q.entscheidung, "hinweis": q.hinweis}
                    for q in zustand.register]})
            return self._json(HTTPStatus.NOT_FOUND, {"fehler": "Nicht gefunden"})

        def do_POST(self):
            ziel = urlsplit(self.path).path
            if ziel not in ("/api/import", "/api/openprices"):
                return self._json(HTTPStatus.NOT_FOUND, {"fehler": "Nicht gefunden"})
            # Schutz gegen fremde Webseiten, die im Hintergrund Daten hochladen wollen
            if self.headers.get("X-Schnapper") != "1":
                return self._json(HTTPStatus.FORBIDDEN, {"fehler": "Anfrage nicht erlaubt"})
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


def erstelle_server(datei, host="127.0.0.1", port=8765, quellen=None, verlauf=None) -> ThreadingHTTPServer:
    datei = pathlib.Path(datei)
    quellen_datei = pathlib.Path(quellen) if quellen else datei.parent / "quellen.json"
    register = Register.mit_datei(quellen_datei) if quellen_datei.is_file() else Register()
    geladen = lies_datei(datei, register)
    v = Verlauf.laden(verlauf) if verlauf else None
    zustand = Zustand(register, geladen, datei.name, beispiel=datei.parent.name == "beispiele", verlauf=v)
    zustand.preise_merken(geladen)
    return ThreadingHTTPServer((host, port), baue_handler(zustand))


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="schnapper.web", description="SCHNAPPER im Browser")
    p.add_argument("datei", help="Start-Liste (.csv/.json)")
    p.add_argument("--host", default="127.0.0.1", help="0.0.0.0 = im eigenen WLAN erreichbar")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--quellen", help="quellen.json mit zusätzlichen Freigaben")
    p.add_argument("--verlauf", help="Datei für den Preisverlauf, z. B. verlauf.json (wird angelegt)")
    a = p.parse_args(argv)
    try:
        server = erstelle_server(a.datei, a.host, a.port, a.quellen, a.verlauf)
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
