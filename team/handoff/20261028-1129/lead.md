# LEAD – Lauf 20261028-1129

## Gewählte Aufgabe
- **F4 / S-011 / PR #41** (Barcode per Kamera), Fortsetzung des offenen Team-Draft-PRs
- Branch für BRAIN: **`agent/master/20261022-2238`** (bestehender Branch, Kopf `16e914b`). Er liegt 0 Commits hinter origin/main 6dbe114, deshalb ist kein `git merge origin/main` nötig. Falls main sich bis zum Start bewegt: `git merge origin/main` (kein Rebase, kein Force-Push).
- Vorgehen: `git checkout -B agent/master/20261022-2238 origin/agent/master/20261022-2238`

## Begründung
- Laut Prioritätsregel geht die Fortsetzung eines offenen Team-Draft-PRs vor. Alle F1–F6 haben offene PRs. Der letzte Bericht nennt für #41 einen konkreten nächsten Schritt.
- Der Vorbericht hat diesen Restfall als „kosmetisch“ eingestuft. LEAD hat ihn jetzt in Chromium (Playwright, `/opt/pw-browsers/chromium-1243`) auf `16e914b` nachgestellt. **Der Fall ist nicht kosmetisch, sondern ein echter Funktionsfehler.** Dazu wurde `BarcodeDetector.getSupportedFormats()` ab dem 2. Aufruf verzögert. Der 1. Aufruf kommt aus `kameraVerfuegbar()` beim Laden.
  - **Fall A (Abbrechen, während die Formatabfrage läuft):** Nach dem Klick auf „Abbrechen“ lautet der Status „Kamera-Scan abgebrochen.“. Trotzdem ist danach `#kamera-bereich.hidden === false` und `#kamera-bild.srcObject !== null` (ein beendeter Stream). Der Kamerabereich taucht also nach dem Abbruch schwarz wieder auf.
  - **Fall B (Seite verborgen und Neustart, während die Formatabfrage von Lauf 1 noch offen ist; Lauf 2 löst zuerst auf, danach Lauf 1):** `#kamera-bild.srcObject` ist danach der **beendete** Stream von Lauf 1 (`readyState` = `ended`). Der Status zeigt „Barcode vor die Kamera halten …“. Der **live** Stream von Lauf 2 wird nicht angezeigt, die Erkennung läuft auf einem toten Video und kann nie treffen. Die Kamera von Lauf 2 bleibt bis zum Zeitlimit (20 s) aktiv, ohne dass der Nutzer ein Bild sieht.
- Die Alternative `upc_e` in `KAMERA_FORMATE` wurde verworfen. Sie wäre eine Erweiterung des Funktionsumfangs und keine Fehlerbehebung, und sie würde `test_app_js` und die AK1-Formatprüfung ändern. Sie bleibt ein möglicher späterer Schritt.
- Andere Restpunkte wurden verworfen. #45 `_anfrage` mit Nicht-String-URL ist im Produktivpfad unerreichbar. Der fehlende Bericht auf `agent/master/reports` betrifft keinen Code und gehört COMMAND bzw. Orchestrator, nicht BRAIN.

## Mangel (genau)
Datei `app/schnapper/web/app.js`, Funktion `kameraScannen()` (Abschnitt `// ---------- Kamera-Scan (S-011)`):

```js
  kamera.stream = stream;
  const video = $("kamera-bild");
  try {
    const detektor = new BarcodeDetector({ formats: await kameraFormate() });
    video.srcObject = stream;            // <- läuft auch, wenn der Lauf inzwischen veraltet ist
    $("kamera-bereich").hidden = false;  // <- zeigt den Bereich nach Abbruch wieder an
    await video.play();
```

Nach `await kameraFormate()` fehlt die Prüfung, ob der Lauf noch aktuell ist. Inzwischen kann `kameraStoppen()` gelaufen sein (Abbrechen, `visibilitychange`, `pagehide`), oder ein neuer Lauf kann begonnen haben. Dann überschreibt der veraltete Lauf `srcObject` und `hidden` des aktiven Zustands.

## Lösungsrichtung (Vorschlag, minimal)
Direkt nach dem `await kameraFormate()` und **vor** `video.srcObject = stream` gilt: Ist der Lauf veraltet (`lauf !== kamera.lauf` bzw. `kamera.stream !== stream`), wird still zurückgekehrt. Es gibt dann keine DOM-Änderung, keine Statusänderung und kein `kameraStoppen()`. Die Tracks dieses Streams hat `kameraStoppen()` bereits gestoppt. Zur Sicherheit dürfen sie idempotent erneut gestoppt werden, aber `__gestoppt` darf dabei nicht doppelt zählen. Deshalb lieber nicht erneut stoppen: `t.stop()` ist zwar idempotent, der Test-Zähler zählt aber jeden Aufruf. Die Formate können alternativ vor `getUserMedia` ermittelt werden. In diesem Fall muss auch dort eine Lauf-Prüfung stehen, und die Erwartung „`__gum` erst nach Klick“ (AK1) muss erhalten bleiben. Die kleinste Änderung ist die eine Prüfzeile.

