"""Echte KI ohne kostenpflichtige API: ausschließlich lokal installiertes Ollama.

Sicherheitsgrenze: 127.0.0.1:11434, keine Umgebungs-URL, keine Weiterleitung,
kein Proxy, kein Download und kein Wechsel zu Cloud-/Bezahlanbietern.
Bei fehlendem lokalen Modell wird der KI-Lauf ehrlich blockiert.
"""
import datetime as dt
import json
import os
import pathlib
import re
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
        try:
            bisher = int(self.zaehler.read_text()) if self.zaehler.exists() else 0
        except (OSError, ValueError) as exc:
            raise KINichtVerfuegbar("Ungültiger KI-Aufrufzähler.") from exc
        if bisher >= MAX_AUFRUFE:
            raise KINichtVerfuegbar(
                f"Maximal {MAX_AUFRUFE} lokale KI-Aufrufe pro Stundenlauf."
            )
        self.zaehler.parent.mkdir(parents=True, exist_ok=True)
        self.zaehler.write_text(str(bisher + 1), encoding="utf-8")

    def frage(self, system, nutzer):
        self._pruefe_modell()
        self._zaehle()
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
            "aufruf_nr": int(self.zaehler.read_text(encoding="utf-8")),
            "laufzeit": "Ollama lokal (keine bezahlte KI-API)",
            "erstellt_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        }
