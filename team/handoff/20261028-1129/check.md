# CHECK – Lauf 20261028-1129

## Urteil: **bestanden**

Geprüft wurde unabhängig auf dem lokalen Branch `agent/master/20261022-2238`, Kopf `a3b1f9d`. Der Branch ist 1 Commit vor `origin/agent/master/20261022-2238` (`16e914b`) und nicht gepusht. `origin/main` ist `6dbe114`, der Branch liegt 0 Commits dahinter und 5 Commits davor.

## 1. Branch und Diff
- `git log --oneline -3` ergibt `a3b1f9d` (dieser Lauf), dann `16e914b` und `a3fcfab`.
- Die Commit-Nachricht entspricht wörtlich der Vorgabe. Die Trailer `Co-Authored-By: Claude Opus 5.5 …` und `Claude-Session: https://claude.ai/code/session_01Km4oq1spj2vQd4c2gqP6Ai` sind vorhanden.
- `git diff origin/agent/master/20261022-2238..HEAD` zeigt nur zwei Dateien:
  - `app/schnapper/web/app.js` (+3 −1, nur in `kameraScannen()`)
  - `tests/test_app_kamera_s011.py` (+62 −1)
- `git diff --stat origin/main...HEAD` für den gesamten PR #41 ergibt `app.css` +5, `app.js` +94, `index.html` +6 und Testdatei +473. Zusammen sind das 4 Dateien und +578 Zeilen. `app.css` und `index.html` stammen aus früheren Läufen.

## 2. Tests (selbst ausgeführt)
| Befehl | Ergebnis |
|---|---|
| `python3 -m unittest -v tests.test_app_kamera_s011` | **Ran 17, OK** (15 alte + 2 neue, 0 Skips, Chromium vorinstalliert) |
| `python3 -m unittest discover -s tests` | **Ran 233, OK**, 0 Skips |
| `cd cloudflare && node --test test/*.test.mjs` | **10 pass / 0 fail** |

Es wurde kein `playwright install` ausgeführt.

## 3. Gegenprobe (AK5)
- Vorgehen: `git show origin/agent/master/20261022-2238:app/schnapper/web/app.js > app/schnapper/web/app.js`, danach `python3 -m unittest -v tests.test_app_kamera_s011`.
- Ergebnis: **Ran 17, FAILED (failures=2)**. Rot sind genau die beiden neuen Tests:
  - `test_abbrechen_waehrend_formatabfrage` scheitert in Z. 423: `#kamera-bereich.hidden` ist `false`. Damit ist Fall A nachgestellt.
  - `test_neustart_waehrend_formatabfrage` scheitert in Z. 444: `srcObject` ist nicht der Stream von Lauf 2. Damit ist Fall B nachgestellt.
  - Die übrigen 15 Tests sind grün.
- Danach wurde `git checkout HEAD -- app/schnapper/web/app.js` ausgeführt. `git status --short` ist leer.

## 4. Secret-Scan und Tabu-Pfade
- `git diff origin/main...HEAD | grep -Ei "sk-ant-|ghp_|github_pat_|AKIA|PRIVATE KEY|passw|secret|token"` findet nichts.
- `git diff --name-only origin/main...HEAD | grep -Ei "\.github|ZENTNA|JERRY|Beatmaster"` findet nichts.
- `git diff --name-only 16e914b HEAD` nennt nur `app/schnapper/web/app.js` und `tests/test_app_kamera_s011.py`. Beide Dateien sind laut lead.md erlaubt.

## 5. Akzeptanzkriterien
1. **AK1 (Lauf-Prüfung): erfüllt.**
   - Direkt nach `const formate = await kameraFormate();` steht `if (lauf !== kamera.lauf || kamera.stream !== stream) return;`.
   - Die Prüfung steht vor `new BarcodeDetector`, `srcObject`, `hidden`, Status, Knopf und Timer.
   - Die Rückkehr erfolgt still, ohne DOM-Änderung.
2. **AK2 (Fall A): erfüllt.**
   - Der Test prüft nach dem Auflösen: `hidden === true`, `srcObject === null`, Status „Kamera-Scan abgebrochen.“ und `__detect === 0`.
   - Dazu kommt `alles_gestoppt()`. Es prüft, dass der Knopf aktiv ist, alle Tracks `ended` sind und `__gestoppt === __tracks.length` gilt (siehe Z. 249–255).
