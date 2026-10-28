# BRAIN – Lauf 20261028-2328

## Branch
- `agent/master/20261022-2238`, Basis `ca5420e` (origin). origin/main `6dbe114` ist Vorfahr (`merge-base --is-ancestor` → ja). Kein Rebase nötig.
- Neuer Commit: **`6165af4f3647be01af424a7c8d514ed8b085ad4a`** (Fast-Forward auf ca5420e). **Nicht gepusht.**

## Geänderte Dateien
- `app/schnapper/web/app.js` (+3 Zeilen, nur Kamera-Abschnitt):
  - `kameraScannen()`: `$("kamera-abbrechen").focus()` direkt nach `hidden = false`, vor `getUserMedia`.
  - `kameraStoppen()`: `const fokusZurueck = document.activeElement === $("kamera-abbrechen")` vor dem Ausblenden; nach `disabled = false` → `if (fokusZurueck) $("kamera-knopf").focus()`.
- `tests/test_app_kamera_s011.py` (+51 Zeilen): Hilfen `starte_tastatur()` (focus + Enter, kein Klick) und `fokus()`; neue Tests `test_tastatur_fokus_start_und_abbrechen`, `test_fokus_waehrend_kamera_anfrage`, `test_fokus_zurueck_nach_zeitlimit`, `test_fokus_bleibt_im_feld`.

## Testergebnisse
- `python3 -m unittest tests.test_app_kamera_s011 -v` → **Ran 25, OK, 0 Skips** (Chromium vorinstalliert gefunden).
- `python3 -m unittest discover -s tests` → **Ran 241, OK**.
- `cd cloudflare && node --test test/*.test.mjs` → **10 tests, 10 pass, 0 fail**.

## Gegenprobe (AK 9)
- `app.js` aus `ca5420e` + neue Tests → **FAILED (failures=3)**: `test_tastatur_fokus_start_und_abbrechen`, `test_fokus_waehrend_kamera_anfrage`, `test_fokus_zurueck_nach_zeitlimit`. `test_fokus_bleibt_im_feld` grün (erwartet). Danach `app.js` wiederhergestellt, Arbeitsbaum sauber.

## Prüfungen AK 11
- Kein neues `innerHTML`/`console.`, keine neue Abhängigkeit; `index.html`, CSP, `app.css`, Workflows unverändert.

## Abweichungen von lead.md
- Keine inhaltlichen. Kleine Ergänzungen in Tests: `test_fokus_waehrend_kamera_anfrage` bricht am Ende per Enter ab und prüft Fokus-Rückgabe auf `kamera-knopf`; `test_fokus_zurueck_nach_zeitlimit` wartet vor `run_for(21000)` zusätzlich auf laufende Erkennung (wie bestehender `test_ak5_zeitlimit`).
