"""Datenmodell und Prüfregeln für ein einzelnes Angebot.

Nur Standardbibliothek. Preise werden als Decimal in Cent-Genauigkeit geführt,
damit keine Rundungsfehler aus Fließkommazahlen entstehen.
"""
from __future__ import annotations

import datetime as dt
import re
import unicodedata
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

ZUSTAENDE = ("neu", "wie_neu", "gebraucht", "defekt", "unbekannt")
CENT = Decimal("0.01")
# Parameter, die nur Tracking sind und für die Dubletten-Erkennung entfallen.
TRACKING_PARAMETER = re.compile(r"^(utm_.*|ref|ref_.*|tag|campaign|fbclid|gclid|mc_.*|affiliate.*)$", re.I)


class AngebotFehler(ValueError):
    """Ein Angebot ist unvollständig oder unplausibel."""


def geld(wert) -> Decimal:
    """Wandelt 12, "12,50", "12.50 €" usw. in einen Decimal-Betrag um."""
    if isinstance(wert, Decimal):
        betrag = wert
    elif isinstance(wert, bool):
        raise AngebotFehler("Preis darf kein Wahrheitswert sein")
    elif isinstance(wert, (int, float)):
        betrag = Decimal(str(wert))
    elif isinstance(wert, str):
        text = wert.strip().replace("€", "").replace("EUR", "").replace(" ", "").replace(" ", "")
        if "," in text and "." in text:  # 1.299,99 -> 1299.99
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", ".")
        try:
            betrag = Decimal(text)
        except InvalidOperation as exc:
            raise AngebotFehler(f"Preis nicht lesbar: {wert!r}") from exc
    else:
        raise AngebotFehler(f"Preis nicht lesbar: {wert!r}")
    if not betrag.is_finite():
        raise AngebotFehler("Preis ist keine endliche Zahl")
    return betrag.quantize(CENT, rounding=ROUND_HALF_UP)


def zeitpunkt(wert) -> dt.datetime:
    """ISO-Zeitstempel einlesen; ohne Zeitzone wird UTC angenommen."""
    if isinstance(wert, dt.datetime):
        z = wert
    elif isinstance(wert, str) and wert.strip():
        try:
            z = dt.datetime.fromisoformat(wert.strip().replace("Z", "+00:00"))
        except ValueError as exc:
            raise AngebotFehler(f"Zeitpunkt nicht lesbar: {wert!r}") from exc
    else:
        raise AngebotFehler("Zeitpunkt fehlt")
    return z if z.tzinfo else z.replace(tzinfo=dt.timezone.utc)


def normalisiere_titel(titel: str) -> str:
    """Kleinbuchstaben, Umlaute als ae/oe/ue, Satzzeichen entfernt (Kopfhörer == Kopfhoerer)."""
    t = titel.lower().replace("ß", "ss")
    for umlaut, ersatz in (("ä", "ae"), ("ö", "oe"), ("ü", "ue")):
        t = t.replace(umlaut, ersatz)
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return " ".join(t.split())


