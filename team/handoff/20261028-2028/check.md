# CHECK – Lauf 20261028-2028

**Urteil: bestanden**

Geprüft: lokaler Commit `ca5420e` auf `agent/master/20261022-2238` (Basis `origin/agent/master/20261022-2238` = 662cf81). Ich habe unabhängig geprüft, keinen Code geändert, nichts committet und nichts gepusht.

## Tests (selbst ausgeführt)
- `python3 -m unittest tests.test_app_kamera_s011 -v`: **21 Tests, OK, 0 Skips** (im Log kommt „skip“ 0-mal vor, Chromium wurde gefunden).
- `python3 -m unittest discover -s tests`: **237 Tests, OK** (0 failures/errors).
- `cd cloudflare && node --test test/*.test.mjs`: **tests 10, pass 10, fail 0**.
- Gegenprobe in einem eigenen Worktree im Scratch-Verzeichnis (`app.js` und `index.html` aus 662cf81 eingesetzt, neue Tests behalten): **FAILED (failures=4)**. Fehlgeschlagen sind `test_markup`, `test_abbrechen_waehrend_formatabfrage`, `test_abbrechen_waehrend_kamera_anfrage` und `test_abbrechen_waehrend_kamera_anfrage_spaeter_fehler`. Der Worktree ist wieder entfernt (`git worktree list` zeigt nur den Klon).

## Diff und Umfang
- Diff `origin/agent/master/20261022-2238..agent/master/20261022-2238` umfasst nur `app/schnapper/web/app.js` (+2), `app/schnapper/web/index.html` (+1/−1) und `tests/test_app_kamera_s011.py` (+56/−3). Alle drei Dateien sind erlaubt; `app.css` ist unverändert.
- Diff `origin/main...agent/master/20261022-2238` umfasst nur `app.css`, `app.js`, `index.html` und `tests/test_app_kamera_s011.py`. Er enthält keine Änderung an `.github/workflows` und keine Tabu-Pfade (grep nach `.github`, ZENTNA, JERRY, Beatmaster: kein Treffer).
- Secret-Scan über die hinzugefügten Zeilen (sk-ant-, ghp_, github_pat_, AKIA, PRIVATE KEY, passw): **0 Treffer**.
- `innerHTML` kommt in keiner neuen Zeile vor (0 Treffer). Die CSP ist unverändert (`test_csp_unveraendert` grün). Es gibt keine neue Bibliothek und keinen Netzabruf.

## Akzeptanzkriterien
1. **erfüllt.** `kameraScannen()` setzt `kamera-abbrechen.hidden = false` vor `await getUserMedia`. `abbrechen_sichtbar()` prüft `is_visible()` sowohl bei offener `getUserMedia`-Anfrage (`verzoegert=True`) als auch bei offener Formatabfrage (`formate_verzoegert=True`).
2. **erfüllt.** In beiden Zuständen wird echt mit `self.seite.click("#kamera-abbrechen")` geklickt. Danach ist der Status „Kamera-Scan abgebrochen.“, `#kamera-knopf` ist wieder frei (`disabled` false) und der Abbrechen-Knopf ist nicht mehr sichtbar.
3. **erfüllt.** Der Test löst `__aufloesen(0)` nach dem Abbrechen aus. Der späte Stream endet (alle Tracks `ended`), `alles_gestoppt()` prüft `srcObject === null` und dass `#kamera-bereich` verborgen bleibt, und `__detect` ist 0. Im Code zuständig: Prüfung `lauf !== kamera.lauf` mit anschließendem Stop der Tracks.
4. **erfüllt.** `#kamera-bereich` (Video) wird weiterhin erst nach der Formatabfrage eingeblendet. `abbrechen_sichtbar()` prüft, dass der Bereich verborgen und `#kamera-bild` unsichtbar ist. `test_ak4_abbrechen` prüft, dass das Video nach dem Start sichtbar ist.
5. **erfüllt.** Alle Endpfade gehen über `kameraStoppen()`, das den Abbrechen-Knopf ausblendet: Klick, `visibilitychange`, `pagehide`, Zeitlimit, Treffer und Fehler. `alles_gestoppt()` und `fehlerfall()` prüfen das; sie laufen in den Tests für Treffer, Zeitlimit, Fehlerfälle, Abbrechen, visibilitychange und pagehide. `starte()` prüft, dass der Knopf im Ruhezustand verborgen ist.
6. **erfüllt.** Der JS-Direktklick samt Kommentar ist durch einen echten Klick ersetzt. Es gibt zwei neue Tests für den Zustand „getUserMedia offen“.
7. **erfüllt.** 21/21 Tests grün, 0 Skips.
8. **erfüllt.** Die Gegenprobe ist rot (4 failures), der neue Stand grün.
9. **erfüllt.** 237 Tests (≥ 235), Cloudflare 10/10.
10. **erfüllt.** Siehe oben.
11. **erfüllt.** Ein Commit mit dem Titel „SCHNAPPER MASTER: F4 Kamera – Abbrechen schon während des Kamera-Starts sichtbar (S-011)“ und beiden Attributionszeilen (Co-Authored-By, Claude-Session).

## Regressionen
- Der Stream wird auf allen Pfaden gestoppt: Bei Abbruch während der Formatabfrage stoppt `kameraStoppen()` den bereits gesetzten `kamera.stream`; ein später Stream wird direkt gestoppt. Die Lauf-ID-Logik ist unverändert.
- Knopf-Zustände sind konsistent: Der Kamera-Knopf ist während des Laufs gesperrt und danach frei, der Abbrechen-Knopf ist nur während des Laufs sichtbar.
- Das Layout des herausgelösten Knopfs passt: Die bestehende CSS-Regel `#kamera-knopf, #kamera-abbrechen` (min-height 44px) wirkt weiter.

## Hinweise (kein Mangel)
- Fokus-Management beim Start ist nicht umgesetzt, war aber nicht gefordert.
- BRAIN hat im Klon gearbeitet und keinen eigenen Worktree angelegt. Ergebnis und Branch sind korrekt, der Arbeitsbaum ist sauber.
