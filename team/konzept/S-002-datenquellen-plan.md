# S-002 – Sicherer Plan: Datenquellen, Nutzungsrechte, Mindestfunktionen, Testfälle

Stand: 21.10.2026, 21:36 UTC · Autor: SCHNAPPER MASTER · Status: zur Prüfung (review)

> Keine Rechtsberatung. Die Angaben unten geben die verlinkten Originalseiten zum Stand der Prüfung
> (21.10.2026) wieder. Vor jeder echten Anbindung entscheidet Jefrey; bei Unklarheit gilt: **nicht anbinden**.

## Datenquellen und Nutzungsrechte

| Quelle | Zugang | Bedingung laut Originalquelle | Kosten | Entscheidung |
| --- | --- | --- | --- | --- |
| Q1 eBay Browse API | offizielle REST-API | Sandbox frei; „use of the APIs in production is restricted“ – Produktivnutzung erfordert Genehmigungen und Verträge mit eBay; Buy APIs brauchen eine zusätzliche Lizenz; Standardlimit 5.000 Aufrufe/Tag. Belege: [Browse-Überblick](https://developer.ebay.com/api-docs/buy/browse/overview.html), [Aufruflimits](https://developer.ebay.com/develop/api/buy/api_call_limits) | 0 € (Entwicklerkonto) | **später möglich** – erst nach Freigabe durch eBay und Jefrey; bis dahin nur Mock |
| Q2 Kleinanzeigen | **keine** öffentliche Drittanbieter-API | § 5 Nr. 1 der Nutzungsbedingungen: kein Einsatz von „Crawler, Spider, Scraper“ und kein Vervielfältigen von Inhalten ohne ausdrückliche schriftliche Zustimmung. Beleg: [Nutzungsbedingungen](https://themen.kleinanzeigen.de/nutzungsbedingungen/) | – | **ausgeschlossen** (kein Scraping) |
| Q3 Eigene/manuelle Daten (CSV/JSON) | Import aus Datei | Daten, die der Nutzer selbst erfasst oder rechtmäßig besitzt | 0 € | **erlaubt** – MVP-Quelle (Import liegt in PR #5 vor) |
| Q4 Testdaten (Mock) | im Repo, klar als erfunden markiert | keine Rechte Dritter berührt | 0 € | **erlaubt** – für alle Tests |

Nicht weiter geprüft und daher **nicht freigegeben**: Preisvergleichsportale, Affiliate-Feeds anderer Netzwerke.
Diese brauchen jeweils eine eigene Prüfung wie oben, bevor sie im Code auftauchen.

## Sicherheitsregeln für jede Quelle
1. Jeder Adapter trägt eine feste Kennung und `nutzungsrecht_geklaert` (siehe S-000-Schema); `false` ⇒ Treffer werden nicht angezeigt.
2. Kein Netzwerkzugriff in Tests; echte Adapter nur mit ausdrücklichem Schalter und Zugangsdaten aus der Umgebung (nie im Repo).
3. Kein Adapter für eine Quelle mit Entscheidung „ausgeschlossen“.
4. Abrufzeitpunkt wird gespeichert; Preise älter als 24 h werden als veraltet markiert (F1).

## Mindestfunktionen
Die Kernfunktionen Prüfen, Dubletten, Suche und Import sind in **PR #5** (`app/schnapper`, noch nicht gemergt) umgesetzt
und werden hier nicht doppelt gebaut. Für diesen Plan fehlen nur noch:
- **MF1 Quellen-Register:** Liste erlaubter Quellen (Q3, Q4) mit Entscheidung; unbekannte Quelle ⇒ Fehler.
- **MF2 Adapter-Schnittstelle:** `suche(anfrage) -> Liste von Angeboten` mit Mock-Adapter (Q4); eBay-Adapter (Q1) erst nach Freigabe.

## Testfälle
| # | Fall | Erwartung |
| --- | --- | --- |
| T1 | Angebot aus Quelle `kleinanzeigen` | wird abgewiesen, Hinweis „Quelle ausgeschlossen“ |
| T2 | Angebot aus unbekannter Quelle | wird abgewiesen, Hinweis „Quelle nicht freigegeben“ |
| T3 | Mock-Adapter liefert Angebote | Treffer erscheinen, Quelle = `mock` |
| T4 | eBay-Adapter ohne Freigabeschalter/Zugangsdaten | wird nicht aktiviert, kein Netzwerkaufruf |
| T5 | Test-Suite läuft ohne Netz | alle Tests grün |

## Ergebnis
- **Fertig:** Quellen bewertet (1 später möglich, 1 ausgeschlossen, 2 erlaubt) mit Belegen; Regeln, Mindestfunktionen, Testfälle.
- **Offen:** Produktivfreigabe der eBay Buy API (Antrag bei eBay nötig, Entscheidung Jefrey).
- **Nächster Schritt:** nach Merge von PR #5 MF1 (Quellen-Register) mit T1–T2 in `app/schnapper` umsetzen.