## Akzeptanzkriterien
1. In `kameraScannen()` steht unmittelbar nach `await kameraFormate()` und vor jeder Änderung an `#kamera-bild`/`#kamera-bereich` eine Lauf-Prüfung. Bei einem veralteten Lauf kehrt die Funktion zurück, ohne `srcObject`, `hidden`, `#kamera-status`, `#kamera-knopf` oder Timer anzufassen.
2. **Fall A:** Wird während einer offenen `getSupportedFormats()`-Anfrage „Abbrechen“ geklickt und die Anfrage danach aufgelöst, gilt anschließend: `#kamera-bereich.hidden === true`, `#kamera-bild.srcObject === null`, Status bleibt „Kamera-Scan abgebrochen.“, `#kamera-knopf` ist aktiv, alle Tracks sind `ended`, und `__gestoppt === __tracks.length`.
3. **Fall B:** Seite verborgen und Neustart während einer offenen Formatabfrage von Lauf 1. Erst löst Lauf 2 auf, dann Lauf 1. Danach gilt: `#kamera-bild.srcObject === ` Stream von Lauf 2, dessen Tracks sind `live`, `#kamera-bereich` ist sichtbar, Status ist „Barcode vor die Kamera halten …“, die Erkennung läuft (`__detect > 0`), und der Stream von Lauf 1 ist `ended`. Nach „Abbrechen“ ist alles gestoppt (`alles_gestoppt()`).
4. Für Fall A und Fall B gibt es je einen neuen Browsertest in `tests/test_app_kamera_s011.py`. Er nutzt eine verzögerte `getSupportedFormats`-Attrappe als neues Init-Skript neben `DETEKTOR`. Der 1. Aufruf (`kameraVerfuegbar()` beim Laden) löst sofort auf, ab dem 2. Aufruf erst auf Kommando. Die Tests laufen tatsächlich (kein Skip) mit dem vorinstallierten Chromium.
5. **Gegenprobe:** Die neuen Tests **schlagen** mit dem `app.js` aus `16e914b` **fehl**. Prüfung: `git show 16e914b:app/schnapper/web/app.js > app/schnapper/web/app.js`, Tests laufen lassen, Ergebnis notieren, danach Datei zurücksetzen. Beide neuen Tests müssen rot sein.
6. Alle bisherigen 15 Tests in `tests.test_app_kamera_s011` bleiben unverändert grün, auch `test_app_js` (`KAMERA_FORMATE` bleibt `["ean_13", "ean_8", "upc_a"]`).
7. Gesamtsuite grün: `python3 -m unittest discover -s tests`. Erwartet sind 233 OK (231 + 2); BRAIN meldet die tatsächliche Zahl. Cloudflare: 10/10 pass.
8. Die CSP ist unverändert (`git diff origin/main -- app/schnapper/web.py` leer). In `app.js` gibt es kein `innerHTML`, kein `eval`, keine neuen Netzwerkaufrufe, keine Bildspeicherung. Die Verbotsliste in `test_app_js` gilt weiter.
9. Der Diff gegen `16e914b` betrifft nur `app/schnapper/web/app.js` (wenige Zeilen im Kamera-Abschnitt) und `tests/test_app_kamera_s011.py`. Ein Commit auf `agent/master/20261022-2238` mit der Nachricht „SCHNAPPER MASTER: F4 Kamera – veralteter Lauf überschreibt nach Formatabfrage keine Anzeige (S-011)“, dazu die Attributionszeilen Co-Authored-By und Claude-Session. **BRAIN pusht nicht** (Push nur durch COMMAND nach CHECK).

## Testbefehle
```bash
cd /home/claude/schnapper
python3 -m unittest -v tests.test_app_kamera_s011
python3 -m unittest discover -s tests
(cd cloudflare && node --test test/*.test.mjs)
git diff origin/main -- app/schnapper/web.py   # muss leer sein
# Gegenprobe (AK5):
cp app/schnapper/web/app.js /tmp/claude-0/-home-claude-schnapper/b0563ebd-e8f4-5bb8-bdbe-8da78b35c5af/scratchpad/app.js.neu
git show 16e914b:app/schnapper/web/app.js > app/schnapper/web/app.js
python3 -m unittest -v tests.test_app_kamera_s011   # neue Tests müssen FAILEN
git checkout -- app/schnapper/web/app.js 2>/dev/null || cp /tmp/claude-0/-home-claude-schnapper/b0563ebd-e8f4-5bb8-bdbe-8da78b35c5af/scratchpad/app.js.neu app/schnapper/web/app.js
git diff --stat 16e914b   # nur app.js + Testdatei
```
- Playwright mit vorinstalliertem Chromium unter `/opt/pw-browsers/chromium-1243`. Die Testdatei findet es selbst über `_finde_chromium()`. **Kein `playwright install`.**
- In Browsertests kein `wait_for_function` verwenden (die CSP verbietet `unsafe-eval`). Stattdessen die vorhandene Hilfe `self.warte(...)` nutzen.

## Erlaubte Dateien
- `app/schnapper/web/app.js` (nur der Kamera-Abschnitt in `kameraScannen()`)
- `tests/test_app_kamera_s011.py`

## Verbote
- Keine Änderungen an `.github/workflows` bzw. `.github/`, keine Secrets und Tokens, keine CSP-/`web.py`-Änderung.
- Keine Änderung an `team/tasks.json`, `team/STATUS.md` oder README auf dem Feature-Branch, weil das #41 verbreitert und mit #36 kollidiert.
- Kein Rebase, kein Force-Push, kein Merge des PRs. Fremde Branches und PRs (nicht `agent/master/...`) sowie #36/#39/#40/#44/#45/#50 nicht anfassen. Nichts von ZENTNA, JERRY AL oder Beatmaster.
- Keine Live-Abrufe externer Preisquellen (eBay/Open Prices). Der Testserver fängt `/api/openprices` ab, das bleibt so. Budget 0 €.
- `KAMERA_FORMATE` nicht erweitern (`upc_e` ist ausdrücklich nicht Teil dieses Laufs).
