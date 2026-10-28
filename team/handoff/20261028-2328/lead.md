# LEAD – Lauf 20261028-2328

## Aufgabe
- **F4 / S-011 „Barcode per Kamera scannen“**, Draft-PR **#41**
- Schritt: **Tastaturfokus beim Kamera-Scan steuern** – beim Start auf „Abbrechen“, beim Stoppen zurück auf „Mit Kamera scannen“ (Barrierefreiheit Tastatur/Screenreader).

## Branch
- Bestehender Team-Branch fortsetzen: `agent/master/20261022-2238` (Kopf auf origin: `ca5420e`).
- Kein neuer Branch, kein neuer PR. Nur Fast-Forward-Push auf diesen Branch (COMMAND), PR bleibt Draft.

## Begründung (Mangel belegt)
- `app.js` (Branch, Z. 268–273): `kameraScannen()` setzt `$("kamera-knopf").disabled = true`. Wer per Tastatur (Enter/Leertaste) auf „Mit Kamera scannen“ startet, verliert dadurch den Fokus – ein deaktivierter Knopf gibt den Fokus ab, er landet auf `<body>`. Der neue Abbrechen-Knopf (seit `ca5420e` sofort sichtbar) ist dann für Tastatur-/Screenreader-Nutzer nur durch erneutes Tabben vom Seitenanfang aus erreichbar.
- `kameraStoppen()` (Z. 247–260) blendet `#kamera-abbrechen` aus. Lag der Fokus dort (Abbruch per Enter, Zeitlimit, Treffer), fällt er wieder auf `<body>`.
- Im Branch gibt es kein `focus(` im Kamera-Abschnitt (`git show origin/agent/master/20261022-2238:app/schnapper/web/app.js | grep -n focus` → leer); kein Test prüft `document.activeElement`. Der Schritt ist also noch nicht umgesetzt.
- Der letzte Bericht (Lauf 20261028-2028) nennt genau diesen Punkt als nächsten kleinsten Schritt. In `team/runs/INDEX.md` ist er nicht erledigt. Gewählt statt `upc_e`, weil `upc_e` ohne Normalisierung auf UPC-A/EAN-13 6- bzw. 8-stellige Codes liefert, die die Treffer-Prüfung `/^[0-9]{8,14}$/` teils verwirft bzw. die Ladenpreis-Suche nicht findet – das wäre kein 15-Minuten-Schritt.

## Akzeptanzkriterien
1. **Start:** In `kameraScannen()` erhält `#kamera-abbrechen` direkt nach dem Einblenden (`hidden = false`) den Fokus (`.focus()`), noch **vor** `await getUserMedia(...)`. Damit hat er den Fokus auch, während der Berechtigungsdialog offen ist.
2. **Stoppen:** `kameraStoppen()` merkt sich **vor** dem Ausblenden, ob `document.activeElement === $("kamera-abbrechen")` ist. Nur in diesem Fall bekommt `#kamera-knopf` den Fokus, und zwar **nach** `disabled = false`. Liegt der Fokus woanders (z. B. im Barcode-Feld), wird er nicht verschoben.
3. Das gilt für alle Stopp-Wege, die über `kameraStoppen()` laufen: Abbrechen, Zeitlimit, Fehler (verweigert/keine Kamera), Treffer und `visibilitychange`. Eine eigene Sonderlogik je Weg ist nicht nötig.
4. Der Treffer-Ablauf bleibt unverändert: Barcode-Feld füllen → `kameraStoppen(...)` → `requestSubmit()`. Die Preisabfrage läuft wie bisher genau einmal.
5. Neuer Browsertest `test_tastatur_fokus_start_und_abbrechen` in `tests/test_app_kamera_s011.py` (Klasse `Browser`):
   - `oeffne("leer")`, warten, bis `#kamera-knopf` aktiv ist, dann `self.seite.focus("#kamera-knopf")` und `self.seite.keyboard.press("Enter")`. Kein Mausklick.
   - warten auf `document.activeElement && document.activeElement.id === 'kamera-abbrechen'`
   - `self.seite.keyboard.press("Enter")` → Status „Kamera-Scan abgebrochen.“, `alles_gestoppt()`, `document.activeElement.id === 'kamera-knopf'`
