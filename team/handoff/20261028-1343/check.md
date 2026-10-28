# CHECK – Lauf 20261028-1343

- Start: 2026-10-28T13:48:14Z
- Ende: 2026-10-28T13:50:10Z
- Geprüft: lokaler Branch `agent/master/20261022-2238`, HEAD `662cf81fa3ddb4596dac053d77bc9d713fe78122` (= brain.md `662cf81`)
- Basis `origin/agent/master/20261022-2238` = `a3b1f9d`, genau 1 Commit darüber (`git rev-list --count` = 1), 0 hinter `origin/main`, 6 vor `origin/main`.

## Urteil: **bestanden**

## Eigene Testläufe
| Befehl | Ergebnis |
|---|---|
| `python3 -m unittest -v tests.test_app_kamera_s011` | Ran 19, OK, 0 skipped (alle 15 Browser-Tests liefen mit Chromium) |
| `python3 -m unittest discover -s tests` | Ran 235, OK, 0 skipped |
| `cd cloudflare && node --test test/*.test.mjs` | tests 10, pass 10, fail 0, skipped 0 |

## Diff-Prüfung
- `git diff --name-only origin/agent/master/20261022-2238 HEAD`: nur `tests/test_app_kamera_s011.py`, numstat 32 hinzu / 0 entfernt (reiner Zuwachs).
- `git diff --name-only origin/main...HEAD` (ganzer PR #41): `app/schnapper/web/app.css`, `app.js`, `index.html`, `tests/test_app_kamera_s011.py`. Das sind die bekannten Dateien des PR, keine weiteren.
- Keine `.github/`-Dateien, keine `team/`-Dateien, keine Tabu-Pfade (ZENTNA, JERRY AL, Beatmaster): grep ohne Treffer.
- Secret-Scan auf `git diff origin/main...HEAD` (sk-ant-, ghp_, github_pat_, AKIA, PRIVATE KEY, passw, secret, token, api_key): kein Treffer.
- Commit-Nachricht: „SCHNAPPER MASTER: F4 Kamera – Seite verlassen während Formatabfrage per Browsertest abgesichert (S-011)“, Trailer `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` und `Claude-Session: https://claude.ai/code/session_01Km4opyUk7XR4UurYRx46ak` vorhanden.

## Gegenprobe
1. `app.js` aus `16e914b` eingesetzt: Ran 19, **FAILED (failures=4)**. Es schlugen fehl: `test_verstecken_waehrend_formatabfrage`, `test_pagehide_waehrend_formatabfrage`, `test_abbrechen_waehrend_formatabfrage` und `test_neustart_waehrend_formatabfrage`. Das deckt sich mit brain.md.
2. Zusätzliche eigene Gegenprobe: In der aktuellen `app.js` habe ich nur die beiden Listener für `visibilitychange` und `pagehide` (Z. 468–469) entfernt. Ergebnis: FAILED (failures=7), darunter beide neuen Tests. Damit ist belegt, dass die neuen Tests wirklich von den Seiten-Verlassen-Handlern abhängen und nicht über einen anderen Pfad grün werden.
3. Danach jeweils `git checkout -- app/schnapper/web/app.js`. `git status --short` ist leer und HEAD ist unverändert `662cf81`.

## Akzeptanzkriterien
1. **Erfüllt.** Nur die Testdatei ist geändert. app.js, index.html, app.css und web.py sind gegenüber der Basis unverändert (siehe name-only).
2. **Erfüllt.** Beide Methoden stehen in `class Browser` direkt nach `test_neustart_waehrend_formatabfrage`, also im Abschnitt „Abbruch/Neustart während offener Formatabfrage“ und vor „Seite verlassen“. Der Diff hat 0 entfernte Zeilen, vorhandene Tests sind also nicht abgeschwächt.
3. **Erfüllt.** Beide Tests enthalten `warte("window.__formatAnfragen.length === 1")`, danach `assertEqual(__formatAnfragen.length, 1)` und `assertEqual(__gum, 1)`, jeweils vor dem Abbruch.
4. **Erfüllt.** Test 1 bricht nur über `self.verstecken()` ab. Die Hilfe setzt `visibilityState` auf 'hidden' und löst einen echten `visibilitychange` auf `document` aus. Test 2 bricht nur über `window.dispatchEvent(new Event('pagehide'))` ab. In keinem der beiden Tests gibt es einen Klick oder `.click()`.
5. **Erfüllt.** Test 1 prüft den Status „Kamera-Scan beendet.“ direkt nach `verstecken()` und erneut nach `__formateAufloesen(0)` plus `kurz_warten()`.
6. **Erfüllt.** Beide Tests prüfen `#kamera-bereich` hidden, `srcObject === null`, `__detect == 0` und rufen `alles_gestoppt()` auf. Diese Hilfe prüft zusätzlich: alle Tracks sind 'ended', `__gestoppt` entspricht der Track-Anzahl und der Knopf ist wieder aktiv.
7. **Erfüllt.** Siehe Gegenprobe: mit 16e914b rot (beide neuen Tests FAIL), mit dem aktuellen Stand grün.
8. **Erfüllt.** 235 OK und 0 skipped. Das Einzelmodul ergibt 19/19 OK, und die Browsertests liefen tatsächlich.
9. **Erfüllt.** 10 pass / 0 fail.
10. **Erfüllt.** `tearDown` prüft `fremd == []` und `meldungen == []` (Konsolen- und Seitenfehler). Alle Tests sind grün, also greifen diese Prüfungen ohne Befund. Keine Änderungen unter `.github/` oder `team/`, kein Secret im Diff.
11. **Erfüllt.** Es ist ein einzelner Commit mit korrektem Präfix und beiden Trailern. Er ist noch nicht gepusht, wie in brain.md angegeben.

## Anmerkungen (nicht blockierend)
- Test 2 prüft keinen Status. Das ist korrekt, denn der `pagehide`-Handler ruft `kameraStoppen()` ohne Meldung auf, und lead.md verlangt hier keine Statusprüfung.
- `verstecken()` simuliert `visibilityState` per `defineProperty`. Bei Playwright im Headless-Modus geht das nicht anders, und es löst den echten Handler in app.js aus (belegt durch Gegenprobe 2).
- Offen ist nur noch der Push von `662cf81`. Das ist nicht Aufgabe von CHECK.
