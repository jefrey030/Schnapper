"""Echte KI ohne kostenpflichtige API: ausschließlich lokal installiertes Ollama.

Sicherheitsgrenze: 127.0.0.1:11434, keine Umgebungs-URL, keine Weiterleitung,
kein Proxy, kein Download und kein Wechsel zu Cloud-/Bezahlanbietern.
Bei fehlendem lokalen Modell wird der KI-Lauf ehrlich blockiert.
"""
import datetime as dt
import fcntl
import json
import os
import pathlib
import re
import stat
import urllib.error
import urllib.request
import uuid

from ki import KINichtVerfuegbar, MAX_AUFRUFE

LOKAL = "http://127.0.0.1:11434"
MODELL_DEFAULT = "qwen2.5:1.5b"
class KeineWeiterleitungen(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise KINichtVerfuegbar("Ollama darf keine HTTP-Weiterleitungen verwenden.")


_HTTP = urllib.request.build_opener(
    urllib.request.ProxyHandler({}), KeineWeiterleitungen()
)


def _request(pfad, payload=None, timeout=10):
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


class KI:
    def __init__(self, zaehler_datei):
        if os.environ.get("SCHNAPPER_KI_BACKEND") != "ollama":
            raise KINichtVerfuegbar("Lokale KI ist nicht freigegeben.")
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
        modelle = {
            v.get("name") for v in tags.get("models", [])
            if isinstance(v, dict)
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
                fcntl.flock(datei.fileno(), fcntl.LOCK_EX)
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
        self._pruefe_modell()
        aufruf_nummer = self._zaehle()
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
        try:
            inhalt = antwort["message"]["content"].strip()
        except (KeyError, TypeError, AttributeError) as exc:
            raise KINichtVerfuegbar("Lokale KI ohne verwertbaren Antworttext.") from exc
        if not inhalt:
            raise KINichtVerfuegbar("Leere lokale KI-Antwort.")
        return {
            "text": inhalt, "modell": self.modell,
            "antwort_id": "lokal-" + uuid.uuid4().hex,
            "nutzung": {"prompt_eval_count": antwort.get("prompt_eval_count"),
                       "eval_count": antwort.get("eval_count")},
            "aufruf_nr": aufruf_nummer,
            "laufzeit": "Ollama lokal (keine bezahlte KI-API)",
            "erstellt_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        }