6. Neuer Browsertest `test_fokus_waehrend_kamera_anfrage`: `oeffne("leer", verzoegert=True)`, Start per Tastatur (wie in 5), `window.__gum === 1`. Danach muss `activeElement.id === 'kamera-abbrechen'` sein, solange die Anfrage offen ist.
7. Neuer Browsertest `test_fokus_zurueck_nach_zeitlimit`: `oeffne("leer", uhr=True)`, Start per Tastatur, Fokus auf Abbrechen, `clock.run_for(21000)` → `alles_gestoppt()` und `activeElement.id === 'kamera-knopf'`.
8. Neuer Browsertest `test_fokus_bleibt_im_feld`: Start per Tastatur, dann `self.seite.focus("#barcode")` und Abbruch über `self.verstecken()` (visibilitychange). Danach muss `activeElement.id === 'barcode'` bleiben. Prüft AK 2: Der Fokus wird nicht gestohlen.
9. **Gegenprobe:** Mit `app.js` aus `ca5420e` (`git show ca5420e:app/schnapper/web/app.js > app/schnapper/web/app.js`) und den neuen Tests sind die Tests aus 5, 6 und 7 **rot**, weil `activeElement` dann `BODY` ist. Test 8 darf auch ohne Änderung grün sein, er sichert nur den Rand ab. Danach `app.js` wiederherstellen. Die Zahl der Fehlschläge steht im BRAIN-/CHECK-Bericht.
10. Alle bisherigen Tests bleiben grün, auch `test_markup`, `test_app_js` und `test_csp_unveraendert`. Im Modul gibt es **0 Skips** (Chromium wird über `_finde_chromium()` gefunden).
11. Kein `innerHTML`, kein `console.`, keine neue Abhängigkeit, CSP und `index.html` unverändert.

## Testbefehle
```
cd /home/claude/schnapper   # bzw. Worktree des Branches
python3 -m unittest tests.test_app_kamera_s011 -v          # gezielt: erwartet 25/25 OK, 0 Skips
python3 -m unittest discover -s tests                      # gesamt: erwartet 241 OK (237 + 4)
cd cloudflare && node --test test/*.test.mjs               # erwartet 10/10 pass
```
Gegenprobe (siehe AK 9):
```
cp app/schnapper/web/app.js /tmp/.../app.js.neu
git show ca5420e:app/schnapper/web/app.js > app/schnapper/web/app.js
python3 -m unittest tests.test_app_kamera_s011 -v          # erwartet: FAILED (failures>=3)
cp /tmp/.../app.js.neu app/schnapper/web/app.js
```

## Betroffene Dateien (erlaubt)
- `app/schnapper/web/app.js` (nur Kamera-Abschnitt `kameraScannen()` / `kameraStoppen()`)
- `tests/test_app_kamera_s011.py` (nur neue Tests, bei Bedarf eine kleine Hilfsmethode)

## Grenzen
- Keine anderen Dateien ändern. Das gilt besonders für `index.html`, `app.css`, die CSP, `.github/workflows/**`, `team/tasks.json`, `team/STATUS.md` (diese nur als Entwurf im Übergabeordner) und alles außerhalb von S-011.
- `KAMERA_FORMATE`, `KAMERA_ZEITLIMIT`, Treffer-Regex, Zeitlimit-Logik und Lauf-Zähler (`kamera.lauf`) nicht anfassen. `upc_e` ist **nicht** Teil dieses Schritts.
- Keine Live-Abrufe externer Preisquellen (die Tests nutzen nur die bestehenden Mocks/Routen), keine Secrets, 0 € Budget.
- Kein Push auf main, kein Merge, kein Force-Push. PR #41 bleibt Draft. Nur ein Fast-Forward auf `agent/master/20261022-2238`.
- Nichts von ZENTNA, JERRY AL oder Beatmaster anfassen. Fremde PRs (z. B. #95, ändert ebenfalls `app/schnapper/web`) nicht berühren.
