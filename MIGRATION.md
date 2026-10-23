# GitHub-Umzug: SCHNAPPER ONE als eigenes Repository

Der aktuelle Verbund aus einem eigenen Projektzweig und einem separaten
Projektverzeichnis ist für die Vorbereitung geeignet, **aber noch kein eigenes
GitHub-Repository**. Der verbundene GitHub-Zugang kann im aktuellen Chat
kein Repository anlegen.

## Auslieferbarer, reiner Projektstand

Im Repository `jefrey030/Schnapper` gibt es den Zweig
`export/schnapper-one-standalone`. Dieser Branch enthält im Arbeitsbaum
**ausschließlich** SCHNAPPER ONE, nicht den App-Code des Hauptprojekts.
Achtung: Die Git-Commit-Historie dieses Zweigs hat weiterhin die ursprüngliche
SCHNAPPER-Historie als Vorfahren; für wirklich unabhängige Historie nur die
Dateien (ohne Git-Historie) in ein neues Repository kopieren.

### Empfohlener Weg

1. Auf GitHub ein **leeres Repository `schnapper-one`** erstellen. Es sollte
   nicht automatisch einen README/License/.gitignore-Commit erhalten.
2. Dem bestehenden ChatGPT-GitHub-Zugang explizit Zugriff auf
   `schnapper-one` geben; Zugriff auf andere Repositories bleibt unverändert.
3. Danach nur den SCHNAPPER-ONE-Dateibaum, **ohne Historie** von
   `export/schnapper-one-standalone`, als neue Dateien in das neue Repo kopieren.
4. CI laufen lassen und **6/6 Offline-Tests** dort erneut bestätigen.
5. `SCHNAPPER_ONE_KI_ENABLED` weiter ausgeschaltet lassen, bis GitHub-Models-
   Kostenfreigrenzen und Sicherheit geprüft sind. Vier echte Modellantworten
   und CHECK-/COMMAND-Protokolle im manuell ausgelösten Pilot nachweisen.

**Kein Merge** dieses Exportzweigs in den bisherigen `main`-Branch von
SCHNAPPER: Er soll nur beim Repository-Umzug helfen.

## Nachweisgrenzen

- Vier Agenten als Code: vorbereitet
- Vier Agenten im Offline-Simulationstest: bestanden
- Vier echte KI-Antworten: noch nicht nachgewiesen
- KI-Kostenkonto: nicht verifiziert
- Laufender Stundenplan: absichtlich nicht vorhanden
- Premium-/KI-Abonnements: Konzept, noch keine Abrechnung
