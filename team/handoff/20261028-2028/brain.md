# BRAIN – Lauf 20261028-2028

## Aufgabe
F4 / S-011, Draft-PR #41: Abbrechen-Knopf schon während des Kamera-Starts sichtbar und bedienbar.

## Branch / Commit
- Branch `agent/master/20261022-2238`, Ausgang `origin/agent/master/20261022-2238` (662cf81), gearbeitet im Klon /home/claude/schnapper (kein separater Worktree).
- Commit: `ca5420eb53a8615afbbe6d431dd4638731094ddf` – „SCHNAPPER MASTER: F4 Kamera – Abbrechen schon während des Kamera-Starts sichtbar (S-011)“, mit beiden Attributionszeilen.
- Kein Push, kein Merge, kein Rebase.

## Geänderte Dateien
- `app/schnapper/web/index.html`: `<button id="kamera-abbrechen" type="button" hidden>` aus `#kamera-bereich` herausgelöst (direkt dahinter).
- `app/schnapper/web/app.js`: `kameraScannen()` blendet Abbrechen direkt nach `kamera-knopf.disabled = true` ein (vor `getUserMedia`); `kameraStoppen()` blendet ihn aus. Lauf-ID-Logik unverändert. Video/`#kamera-bereich` erscheint weiterhin erst nach erfolgreichem Start.
- `tests/test_app_kamera_s011.py`: Markup-Test angepasst (+ Prüfung, dass Abbrechen nicht im Videobereich liegt); `alles_gestoppt()` und `fehlerfall()` prüfen Abbrechen verborgen; `starte()` prüft Ruhezustand verborgen; `test_ak4_abbrechen` prüft Video + Abbrechen sichtbar; neue Hilfe `abbrechen_sichtbar()`; in `test_abbrechen_waehrend_formatabfrage` JS-Direktklick samt Kommentar durch `self.seite.click("#kamera-abbrechen")` ersetzt; neu: `test_abbrechen_waehrend_kamera_anfrage` (AK 1–3, später Stream sofort gestoppt, kein detect) und `test_abbrechen_waehrend_kamera_anfrage_spaeter_fehler`.
- `app.css` unverändert (globales `[hidden] { display:none !important }` genügt).

## Testergebnisse
- `python3 -m unittest tests.test_app_kamera_s011 -v`: 21 Tests, OK, 0 Skips (Chromium gefunden).
- Gegenprobe (app.js/index.html aus 662cf81): 21 Tests, FAILED (failures=4): test_markup, test_abbrechen_waehrend_formatabfrage, test_abbrechen_waehrend_kamera_anfrage, test_abbrechen_waehrend_kamera_anfrage_spaeter_fehler. Danach neuer Stand wiederhergestellt.
- `python3 -m unittest discover -s tests`: 237 Tests, OK (0 failures/errors, 0 Skips).
- `cd cloudflare && node --test test/*.test.mjs`: 10/10 pass.
- `test_csp_unveraendert` grün; keine neue Bibliothek, kein Netzabruf.
- Secret-Scan über Diff (sk-ant-, ghp_, github_pat_, AKIA, PRIVATE KEY): 0 Treffer.

## Offene Punkte
- Push (Fast-Forward) durch COMMAND nach CHECK; PR #41 bleibt Draft.
- Fokus-Management (z. B. Fokus auf Abbrechen beim Start) nicht umgesetzt – nicht gefordert.
