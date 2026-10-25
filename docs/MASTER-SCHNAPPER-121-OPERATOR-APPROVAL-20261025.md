# MASTER 121 – SCHNAPPER: eigenständige lokale KI-Betreiberfreigabe

**Datum:** 25.10.2026 | **Basis:** Integrations-Draft #55 | **Modus:** Entwicklung/Offline-Tests | **Kosten:** 0 EUR | **Freigabe:** NO-GO

## Ausgangslücke und Ziel
In `team/local_service.py` wird `SCHNAPPER_KI_BACKEND=ollama` durch den Dienst selbst gesetzt. Das ist eine **Backend-Auswahl**, keine durch den Betreiber abgegebene Einwilligung. Wenn später eine Aufgabe geöffnet wird, könnte der Dienst damit einen Modellkontakt ohne separate Bedienhandlung starten. Master 121 setzt eine zusätzliche, standardmäßig fehlende lokale Zustimmungsschranke.

## Änderungen
- `team/operator_approval.py`: erlaubt nur eine **separat vom Betreiber vorbereitete lokale Datei** `team/work/operator_approval.json` mit `approved: true`, `scope: LOCAL_OLLAMA_ONLY`, `task_id`, `expires_at_utc`; max. 1 Stunde Restgültigkeit, UTC zwingend. Datei muss regulär sein, ohne Symlink/Hardlink, mit POSIX-Rechten nicht weiter als 0600 und passendem Dateieigentümer. Keine Secrets, keine externen Dienste.
- Dazu muss **genau eine** `open`-Aufgabe in `team/tasks.json` stehen und ihre ID mit der Einwilligung übereinstimmen. 0 oder mehr als 1 `open` => gesperrt.
- `team/local_service.py`: verweigert Agentenprozesse **vor** Laufordner-Erzeugung, wenn das Gate nicht besteht; unterbricht den `--loop`-Betrieb bei negativem Laufstatus statt ohne Zustimmung stündlich weiterzuprüfen.
- `team/local_ollama.py`: prüft Einwilligung beim Initialisieren, vor jedem `frage()` und direkt vor jedem `/api/chat`-HTTP-Kontakt. Änderungen/Not-Aus zwischen Rollen erfordern beim nächsten Kontakt eine neue positive Prüfung. Keine Caches.
- Alte rein deterministische Service-Fake-Tests mocken die Einwilligung **nur in ihrer eigenen Test-Fixture**; reale Negativtests prüfen den tatsächlichen Gate-Code.
- Offline-Regressionen für fehlende/falsche/abgelaufene Zustimmung, gefährliche Rechte, Symlink, verbotene Backend-Selbstfreigabe, falsche offene Aufgabe, STOP, direkte HTTP-Umgehung und Subprocess-Start.

## Konkrete Prüf- und Sicherheitsmatrix
1. Kein Approvalfile im Repository, kein File automatisch erzeugen.
2. Kein Modellstart bei fehlender expliziter Betreiberfreigabe.
3. Einmal/Loop und direktes KI-API-Gate dürfen Betreiberfreigabe nicht umgehen.
4. Kein Modellstart mit 0 oder mehrfachen offenen Aufgaben.
5. Keine Schlüssel, Download-, Cloud- oder Bezahl-KI-Aktivierung.
6. Keine Vergabe der Freigabe durch einen KI-Agenten selbst.
7. Alle Unit- und Offline-Tests auf finalem PR-HEAD tatsächlich ausführen; SKIP separat dokumentieren.
8. Python-CI, Cloudflare-CI und unabhängige Review getrennt abnehmen.
9. STOP jederzeit erneut prüfen; TOCTOU-Grenzen mit denselben lokalen Benutzerrechten ehrlich benennen.
10. Vor echten Modellkontakten: eigene gesonderte Betreiberaktion, kontrollierter Host-E2E, Review und Freigabe.

## Aktuell ausgeführte Entwicklungstests
Die **isolierte Modulfassung** vor GitHub-Integration wurde lokal mit Python-`unittest` ausgeführt: **13/13 Offline-Tests PASS**. Das beweist nicht die vollständige Regression auf dem gesamten finalen GitHub-Commit. Für GitHub-CI und Gesamtregression wird ein neuer Run auf dem finalen SHA geprüft. Ein lokal ausgelöstes Modell wurde **nicht** kontaktiert.

## Sicherheitsgrenzen
Die manuell bereitgestellte Freigabe-Datei ist **kein kryptographisch authentifiziertes menschliches Einverständnis**. Ein Angreifer mit Schreibrechten auf dieselben lokalen Dateien kann sie manipulieren. Für diesen Betriebsmodus werden lediglich versehentliche Starts und fehlende Betriebsfreigaben abgesichert; gegen lokale kompromittierte Accounts wäre eine externe vertrauenswürdige Bestätigung nötig. Auf Plattformen ohne `O_NOFOLLOW` wird aus Vorsicht blockiert.

**Kein Approvalfile wurde erstellt, kein echtes Ollama-Modell kontaktiert, keine Produktionsänderung, kein Merge. MASTER-121-PR bleibt Draft.**
