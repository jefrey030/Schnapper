# CHECK – Lauf 20261028-1028

## Urteil: **bestanden**

Geprüft wurde der lokale Branch `agent/master/20261022-2238` mit HEAD `16e914b`. Basis ist origin `a3fcfab`, 1 Commit voraus, nicht gepusht. CHECK hat nichts geändert. Der Arbeitsbaum ist sauber (`git status --short` liefert 0 Zeilen), und der Worktree für die Gegenprobe ist wieder entfernt.

## Eigene Testläufe
| Befehl | Ergebnis |
|---|---|
| `python3 -m unittest -v tests.test_app_kamera_s011` | Ran 15 tests in 10.3s, **OK**. Alle 11 Browsertests melden „ok“, kein Skip. |
| `python3 -m unittest discover -s tests` | Ran **231** tests in 20.1s, **OK**, kein „skipped“. |
| `cd cloudflare && node --test test/*.test.mjs` | tests 10, pass 10, fail 0, skipped 0 |

## Gegenprobe (AK6, eigener Lauf)
Ablauf: `git worktree add --detach /tmp/claude-0/check-wt HEAD`, danach dort `git show a3fcfab:app/schnapper/web/app.js > app/schnapper/web/app.js` (Diff: 3+/5−). Dann liefen die neuen Tests:
```
test_neustart_alter_fehler_stoert_nicht ... FAIL
test_neustart_alter_stream_sofort_gestoppt ... FAIL
AssertionError: True is not false
AssertionError: Zeitüberschreitung: window.__streams[0].getTracks().every((t) => t.readyState === 'ended')
Ran 15 tests in 13.497s
FAILED (failures=2)
```
Das deckt sich mit brain.md. Die Tests für visibilitychange und pagehide laufen auch mit dem alten Code grün. Das ist korrekt, denn sie sichern bestehendes Verhalten ab. Der Worktree wurde danach mit `git worktree remove --force` entfernt.

## Diff-Prüfung
- `git rev-list --count origin/agent/master/20261022-2238..HEAD`: 1 Commit.
- Die Nachricht lautet „SCHNAPPER MASTER: F4 Kamera – kein offener Stream bei Neustart während Berechtigungsdialog (S-011)“. Sie enthält Co-Authored-By und Claude-Session.
- `git diff --stat a3fcfab..HEAD` betrifft nur `app/schnapper/web/app.js` (+5/−3) und `tests/test_app_kamera_s011.py` (+106/−2).
- `git diff --stat origin/main...HEAD` umfasst app.css, app.js, index.html und den Test. Alle stammen aus dem bestehenden PR #41, keine Datei unter `.github/`, `team/` oder `docs/`.
- `git diff origin/main -- app/schnapper/web.py` hat 0 Zeilen, die CSP ist also unverändert.
- Der Secret- und Tabu-Scan über die +-Zeilen von `origin/main...HEAD` (sk-ant-, ghp_, github_pat_, AKIA, PRIVATE KEY, passw, ZENTNA, JERRY AL, Beatmaster) ergab keinen Treffer.
- Im Kamera-Abschnitt (app.js Z. 227–309) gibt es kein `innerHTML`, kein `fetch(` und kein `console.`.

## Code-Review
- Kann ein veralteter Lauf UI oder Status des neuen ändern?
  - **Nach getUserMedia nicht.** Erfolg mit veralteter `lauf`-ID: Der Lauf stoppt nur die eigenen Tracks und kehrt zurück (Z. 280). Fehler mit veralteter ID: Er kehrt still zurück (Z. 277). `kameraStoppen` erhöht `lauf` (Z. 252), deshalb verfallen auch Abbruch, Zeitlimit, visibilitychange und pagehide korrekt.
  - **Später gibt es nur noch einen kosmetischen Restfall, der schon vorher bestand und keinen Datenschutzbezug hat.** Er tritt ein, wenn Lauf 1 schon aufgelöst ist und in `await kameraFormate()` (Z. 284) hängt, während gestoppt und neu gestartet wird. Dann setzt Lauf 1 noch `srcObject` auf seinen bereits gestoppten Stream und blendet den Bereich ein (Z. 285 f.), bevor die Prüfung `kamera.stream !== stream` in Z. 288 greift. Die Tracks sind zu diesem Zeitpunkt schon beendet, weil kameraStoppen `kamera.stream` gestoppt hat. Lauf 2 überschreibt das später bzw. blendet den Bereich beim Fehler wieder aus. Das Zeitfenster ist sehr klein (Auflösung von getSupportedFormats). Das ist keine AK-Verletzung und nur ein möglicher späterer Feinschliff: eine `lauf`-Prüfung nach `await kameraFormate()`.
