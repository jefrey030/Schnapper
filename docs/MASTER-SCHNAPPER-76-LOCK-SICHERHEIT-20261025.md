# SCHNAPPER MASTER 76 – Crash-sichere Vier-KI-Sperre und Parallelstartschutz

**Datum:** 25. Oktober 2026  
**Repo:** jefrey030/Schnapper  
**Ausgangsbasis:** MASTER-75-Draft PR #85, Commit `2cb61b1f8a38541831d34372634685730c4e41ca`  
**Master-Branch:** `fix/master76-local-lock-recovery-20261025`  
**Priorität:** P0/P1  
**Budget:** 0 €  
**Betriebsfreigabe:** NO-GO, ausschließlich Review-Änderungen

## Mission

Ersetze den lokalen, gegen Prozessabstürze anfälligen `O_EXCL`-Dateiexistenzschutz
im Vier-KI-Dienst durch eine vom Betriebssystem verwaltete, nicht blockierende,
gegenseitig ausschließende Dateisperre. Der KI-Dienst darf einen bestehenden
Prozess nicht überholen und muss nach einem Crash ohne manuelles Entsperren
neu startbar sein, sofern keine aktive Sperre besteht.

## 24 Arbeitspunkte und Abnahmekriterien

| Nr. | Ziel | Nachweis-/Abnahmezustand |
|---|---|---|
| 01 | SCHNAPPER-Repo und aktuelle PR-Stackbasis feststellen | PR #55/#85 gelesen |
| 02 | Vorherigen CI-Stand verifizieren | Run #197 erfolgreich |
| 03 | Bestehende Lock-Implementierung lesen | `O_EXCL` + `unlink` bestätigt |
| 04 | Verwaiste Sperrdatei als Verfügbarkeitsrisiko identifizieren | Quellcodebefund |
| 05 | Parallele Ausführung als potentielles KI-Zähler-/Protokollrisiko priorisieren | Designprüfung |
| 06 | Eigenen Branch auf #85 erstellen | erledigt |
| 07 | Kein fremder Branch verändern | erfüllt |
| 08 | POSIX `flock` für Android/Termux, Linux, macOS einsetzen | umgesetzt |
| 09 | Nicht blockierenden Lock benutzen | `LOCK_EX | LOCK_NB` |
| 10 | Alte PID nicht als Berechtigung verwenden | umgesetzt |
| 11 | Sperrdatei nicht mehr löschen (Race vermeiden) | umgesetzt |
| 12 | File-Descriptor auch bei Fehler/Abbruch schließen | `finally` |
| 13 | Symlink-Folgen beim Öffnen soweit unterstützt verhindern | `O_NOFOLLOW` |
| 14 | Fehler beim sicheren Öffnen fail-closed behandeln | Rückgabecode 2 |
| 15 | Aktive Sperre fail-closed behandeln | Rückgabecode 2 |
| 16 | Bestehenden STOP-Datei-Not-Aus bewahren | `einmal()/--loop` unverändert |
| 17 | Keine externen Provider/Netzwerkaufrufe ergänzen | Quellcodeänderung ausschließlich Lock |
| 18 | Test: verwaiste Datei darf Pilot nicht blockieren | neuer Offline-Unit-Test |
| 19 | Test: aktive Sperre verhindert zweite Ausführung | neuer Offline-Unit-Test |
| 20 | Test: aufeinanderfolgende Ausführungen möglich | neuer Offline-Unit-Test |
| 21 | Test: Sperr-Symlink verweigern | neuer Offline-Unit-Test auf POSIX |
| 22 | Alle Python-Unit-Tests inklusive neuer Tests ausführen | **CI ausstehend beim Schreiben** |
| 23 | Cloudflare-Offline-Regressionen ausführen | **CI ausstehend beim Schreiben** |
| 24 | Unabhängiger Review, finaler Git-SHA, Mergeentscheidung | **ausstehend / NO-GO** |

## Prüfung und Grenzen

Der Lock ist bewusst **nicht** eine neue KI-Berechtigung. Ein erfolgreicher
`flock`-Erwerb berechtigt weder zu einem Modellaufruf noch zu Produktivaktionen.
Die separaten STOP-, Budget-, CHECK-, Secret- und Test-Gates gelten unverändert.

Im Gegensatz zu einem bloßen `O_EXCL`-Dateiexistenztest wird ein vom Kernel
gehaltenes Dateilock beim Schließen des Datei-Descriptors bzw. beim unerwarteten
Prozessende freigegeben. Die Lockdatei bleibt dauerhaft vorhanden, damit ein
zweiter Prozess nicht eine zwischenzeitlich neu angelegte Inode sperrt.

Die Implementierung ist explizit auf **POSIX-Systeme** (Linux, Termux/Android,
macOS) ausgerichtet. Für Windows ist eine separate Portierung erforderlich; hier
wird keine Windows-Kompatibilität behauptet.

**Technische Restgrenzen:** Eine unzuverlässige Network-Filesystem-Locksemantik
und Symlink-/Verzeichnis-Manipulationen durch andere Benutzer sind nicht
vollständig abgenommen. Es wurde kein realer Ollama-Dauerdienst, keine
gleichzeitige Mehrmaschinenbereitstellung und kein kostenloses oder bezahltes
Cloud-Modell in Betrieb genommen.

## Dokumentation tatsächlicher Arbeiten

- `team/local_service.py`: atomare lokale Sperre statt nicht wiederauflösbarer
  Exklusiv-Dateiexistenz; kein automatisches `unlink`.
- `tests/test_master76_lock.py`: vier getrennte Offline-Regressionen.
- Dieses Dokument: ausführbare Freigabe- und Stoppliste.
- GitHub-Tests zählen nur dann als Beleg, wenn Workflow-Run, finaler SHA,
  Status und Job-Logs übereinstimmen. Ein früherer Run ist kein Nachweis.

## Stoppsignale

NO-GO bei unbewiesenen 4 echten Antworten, falschen Checks, unvalidierten
Geheimnissen, roten Tests, unsicheren Dateirechten, unklaren Kosten, fehlenden
Logs oder ungewollten Änderungen an `main`. Keine Auto-Merge- oder Deploy-Freigabe.

## Referenzen

- Sicherheitsintegration: https://github.com/jefrey030/Schnapper/pull/55
- MASTER 75 / CI-Härtung: https://github.com/jefrey030/Schnapper/pull/85
- Bisheriger grüner CI-Run: https://github.com/jefrey030/Schnapper/actions/runs/40199595504
