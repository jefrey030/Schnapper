# MASTER 122 – großer Fertigstellungs- und Sicherheitsmaster

**Stand:** 25.10.2026 · **Bereich:** ZENTNA × SCHNAPPER × JERRY AL · **Priorität:** P0/P1 · **Kosten:** 0 EUR Zusatzkosten.

**Status:** P0-Sicherheitsfix in isoliertem SCHNAPPER-Entwicklungszweig implementiert und lokal geprüft. **Keine Produktionsfreigabe. Kein Merge/Deployment/Autostart.** Projekte bleiben getrennt; dieser SCHNAPPER-PR ist ein gestapelter Draft auf PR #110 (operator consent), dessen Basis PR #55 ist.

## 1. Ursache und tatsächlich umgesetzte Änderung

Der vorhandene Genehmigungsprüfer `team/operator_approval.py` prüfte bei `_read_json()` den Dateityp erst **nach** einem blockierenden `os.open(O_RDONLY | O_NOFOLLOW)`. Ersetzte jemand `team/work/operator_approval.json` oder `team/tasks.json` durch eine POSIX-FIFO ohne Schreiber, konnte bereits das Öffnen des Pfads hängen. `fstat()` und die nachfolgende Ablehnung wurden dann nie erreicht.

**Fix:** `os.O_NONBLOCK` bei beiden Dateizugriffen verpflichtend, zusätzlich zum vorhandenen `os.O_NOFOLLOW`. Auf Plattformen ohne eine dieser beiden Konstanten wird die Prüfung verweigert. Der bestehende `fstat()`-Filter für reguläre Dateien, Einzel-Link, Eigentümer und 0600-Schutz bei Approval bleibt unangetastet. Keine automatische Betreiberfreigabe wird erstellt.

**Vier neue Offline-Tests:** reguläre Datei weiterhin gültig; Freigabe-FIFO blockiert nicht; Aufgaben-FIFO blockiert nicht; beide Dateizugriffe verlangen `O_NONBLOCK | O_NOFOLLOW`. Die FIFO-Tests benutzen getrennte Unterprozesse mit 3-Sekunden-Timeout, sodass Regressionen die gesamte CI nicht endlos festhalten.

**Lokaler Vorabtest (exakt die anschließend veröffentlichten GitHub-Blob-SHAs):** 17/17 isolierte Tests erfolgreich (13 aus Master 121, 4 neu); keine echten Modelle oder Netzwerkaufrufe. **Vollständige GitHub-CI auf finalem PR-Head gesondert nachweisen.**

## 2. SCHNAPPER – LEAD / BUILDER / CHECK / GUARD (18 Arbeitspakete)

1. [x] Bereits geöffneten Master-121-Draft #110 und Basis-PR #55 identifizieren.
2. [x] Betreiberfreigabemodul und die negativen Tests aus GitHub-Blob lesen.
3. [x] Dateizugriff mit erst nach `open()` ausgeführter Typprüfung als Ursache einordnen.
4. [x] Neuen eigenen Reparaturzweig von exakt #110 HEAD anlegen; fremde Branches nicht ändern.
5. [x] `O_NONBLOCK` zur bestehenden `O_NOFOLLOW`-Sperre hinzufügen.
6. [x] Fehlende Nonblock-Plattformunterstützung auf Fail-Closed umstellen.
7. [x] Bisherige Datei-/Eigentümer-/Privilegienprüfungen erhalten.
8. [x] Test: reguläre kurze Freigabe erlaubt.
9. [x] Test: Approval-FIFO sicher verweigert, keine Prozessblockade.
10. [x] Test: Task-FIFO sicher verweigert, keine Prozessblockade.
11. [x] Test: beide `open`-Aufrufe mit erforderlichen Flags.
12. [x] 13 vorhandene Approval-Tests gegen die neue Modulversion lokal wiederholen.
13. [x] 4 neue Regressionen lokal ausführen, 17/17 PASS.
14. [x] Code- und Testblobs nach GitHub-Schreibzugriff verifizieren.
15. [ ] Vollständige Python- und Cloudflare-GitHub-CI am finalen HEAD prüfen, inklusive Skip/Fehler.
16. [ ] Unabhängige Review (insbesondere Windows/Termux/POSIX-Sonderfälle).
17. [ ] PR #110/#55 und parallele Sicherheitspatches kollisionsfrei konsolidieren; kein automatischer Merge.
18. [ ] Betreiberseitigen echten Host-Test mit separat erteilter Zustimmung durchführen, ohne Cloud-Fallback.

