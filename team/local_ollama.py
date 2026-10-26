"""Echte KI ohne kostenpflichtige API: ausschließlich lokal installiertes Ollama.

Sicherheitsgrenze: 127.0.0.1:11434, keine Umgebungs-URL, keine Weiterleitung,
kein Proxy, kein Download und kein Wechsel zu Cloud-/Bezahlanbietern.
Bei fehlendem lokalen Modell wird der KI-Lauf ehrlich blockiert.
"""
import datetime as dt
import errno
import fcntl
import json
import os
import pathlib
import re
import stat
import time
import urllib.error
import urllib.request
import uuid

from ki import KINichtVerfuegbar, MAX_AUFRUFE
from operator_approval import pruefe_freigabe

LOKAL = "http://127.0.0.1:11434"
MODELL_DEFAULT = "qwen2.5:1.5b"
# Unabhaengig von Umgebungsfehlern niemals ueber sechs Reservierungen.
MAX_SICHERE_AUFRUFE = 6
LOCK_WARTEZEIT_SEKUNDEN = 2.0


def _hole_zaehlersperre(fd):
    """Dateisperre nur begrenzt erwarten; sonst blockiert statt Endlosschleife."""
    ende = time.monotonic() + LOCK_WARTEZEIT_SEKUNDEN
    while True:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return
        except OSError as exc:
            if exc.errno not in (errno.EAGAIN, errno.EWOULDBLOCK, errno.EACCES):
                raise
            verbleibend = ende - time.monotonic()
            if verbleibend <= 0:
                raise KINichtVerfuegbar(
                    "Lokale Zaehlerdatei belegt: Wartezeit ueberschritten.") from None
            time.sleep(min(0.02, verbleibend))


class KeineWeiterleitungen(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise KINichtVerfuegbar("Ollama darf keine HTTP-Weiterleitungen verwenden.")


_HTTP = urllib.request.build_opener(
    urllib.request.ProxyHandler({}), KeineWeiterleitungen()
)


def _request(pfad, payload=None, timeout=10):
    # Enforce permission at the final HTTP boundary, including direct callers.
    if pfad == "/api/chat":
        pruefe_freigabe()
    if pfad not in ("/api/tags", "/api/chat"):
        raise KINichtVerfuegbar("Unzulässiger Ollama-Pfad.")
    if payload is not None and pfad != "/api/chat":
        raise KINichtVerfuegbar("Unerlaubte Ollama-Anfrage.")
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        LOKAL + pfad, data=data, method="POST" if data is not None else "GET",
        headers={"Content-Type": "application/json"},
    )
    try:
        with _HTTP.open(req, timeout=timeout) as antwort:
            # Kleine Antworten; keine Remote-URLs oder Drittanbieter.
            raw = antwort.read(200_001)
            if len(raw) > 200_000:
                raise KINichtVerfuegbar("Ollama-Antwort zu groß.")
            return json.loads(raw)
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        raise KINichtVerfuegbar(
            "Lokales Ollama nicht erreichbar oder ungültige Antwort. "
            "Prüfe: ollama serve und ollama list."
        ) from exc


def _validiere_chat_antwort(antwort, modell):
    """Prüft Ollama-API-Metadaten; lokale UUIDs sind KEINE Anbieter-Attestierung."""
    if not isinstance(antwort, dict):
        raise KINichtVerfuegbar("Ungültiger Ollama-Antworttyp.")
    if antwort.get("model") != modell:
        raise KINichtVerfuegbar("Ollama meldet ein unerwartetes Modell.")
    if antwort.get("done") is not True or antwort.get("done_reason") != "stop":
        raise KINichtVerfuegbar("Ollama-Antwort nicht vollständig erfolgreich abgeschlossen.")
    message = antwort.get("message")
    if not isinstance(message, dict) or message.get("role") != "assistant":
        raise KINichtVerfuegbar("Ollama-Nachricht stammt nicht aus der Assistant-Rolle.")
    text = message.get("content")
    if not isinstance(text, str) or not text.strip():
        raise KINichtVerfuegbar("Leere oder ungültige Ollama-Antwort.")
    erstellt = antwort.get("created_at")
    if not isinstance(erstellt, str) or len(erstellt) > 80:
        raise KINichtVerfuegbar("Ollama-Antwort hat keinen gültigen Zeitstempel.")
    try:
        zeit = dt.datetime.fromisoformat(erstellt.replace("Z", "+00:00"))
    except ValueError as exc:
        raise KINichtVerfuegbar("Ollama-Antwort hat keinen gültigen Zeitstempel.") from exc
    if zeit.tzinfo is None:
        raise KINichtVerfuegbar("Ollama-Zeitstempel braucht eine Zeitzone.")
    prompt_tokens, erzeugte_tokens = antwort.get("prompt_eval_count"), antwort.get("eval_count")
    if (type(prompt_tokens) is not int or prompt_tokens < 0
            or type(erzeugte_tokens) is not int or erzeugte_tokens < 1):
        raise KINichtVerfuegbar("Ollama-Tokenzählung fehlt oder ist ungültig.")
    return {
        "text": text.strip(),
        "modell_antwort": antwort["model"],
        "done": True,
        "done_reason": "stop",
        "rolle": "assistant",
        "created_at": erstellt,
        "prompt_eval_count": prompt_tokens,
        "eval_count": erzeugte_tokens,
    }



