# SCHNAPPER – großer Fertigstellungs-Master P2: Export und Offline-Funktionsabnahme

**Datum:** 25.10.2026 · **Zielbranch:** `integration/schnapper-p0-mainbased-20261025` · **PR:** [Review-Entwurf #55](https://github.com/jefrey030/Schnapper/pull/55) · **Zusatzkosten: 0 €** · **Release: NO-GO**

## Verifizierter Ausgangsstand
Der vorherige [Fertigstellungs-Master](MASTER-SCHNAPPER-FERTIGSTELLUNG-20261025.md) hat F1–F4 erledigt: kontrollierte CLI-Suchfilter, atomare Preisverlaufs-Übernahme, lokaler End-to-End-Test, grüne Offline-CI. Noch offen sind unabhängige Sicherheitsabnahme, echte Datenquelle mit Nutzungsrecht und Freigabe, Android-Gerätetest, produktives Hosting und tatsächlich aktive vier Modellagenten. **Nicht als erledigt ausgeben.**

Die lokale Browser-App besitzt Suche und Hochladen eigener CSV/JSON-Dateien, aber in `app/schnapper/web.py` existiert noch kein Download-Endpunkt für aktuelle Suchtreffer. Eine Ergebnisliste muss daher bisher außerhalb der App manuell übertragen werden.

## Große Arbeitsblöcke

| ID | Funktion | Akzeptanzbedingung |
| --- | --- | --- |
| E1 | Gefilterte Treffer als CSV herunterladen | Derselbe Suchfilter/Sortierung wie `/api/suche`; UTF-8, korrekte CSV-Struktur, sinnvolle feste Felder, BOM für Tabellenprogramme |
| E2 | Gefilterte Treffer als JSON herunterladen | Identischer Trefferbestand; keine fremden Zusatzfelder oder Live-Daten |
| E3 | Sicherheit für Excel-/CSV-Formeln | Untrusted Text, beginnend mit `=`, `+`, `-`, `@` (auch bei Steuerzeichen/Leerraum), wird als Text exportiert; keine Formel |
| E4 | Web-UI | Eindeutige Download-Links für CSV/JSON passen zum aktuellen Suchfilter, auf Android bedienbar |
| E5 | Negative Offline-HTTP-Tests | Invalides Filter-/Sortierfeld 400; Download nur auf eigenen lokalen Server, keine fremde API |
| E6 | Reproduzierbare Offline-CI | Python- und Cloudflare-Tests erfolgreich auf exaktem Final-HEAD, Anzahl/Skip dokumentiert |
| E7 | Release-Abgrenzung | Keine Änderung an `main`, kein Merge, kein Deploy, kein Abonnement; Live-Datenquellen und echte Endgerätetests weiterhin gesperrt |

## Rollenverteilung als Arbeitsprozess
**LEAD:** Master, Scope, Sicherheits-/Kostenrestriktionen. **BRAIN:** HTML/JS und Python-Export implementieren. **CHECK:** HTTP-/CSV-Injection-/Filter-Regressionen, aktuelle Actions. **COMMAND:** finalen SHA/Testlauf dokumentieren, Restblocker nennen. Diese Rollen sind *keine* Behauptung autonom laufender KI-Prozesse.

## Technische Entscheidung
Der Server exportiert ausschließlich die bereits geladenen und durch das Quellenregister geprüften Angebote. `/api/export.csv` und `/api/export.json` verwenden dieselbe `filter_aus_query` und `finde_in`-Logik wie `/api/suche`. Bei 0 Treffern ist die CSV-Headerzeile zulässig. Feste Download-Dateinamen verhindern Dateinamen-Injektion; `Cache-Control: no-store` bleibt bestehen.

## Grenzen / NO-GO
- Ein CSV-Export ist kein Live-Preisvergleich; automatische eBay-/Kleinanzeigen-Abfragen ohne Freigabe bleiben verboten.
- Exportdateien werden auf das anfragende Gerät heruntergeladen; sie werden nicht in Cloud-Datenbanken gesichert.
- Die neue Funktion ersetzt keine externe Sicherheitsreview, echte Android-Hardwareabnahme, Lizenzprüfung oder autonom laufendes Vier-KI-Team.
- **0 € zusätzliche Kosten.** Alle Testpreise und Fremdquellen sind ausschließlich synthetisch.

## Ergebnisprotokoll – tatsächlich ausgeführt und überprüft

**Erledigte Arbeitspakete:** E1 ✅, E2 ✅, E3 ✅, E4 ✅, E5 ✅, E6 ✅ für den unten belegten Code-Stand; E7 ✅ als eingehaltene Sperren. Dies sind **7 Abnahmekriterien dieses Export-Masters**, nicht sieben der noch offenen F5–F10 aus dem Gesamtprojekt.

### Reale Implementierung
- **`app/schnapper/web.py`:** `/api/export.csv` und `/api/export.json` teilen die Filter- und Sortierlogik mit `/api/suche`. Beide Dateitypen werden aus den geprüften, bereits geladenen Angeboten erzeugt; es gibt keine zusätzliche Datenquelle und keinen versteckten Schreibvorgang. Antwort-Header enthalten feste Downloaddateinamen und `Cache-Control: no-store`.
- **`exportiere_csv`:** UTF-8 BOM, Semikolonfelder und CRLF; feste Spalten für Kennung, Titel, Preis, Versand, Gesamtpreis, Rabatt, Zustand, Quelle, Kategorie, URL, Zeitpunkt und Warnungen. Tab-/Zeilenumbrüche in Freitextfeldern werden neutralisiert. Mögliche Tabellenformeln mit führendem `=`, `+`, `-` oder `@` werden durch ein vorangestelltes Apostroph als Text markiert.
- **`app/schnapper/web/index.html`, `app.js`, `app.css`:** Berührungsfreundliche CSV-/JSON-Downloadlinks in der Suchansicht, deren URLs bei Änderungen der Filter aktualisiert werden.
- **`tests/test_export_offline.py`:** Neun neue Unit-/HTTP-Regressionstests für CSV-Header, BOM, feste Dateinamen, Filter-/Sortiergleichheit mit der Such-API, JSON, leere Trefferlisten, ungültige Filter, HEAD, Browser-Links sowie Formel-/Zeileninjektion. Alle Tests verwenden nur lokale Endpunkte oder reine Python-Funktionen.

### Prüfnachweis
**Bestandener CI-Lauf für den implementierten Code:** [GitHub Actions #40224771258](https://github.com/jefrey030/Schnapper/actions/runs/40224771258), Code-SHA `2ef44595c55f5e2522f62008664a88bb2dd2b4d8`:
- `python-tests` **301 Tests** ausgeführt, **1 Skip**, **0 Fehler**;
- `cloudflare-tests` **16/16 Tests bestanden**, **0 Skip**, **0 Fehler**.

Zusätzlicher README-/Master-Dokumentationscommit erhält einen eigenen CI-Lauf. Nur der abgeschlossene GitHub-Status seiner genauen SHA gilt als finale Bestätigung.

### Unveränderte offene Punkte / harte Grenzen
Der neue Export vervollständigt die **Offline-Nutzung** für eigene Angebotsdateien. Er ersetzt **keine** echte automatische und genehmigte eBay-/Markt-Datenquelle, **keinen** Android-Gerätetest, **keine** separate unabhängige Sicherheitsabnahme und **keinen** tatsächlichen Vier-KI-Stundenbetrieb. Kein Merge auf `main`, kein Deployment, keine Bezahlfunktion, kein Scraping. Bis zur Betreiberfreigabe bleibt PR #55 Draft und **NO-GO für die Produktivfreigabe**.

