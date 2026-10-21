"""SCHNAPPER: Zugang zu einer echten, kostenlosen KI-Laufzeit.

Einzige erlaubte Laufzeit: GitHub Models (https://models.github.ai), aufgerufen
mit dem automatischen GITHUB_TOKEN eines GitHub-Actions-Laufs
(Workflow-Berechtigung `models: read`). Für persönliche Konten ist das
ratenbegrenzt kostenlos; kostenpflichtig wird es nur, wenn der Kontoinhaber
bezahlte Nutzung ausdrücklich einschaltet. Ohne diese Freigabe wird nach
Erreichen des Freikontingents blockiert statt abgerechnet.

Kostenbremsen in diesem Modul:
- Nur der Host models.github.ai ist erlaubt (fest verdrahtet, keine Umgehung).
- Höchstens MAX_AUFRUFE Inferenz-Aufrufe pro Stundenlauf (gezählt in einer Datei).
- Kurze Antworten (max_tokens begrenzt).
- Bevorzugt Open-Weight-Modelle der niedrigen Ratenstufe (150 Anfragen/Tag frei).
"""
import json
import os
import pathlib
import urllib.error
import urllib.parse
import urllib.request

ERLAUBTER_HOST = "models.github.ai"
INFERENZ_URL = "https://models.github.ai/inference/chat/completions"
KATALOG_URL = "https://models.github.ai/catalog/models"
# Open-Weight-Modelle in Wunschreihenfolge; verwendet wird das erste, das im
# Katalog vorhanden ist.
OPEN_WEIGHT_BEVORZUGT = (
    "meta/Llama-4-Scout-17B-16E-Instruct",
    "meta/Llama-3.3-70B-Instruct",
    "mistral-ai/Mistral-Small-3.1",
    "microsoft/Phi-4",
    "meta/Meta-Llama-3.1-8B-Instruct",
    "mistral-ai/Ministral-3B",
)
OPEN_WEIGHT_ANBIETER = ("meta", "mistral-ai", "microsoft", "deepseek", "ai21-labs", "cohere")
MAX_AUFRUFE = int(os.getenv("SCHNAPPER_MAX_AUFRUFE", "6"))
MAX_TOKENS = 700


class KINichtVerfuegbar(RuntimeError):
    """Keine echte KI-Antwort erhalten. Darf nie durch Regeltext ersetzt werden."""


def _pruefe_url(url):
    host = urllib.parse.urlparse(url).hostname
    if host != ERLAUBTER_HOST:
        raise KINichtVerfuegbar(f"Host {host!r} ist nicht erlaubt (nur {ERLAUBTER_HOST}).")


def _token():
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if not token:
        raise KINichtVerfuegbar("Kein GITHUB_TOKEN vorhanden – KI läuft nur in GitHub Actions mit 'models: read'.")
    return token


def _http(url, token, body=None, timeout=60):
    _pruefe_url(url)
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST" if data else "GET", headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:300]
        if exc.code == 429:
            raise KINichtVerfuegbar("Freikontingent von GitHub Models erreicht (HTTP 429). Keine Kosten, Lauf blockiert.") from exc
        raise KINichtVerfuegbar(f"GitHub Models HTTP {exc.code}: {detail}") from exc
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        raise KINichtVerfuegbar(f"GitHub Models nicht erreichbar: {exc}") from exc


def waehle_modell(katalog, wunsch=None):
    """Wählt ein Modell aus dem Katalog: Wunsch > bevorzugte Open-Weight > Open-Weight niedrige Stufe."""
    ids = {m.get("id"): m for m in katalog if isinstance(m, dict) and m.get("id")}
    if wunsch:
        if wunsch in ids:
            return wunsch
        raise KINichtVerfuegbar(f"Gewünschtes Modell {wunsch!r} ist nicht im GitHub-Models-Katalog.")
    for mid in OPEN_WEIGHT_BEVORZUGT:
        if mid in ids:
            return mid
    for mid, m in sorted(ids.items()):
        if mid.split("/")[0] in OPEN_WEIGHT_ANBIETER and str(m.get("rate_limit_tier", "")).lower() == "low":
            return mid
    raise KINichtVerfuegbar("Kein Open-Weight-Modell im GitHub-Models-Katalog gefunden.")


class KI:
    def __init__(self, zaehler_datei, modell=None, inferenz_url=INFERENZ_URL, katalog_url=KATALOG_URL):
        self.zaehler = pathlib.Path(zaehler_datei)
        self.inferenz_url = inferenz_url
        self.katalog_url = katalog_url
        self._wunsch = modell or os.getenv("SCHNAPPER_MODELL", "").strip() or None
        self._modell = None

    def modell(self):
        """Modell aus dem echten Katalog bestimmen (auch ein Wunschmodell muss dort existieren)."""
        if not self._modell:
            katalog = _http(self.katalog_url, _token())
            self._modell = waehle_modell(katalog if isinstance(katalog, list) else [], self._wunsch)
        return self._modell

    def _zaehle(self):
        bisher = int(self.zaehler.read_text() or 0) if self.zaehler.exists() else 0
        if bisher >= MAX_AUFRUFE:
            raise KINichtVerfuegbar(f"Kostenbremse: höchstens {MAX_AUFRUFE} KI-Aufrufe pro Stundenlauf.")
        self.zaehler.parent.mkdir(parents=True, exist_ok=True)
        self.zaehler.write_text(str(bisher + 1))
        return bisher + 1

    def frage(self, system, nutzer):
        token = _token()
        modell = self.modell()
        nummer = self._zaehle()
        antwort = _http(self.inferenz_url, token, {
            "model": modell,
            "max_tokens": MAX_TOKENS,
            "temperature": 0.2,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": nutzer[:12000]}],
        }, timeout=90)
        try:
            text = antwort["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError, AttributeError) as exc:
            raise KINichtVerfuegbar("Antwort von GitHub Models ohne Inhalt.") from exc
        if not text:
            raise KINichtVerfuegbar("Leere KI-Antwort.")
        return {
            "text": text,
            "modell": antwort.get("model") or modell,
            "antwort_id": antwort.get("id"),
            "nutzung": antwort.get("usage"),
            "aufruf_nr": nummer,
            "laufzeit": "GitHub Models (kostenloses Kontingent)",
        }
