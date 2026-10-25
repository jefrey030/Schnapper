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

## Implementierung und Abnahme

- **E1–E2 umgesetzt:** Responsive, aufklappbares Eingabeformular in `app/schnapper/web/index.html`, Layout in `app.css`, JavaScript-Funktion `eigenesAngebotErfassen` in `app.js`. Neue Suche und gespeicherte Preisalarme werden nach erfolgreichem HTTP-201 aktualisiert.
- **E3 umgesetzt:** Nur `POST /api/eigenes-angebot` mit `X-Schnapper: 1`, JSON-Medientyp und maximal 4096 Byte Eingabe. Falscher Inhalt, fehlende Genehmigungskennung und überlange Daten werden abgewiesen.
- **E4 umgesetzt:** `Angebot.aus_dict` prüft Preis, URL, Zustand und Felder. Backend erzwingt `quelle=eigene`, vergibt eine zufällige eindeutige ID und setzt einen eigenen UTC-Erfassungszeitpunkt.
- **E5 umgesetzt:** `Zustand.manuell_hinzufuegen` verhindert doppelte (normalisierte, trackingbereinigte) URLs und beschränkt Listen auf 5000 Angebote.
- **E6 umgesetzt:** Unter der bestehenden Importsperre wird zunächst der Preisverlauf gesichert; erst bei Erfolg wird der aktive Angebotsbestand atomar ausgetauscht.
- **E7 umgesetzt:** Positive Rückmeldung, Fehlermeldung und Warnung „vor Serverneustart exportieren“ im Browser. Daten nur im RAM; keine Behauptung einer dauerhaften Speicherung.
- **E8 umgesetzt:** `tests/test_manuelle_einzel_erfassung.py` hat **12 neue echte localhost-HTTP-Testmethoden**: Erfolg/Export, manipulierte Quellen/IDs/Uhrzeit, Tracking-Dubletten, Wiederholung, Header/Content-Type/Größenlimit, falsche JSON-Typen, ungültige Angebote, simulierten Speicherfehler, Mengenlimit, zwei gleichzeitige identische Einträge, statische Browserassets und unzulässige Pfade.
- **E9:** Ganze Python-Testsuite plus Cloudflare-Tests werden mit GitHub Actions auf dem **finalen Branch-HEAD** bewertet. Die Abnahme gilt nur für die konkret geprüfte SHA.
- **E10 beibehalten:** Keine Live-Quelle, Bezahl-API, echter Android-Gerätetest, authentifizierte öffentliche App oder vier tatsächlich autonome KI-Modelle. Kein Merge, kein Deployment und kein Eingriff in `main`.

**Abgrenzung:** Mit dem Backend lassen sich eigene Angebote speichern, solange der lokale Server läuft. Für den echten Betrieb fehlen weiterhin verifizierte Live-Datenrechte, dauerhafte Speicherung/Backup, Authentifizierung vor öffentlicher Erreichbarkeit, reale Android-Bedienprüfung, unabhängige Sicherheitsreview und Betreiberfreigabe.

**Produktivfreigabe: NO-GO.** Es werden keine erfundenen Fertigstellungsprozente oder Live-Erfolge verwendet.

