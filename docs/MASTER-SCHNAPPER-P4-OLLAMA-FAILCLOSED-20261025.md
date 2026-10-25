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
- [ ] Ausführung im bestehenden Draft verifiziert
- [ ] Katalog-/Counter-/Response-Fehler mit Fail-Closed behandelt
- [ ] Passende Negativtests ergänzt und grüner Positivtest erhalten
- [ ] Python- und Cloudflare-Tests auf finalem HEAD erfolgreich
- [ ] SHA, CI-Run, Anzahl der Tests, Einschränkungen dokumentiert
- [ ] Keine Live-KI, kein Deployment, keine Bezahldienste; Release NO-GO
