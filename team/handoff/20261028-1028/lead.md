# LEAD – Lauf 20261028-1028

## Aufgabe
**PR #41 (F4 / S-011, Barcode per Kamera) fortsetzen:** Im Kamera-Scan kann ein Kamera-Stream offen bleiben. Das wird mit einer Lauf-ID (Generationszähler) behoben. Dazu kommen Browsertests für diesen Fall und für `visibilitychange`/`pagehide`. Für beide gibt es bisher keinen Test.

## Begründung der Wahl
- Die Wahl folgt der Regel „offenen Team-Draft-PR fortsetzen“. F1–F6 haben alle einen offenen Draft-PR, und in tasks.json auf main ist keine Aufgabe „open“.
- Der Mangel ist **echt und im Browser belegt**. LEAD hat ihn mit Chromium und Playwright auf dem Kopf a3fcfab nachgestellt. Dabei war `getUserMedia` verzögert. Ablauf: Klick auf „Mit Kamera scannen“, dann `visibilitychange`→hidden (Knopf wird wieder aktiv), dann zweiter Klick, dann löst die erste Anfrage auf, dann die zweite, dann „Abbrechen“. Ergebnis: `gum 2, tracks 2, gestoppt 1, live 1`. **Eine Kamera-Spur läuft nach dem Abbrechen weiter.**
  - Ursache in `kameraScannen()`: Nach `await getUserMedia` wird nur `kamera.laeuft` geprüft. Der zweite Start setzt `laeuft` wieder auf true. Deshalb übernimmt der erste Aufruf seinen Stream nach `kamera.stream`. Der zweite überschreibt ihn, und Stream 1 wird nie gestoppt.
  - Das verletzt die Zusage im PR-Body („In jedem Fall wird die Kamera sauber beendet: alle Tracks gestoppt“). CHECK hatte den Randfall schon notiert, er blieb aber unbehoben. Im PR-Body steht außerdem: „Für visibilitychange/pagehide gibt es keinen Browsertest.“ Bei einer Kamera ist das ein Datenschutzthema.
