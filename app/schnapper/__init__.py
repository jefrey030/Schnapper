"""SCHNAPPER-Kern: Angebote prüfen, Dubletten entfernen, Schnäppchen finden."""
from .angebot import Angebot, AngebotFehler, warnungen
from .dubletten import entferne_dubletten
from .einlesen import lies_datei, lies_text
from .suche import Filter, suche

__all__ = ["Angebot", "AngebotFehler", "warnungen", "entferne_dubletten",
           "lies_datei", "lies_text", "Filter", "suche"]
