# S-006 – Übersicht der offenen PRs (Entscheidungsvorlage)

Stand: 22.10.2026, 11:30 UTC. Vergleichsbasis: main = `4bc37e7` (fester Commit, nicht das wandernde `origin/main`).
Ermittelt mit `git rev-list --count 4bc37e7..<Kopf>`, `git diff --name-only 4bc37e7...<Kopf>` und
`git merge-tree --write-tree 4bc37e7 <Kopf>`. Geprüft durch `tests/test_pr_uebersicht_s006.py`.

**Entscheidung über Übernehmen, Zusammenführen oder Schließen liegt allein bei Jefrey. Agenten mergen und schließen keine PRs.**

## Tabelle

| PR | Kopf | Commits vor main | Dateien | Merge mit main | Enthalten in |
| --- | --- | --- | --- | --- | --- |
| #2 | cdce320 | 6 | 5 | Konflikt | – |
| #6 | f83281a | 25 | 24 | ok | – |
| #7 | 478b2c1 | 17 | 8 | ok | #15, #16 |
| #8 | d232611 | 13 | 7 | ok | #15, #16 |
| #12 | 6017b6f | 20 | 22 | Konflikt | #15, #16 |
| #13 | 954dd7c | 3 | 3 | ok | #15, #16 |
| #14 | 726780f | 1 | 14 | ok | #15, #16 |
| #15 | d67c5ea | 82 | 59 | ok | – |
| #16 | 446016c | 77 | 59 | ok | – |

„Enthalten in“ = Kopf des PRs ist Vorfahre des anderen PR-Kopfs (`git merge-base --is-ancestor`).

## Befunde

- **#15 (Sammelstand)** enthält #7, #8, #12, #13 und #14 vollständig. Es fehlen 9 Commits aus #16 und 6 Commits aus #6 (darunter `0b758dd`, die Korrektur des S-006-Tests). Auf #15 schlagen 2 von 143 Tests fehl (Bericht `team/runs/20261022-1030-master.md`).
- **#16** ist Geschwister von #15: 9 eigene Commits (Preisherkunft), 14 Commits aus #15 fehlen. Ebenfalls 2 Fehlschläge (147 Tests).
- **#6** (dieser Arbeitsbranch) ist auf Stand von main; nur Berichte, Aufgabenliste, Konzepte und Tests.
- **#12** hat einen Merge-Konflikt mit main in `team/agent.py`, ist aber in #15 enthalten.
- **#2** ist der älteste PR (18 Commits hinter main), hat Konflikte in `.github/workflows/schnapper-hourly.yml`, `README.md` und `team/runner.py` und ändert eine Workflow-Datei. Er ist in keinem anderen PR enthalten.
- **#14** ist kein Draft, aber vollständig in #15 enthalten.

## Empfehlung (nur Vorschlag)

1. #16 in #15 übernehmen und `0b758dd` aus #6 mitnehmen, damit der Sammelstand grün ist.
2. Wird #15 übernommen, sind #7, #8, #12, #13 und #14 danach überflüssig (schließen).
3. #6 danach auf den neuen main-Stand bringen oder schließen; Berichte bleiben in der Historie.
4. #2 inhaltlich sichten: wegen Workflow-Änderung und Konflikten nicht ohne Überarbeitung übernehmbar.
