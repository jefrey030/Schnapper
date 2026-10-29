# BRAIN – Lauf 20261029-0829

- Start: Thu Oct 29 08:33:22 UTC 2026
- Ende: Thu Oct 29 08:36:02 UTC 2026
- Branch: `agent/master/20261022-21` (Ausgangskopf a87a977), lokaler Commit **778e998** („SCHNAPPER MASTER: F2 Doppeltes Absenden beim Erfassen verhindern (S-009)“), kein Push.
- Aufgabe: F2 = S-009, Draft-PR #39 bleibt Draft.

## Geänderte Dateien
- `app/schnapper/web/app.js` (+10): nur `angebotSpeichern` und das Flag direkt davor
- `tests/test_app_erfassen_s009.py` (+110): neue Klasse `DoppeltAbsenden` (5 Browsertests)

## Fix
- `let angebotLaeuft = false;` steht direkt vor `angebotSpeichern`. Nach `ev.preventDefault()` gilt `if (angebotLaeuft) return;`, also kein fetch und keine Statusänderung.
- Vor dem fetch werden `angebotLaeuft = true` und `#angebot-knopf.disabled = true` gesetzt.
- Ein neues `finally` setzt Flag und Knopf in allen Ausgängen zurück: Erfolg, Fehlerantwort (frühes return) und catch.
- Sonst ist nichts geändert: dieselben Meldungen, Header `X-Schnapper: 1`, kein innerHTML, Server unverändert.

## Tests (Klasse DoppeltAbsenden)
Jeder Test startet Chromium aus `/opt/pw-browsers` über `_finde_chromium` und blockiert alle Anfragen außer an 127.0.0.1. Zusätzlich werden POSTs an `/api/angebot` gezählt.
- AK1 `test_ak1_doppelklick_ein_angebot`: `dblclick()` ergibt 1 POST und 1 CSV-Datenzeile, Status „Gespeichert. Deine Liste hat jetzt 1 Angebot.“, keine Konsolenmeldungen.
- AK2 `test_ak2_zweimal_request_submit_ein_angebot`: 2× `requestSubmit()` ergibt 1 POST und 1 Datenzeile.
- AK3 `test_ak3_knopf_gesperrt_waehrend_anfrage`: Die Antwort wird über `seite.route` zurückgehalten (Route liegt in einer Liste, kein sleep). Der Knopf ist dabei disabled. Nach `continue_()` ist er wieder enabled, CSV hat 1 Zeile.
- AK4 `test_ak4_nach_fehlerantwort_wieder_aktiv`: Ein `http://`-Link löst 422 und eine Fehlermeldung aus, danach ist der Knopf aktiv. Korrigiert auf https wird gespeichert, CSV hat 1 Zeile.
- AK5 `test_ak5_server_nicht_erreichbar_wieder_aktiv`: `route.abort()` führt zu „Server nicht erreichbar …“, der Knopf ist wieder aktiv.
- AK6 und Abweichung zu Konsolenfehlern: AK1 bis AK3 prüfen eine leere Meldungsliste. In AK4 und AK5 meldet Chromium die gewollten Netzfehler selbst als Konsolenfehler. Es kommt jeweils genau eine Meldung, nachweislich „Failed to load resource: … status of 422“ bzw. „net::ERR_FAILED“. Nur diese eine Meldung wird herausgefiltert, und es gibt kein `pageerror`. **CHECK bitte bewerten.**

## Ergebnisse
- `python3 -m unittest tests.test_app_erfassen_s009`: **32/32 OK**, 0 Skips (vorher 27, dazu 5 neue)
- `python3 -m unittest discover -s tests`: **248 Tests OK**, 0 Skips
- `cd cloudflare && node --test test/*.test.mjs`: **10/10 pass**, 0 fail, 0 skipped
- **Gegenprobe (AK7)**: Mit dem alten app.js aus a87a977 meldet die Suite **FAILED (failures=3)** bei 32 Tests:
  - AK1: `2 != 1` (POSTs)
  - AK2: `2 != 1`
  - AK3: `False is not true` (Knopf nicht disabled)
  - AK4 und AK5 bestehen auch mit dem alten Code, was zu erwarten war.
  - Danach wurde die Fix-Kopie zurückgespielt. sha256 vorher und nachher ist gleich: `9214c178d579d3dc5e14bde5288e210854d4bb81be4a856274aa6721dea2d5fd`
- Kein `playwright install`, kein Netzzugriff nach außen, keine neuen Abhängigkeiten. web.py, index.html, app.css und workflows sind unberührt.
