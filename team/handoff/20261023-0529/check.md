# CHECK – Lauf 20261023-0529

- Start: 2026-10-23T05:34:26Z (UTC)
- Ende: 2026-10-23T05:35:36Z (UTC)
- Geprüft: lokaler Branch `work-36`, Kopf `8d4e90b6cfd72ad8f51f58a27544de6256d9d4a8`, Push-Ziel `agent/master/20261022-20`. Vergleichsbasis: origin/main `6dbe114`. Beide Remote-Refs waren nach `git fetch` unverändert (origin/main 6dbe114, origin/agent/master/20261022-20 4d48068).
- Arbeitsbaum danach: detached auf origin/main, sauber. `work-36` ist noch vorhanden, nicht gelöscht.

## Urteil: **bestanden**

Die Kriterien 1–12 sind lokal belegt. Kriterium 13 (Push, PR-Body) ist Aufgabe von COMMAND und erst nach dem Push prüfbar. Der Vorzustand stimmt aber: PR #36 ist offen, Draft, head 4d48068.

## Kriterien

| # | Kriterium | erfüllt | Beleg |
|---|---|---|---|
| 1 | 4d48068 ist Vorfahr, Fast-Forward möglich | ja | `merge-base --is-ancestor` für 4d48068 und origin/agent/master/20261022-20 → OK. Gepusht wurde noch nicht (COMMAND). |
| 2 | Merge-Commit: Eltern 4d48068 und 6dbe114, Baum ab6822b | ja | 2a43d86: Eltern 4d48068d… und 6dbe1142…, Baum ab6822b07f07ab133a5f6d0fbb0debc198d1fb04. Unabhängig nachgeprüft: `git merge-tree --write-tree origin/main 4d48068` ergibt denselben Baum. |
| 3 | origin/main ist in HEAD enthalten | ja | `merge-base --is-ancestor origin/main HEAD` → OK |
| 4 | Der eigene Commit ändert nur 2 Dateien | ja | `diff --name-only HEAD^1 HEAD` → docs/SCHNAPPER-MASTERPLAN.md, team/tasks.json |
| 5 | Diff gegen origin/main zeigt genau 3 Dateien | ja | docs/SCHNAPPER-MASTERPLAN.md, team/tasks.json, tests/test_branches_s006.py (Änderung `proposed`→`done`, stammt schon aus #36) |
| 6 | Abschnitt B: Basiszeile, Tabellen mit 15/19/9 Zeilen, jede PR genau einmal, Daten stimmen | ja | Die Zeile „Basis `main` @ 6dbe114“ ist vorhanden. Per Skript gezählt: Offen 15/15, Gemergt 19/19, Geschlossen 9/9, 43 Zeilen, keine doppelt, keine fehlt (1–45 ohne 4 und 38). **Alle 43 Zeilen**, nicht nur eine Stichprobe, gegen den Live-REST-Stand verglichen (Titel, Branch, Draft, Zustand, merged_at auf die Minute in UTC): 0 Abweichungen. #4 und #38 sind laut REST Issues (`pull_request` null). |
| 7 | Masterplan außerhalb von B unverändert (HEAD^1→HEAD) | ja | Der Teil bis „## B.“ und der Teil ab „## C.“ sind gegenüber HEAD^1 per `diff` identisch. Alle Hunks liegen zwischen den alten Zeilen 25 und 78 (in HEAD^1 steht „## C.“ in Zeile 79). |
| 8 | S-009–S-013 auf review, Hinweise korrekt, S-000–S-006 unverändert, JSON gültig | ja | Zuordnung #39/-21, #40/-22, #41/-2238, #44/-23, #45/20261023-01 stimmt. Der alte Hinweis wird nur ergänzt (Präfix bleibt gleich). Feldweiser Vergleich mit 4d48068: Nur `status` und `hinweis` bei S-009–S-013 haben sich geändert. S-000–S-003 stehen auf review, S-004–S-006 auf done. `json.tool` → OK. Das Format (indent 2, ensure_ascii=False, Zeilenumbruch am Ende) ist byte-identisch zu einem Re-Dump. |
| 9 | Kein Eintrag hat `open` | ja | Statusliste: nur review und done |
| 10 | Python-Tests | ja | `python3 -m unittest discover -s tests` → Ran 216 tests, OK |
| 11 | Cloudflare-Tests | ja | `node --test test/*.test.mjs` → tests 10, pass 10, fail 0 |
| 12 | Secret-Scan, `.github`, Tabu-Begriffe | ja | sk-ant-/ghp_/github_pat_/AKIA/PRIVATE KEY: 0 Treffer. Passwort/password: 0 Treffer. Einziger Treffer für „SECRET“ ist der Name der Umgebungsvariable `SCHNAPPER_EBAY_CLIENT_SECRET` im Akzeptanztext von S-013, ohne Wert, also kein Secret. Keine Änderung unter `.github/`. ZENTNA, JERRY AL/Jerry-AL und Beatmaster kommen nicht vor. |
| 13 | PR #36 bleibt Draft und offen, head = Push, Body ergänzt | offen (COMMAND) | Vorzustand per REST: #36 offen, draft true, head 4d48068. Push und Body-Ergänzung stehen noch aus. Danach nachprüfen: head.sha = 8d4e90b, der Body enthält „Update Lauf 20261023-0529“ und nennt open→review. |

## Testzahlen
- Python: 216 Tests, OK (0 Fehler)
- Cloudflare: 10/10 bestanden
- JSON: gültig

## Befunde
1. Keine blockierenden Befunde.
2. Der Hinweis zu den Überschneidungen ist geprüft: #39, #40 und #41 ändern gegenüber main jeweils `app/schnapper/web/app.js` und `app/schnapper/web/index.html`. Die Aussage stimmt.
3. Der Diff gegen origin/main enthält auch Abschnitt D, Punkt 3 („keine feste Reihenfolge mehr …“). Diese Änderung stammt schon aus 4d48068 (#36), nicht aus diesem Lauf. Sie verletzt deshalb weder Kriterium 7 noch die erlaubten Pfade.
4. Die Zeile „Der frühere Abschnitt (Empfehlung #6 → #12 → #7 → #8) ist überholt …“ in Abschnitt B steht nicht in der LEAD-Vorgabe. Sie war schon vorher vorhanden und wurde nur stehen gelassen. Das ist unkritisch und liegt innerhalb von B.
5. Hinweis an COMMAND: Der Titel von PR #36 lautet noch „… S-009–S-013 open“. Er steht so auch in der Tabelle, weil die Tabelle den REST-Titel korrekt wiedergibt. Eine Titeländerung gehört nicht zum Auftrag. Wird der Titel geändert, weicht die Tabellenzeile von #36 davon ab.
6. Schritt 9 (`work-36` lokal löschen) erst nach erfolgreichem Push ausführen.