- **Streams werden in allen Pfaden gestoppt.** Das gilt für eine veraltete Auflösung (sofort), für Abbruch, Treffer, Zeitlimit, visibilitychange, pagehide und Detektor- bzw. play-Fehler (Z. 307, über kameraStoppen).
- **Die Tests sind aussagekräftig.**
  - AK1 prüft, dass Stream 0 direkt nach `__aufloesen(0)` `ended` ist und `__gestoppt == 1` gilt, während der Bereich noch versteckt ist, also vor dem Abbrechen. Die Gegenprobe zeigt, dass beide Rennen-Tests am alten Code scheitern.
  - Die Simulation umhüllt das echte `track.stop()` mit einem Zähler, und `readyState` kommt vom echten Canvas-captureStream. Es gibt also keine Tautologie.
  - `MEDIEN` und `DETEKTOR` sind unverändert. `oeffne()` hat nur den optionalen Parameter `verzoegert=False` bekommen, das Standardverhalten ist identisch.

## Akzeptanzkriterien
| AK | Bewertung | Beleg |
|---|---|---|
| 1 Rennen behoben | erfüllt | `test_neustart_alter_stream_sofort_gestoppt` ok. Er prüft gum 2, tracks 2, gestoppt 2, `alles_gestoppt()` (alle `ended`) und dass Stream 0 sofort nach der Auflösung `ended` ist. Am alten Code FAIL. |
| 2 Veralteter Lauf stört nicht | erfüllt | Nach `__aufloesen(1)` gilt im selben Test: Bereich sichtbar, `srcObject === __streams[1]`, Stream live, Knopf disabled, Status „Barcode vor die Kamera halten …“. |
| 3 Veralteter Fehler stört nicht | erfüllt | `test_neustart_alter_fehler_stoert_nicht` ok. Nach NotAllowedError für Anfrage 0 ist der Bereich sichtbar, srcObject = Stream 2, live, gestoppt 0, Status ohne „Kamerazugriff verweigert“. Danach gilt `alles_gestoppt()`. Am alten Code FAIL. |
| 4 visibilitychange | erfüllt | `test_visibilitychange_beendet_scan` ok. Status „Kamera-Scan beendet.“ und `alles_gestoppt()`. |
| 5 pagehide | erfüllt | `test_pagehide_beendet_scan` ok, `alles_gestoppt()`. |
| 6 Gegenprobe | erfüllt | Von brain.md dokumentiert und von CHECK selbst nachvollzogen: FAILED (failures=2). |
| 7 Alte 11 Tests grün, kein Skip | erfüllt | 15/15 ok, darunter `test_app_js`. KAMERA_FORMATE und die Zeile `getTracks().forEach((t) => t.stop())` sind unverändert. |
| 8 discover | erfüllt | 231 = 227 + 4, OK, 0 Skips. LEAD erwartete höchstens 1 Skip, also unkritisch. |
| 9 Node | erfüllt | 10/10 pass |
| 10 Kamera-Abschnitt und CSP | erfüllt | grep ohne Treffer, web.py-Diff leer |
| 11 Diff-Umfang und Commit | erfüllt | 2 Dateien, app.js +5/−3 nur im Kamera-Abschnitt (Z. 231, 252, 272, 277, 280), 1 Commit, Nachricht und Attribution korrekt |
| 12 Secrets und Tabu | erfüllt | Scan ohne Treffer |

## Nachbesserungen
Keine sind erforderlich.

Optional für später, nicht blockierend:
1. Im PR-Body von #41 den Satz „Für visibilitychange/pagehide gibt es keinen Browsertest“ aktualisieren. Das ist Sache von COMMAND.
2. Eine zusätzliche Lauf-Prüfung nach `await kameraFormate()` in `kameraScannen()` einbauen. Sie würde den oben beschriebenen kosmetischen Restfall schließen.
