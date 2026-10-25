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
            result = json.loads(raw)
            if not isinstance(result, dict):
                raise KINichtVerfuegbar("Lokale Ollama-API lieferte kein JSON-Objekt.")
            return result
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
        # Falsche Katalogtypen dürfen keine unkontrollierte Ausnahme auslösen.
        installiert = any(
            isinstance(v, dict) and isinstance(v.get("name"), str)
            and v["name"] == self.modell for v in tags["models"]
        )
        if not installiert:
            raise KINichtVerfuegbar(
                f"Lokales Modell {self.modell!r} nicht installiert; "
                f"auf dem eigenen Rechner: ollama pull {self.modell}"
            )

    def _zaehle(self):
        """Reserviert exakt einen Modellversuch unter exklusiver Dateisperre.

        Die Sperre wird per atomarem mkdir erstellt: ein paralleler Prozess
        wird ohne Modellaufruf blockiert. Verwaiste Sperren bleiben aus
        Sicherheitsgründen bestehen, bis der Betreiber sie geprüft hat.
        """
        sperre = self.zaehler.with_name(self.zaehler.name + ".lock")
        try:
            self.zaehler.parent.mkdir(parents=True, exist_ok=True)
            sperre.mkdir(mode=0o700)
        except FileExistsError as exc:
            raise KINichtVerfuegbar(
                "KI-Aufrufzähler gesperrt; paralleler oder verwaister Lauf."
            ) from exc
        except OSError as exc:
            raise KINichtVerfuegbar("KI-Aufrufzähler kann nicht gesperrt werden.") from exc

        try:
            try:
                if self.zaehler.is_symlink():
                    raise ValueError("Aufrufzähler darf kein Symlink sein")
                if self.zaehler.exists():
                    if self.zaehler.stat().st_size > 32:
                        raise ValueError("Aufrufzähler zu groß")
                    bisher = int(self.zaehler.read_text(encoding="utf-8"))
                else:
                    bisher = 0
                if type(MAX_AUFRUFE) is not int or not 1 <= MAX_AUFRUFE <= 6:
                    raise ValueError("Ungültiges Aufrufbudget")
                if bisher < 0 or bisher > MAX_AUFRUFE:
                    raise ValueError("Ungültiger Aufrufzähler")
            except (OSError, ValueError, UnicodeError) as exc:
                raise KINichtVerfuegbar(
                    "Ungültiger KI-Aufrufzähler oder Aufrufbudget."
                ) from exc
            if bisher >= MAX_AUFRUFE:
                raise KINichtVerfuegbar(
                    f"Maximal {MAX_AUFRUFE} lokale KI-Aufrufe pro Stundenlauf."
                )
            nummer = bisher + 1
            try:
                self.zaehler.write_text(str(nummer), encoding="utf-8")
            except OSError as exc:
                raise KINichtVerfuegbar(
                    "KI-Aufrufzähler konnte nicht gesichert werden."
                ) from exc
            return nummer
        finally:
            try:
                sperre.rmdir()
            except OSError as exc:
                # Ein nicht entfernbarer Lock bleibt stehen und blockiert den
                # Folgelauf. Niemals trotzdem eine neue Modellanfrage senden.
                raise KINichtVerfuegbar(
                    "Sperre des KI-Aufrufzählers konnte nicht aufgehoben werden."
                ) from exc

    def frage(self, system, nutzer):
        self._pruefe_modell()
        nummer = self._zaehle()
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
            inhalt = antwort["message"]["content"]
        except (KeyError, TypeError, AttributeError) as exc:
            raise KINichtVerfuegbar("Lokale KI ohne verwertbaren Antworttext.") from exc
        if not isinstance(inhalt, str):
            raise KINichtVerfuegbar("Lokale KI ohne gültigen Textinhalt.")
        if len(inhalt) > 12_000:
            raise KINichtVerfuegbar("Lokale KI-Antwort überschreitet das Größenlimit.")
        inhalt = inhalt.strip()
        if not inhalt:
            raise KINichtVerfuegbar("Leere lokale KI-Antwort.")
        return {
            "text": inhalt, "modell": self.modell,
            "antwort_id": "lokal-" + uuid.uuid4().hex,
            "nutzung": {"prompt_eval_count": antwort.get("prompt_eval_count"),
                       "eval_count": antwort.get("eval_count")},
            "aufruf_nr": nummer,
            "laufzeit": "Ollama lokal (keine bezahlte KI-API)",
            "erstellt_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        }
