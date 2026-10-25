# SCHNAPPER MASTER 85 – Runner-Sperrdatei gegen Dateityp- und Link-Angriffe absichern

**Datum:** 25.10.2026  
**Projekt:** `jefrey030/Schnapper`  
**Basis:** MASTER 84 / [PR #109](https://github.com/jefrey030/Schnapper/pull/109), `36c7e28185444e43b8846d632ac92329adcde80d`, GitHub Actions #243 grün.  
**Arbeitszweig:** `fix/master85-runner-lock-fd-integrity-20261025`  
**Modus:** Isolierter Draft, ausschließlich sichere Codeänderung und Offline-Regressionsprüfungen  
**Budget:** 0 € zusätzliche Kosten. Keine bezahlten APIs und keine Produktiv-/Cloudflare-Bereitstellung.  
**Freigabe:** **NO-GO** für Merge, Deployment, echte KI-Rotation und Branchlöschung.

## Gesicherter Ausgangsbefund

Der lokale SCHNAPPER-Service in `team/local_service.py` öffnete seine permanente Datei `team/work/local_runner.lock` bislang mit `O_CREAT | O_RDWR | getattr(os, "O_NOFOLLOW", 0)`. Zwar verhindert flock zwei kooperierende Runner und ermöglicht Neustarts nach einem Crash. Aber es bestand keine `fstat`-Typprüfung und keine Hardlink-Sperre, und `O_NOFOLLOW` konnte unbemerkt fehlen. Vor dem PID-Schreibzugriff rief der Dienst `os.ftruncate(fd, 0)` direkt auf. Ein Link auf eine fremde Datei oder ein spezieller lokaler Inode hätte dadurch ungewollt beschrieben werden können. Spezialdateien konnten zudem beim Öffnen blockieren.

## Tatsächlich geänderte Laufzeitlogik

- `_oeffne_runner_sperre()` verlangt `O_NOFOLLOW`, ergänzt `O_NONBLOCK`/`O_CLOEXEC`, prüft `fstat` auf reguläre Datei und `st_nlink == 1`, und schließt den FD bei jedem Prüfungsfehler.
- `start()` verwendet diesen abgesicherten FD und behält das nichtblockierende `flock(LOCK_EX|LOCK_NB)` bei; abgestürzte Lockdateien bleiben wiederverwendbar.
- **Unmittelbar vor dem PID-Schreiben** wird nach der exklusiven Sperre noch einmal `fstat` geprüft. Fehlerhafte Dateitypen, weitere Hardlinks und unvollständige PID-Schreibzugriffe, `ftruncate`- oder `fsync`-Fehler führen zu `BLOCKIERT` / Exit 2. Der Agentenprozess startet nicht.
- `tests/test_master85_runner_lock.py` ergänzt 18 synthetische Testfälle ohne Modell- oder Netzwerkaufrufe.

## 60-Punkte-Auftragsmatrix

| # | Bereich | Prüfschritt |
|--:|---|---|
| 1 | Basis und Isolation | Repository jefrey030/Schnapper prüfen |
| 2 | Basis und Isolation | MASTER 84 Draft #109 und SHA 36c7e28185444e43b8846d632ac92329adcde80d verifizieren |
| 3 | Basis und Isolation | MASTER 84 S-006 Fail-Closed-CI als getestete Basis übernehmen |
| 4 | Basis und Isolation | MASTER 84 unverändert lassen |
| 5 | Basis und Isolation | Eigenen MASTER-85-Branch erzeugen |
| 6 | Basis und Isolation | Keine parallelen PRs oder main verändern |
| 7 | Basis und Isolation | 0 € neue Kosten, keine Bezahl-API |
| 8 | Bedrohungsmodell | Veraltete Runner-Lockdatei nach Crash weiterhin erlauben |
| 9 | Bedrohungsmodell | Aktive zweite Runner-Instanz blockieren |
| 10 | Bedrohungsmodell | Symlink am letzten Pfadglied beim Öffnen blockieren |
| 11 | Bedrohungsmodell | Dangling Symlink verweigern |
| 12 | Bedrohungsmodell | Hardlink auf fremde Datei vor Schreibzugriff erkennen |
| 13 | Bedrohungsmodell | Nichtreguläre Inodes erkennen |
| 14 | Bedrohungsmodell | FIFO ohne Hängen ablehnen |
| 15 | Bedrohungsmodell | Verzeichnis als Lockdatei ablehnen |
| 16 | Bedrohungsmodell | Optionales O_NOFOLLOW durch erforderliches O_NOFOLLOW ersetzen |
| 17 | Bedrohungsmodell | Race zwischen altem exists() und open() vermeiden |
| 18 | Codehärtung | Separaten _oeffne_runner_sperre()-Helper ergänzen |
| 19 | Codehärtung | os.open mit O_NOFOLLOW, O_NONBLOCK und O_CLOEXEC verwenden |
| 20 | Codehärtung | FD vor Rückgabe mit fstat prüfen |
| 21 | Codehärtung | st_nlink == 1 verlangen |
| 22 | Codehärtung | Unsichere FD bei Exceptions sicher schließen |
| 23 | Codehärtung | Kein unlink der Lockdatei beim Prozessende |
| 24 | Codehärtung | flock LOCK_EX|LOCK_NB unverändert lassen |
| 25 | Codehärtung | Nach Lock zweite fstat-Verifikation vor PID-Schreibzugriff |
| 26 | Codehärtung | os.ftruncate erst nach Sicherheitsprüfung |
| 27 | Codehärtung | Nur vollständige PID-Bytes als gültige Diagnose akzeptieren |
| 28 | Codehärtung | PID-Schreibfehler kontrolliert mit Return-Code 2 blockieren |
| 29 | Codehärtung | fsync-Fehler kontrolliert blockieren |
| 30 | Codehärtung | Lock-FD am Ende immer schließen |
| 31 | Regressionen | Symlink greift nicht auf fremde Datei zu |
| 32 | Regressionen | Dangling Symlink blockiert |
| 33 | Regressionen | Hardlink greift nicht auf fremde Datei zu |
| 34 | Regressionen | Directory blockiert |
| 35 | Regressionen | FIFO blockiert ohne Endlosschleife |
| 36 | Regressionen | Reguläre Lockdatei startet |
| 37 | Regressionen | Verwaiste PID wird überschrieben |
| 38 | Regressionen | Parallele Instanz blockiert ohne PID-Mutation |
| 39 | Regressionen | Nach Freigabe erneuter Start |
| 40 | Regressionen | FD ist reguläre Einzeldatei |
| 41 | Regressionen | Fehlendes O_NOFOLLOW blockiert |
| 42 | Regressionen | fstat-Fehler schließt den FD |
| 43 | Regressionen | Zwischen Open und PID-Schreiben angelegter Hardlink blockiert |
| 44 | Regressionen | ftruncate-Fehler blockiert |
| 45 | Regressionen | Kurzer os.write blockiert |
| 46 | Regressionen | fsync-Fehler blockiert |
| 47 | Regressionen | Neue Datei hat private Berechtigungen |
| 48 | Regressionen | Ungültiges Lock startet keine Unterprozesse |
| 49 | Abnahme / Restblocker | Alle bisherigen Python-Unittests laufen auf finalem HEAD |
| 50 | Abnahme / Restblocker | Cloudflare-Offline-Suite läuft auf finalem HEAD |
| 51 | Abnahme / Restblocker | S-006-Gate darf im GitHub-CI nicht übersprungen werden |
| 52 | Abnahme / Restblocker | Logs, Gesamtsummen und Run-ID dokumentieren |
| 53 | Abnahme / Restblocker | Stacked-PR-Abhängigkeit auf MASTER 84 beibehalten |
| 54 | Abnahme / Restblocker | Unabhängiger Review und Konfliktprüfung bleiben offen |
| 55 | Abnahme / Restblocker | Keine Live-KI-, Cloudflare- oder Zahlungs-Aktivierung |
| 56 | Abnahme / Restblocker | Keine Modelle herunterladen und keine Produktivdaten bearbeiten |
| 57 | Abnahme / Restblocker | PID und lokales flock sind keine unabhängigen Beweise echter KI |
| 58 | Abnahme / Restblocker | Privilegierte Manipulationen von Elternverzeichnissen bleiben gesonderter Restpunkt |
| 59 | Abnahme / Restblocker | Kein Merge, kein Deploy, kein Auto-Delete |
| 60 | Abnahme / Restblocker | 0 € zusätzliche Kosten beibehalten |

## Vererbte Integration

Die MASTER-85-Änderung baut auf MASTER 84 mit dem verpflichtenden S-006-CI-Ref-Fetch auf. Dieser checkt die vier benannten historischen Branches einschließlich der unveränderten `origin/main`-Vergleiche. CI-Erfolg muss auf dem finalen MASTER-85-Commit nochmals verifiziert werden.

Parallel existieren weiterhin [PR #69](https://github.com/jefrey030/Schnapper/pull/69), [PR #80](https://github.com/jefrey030/Schnapper/pull/80) und [PR #90](https://github.com/jefrey030/Schnapper/pull/90) mit teilweise überlappenden Codeänderungen. Keine ungeprüfte automatische Integration.

## Sicherheits- und Beweisgrenzen

- Auf POSIX-Zielplattformen (Linux, Termux/Android, macOS) schützt der Patch den **geöffneten Lock-FD** gegen Symlink-, Hardlink- und Spezialdatei-Gefahren. Unter Windows wird dieser Ablauf nicht als unterstützt behauptet.
- Ein bösartiger oder privilegierter lokaler Akteur mit Kontrolle über den Prozess oder Elternordner könnte weitere Rennen oder Manipulationen herbeiführen. Die Sperre ist keine unabhängige Authentizitätsbestätigung.
- Eine PID-Datei, SHA256-Manifestdateien und rein synthetische MOCK-Tests beweisen weiterhin **keine vier echten KI-Inferenzantworten**.
- Alle Live-/PROD-Gates bleiben gesperrt: kein Modell-Download, kein Ollama-Dienst, keine Bezahl-API, kein Cloudflare-Deploy, kein manueller/automatischer Merge.

## Abnahmeregel

**CODE-GO** nur nach grüner Python- und Cloudflare-CI auf dem finalen Commit, einschließlich echtem S-006 `... ok` (kein `skipped`).  
**MERGE-GO / LIVE-GO:** offen, unabhängige Review und E2E-Test erforderlich.
