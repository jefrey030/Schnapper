# LEAD – Lauf 20261028-1343

## Aufgabe
PR #41 (F4 / S-011, Barcode per Kamera) fortsetzen, **nur Tests, keine Codeänderung**.
In `tests/test_app_kamera_s011.py` 2 Browsertests ergänzen. Sie decken Fall A (Abbruch während der offenen Formatabfrage `getSupportedFormats()`) über die **realen Seiten-Verlassen-Pfade** ab, nicht über den Klick auf „Abbrechen“:
1. `test_verstecken_waehrend_formatabfrage`: Der Abbruch läuft über `self.verstecken()`, also `visibilitychange` mit `visibilityState` „hidden“.
2. `test_pagehide_waehrend_formatabfrage`: Der Abbruch läuft über `window.dispatchEvent(new Event('pagehide'))`.

Beide Tests bauen auf `test_abbrechen_waehrend_formatabfrage` auf (ab Z. 412) und nutzen die vorhandenen Hilfen `oeffne("leer", formate_verzoegert=True)`, `starte()`, `warte(...)`, `verstecken()`, `kurz_warten()` und `alles_gestoppt()`. Ablauf:
1. Starten.
2. Warten auf `window.__formatAnfragen.length === 1`.
3. Abbruch über das jeweilige Ereignis.
4. `window.__formateAufloesen(0)` aufrufen.
5. `kurz_warten()`.
6. Prüfungen.

## Branch
`agent/master/20261022-2238` (Kopf `a3b1f9d`, PR #41, Draft, 0 hinter main). Auf diesem Branch committen. Normaler Push, kein Force. Kein anderer Branch.

## Begründung
- In `team/tasks.json` auf main ist keine Aufgabe „open“. Deshalb gilt nach der Priorität: offenen Team-Draft-PR fortsetzen.
- Der letzte Bericht (20261028-1129) nennt genau diesen Schritt als „nächsten kleinsten Schritt“. Er steht auch als Beobachtung im Bericht: Fall A war nur per `element.click()` getestet. Der reale Pfad (`visibilitychange`/`pagehide` → `kameraStoppen()`) war während der Formatabfrage ungetestet.
- Im Diff geprüft (`app.js` Z. 468–469): Beide Handler greifen nur bei `kamera.laeuft`. Während der Formatabfrage ist `kamera.laeuft === true`, der Pfad ist also erreichbar. Die Lauf-Prüfung in Z. 285 muss danach greifen.
- Der Schritt ist reiner Testzuwachs mit wenigen Zeilen und braucht keine neue Freigabe.
- Bewusst **nicht** gewählt: `upc_e` in `KAMERA_FORMATE`. Das braucht laut Bericht die Freigabe durch Jefrey und ist eine Erweiterung.

## Akzeptanzkriterien
1. Nur `tests/test_app_kamera_s011.py` ist geändert (`git diff --name-only origin/agent/master/20261022-2238` zeigt genau diese Datei). `app/schnapper/web/app.js`, `index.html`, `app.css` und `web.py` sind unverändert.
2. Es gibt 2 neue Testmethoden: `test_verstecken_waehrend_formatabfrage` und `test_pagehide_waehrend_formatabfrage`, in der Klasse `Browser`, im Abschnitt „Abbruch/Neustart während offener Formatabfrage“. Vorhandene Tests sind weder gelöscht noch abgeschwächt.
3. Beide Tests prüfen vor dem Abbruch `window.__formatAnfragen.length === 1` und `window.__gum === 1`. Damit ist belegt, dass der Abbruch wirklich während der offenen Formatabfrage passiert.
4. Der Abbruch erfolgt in Test 1 ausschließlich über `self.verstecken()` und in Test 2 ausschließlich über das Ereignis `pagehide`. Es gibt weder einen Klick noch ein `.click()` auf `#kamera-abbrechen`.
5. Test 1 prüft direkt nach dem Abbruch und erneut nach `__formateAufloesen(0)` plus `kurz_warten()` den Status „Kamera-Scan beendet.“.
6. Beide Tests prüfen nach dem Auflösen der Formatabfrage:
   - `#kamera-bereich` ist `hidden`.
   - `#kamera-bild.srcObject === null`.
   - `window.__detect === 0`.
   - `alles_gestoppt()` läuft durch.
7. Die Gegenprobe ist rot: Mit `app/schnapper/web/app.js` aus `16e914b` (vor dem Fix, nur temporär ausgecheckt und danach wiederhergestellt) schlagen mindestens die 2 neuen Tests fehl, `FAILED`. Mit dem aktuellen app.js sind alle grün.
8. Gesamtsuite: `python3 -m unittest discover -s tests` ergibt **Ran 235, OK**. Das sind die bisherigen 233 plus 2 neue, 0 skipped. Das Einzelmodul ergibt 19/19 OK. Die Browsertests laufen tatsächlich mit Chromium und werden nicht übersprungen.
9. Node ergibt `cd cloudflare && node --test test/*.test.mjs` 10 pass / 0 fail.
10. Weitere Bedingungen:
    - Keine Netzwerkzugriffe nach außen (die vorhandene `tearDown`-Prüfung `self.fremd == []` greift).
    - Keine Konsolenfehler.
    - Keine Änderung unter `.github/`.
    - Kein Secret im Diff.
    - Keine Änderung an `team/STATUS.md` oder `team/tasks.json`.
11. Der Commit ist ein einzelner Commit auf `agent/master/20261022-2238` mit Präfix „SCHNAPPER MASTER: F4 Kamera – …(S-011)“ und den Trailern `Co-Authored-By` und `Claude-Session` laut Vorgabe.

## Erlaubte Dateien
- `tests/test_app_kamera_s011.py` (einzige Datei, die geändert werden darf).
- Nur lesen: `app/schnapper/web/app.js`, `app/schnapper/web/index.html`.

## Testbefehle
```
cd /home/claude/schnapper
python3 -m unittest -v tests.test_app_kamera_s011
python3 -m unittest discover -s tests
cd cloudflare && node --test test/*.test.mjs
# Gegenprobe (danach zwingend wiederherstellen):
git show 16e914b:app/schnapper/web/app.js > app/schnapper/web/app.js
python3 -m unittest tests.test_app_kamera_s011   # erwartet FAILED
git checkout -- app/schnapper/web/app.js && git status --short   # muss leer sein bis auf die Testdatei
```
Hinweis: Die Browsertests nutzen Playwright mit dem vorinstallierten Chromium (`/opt/pw-browsers`, gefunden über `_finde_chromium()`). **Kein** `playwright install` ausführen.