- Die Kandidaten aus dem letzten Bericht wurden verworfen:
  - (a) Nicht-String-URL in `_anfrage` (#45): Der Fall ist im Produktivpfad unerreichbar und verletzt kein Akzeptanzkriterium von S-013. Das wäre nur weiteres Polieren.
  - (b) Der Bericht zu 2666d8b gehört auf `agent/master/reports` und ist Sache des ORCHESTRATORs, nicht eines Feature-PRs.
- Weitere Prüfung: Alle sechs Team-Branches laufen grün (Python discover 216/233/226/227/232/252 OK, je 1 Skip, Node 10/10). Für #39 hat LEAD `POST /api/angebot` mit NaN, Infinity, 2000-fach verschachteltem JSON, Listen, Bool und zu langen Zahlen geprüft. Alle Eingaben werden sauber mit 400, 413 oder 422 abgewiesen, ein Mangel war nicht zu finden.

## Branch
`agent/master/20261022-2238` (PR #41, Draft). Kopf a3fcfab, Basis main 6dbe114, 0 Commits hinter main.
BRAIN arbeitet lokal: `git fetch origin && git checkout -B agent/master/20261022-2238 origin/agent/master/20261022-2238`. Commit nur lokal, kein Push (das macht COMMAND).

## Betroffene Dateien (nur diese)
1. `app/schnapper/web/app.js`: nur der Abschnitt `// ---------- Kamera-Scan (S-011) ----------` (Objekt `kamera`, `kameraStoppen`, `kameraScannen`)
2. `tests/test_app_kamera_s011.py`: neue Browsertests in der Klasse `Browser`, dazu bei Bedarf eine zusätzliche Medien-Simulation mit verzögertem `getUserMedia`. Die bestehende `MEDIEN`-Vorlage bleibt unverändert.

## Umsetzungsskizze (Vorschlag, nicht bindend)
- `kamera` bekommt ein Feld `lauf: 0`. `kameraStoppen()` erhöht `kamera.lauf`.
- In `kameraScannen()` steht vor `getUserMedia` `const lauf = ++kamera.lauf;`. Nach dem `await` gilt: Ist `lauf !== kamera.lauf`, werden alle Tracks des Streams gestoppt und die Funktion bricht still ab. Sie ändert dann weder den UI-Zustand des neueren Laufs noch dessen Statustext.
- Die gleiche Prüfung gilt im `catch` von `getUserMedia`. Ein veralteter Fehler darf den neueren Lauf nicht stoppen und seine Meldung nicht überschreiben.

## Akzeptanzkriterien
1. **Rennen behoben (Browsertest):** `getUserMedia` wird so simuliert, dass es erst auf Kommando auflöst. Ablauf: Klick, dann `visibilitychange`→hidden, dann zweiter Klick, dann Auflösung von Anfrage 1 und danach von Anfrage 2, dann „Abbrechen“. Danach gilt `__gum == 2`, `__tracks.length == 2` und `__gestoppt == 2`, und alle Tracks haben `readyState === 'ended'`. Der Test belegt außerdem, dass der Stream aus Anfrage 1 **sofort nach seiner Auflösung** beendet ist und nicht erst nach dem Abbrechen.
2. **Veralteter Lauf stört den neuen nicht:** Im Ablauf aus AK1 ist nach der Auflösung von Anfrage 2 und vor dem Abbrechen der Kamerabereich sichtbar. `kamera-bild.srcObject` ist dann der Stream aus Anfrage 2, und der Knopf ist deaktiviert.
3. **Veralteter Fehler stört den neuen nicht:** Variante mit Ablehnung. Anfrage 1 wird mit `NotAllowedError` abgelehnt, nachdem Lauf 2 gestartet und aufgelöst ist. Danach bleibt Lauf 2 aktiv: Bereich sichtbar, Stream live, Status nicht „Kamerazugriff verweigert …“. Mit „Abbrechen“ wird anschließend alles gestoppt (`alles_gestoppt()`).
4. **visibilitychange getestet:** Bei laufendem Scan (Detektor „leer“) setzen `document.visibilityState='hidden'` und das Ereignis `visibilitychange` den Status auf „Kamera-Scan beendet.“. `alles_gestoppt()` ist erfüllt.
5. **pagehide getestet:** Bei laufendem Scan stoppt `window.dispatchEvent(new Event('pagehide'))` alle Tracks (`alles_gestoppt()`).
6. **Gegenprobe:** Mit dem alten `app.js` (a3fcfab) schlägt mindestens der Test aus AK1 fehl. BRAIN führt das in einer Scratch-Kopie vor und dokumentiert es in brain.md mit der Ausgabe.
7. Alle bestehenden 11 Tests in `tests.test_app_kamera_s011` bleiben unverändert grün, auch `test_app_js`, also mit unverändertem `KAMERA_FORMATE` und der Zeile `getTracks().forEach((t) => t.stop())`. Die Browsertests laufen tatsächlich, ohne Skip.
8. `python3 -m unittest discover -s tests` ist grün und hat mindestens 227 + neue Tests, 0 Fehler, höchstens 1 Skip wie bisher.
9. `cd cloudflare && node --test test/*.test.mjs` ergibt 10/10 pass.
10. Im Kamera-Abschnitt von app.js gilt weiterhin: kein `innerHTML`, kein `fetch(`, kein `console.`, kein Speichern oder Hochladen von Bildern und keine externe Bibliothek. Die CSP ist unverändert (`git diff origin/main -- app/schnapper/web.py` ist leer).
11. Der Diff gegenüber a3fcfab betrifft nur die 2 genannten Dateien. Er ist klein: app.js etwa +5 bis 15 Zeilen, nur im Kamera-Abschnitt. Es gibt genau einen Commit mit einer Nachricht nach dem Muster `SCHNAPPER MASTER: F4 Kamera – kein offener Stream bei Neustart während Berechtigungsdialog (S-011)` und den vorgegebenen Attributionszeilen.
12. Keine Secrets und keine Tabu-Begriffe im Diff.

## Testbefehle
```
cd /home/claude/schnapper
python3 -m unittest -v tests.test_app_kamera_s011
python3 -m unittest discover -s tests
cd cloudflare && node --test test/*.test.mjs
```
Gegenprobe (AK6) in einer Scratch-Kopie mit dem alten `app/schnapper/web/app.js` aus a3fcfab und den neuen Tests:
`python3 -m unittest -v tests.test_app_kamera_s011` muss dann FAILED melden.

## Was NICHT geändert werden darf
- `KAMERA_FORMATE`, `KAMERA_ZEITLIMIT`, Meldungstexte, `index.html`, `app.css`, `app/schnapper/web.py` und die CSP. Das Ergänzen von `upc_e` ist ein eigener, späterer Vorschlag und gehört nicht in diesen Schritt.
- `team/tasks.json`, `team/STATUS.md`, `README.md`, `docs/`, `.github/` (insbesondere `.github/workflows`).
- Andere Branches oder PRs (#36, #39, #40, #44, #45, #50), `main` und `agent/master/reports`. Kein Merge, kein Rebase, kein Force-Push, kein Push durch BRAIN.
- Bestehende Tests nicht abschwächen oder löschen. Die Vorlagen `MEDIEN` und `DETEKTOR` bleiben für die alten Tests unverändert. Neue Simulationen kommen als eigene Konstante dazu.

## Nicht blockierende Beobachtungen (für den Bericht, nicht umsetzen)
- S-011 AK1 nennt „EAN-13/EAN-8/UPC“, `KAMERA_FORMATE` enthält aber nur `upc_a` und kein `upc_e`. Das ist ein Kandidat für einen späteren kleinen Schritt in #41.
- #45: Eine Nicht-String-URL in `_anfrage` wirft weiterhin `AttributeError`. Im Produktivpfad ist das unerreichbar und hat niedrige Priorität.
- Der Bericht zu 2666d8b (#39) fehlt weiterhin. Das ist Aufgabe des ORCHESTRATORs auf `agent/master/reports`.
