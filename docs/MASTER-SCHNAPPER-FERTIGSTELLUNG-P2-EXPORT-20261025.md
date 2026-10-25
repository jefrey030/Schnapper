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

## Ergebnisprotokoll
Nach den Commits anhand der tatsächlich erfolgreichen GitHub-Tests ergänzen. Keine Freigabe aufgrund bloßer Testpläne.