class KI:
    def __init__(self, zaehler_datei):
        if os.environ.get("SCHNAPPER_KI_BACKEND") != "ollama":
            raise KINichtVerfuegbar("Lokale KI ist nicht freigegeben.")
        if (type(MAX_AUFRUFE) is not int
                or not 1 <= MAX_AUFRUFE <= MAX_SICHERE_AUFRUFE):
            raise KINichtVerfuegbar(
                "Ungültiges KI-Aufruflimit: höchstens sechs lokal erlaubt.")
        # Backend selection is not operator consent.
        pruefe_freigabe()
        self.zaehler = pathlib.Path(zaehler_datei)
        self.modell = os.environ.get("SCHNAPPER_OLLAMA_MODELL", MODELL_DEFAULT).strip()
        if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.:/-]{0,79}", self.modell):
            raise KINichtVerfuegbar("Ungültiger lokaler Modellname.")
        # Ollama kann auch Cloud-Modelle vermitteln. Das ist hier strikt verboten.
        # Auch bei einem lokalen API-Endpunkt wäre :cloud eine externe KI.
        if self.modell.lower().endswith(":cloud"):
            raise KINichtVerfuegbar("Cloud-Modelle sind in SCHNAPPER ausdrücklich gesperrt.")

    def _pruefe_modell(self):
        tags = _request("/api/tags")
        if not isinstance(tags, dict) or not isinstance(tags.get("models"), list):
            raise KINichtVerfuegbar("Ungültige lokale Modellliste.")
        # Aus lokalen Ollama-Katalogen nur syntaktisch gültige Namen lesen;
        # verschachtelte Listen/Dictionaries dürfen keine Exception auslösen.
        modelle = {
            v["name"] for v in tags["models"]
            if isinstance(v, dict) and isinstance(v.get("name"), str)
        }
        if self.modell not in modelle:
            raise KINichtVerfuegbar(
                f"Lokales Modell {self.modell!r} nicht installiert; "
                f"auf dem eigenen Rechner: ollama pull {self.modell}"
            )

    def _zaehle(self):
        """Atomare Reservierung pro lokaler Anfrage, auch bei Parallelzugriff.

        Die Antwort-ID ist nur eine lokale Kennung. Der Zaehler ersetzt
        keinerlei unabhaengigen Beweis tatsaechlicher Modell-Inferenz.
        """
        if not hasattr(os, "O_NOFOLLOW"):
            raise KINichtVerfuegbar("Sichere lokale Zaehleroeffnung nicht unterstuetzt.")
        # MAX_AUFRUFE kommt aus der Umgebung/Offline-Testpatches:
        # ein zu hoher, boolescher oder sonst ungültiger Wert muss sperren.
        if (type(MAX_AUFRUFE) is not int
                or not 1 <= MAX_AUFRUFE <= MAX_SICHERE_AUFRUFE):
            raise KINichtVerfuegbar(
                "Ungültiges KI-Aufruflimit: höchstens sechs lokal erlaubt.")
        try:
            self.zaehler.parent.mkdir(parents=True, exist_ok=True)
            fd = os.open(
                str(self.zaehler),
                os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW
                | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NONBLOCK", 0),
                0o600,
            )
            with os.fdopen(fd, "r+b") as datei:
                # Auch FIFO, Verzeichnis, Geraetedatei und Hardlink abweisen.
                info = os.fstat(datei.fileno())
                if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                    raise OSError("Zaehler ist keine eigene regulaere Datei")
                _hole_zaehlersperre(datei.fileno())
                roh = datei.read(9)
                if (len(roh) > 8 or
                        (roh and re.fullmatch(rb"[0-9]{1,8}", roh) is None)):
                    raise ValueError("Nichtnumerischer oder zu grosser Zaehler")
                bisher = int(roh) if roh else 0
                if bisher >= MAX_AUFRUFE:
                    raise KINichtVerfuegbar(
                        f"Maximal {MAX_AUFRUFE} lokale KI-Aufrufe pro Stundenlauf.")
                nummer = bisher + 1
                if nummer > 99_999_999:
                    raise ValueError("Zaehlergrenze ueberschritten")
                # Feste Breite vermeidet Truncate-Zwischenzustand.
                datei.seek(0)
                written = datei.write(f"{nummer:08d}".encode("ascii"))
                if written != 8:
                    raise OSError("Unvollstaendige Zaehler-Schreiboperation")
                datei.flush()
                os.fsync(datei.fileno())
                return nummer
        except (OSError, ValueError) as exc:
            raise KINichtVerfuegbar("Lokaler KI-Aufrufzaehler unsicher oder nicht lesbar.") from exc

    def frage(self, system, nutzer):
        # Revalidate consent, selected open task and STOP before every request.
        pruefe_freigabe()
        self._pruefe_modell()
        aufruf_nummer = self._zaehle()
        pruefe_freigabe()  # Recheck after model discovery and counter lock wait.
        antwort = _request("/api/chat", {
            "model": self.modell,
            "stream": False,
            "keep_alive": "5m",
            "messages": [
                {"role": "system", "content": system[:6000]},
                {"role": "user", "content": nutzer[:12000]},
            ],
            "options": {"num_predict": 700, "temperature": 0.2},
        }, timeout=180)
        beleg = _validiere_chat_antwort(antwort, self.modell)
        return {
            "text": beleg["text"], "modell": self.modell,
            # Die UUID belegt lediglich die lokale Zuordnung, keine echte
            # kryptografische Identität eines Ollama-/Modellanbieters.
            "antwort_id": "lokal-" + uuid.uuid4().hex,
            "antwort_id_typ": "nur-lokale-kennung",
            "ollama_beleg": {k: v for k, v in beleg.items() if k != "text"},
            "nutzung": {
                "prompt_eval_count": beleg["prompt_eval_count"],
                "eval_count": beleg["eval_count"],
            },
            # MASTER 80: reservierte Nummer behalten (kein unsicheres
            # Nachlesen des Counters bei parallelen Modellantworten).
            "aufruf_nr": aufruf_nummer,
            "laufzeit": "Ollama lokal (keine bezahlte KI-API)",
            "erstellt_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        }