## 3. ZENTNA – Datenschutz und Käuferabnahme (10 Arbeitspakete)

19. [x] Bestehenden P0-Produktionsvorfall aus den vorherigen Masters als Release-Blocker aufnehmen.
20. [x] Bereits vorhandene Datenschutz-/Rollout-PRs #118, #125, #126 und weitere Prüfarbeiten statt eines konkurrierenden Schnellfixes identifizieren.
21. [ ] Frischen rein lesenden Vergleich von `profiles`-ACL, Moderations-RPCs, `search_zentna_members` und Security-Definer-EXECUTE in Produktion/Staging belegen.
22. [ ] Abhängigkeit Moderationsfunktion **vor** Datenschutzmigration für Review verbindlich festlegen.
23. [ ] Nur isoliertes Staging mit getrennten Testkonten und signierten JWTs prüfen; keine Fremdprofile auslesen.
24. [ ] Spaltenliste der Mitgliedersuche und Creator-/Post-Projektionen negativ testen.
25. [ ] Backup-/Restore- und Rollback-Prüfung isoliert dokumentieren.
26. [ ] GitHub Runner/CI-Startproblem unabhängig klären und vollständige Tests erhalten.
27. [ ] Echte App-Workflows (Anmeldung, Upload, Abstimmung, Shop/Wallet, Kündigung, Android) abnehmen.
28. [ ] Erst dann Sicherheits-, Betriebs- und Käuferfreigabe gesondert erteilen; derzeit NO-GO.

## 4. JERRY AL – reale Studio-/KI-Funktionsabnahme (8 Arbeitspakete)

29. [x] Bestehenden Sicherheits-Draft #118, Kosten-Not-Aus und Authentifizierungs-Gates als Referenz aufnehmen.
30. [ ] CI auf finaler SHA wiederherstellen und Artefakte/Logs verfügbar machen.
31. [ ] Login/Logout und JWT-Fehlerpfade mit getrennten Testidentitäten nachweisen.
32. [ ] Ohne Bezahlprovider erst nur offline Chat-/Provider-Fail-Closed testen.
33. [ ] Musik-/Bild-/Videogeneratoren jeweils mit echten, separat genehmigten Ausführungsbelegen nachweisen.
34. [ ] Secrets, Weiterleitungen, Antwortgrößen, Limits und Kostenschranken unabhängig überprüfen.
35. [ ] Android-/Desktop-/API-Gesamtpfad auf Staging belegen.
36. [ ] Kein Produktivstart oder bezahlter Provider ohne separate Freigabe.

## 5. Unveränderliche Release-Gates (4 Arbeitspakete)

37. [x] Keine produktive Datenbankmigration, Veröffentlichung oder fremden Branchänderung durchgeführt.
38. [x] Keine KI-Instanz, Autostart, Bezahl-API oder Modellinstallation aktiviert.
39. [ ] Externe Reviews, vollständige reproduzierbare CI und echte Staging/Host-E2E getrennt signieren.
40. [ ] Freigabe nur nach konkreter ausdrücklicher Nutzerentscheidung; bis dahin NO-GO.

## 6. Ergebnisdisziplin und nächster kleinster Schritt

**Erledigt:** isolierter Sicherheitscode + 4 neue Negativtests + 13 Altprüfungen lokal. **Nicht erledigt:** globale Projekte vollständig fertigstellen, CI/Review/Produktions-Rollout und echte KI-Modelldurchläufe. Ein erfolgreicher Unit-Test ist kein Produktfreigabenachweis. Der nächste kleinste Schritt ist die GitHub-CI und ein unabhängiger Review auf der exakt geprüften Commit-SHA.

Wichtige Verweise:
- SCHNAPPER Operator Approval: https://github.com/jefrey030/Schnapper/pull/110
- SCHNAPPER Main-Integration: https://github.com/jefrey030/Schnapper/pull/55
- ZENTNA Zwei-Konten-Staging: https://github.com/jefrey030/zentna-core-foundation/pull/118
- JERRY Auth/Kosten: https://github.com/jefrey030/Jerry-Al/pull/118
