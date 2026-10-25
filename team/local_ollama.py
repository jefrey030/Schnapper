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
            v["name"] for v in tags["models"]
            if isinstance(v, dict) and isinstance(v.get("name"), str)
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
        beleg = _validiere_chat_antwort(antwort, self.modell)
        return {
            "text": beleg["text"], "modell": self.modell,
            # Selbst erzeugte Laufkennung, KEINE bestätigte Ollama-Provider-ID.
            "antwort_id": "lokal-" + uuid.uuid4().hex,
            "antwort_id_typ": "nur-lokale-kennung",
            "ollama_beleg": {k: v for k, v in beleg.items() if k != "text"},
            "nutzung": {"prompt_eval_count": beleg["prompt_eval_count"],
                       "eval_count": beleg["eval_count"]},
            "aufruf_nr": int(self.zaehler.read_text(encoding="utf-8")),
            "laufzeit": "Ollama lokal (keine bezahlte KI-API)",
            "erstellt_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        }