def normalisiere_url(url: str) -> str:
    """Entfernt Tracking-Parameter, Fragment, www. und abschließenden Schrägstrich."""
    teile = urlsplit(url.strip())
    host = (teile.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    query = urlencode(sorted((k, v) for k, v in parse_qsl(teile.query, keep_blank_values=True)
                             if not TRACKING_PARAMETER.match(k)))
    pfad = teile.path.rstrip("/") or "/"
    return urlunsplit(("https", host, pfad, query, ""))


@dataclass(frozen=True)
class Angebot:
    id: str
    titel: str
    preis: Decimal
    url: str
    quelle: str
    erfasst_am: dt.datetime
    waehrung: str = "EUR"
    versand: Decimal = Decimal("0.00")
    zustand: str = "unbekannt"
    referenzpreis: Decimal | None = None
    kategorie: str = ""
    extra: dict = field(default_factory=dict, compare=False, hash=False)

    @property
    def gesamtpreis(self) -> Decimal:
        return self.preis + self.versand

    @property
    def rabatt_prozent(self) -> Decimal | None:
        """Ersparnis gegenüber dem Referenzpreis in Prozent (Gesamtpreis inkl. Versand)."""
        if not self.referenzpreis or self.referenzpreis <= 0:
            return None
        return ((self.referenzpreis - self.gesamtpreis) / self.referenzpreis * 100).quantize(
            Decimal("0.1"), rounding=ROUND_HALF_UP)

    @classmethod
    def aus_dict(cls, daten: dict) -> "Angebot":
        """Baut ein geprüftes Angebot aus Rohdaten (z. B. einer Zeile aus JSON/CSV)."""
        if not isinstance(daten, dict):
            raise AngebotFehler("Angebot muss ein Objekt sein")

        def text(name, pflicht=True):
            wert = daten.get(name)
            wert = "" if wert is None else str(wert).strip()
            if pflicht and not wert:
                raise AngebotFehler(f"Feld '{name}' fehlt")
            return wert

        ref = daten.get("referenzpreis")
        angebot = cls(
            id=text("id"),
            titel=text("titel"),
            preis=geld(daten.get("preis")),
            url=text("url"),
            quelle=text("quelle"),
            erfasst_am=zeitpunkt(daten.get("erfasst_am")),
            waehrung=(text("waehrung", False) or "EUR").upper(),
            versand=geld(daten.get("versand") or 0),
            zustand=(text("zustand", False) or "unbekannt").lower(),
            referenzpreis=None if ref in (None, "") else geld(ref),
            kategorie=text("kategorie", False),
            extra={k: v for k, v in daten.items() if k not in cls.__dataclass_fields__},
        )
        pruefe(angebot)
        return angebot


def pruefe(angebot: Angebot) -> None:
    """Harte Regeln: Verstöße machen ein Angebot unbrauchbar."""
    if len(angebot.titel) > 300:
        raise AngebotFehler("Titel länger als 300 Zeichen")
    if angebot.preis <= 0:
        raise AngebotFehler("Preis muss größer als 0 sein")
    if angebot.preis > Decimal("1000000"):
        raise AngebotFehler("Preis unplausibel hoch")
    if angebot.versand < 0:
        raise AngebotFehler("Versandkosten dürfen nicht negativ sein")
    if angebot.referenzpreis is not None and angebot.referenzpreis <= 0:
        raise AngebotFehler("Referenzpreis muss größer als 0 sein")
    if angebot.waehrung != "EUR":
        raise AngebotFehler(f"Nur EUR unterstützt, nicht {angebot.waehrung}")
    if angebot.zustand not in ZUSTAENDE:
        raise AngebotFehler(f"Unbekannter Zustand: {angebot.zustand}")
    teile = urlsplit(angebot.url)
    if teile.scheme != "https" or not teile.hostname:
        raise AngebotFehler("URL muss mit https:// beginnen")
    if angebot.erfasst_am > dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=5):
        raise AngebotFehler("Erfassungszeit liegt in der Zukunft")


def warnungen(angebot: Angebot, jetzt: dt.datetime | None = None, max_alter_stunden: int = 24) -> list[str]:
    """Weiche Regeln: Angebot bleibt nutzbar, wird aber gekennzeichnet."""
    jetzt = jetzt or dt.datetime.now(dt.timezone.utc)
    hinweise = []
    alter = jetzt - angebot.erfasst_am
    if alter > dt.timedelta(hours=max_alter_stunden):
        hinweise.append(f"veraltet: Preis zuletzt vor {int(alter.total_seconds() // 3600)} Std. geprüft")
    rabatt = angebot.rabatt_prozent
    if rabatt is not None and rabatt >= 80 and angebot.zustand in ("neu", "wie_neu"):
        hinweise.append(f"betrugsverdacht: {rabatt} % unter Referenzpreis bei Zustand '{angebot.zustand}'")
    if rabatt is not None and rabatt < 0:
        hinweise.append("teurer als Referenzpreis")
    if angebot.referenzpreis is None:
        hinweise.append("kein Referenzpreis: Ersparnis nicht belegbar")
    return hinweise
