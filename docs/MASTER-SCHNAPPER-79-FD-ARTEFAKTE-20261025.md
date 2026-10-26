# SCHNAPPER MASTER 79 – Verbindliche, symlink-sichere Pilotnachweise

**Stand:** 25. Oktober 2026  
**Repository:** `jefrey030/Schnapper`  
**Basis:** MASTER 78 / Draft PR #97, HEAD `39cf30439ad3fe787b641bcc05e360a8c567f79f`  
**Branch:** `fix/master79-no-follow-artifact-20261025`  
**Priorität:** P0 Schutz der Nachweisdateien; P1 ausführliche Offline-Regression  
**Budget:** 0 € Zusatzkosten, nur kostenlose Standard-CI im öffentlichen Repository  
**Freigabe:** DRAFT / NO-GO für `main`, Merge, Deployment, externe APIs, echten KI-Betrieb oder Produktionsdaten

## Festgestellte Lücke

MASTER 78 prüft `Path.is_symlink()` beziehungsweise `Path.is_file()` vor einem getrennten `read_bytes()`. Ein zwischen Prüfung und Öffnung ausgetauschter Symlink kann diesen zeitabhängigen Test unterlaufen. Außerdem wurden einzelne Rollenartefakte und `ki_aufrufe.txt` bei Fehlen aus der Manifestliste entfernt. Ein vollständiger Nachweis verlangt dagegen sämtliche sieben Pflichtdateien. 

## Korrektur

`team/local_service.py` verwendet `_hash_sicher(path)`: Die Datei wird mit `os.O_NOFOLLOW`, `os.O_NONBLOCK` und einem festen FD geöffnet und anschließend per `os.fstat` als reguläre Datei geprüft. Maximal 2.000.000 Bytes dürfen gelesen werden. Dabei werden alle sieben Artefakte ohne vorherige optionale Filterung aufgenommen: Stundenbericht, Prozessbericht, LEAD/BRAIN/CHECK/COMMAND und der lokale Aufrufzähler. Jede fehlende, zu große, ungeeignete oder unlesbare Datei bewirkt kontrolliert `BLOCKIERT`.

**Grenze:** Dies verhindert das Folgen eines Symlinks im finalen Dateielement beim Hash-Öffnen und reduziert gefährliche Dateitypen. Es ist **kein** kryptografisch unabhängiger Beweis für die Herkunft einer KI-Antwort; Verzeichnisaustausch, Manipulation durch einen berechtigten lokalen Akteur und Änderungen zwischen früherer fachlicher Prüfung und späterem Hash sind weiterhin getrennt zu betrachten.

## 28-Punkte-Arbeitsplan

| # | Aufgabe | Prüfkriterium |
| -: | --- | --- |
| 01 | GitHub-Repository verifizieren | `jefrey030/Schnapper` |
| 02 | MASTER 78 verifizieren | PR #97 und finalen HEAD lesen |
| 03 | Eigener Branch | Basis HEAD unverändert |
| 04 | Andere PRs isolieren | #55/#69/#80/#89/#94/#97 unberührt |
| 05 | Ursächlichen Symlink-Race identifizieren | Vorcheck und Öffnung getrennt |
| 06 | FD-basierte Leseoperation | `os.open` |
| 07 | Symlink-Folgen unterbinden | `O_NOFOLLOW` erforderlich |
| 08 | Nichtreguläre Dateien blockieren | `fstat` + `S_ISREG` |
| 09 | Blockierende FIFOs abweisen | `O_NONBLOCK` |
| 10 | Größe beschränken | 2.000.000 Bytes |
| 11 | Normaldatei korrekt hashen | SHA256 mit erwarteten Bytes |
| 12 | Gültigen Symlink abweisen | OSError/kein Dateiinhalt |
| 13 | Defekten Symlink abweisen | OSError |
| 14 | Austausch unmittelbar vor `open` abweisen | Symlink-Swap-MOCK |
| 15 | Falschen Pfadvorcheck ignorieren | FD-Öffnung entscheidend |
| 16 | Fehlende Datei abweisen | OSError |
| 17 | Verzeichnis abweisen | Nicht regulär |
| 18 | FIFO abweisen | Nicht regulär, kein Hänger |
| 19 | Zu große Datei abweisen | Größenlimit |
| 20 | Grenzwertdatei akzeptieren | Genau 2.000.000 Bytes |
| 21 | Flags kontrollieren | `O_NOFOLLOW` gesetzt |
| 22 | Alle sieben Artefakte verlangen | Bericht + Prozesse + vier Rollen + Zähler |
| 23 | I/O-Fehler in `einmal()` abfangen | BLOCKIERT + Exit 1 |
| 24 | MASTER-78-Testfixture anpassen | Fehler direkt am sicheren Hash-Leser simulieren |
| 25 | Bestehende Sicherungen erhalten | STOP, Lock, CHECK, Rollen-IDs |
| 26 | Unabhängigen CI-Test ausführen | GitHub Python + Cloudflare |
| 27 | Finalen HEAD gegen Logs kontrollieren | nicht nur alte grüne Runs |
| 28 | Unabhängigen Security-Review einholen | ohne Review: NO-GO |

## Nachweise / Weiteres

- `team/local_service.py` – sicherer regulärer Datei-Hash per FD und feste Pflichtliste.
- `tests/test_master78_process_evidence.py` – auf sichere Lesegrenze angepasster negativer I/O-Test.
- `tests/test_master79_artifacts.py` – elf weitere Offline-Testmethoden.
- `docs/MASTER-SCHNAPPER-79-FD-ARTEFAKTE-20261025.md` – diese Prüfliste.

**Stoppsignale:** Rote/übersprungene sicherheitsrelevante Tests, fehlende CI auf finalem HEAD, fehlende unabhängige Review, nachträgliche Änderungen am Branch oder unklare Kosten. Keine Automerges, keine Cloud-KI, keine Aktivierung einer echten Ollama-Instanz. MOCKs bleiben MOCKs.
