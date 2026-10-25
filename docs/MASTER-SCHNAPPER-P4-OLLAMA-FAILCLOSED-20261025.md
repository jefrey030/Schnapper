# MASTER P4 – SCHNAPPER: Ollama Fail-Closed, Kostenlimit und Antwortvalidierung

**Datum:** 25.10.2026 · **Ziel:** [Sicherheits-Draft #55](https://github.com/jefrey030/Schnapper/pull/55) · **Budget:** 0 € zusätzliche Kosten · **Freigabe:** NO-GO

## 1. Gesamtauftrag
Die bestehende lokale Ollama-Anbindung isoliert und ohne echte Modellinferenz auf problematische Zustände prüfen. Unstrukturierte Modellantworten, beschädigte Modellkataloge und manipulierte lokale Aufrufzähler dürfen weder als erfolgreicher Vier-KI-Nachweis erscheinen noch die dokumentierte harte Kosten-/Aufrufgrenze umgehen.

## 2. Verifizierte Befunde bei Start
- `team/local_ollama.py::_pruefe_modell` nimmt `v.get("name")` direkt in ein Set auf. Nicht hashbare Namen (z. B. Listen oder Objekte) erzeugen einen unkontrollierten `TypeError`.
- `team/local_ollama.py::_zaehle` lässt negative bereits gespeicherte Aufrufzahlen und sehr große Counter-Dateien ohne ausdrückliche Validierung zu.
- `team/local_ollama.py::_request` parst JSON, prüft aber nicht, ob die erwartete Serverantwort ein Objekt ist; ungültige Response-Typen können später zu nicht kontrolliertem Laufabbruch führen.
- `KI.frage` erwartet ein String-`content`, aber es fehlen explizite Antwortgrößenkontrolle und feste Strukturprüfung für jeden negativen Typfall.
- Der Adapter bleibt **ausschließlich lokal** auf `127.0.0.1:11434` festgelegt, ohne Proxy oder Weiterleitungen. Keine Cloud-/Provider-Anbindung, kein Modell-Download.

## 3. Vier Prüfrollen, keine behaupteten autonomen KIs

| Rolle | Konkreter Auftrag | Nachweis |
| --- | --- | --- |
| LEAD | Repository-Stand, Kostenregel und bestehende Testabdeckung feststellen | PR #55 und SHA |
| BRAIN | Fail-Closed für Katalog, Counter, Antwort und JSON-Typen implementieren | Commit auf vorhandenen Branch |
| CHECK | Negative Offline-Tests mit Mocks; bestehende positive KI-Fixture erhalten | GitHub Actions mit exakter SHA |
| COMMAND | Testzahlen, finale SHA, Abnahme und Restblocker kommentieren | GitHub-Kommentare/CI-Link |

## 4. Geltende Grenzen
1. **Nie** `main` verändern, mergen, PRs schließen oder Kosten auslösen.
2. Modellliste enthält nur bestätigte String-Namen. Ungültige Typen und fehlendes Modell führen zur dokumentierten `KINichtVerfuegbar`.
3. Aufrufzähler darf nicht negativ, korrupt, übergroß oder über dem festen Budget sein; Symlinks sind kein vertrauenswürdiger Counterbeleg.
4. Nur dict-basierte, begrenzte Modellantworten; fehlender, nicht-textueller und überlanger Inhalt wird ohne Erfolgseintrag blockiert.
5. Tests nutzen `unittest.mock`, keine echte Ollama-Inferenz, keine fremden APIs oder Downloads.
6. Repo `main` und der Legacy-Stundenworkflow bleiben ohne separate Review-/Merge-Freigabe **unverändert**.

## 5. Abnahmecheckliste
- [x] Ausführung im bestehenden Draft #55 verifiziert
- [x] Katalog-/Counter-/Response-Fehler mit Fail-Closed behandelt
- [x] Sechs neue Negativ-Testfunktionen ergänzt, vorhandener positiver Ollama-Mocktest bleibt grün
- [x] Code-HEAD `bd3bb0b6e878f52f94bcd68ca282aef3db88ad49` erfolgreich geprüft: [GitHub Actions #40213052241](https://github.com/jefrey030/Schnapper/actions/runs/40213052241)
- [x] SHA, CI-Run, 277 Python-Tests (1 SKIP) und 16/16 Cloudflare-Tests dokumentiert; Dokumentationscommit erhält eigenen CI-Nachweis
- [x] Keine Live-KI, kein Deployment, keine Bezahldienste; Release NO-GO

## 6. Wirklich ausgeführte Änderungen

### `team/local_ollama.py`
1. Die `/api/tags`-Modellliste wird ohne Umwandlung untrusted `name`-Felder in hashbasierte Container geprüft; List-/Dict-Namen führen zu kontrolliertem Fehlschlag statt `TypeError`.
2. Die Ollama-HTTP-Funktion erwartet ein JSON-Objekt; gültige JSON-Skalare oder Listen werden als ungültige Protokollantwort blockiert.
3. Der lokale Aufrufzähler akzeptiert nur einen nichtnegativen kleinen Integer und ein Budget von 1–6, begrenzt Dateigrößen, lehnt symbolische Links ab und fängt Schreibfehler als `KINichtVerfuegbar` ab. Erfolgt ein später fehlerhafter Modellversuch, bleibt der vorab gezählte Versuch verbraucht.
4. KI-Antworten erfordern tatsächlichen Text, enthalten maximal 12.000 Zeichen und werden bei leeren, fehlenden, nicht textuellen oder übergroßen Inhalten verweigert. Die festen localhost-/Proxy-/Redirect-Grenzen bleiben erhalten.

### `tests/test_local_ollama.py`
Sechs zusätzliche unabhängige Offline-Testfunktionen für ungültige JSON-Wurzeltypen, gemischte/kaputte Modellkataloge, negativen/defekten/zu großen Zähler, zu hohe konfigurierte Limits, Symlink-Zähler und fehlerhafte/übergroße Antwortinhalte. Alle Tests verwenden synthetische Daten und `unittest.mock`. Keine echten Modellaufrufe, Netzwerkzugriffe oder Downloads.

### Reproduzierbarer Nachweis
**Getestete Code-SHA:** `bd3bb0b6e878f52f94bcd68ca282aef3db88ad49`; [GitHub Actions #40213052241](https://github.com/jefrey030/Schnapper/actions/runs/40213052241): `python-tests` **277 ausgeführt (1 SKIP), 0 Fehler**; `cloudflare-tests` **16/16 bestanden, 0 SKIP, 0 Fehler**. Beide Jobs `success`.

### Nicht erreicht / verbleibende Release-Sperren
Die sechs Testfunktionen beweisen die offline getesteten Schutzregeln, **nicht** die Verfügbarkeit eines realen lokalen Modells, eine kryptografische KI-Antwort-Authentifizierung oder einen produktiven Vier-KI-Stundenlauf. Ungeprüfte fremde Systeme/Finanzdaten wurden nicht abgefragt. Draft #55 ist noch nicht nach `main` gemergt; dessen Legacy-Stundenworkflow wird durch diese Draft-Änderungen nicht abgeschaltet. Unabhängige Code-/Sicherheitsreview, reale Testumgebung und ausdrückliche Betreiberfreigabe bleiben notwendig. **NO-GO Produktivbetrieb.**
