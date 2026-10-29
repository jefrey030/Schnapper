# MASTER 4 – P0-Korrekturen, 26.10.2026

Eigener Zweig `fix/master4-p0-stop-paths-20261026`, Ausgangsbaum von PR #126. Replits Dateien und Zweige unverändert. Kein Merge, Deployment oder kostenpflichtiger Dienst.

## Änderungen

- `team/local_service.py`: eigene POSIX-Prozesssession; STOP und Timeout signalisieren die gesamte Prozessgruppe, auch nach Ende des direkten Elternprozesses. Abschließendes Lesen/Warten ist begrenzt. Erfolgreiche Rollen hinterlassen keine Prozesse derselben Gruppe.
- `team/safe_artifacts.py`: Verzeichniskomponenten werden mit verankerten FDs und O_NOFOLLOW geöffnet; atomare private Ausgabedateien; begrenzte Reads nur regulärer Dateien.
- `team/agent.py`: Rollenbelege, BRAIN-Vorschläge und Berichte verwenden sichere Dateizugriffe. Der CLI-Eingang löst Symlinks nicht mehr vor der Prüfung auf.

## Ausgeführte Prüfung

- `python -m unittest discover -s tests`: **482 Tests, OK**, 17,882 Sekunden.
- `cd cloudflare && node --test test/*.test.mjs`: **16 bestanden**, 0 Fehler, 0 Skips.
- Fünf neue Regressionen: Verzeichnis-/Dateisymlinks, atomarer Austausch eines Dateilinks ohne Änderung seines Ziels, STOP mit TERM-ignorierendem Nachkommen, STOP nach Ende des Elternprozesses, Timeout mit Nachkommen. Reale lokale harmlose Prozesse, keine Modellaufrufe.
- `git diff --check`: bestanden.
- PR #127: GitHub-Lauf 40373007155 abgeschlossen mit success auf 1b25970eefe8d12a4f5a04fbbb56d92c3c32b512.

## Offene Grenzen – keine Sicherheitsfreigabe

Ollama ist lokal nicht installiert/erreichbar (127.0.0.1:11434/api/tags: URLError). Kein echter Vier-KI-Lauf. Ein separater Modellserver wird durch Prozessgruppen nicht abgebrochen. Absichtlich aus der Gruppe ausbrechende Prozesse benötigen OS-Isolation/cgroups; diese Korrektur ist keine Sandbox gegen beliebigen feindlichen Code. Verschieben bereits geöffneter Verzeichnisse durch gleichberechtigte fremde Prozesse benötigt ebenfalls weitergehende OS-Isolation.

Die neuen Korrekturen sind lokal geprüft; keine neue GitHub-CI für diese Änderungen und kein unabhängiger Review. App-/Android-Endabnahme bleibt offen. Kein Upload dieser zusätzlichen Korrekturen: Die bisherige ausdrückliche Freigabe betraf den geprüften Integrationsstand; weitere Veröffentlichungen waren ausgenommen.

Nachtrag: Die anschließende ausdrückliche Upload-Freigabe und aktualisierte Restabnahme stehen in `P0-ENDABNAHME-20261026.md`. Die frühere Upload-Sperre beschreibt nur den damaligen Stand.
