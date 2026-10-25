# SCHNAPPER – Fertigstellungs-Master: eigene Angebote am Handy erfassen

**Datum:** 25.10.2026 · **Repo:** `jefrey030/Schnapper` · **Arbeitszweig:** `integration/schnapper-p0-mainbased-20261025` · [Draft PR #55](https://github.com/jefrey030/Schnapper/pull/55) · **Zusatzbudget:** 0 €

## Ziel
Eine vorhandene Bedienlücke des offline nutzbaren SCHNAPPER beheben: Wer am Handy ein Angebot selbst gefunden hat, soll Titel, Preis, Versand, Referenzpreis, URL, Zustand und Kategorie direkt in ein Formular eintragen können, ohne eine CSV-/JSON-Datei händisch zu bearbeiten.

## Arbeitspakete

| ID | Prüffähiger Auftrag | Erwartung |
| --- | --- | --- |
| E1 | Vorhandene Suche, Export und Upload prüfen | Nicht duplizieren oder beschädigen |
| E2 | Manuelles Formular (responsive) | Benannte Felder, mobile Eingabe, Pflicht- und optionale Angaben |
| E3 | Geschützte API | `POST /api/eigenes-angebot`, JSON, begrenzte Größe, bestehende Headerpflicht |
| E4 | Vertrauen und Validierung | Quelle serverseitig fest `eigene`, servergenerierte ID und Erfassungszeit, vorhandene `Angebot.aus_dict`-Prüfungen |
| E5 | Dubletten/Limit | Trackingbereinigte URL-Vergleiche, bereits bekannte Adressen ablehnen, höchstens 5000 geladene Angebote |
| E6 | Atomare Übernahme | Bei Verlaufsspeicherfehler bleibt die sichtbare Liste unberührt |
| E7 | UI-Rückmeldung | Fehler sichtbar ohne Traceback; neue Treffer und Preisalarme neu prüfen |
| E8 | Sicherheitstests | HTTP 403, 400/413, Eingabegrenzen, URL- und Quellenschutz, Dubletten, Verlauf-Rollback |
| E9 | Vollständige Tests & Nachweise | Python-/Cloudflare-CI auf finaler Branch-SHA; dokumentierter Testumfang |
| E10 | Release-Grenzen | Kein Autopilot, kein bezahlter Dienst, kein echter Android-Endtest, kein Merge/Deploy |

## Wichtige Daten- und Sicherheitsgrenzen

- **Bewusste Einschränkung:** Neue Angebote befinden sich im lokalen **Arbeitsspeicher** und gehen beim Neustart verloren. Der CSV-Export sichert eine Kopie der aktuell gefilterten Liste; das ist **kein** serverseitiges Speichersystem.
- Das manuelle Formular ist **keine** öffentliche Möglichkeit, fremde Marktplätze abzurufen. Es ruft keine Nutzer-URL ab.
- Die Backend-Quelle ist unabhängig von einer manipulierten Browser-Anfrage immer `eigene`. Die Quellensperren für eBay/Kleinanzeigen bleiben unverändert.
- Keine externen Kosten, KI-API, veröffentlichte Webadresse, Änderung von `main` oder cronbezogene Freigabe.
- Das bestehende localhost-Standardbinding bleibt. Bei explizitem `0.0.0.0` ist der lokale Server weiterhin **ohne Anmeldung** im selben Netzwerk erreichbar; vor öffentlicher Bereitstellung fehlt Authentifizierung und eine Security-Review.

## Status

Dieser Master erfordert tatsächliche Codeänderungen und einen erfolgreichen CI-Lauf auf der abschließenden SHA. Die Nachweise werden anschließend ergänzt. **Produktivfreigabe: NO-GO.**
