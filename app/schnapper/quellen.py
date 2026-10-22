"""Quellen-Register (Plan S-002, MF1).

Jedes Angebot nennt seine Quelle. Angezeigt wird es nur, wenn diese Quelle hier
mit geklärten Nutzungsrechten freigegeben ist. Unbekannte Quellen werden
abgewiesen. Ausgeschlossene Quellen (z. B. Kleinanzeigen, deren
Nutzungsbedingungen Scraping verbieten) lassen sich auch über eine
Konfigurationsdatei nicht freischalten.
"""
from __future__ import annotations

import json
import pathlib
import re
from dataclasses import dataclass

ERLAUBT, SPAETER, AUSGESCHLOSSEN = "erlaubt", "spaeter", "ausgeschlossen"
KENNUNG = re.compile(r"^[a-z0-9][a-z0-9_-]{0,39}$")


class QuellenFehler(ValueError):
    pass


@dataclass(frozen=True)
class Quelle:
    kennung: str
    name: str
    entscheidung: str
    hinweis: str = ""

    @property
    def freigegeben(self) -> bool:
        return self.entscheidung == ERLAUBT


# Bewertung aus team/konzept/S-002-datenquellen-plan.md (Stand 21.10.2026).
STANDARD = (
    Quelle("mock", "Testdaten (erfunden)", ERLAUBT, "Nur für Tests und Vorführung, keine echten Preise"),
    Quelle("eigene", "Eigene Daten (CSV/JSON)", ERLAUBT, "Selbst erfasste oder rechtmäßig besessene Daten"),
    Quelle("openprices", "Open Prices (Open Food Facts)", SPAETER,
           "Echte Ladenpreise, Lizenz ODbL: Quelle nennen; keine eigene abgeleitete Preisdatenbank bilden ohne Lizenzprüfung; Freigabe erst mit SCHNAPPER_OPENPRICES_FREIGABE=ja (Entscheidung von Jefrey)"),
    Quelle("ebay", "eBay Browse API", SPAETER, "Produktivnutzung erst nach Genehmigung durch eBay und Freigabe durch Jefrey"),
    Quelle("kleinanzeigen", "Kleinanzeigen", AUSGESCHLOSSEN, "Nutzungsbedingungen verbieten Scraper/Crawler ohne schriftliche Zustimmung"),
)


class Register:
    def __init__(self, quellen=STANDARD):
        self._quellen: dict[str, Quelle] = {}
        for q in quellen:
            self._quellen[q.kennung] = q

    def __iter__(self):
        return iter(self._quellen.values())

    def get(self, kennung: str) -> Quelle | None:
        return self._quellen.get(kennung.strip().lower())

    def erlaube(self, kennung: str, name: str, hinweis: str = "") -> Quelle:
        """Zusätzliche Quelle freigeben, z. B. einen geprüften Partner-Feed."""
        kennung = kennung.strip().lower()
        if not KENNUNG.match(kennung):
            raise QuellenFehler(f"Ungültige Quellen-Kennung: {kennung!r}")
        vorhanden = self._quellen.get(kennung)
        if vorhanden and vorhanden.entscheidung != ERLAUBT:
            raise QuellenFehler(f"Quelle '{kennung}' ist '{vorhanden.entscheidung}' und kann nicht per Datei freigegeben werden")
        q = Quelle(kennung, name.strip() or kennung, ERLAUBT, hinweis.strip())
        self._quellen[kennung] = q
        return q

    def pruefe(self, kennung: str) -> str | None:
        """None, wenn freigegeben; sonst der Grund der Ablehnung."""
        q = self.get(kennung)
        if q is None:
            return f"Quelle '{kennung}' nicht freigegeben (nicht im Quellen-Register)"
        if q.entscheidung == AUSGESCHLOSSEN:
            return f"Quelle '{q.kennung}' ausgeschlossen: {q.hinweis}"
        if q.entscheidung != ERLAUBT:
            return f"Quelle '{q.kennung}' noch gesperrt: {q.hinweis}"
        return None

    @classmethod
    def mit_datei(cls, pfad) -> "Register":
        """Standard-Register plus Freigaben aus einer quellen.json:
        {"quellen": [{"kennung": "...", "name": "...", "hinweis": "Nutzungsrecht: ..."}]}"""
        reg = cls()
        daten = json.loads(pathlib.Path(pfad).read_text(encoding="utf-8"))
        eintraege = daten.get("quellen") if isinstance(daten, dict) else None
        if not isinstance(eintraege, list):
            raise QuellenFehler("quellen.json braucht eine Liste unter 'quellen'")
        for e in eintraege:
            if not isinstance(e, dict) or not str(e.get("hinweis", "")).strip():
                raise QuellenFehler("Jede Freigabe braucht 'kennung', 'name' und einen 'hinweis' zum Nutzungsrecht")
            reg.erlaube(str(e.get("kennung", "")), str(e.get("name", "")), str(e["hinweis"]))
        return reg
