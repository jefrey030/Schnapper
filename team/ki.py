"""Historischer GitHub-Models-Adapter (seit 30.07.2026 außer Betrieb).

GitHub hat GitHub Models mit Katalog und Inferenz-API vollständig eingestellt.
Dieser Adapter bleibt für alte Offline-Vertragstests erhalten, darf im echten
Agentenlauf aber niemals einen Netzwerkaufruf zum eingestellten Dienst auslösen.
Als bereits implementierte Alternative existiert team/local_ollama.py:
nur auf einem selbst betriebenen lokalen Host und nur bei explizitem
SCHNAPPER_KI_BACKEND=ollama. Keine Cloud- oder Bezahl-Fallbacks.
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
def _sicheres_aufruflimit(wert):
    """Fehlerhafte oder groessere Umgebungswerte aktiv sperren statt abstuerzen."""
    if wert not in ("1", "2", "3", "4", "5", "6"):
        return 0
    return int(wert)


MAX_AUFRUFE = _sicheres_aufruflimit(os.getenv("SCHNAPPER_MAX_AUFRUFE", "6"))
MAX_TOKENS = 700


class KINichtVerfuegbar(RuntimeError):
    """Keine echte KI-Antwort erhalten. Darf nie durch Regeltext ersetzt werden."""


def _pruefe_url(url):
    """Bearer-Token dürfen ausschließlich per HTTPS an den erwarteten Host."""
    try:
        adresse = urllib.parse.urlsplit(url)
        port = adresse.port
    except (TypeError, ValueError) as exc:
        raise KINichtVerfuegbar("Ungültige KI-API-URL.") from exc
    if (adresse.scheme != "https"
            or adresse.hostname != ERLAUBTER_HOST
            or port not in (None, 443)
            or adresse.username is not None
            or adresse.password is not None
            or adresse.fragment):
        raise KINichtVerfuegbar(
            f"KI-API nur über HTTPS bei {ERLAUBTER_HOST}:443 ohne URL-Zugangsdaten erlaubt."
        )


class _KeineWeiterleitung(urllib.request.HTTPRedirectHandler):
    """GitHub-Tokens niemals an Redirect-Ziele weiterreichen."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise KINichtVerfuegbar("KI-API-Redirect blockiert; Token wird nicht weitergegeben.")


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
    # urlopen() folgt standardmäßig Redirects und könnte dabei Authorization
    # weiterreichen. Der eigene Handler verweigert sämtliche Umleitungen.
    opener = urllib.request.build_opener(_KeineWeiterleitung())
    try:
        with opener.open(req, timeout=timeout) as resp:
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
        """Fail-closed: der eingestellte GitHub-Models-Dienst darf nicht aufgerufen werden."""
        raise KINichtVerfuegbar(
            "GitHub Models ist seit 30.07.2026 eingestellt. "
            "SCHNAPPER-KI nur auf eigenem lokalen Host mit explizit "
            "SCHNAPPER_KI_BACKEND=ollama und bereits installiertem Modell nutzbar."
        )

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
