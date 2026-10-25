# SCHNAPPER – GROSSMASTER 9: Lokaler Not-Aus während aktiver KI-Rolle

**Datum:** 25. Oktober 2026 · **Priorität:** P0 (Betriebssicherheit, Kostenkontrolle)  
**Repository:** `jefrey030/Schnapper` · **Basis:** Sicherheits-Draft #55 / `integration/schnapper-p0-mainbased-20261025`  
**Arbeitsbranch:** `fix/schnapper-stop-running-agent-master9-20261025`  
**Bestehendes zugehöriges Issue:** #87 (MASTER 79, lokaler Stundenbetrieb/STOP). Kein neues doppeltes Aufgaben-Issue.  
**Freigabestatus:** NO-GO für Produktion, Live-KI oder Merge · **Zusatzkosten:** 0 €.

## 1. Bestand / Befund vor dem Fix
Der lokale Scheduler in `team/local_service.py` startet LEAD, BRAIN, CHECK, COMMAND und BERICHT nacheinander über blockierende `subprocess.run(...timeout=240)`-Aufrufe. Er prüft die Datei `team/work/STOP` bisher nur zwischen zwei Rollen und in den Stunden-Wartezyklen. Wird STOP **während** einer Rolle gesetzt, kann deren Kindprozess ohne zusätzliche Überprüfung bis zu 240 Sekunden weiterlaufen; der aktuelle Modellaufruf kann sich fortsetzen. Dies wurde bei Codeinspektion festgestellt, ohne einen echten KI-Prozess zu starten.

Der separate Draft `fix/master76-local-lock-recovery-20261025` verbessert die abgestürzte Sperrdatei-/flock-Behandlung. Er beseitigt **nicht** die blockierende `subprocess.run`-STOP-Lücke und wird hier nicht geändert.

## 2. Großmaster – tatsächlich umgesetzte Codeänderung

### LEAD – Aufgaben- und Sicherheitspriorität
- Eng auf Not-Aus während aktiver Kindprozesse begrenzen.
- Bestehendes STOP-Verhalten vor neuen Rollen behalten.
- Kein Cloudflare-, Billing-, Tasks- oder GitHub-Actions-Betrieb verändern.
- Bericht `BERICHT` soll nach Abbruch soweit möglich den Ausfall dokumentieren; keine nächsten kostenrelevanten Rollen starten.

### BRAIN – technische Umsetzung
- Neue Hilfsfunktion `rolle_starten(...,stop_on_flag=True)` in `team/local_service.py` startet festen Python-Agenten direkt mit `subprocess.Popen`, ohne Shell.
- `communicate(timeout<=0.5)` ermöglicht regelmäßige STOP-Prüfung; bei STOP wird der Kindprozess mit `terminate()` beendet und gegebenenfalls mit `kill()` nach maximal zwei Sekunden nachbehandelt.
- Prozesslogs werden bei STOP **nicht** als positives oder ungefiltertes Teilergebnis übernommen; spezieller negativer Prozessstatus `-4`.
- Das bereits vorhandene `timeout=240`-Limit gilt weiter; am Timeout wird der Kindprozess beendet und der Lauf als fehlgeschlagen protokolliert.
- BERICHT benutzt `stop_on_flag=False` und kann Fehler protokollieren, selbst wenn der Betreiber-STOP aktiv ist.
- Startfehler (`OSError`) werden fail-closed mit negativem Status dokumentiert; niemals als erfolgreiche KI-Rolle gewertet.
- Nach Fehlschlag springen übrige kostenrelevante Agenten weiterhin aus.

### CHECK – zusätzliche Offline-Regressionen
- STOP während simuliert laufender Agentenrolle: Kindprozess terminiert, Code `-4`, keine Teil-Logs/erfundenes OK.
- Zeitüberschreitung: Kindprozess wird beendet, Timeout bleibt negativ.
- Nach aktivem STOP darf BERICHT in der Simulation noch sauber protokollieren.
- Stopp nach LEAD: BRAIN, CHECK und COMMAND starten nicht, `prozesse.json` enthält negative/übersprungene Rollen.
- Die vorherigen Unit-Test-Mocks wurden auf die neue Prozess-Hilfsfunktion umgestellt; Mock-Tests sind **keine** echten Ollama-Calls.

### COMMAND – Abnahme und Nachweise
1. `python -m unittest discover -s tests -v` auf dem letzten SHA; alle neuen Tests müssen im Original-CI-Log als `ok` stehen.
2. `cd cloudflare && node --test test/*.test.mjs` auf derselben SHA als unabhängige Regression.
3. Pass/Fail/Skip sauber zählen; kein SKIP als bestanden ausgeben.
4. Keine Behauptung, der bereits an Ollama übermittelte Request sei rückwirkend abgebrochen: Lokaler Prozess-Stopp kann **nicht** garantieren, dass das Modell auf einem separat laufenden Ollama-Server keine Arbeit zu Ende führt. Diese Grenze braucht spätere reale Pilotprüfung.
5. Privater/lokaler Host und echte Vier-KI-Laufzeit bleiben unbewiesen. Kein Merge nach main ohne unabhängigen Review und ausdrückliche Freigabe.

## 3. Risiken und ausstehende Gates
- Ein extern oder separat laufender Ollama-Server muss zusätzlich eigene Abbruch-/Budgetmechanismen haben; Prozess-Terminierung des Clients ist nicht gleich Provider-Billing-Stop.
- POSIX-Prozesskinder, die selbst weitere Prozesse starten, können einen Prozessgruppen-Abbruch oder gesonderte Orchestrierung benötigen. Dieser Master stoppt den **direkten Agenten-Kindprozess**.
- Der parallele Lock-Recovery-Draft darf später erst **mit Konfliktprüfung** zusammengeführt werden.
- `team/tasks.json` ist derzeit ohne freigegebene offene Aufgaben, und die allgemeine Vier-Agenten-Inbetriebnahme bleibt gesperrt.
- Kein Freischalten des alten GitHub-Models-Backends, der Cloudflare-KI oder produktiver Preisquellen.

## 4. Harte Grenzen
**0 € zusätzliche Kosten.** Keine bezahlten APIs, Modell-Downloads, aktivierten Cloud-Dienste, echten Modellanfragen, Passwörter/Secrets, echten Preisangebote, Commits nach `main`, Merges, Releases, Deployments, Branchlöschungen, Billing-/Repo-Sichtbarkeitsänderungen. Nur Offline-Tests und isolierter Draft. Ein GitHub-Issue oder Pull Request startet Replit nicht automatisch.

**Freigabestatus:** CODED – CI/Review anhand des aktuellen HEAD separat nachweisen. Produktion NO-GO.