3. **AK3 (Fall B): erfüllt.**
   - Nach dem Auflösen gilt: `srcObject.getTracks()[0] === __tracks[1]`, Lauf 2 ist `live`, Lauf 1 ist `ended`, der Bereich ist sichtbar, der Status lautet „Barcode vor die Kamera halten …“ und `__detect > 0` gilt.
   - Nach „Abbrechen“ meldet `alles_gestoppt()` 2 Tracks.
4. **AK4 (neue Browsertests): erfüllt.**
   - Das Init-Skript `FORMATE_VERZOEGERT` wird nach `DETEKTOR` eingebunden.
   - Der 1. Aufruf von `getSupportedFormats` löst sofort auf, ab dem 2. Aufruf erst auf Kommando.
   - Beide Tests laufen tatsächlich, ohne Skip.
5. **AK5 (Gegenprobe): erfüllt.** Beide neuen Tests sind rot, siehe Abschnitt 3.
6. **AK6 (bestehende Tests): erfüllt.**
   - Die 15 bisherigen Tests sind grün, darunter `test_app_js`.
   - `KAMERA_FORMATE` lautet weiterhin `["ean_13", "ean_8", "upc_a"]`.
7. **AK7 (Gesamtsuite): erfüllt.** Python meldet 233 OK, Cloudflare 10/10.
8. **AK8 (CSP und Verbote): erfüllt.**
   - `git diff origin/main -- app/schnapper/web.py` hat 0 Zeilen.
   - Der Diff dieses Laufs fügt kein `innerHTML`, `eval` oder `fetch` hinzu. Die vorhandenen `fetch`- und `localStorage`-Stellen liegen außerhalb des Kamera-Abschnitts und sind älter.
   - `test_csp_unveraendert` und `test_app_js` sind grün.
9. **AK9 (Umfang und Commit): erfüllt.** Es gibt genau 1 Commit mit 2 Dateien, die richtige Nachricht und die Trailer. Der Commit ist nicht gepusht.

## Kritische Code-Durchsicht
- **Die Lauf-Prüfung ist korrekt.**
  - `kamera.lauf` wird nur in `kameraScannen()` und `kameraStoppen()` erhöht.
  - Ein neuer `kameraScannen()` setzt `kamera.laeuft === false` voraus. Das ist nur nach einem `kameraStoppen()` der Fall.
  - Ein veralteter Lauf an dieser Stelle bedeutet daher immer, dass vorher `kameraStoppen()` gelaufen ist, während `kamera.stream === stream` war. Dabei wurden die Tracks dieses Streams gestoppt.
  - Die zweite Bedingung `kamera.stream !== stream` ist redundant, schadet aber nicht.
- **Es entsteht kein neues Leck.**
  - Der stille Return lässt keinen Stream offen, denn den hat `kameraStoppen()` bereits beendet. Fall A belegt das mit `__gestoppt === __tracks.length`.
  - Der Return erfolgt vor `new BarcodeDetector`. Es bleibt also weder ein Timer noch eine `runde()` zurück.
  - Da kein erneutes `t.stop()` erfolgt, zählt `__gestoppt` nicht doppelt.
- **Die Testabweichung in Fall A (`element.click()` statt Playwright-Klick) ist vertretbar.**
  - Der Knopf liegt im noch verborgenen `#kamera-bereich`. Für Nutzer ist er in diesem Moment nicht klickbar.
  - `element.click()` löst denselben Handler aus, der zu `kameraStoppen("Kamera-Scan abgebrochen.")` führt.
  - Die realistischen Auslöser `visibilitychange` und `pagehide` nutzen dieselbe `kameraStoppen()`-Logik. Den Weg über `visibilitychange` deckt Fall B ab.
  - Optional für später: Eine Variante von Fall A mit `verstecken()` statt Klick würde den realen Pfad direkt abdecken. Das ist nicht blockierend.
- **Restpunkt aus brain.md (nach `await video.play()`) bestätigt, nicht blockierend.**
  - Ein Lauf, der während `play()` veraltet, hat `srcObject` und `hidden` bereits gesetzt, bevor `kameraStoppen()` beides zurücksetzt.
  - Danach greift die vorhandene Prüfung `kamera.stream !== stream`. Es bleibt also kein dauerhaft falscher Zustand.

## Zustand nach CHECK
- `git status --short --branch` ergibt `## agent/master/20261022-2238...origin/agent/master/20261022-2238 [ahead 1]`. Der Arbeitsbaum ist sauber.
- Von CHECK wurde nichts geändert, committet oder gepusht. Der Push ist Aufgabe von COMMAND.
