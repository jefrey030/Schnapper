# SCHNAPPER – Masterplan aller offenen Punkte

Stand: 22.10.2026, 10:50 (Berlin) · Basis: `main` @ 4bc37e7 · Erstellt nach echter Prüfung von Repo, PRs, Tests und Actions-Läufen.

**Regeln:** 0 € Zusatzkosten · nichts ungeprüft mergen · nichts ohne Freigabe veröffentlichen · keine erfundenen Ergebnisse.
**Status:** ✅ erledigt (mit Nachweis) · 🔨 in diesem PR · ⏳ wartet auf Jefrey · 🚫 blockiert · 💤 später

## A. App (was Nutzer sehen)

| Nr | Punkt | Status | Nachweis / nächster Schritt |
| --- | --- | --- | --- |
| A1 | Angebots-Kern: Preise prüfen, Dubletten, Suche, Import | ✅ | `main` @ 5343009 (#5) |
| A2 | Handy-Oberfläche im Browser | ✅ | `main` @ 7a0b83e (#10/#11), Browsertest 390×844 |
| A3 | Quellen-Register + Adapter (S-004/S-005) | ✅ | `main` @ 7a0b83e; Kleinanzeigen gesperrt, eBay gesperrt bis Freigabe |
| A4 | **Eigene echte Angebote** laden (Vorlage + Anleitung) | 🔨 | `app/vorlagen/meine-angebote.csv`, `docs/EIGENE-ANGEBOTE.md` |
| A5 | App auf den Startbildschirm (Web-App-Manifest, Icons) | 🔨 | Chromium: 0 Manifest- und 0 Installationsfehler |
| A6 | Start am Android-Handy ohne PC (Termux) | 🔨 | `docs/HANDY-START.md` – **auf echtem Gerät noch ungetestet** |
| A7 | App im Internet, ohne eigenes Gerät | ⏳ | Wäre eine Veröffentlichung → braucht Freigabe. Kostenlos möglich, aber Python-Server müsste dafür umgebaut werden. |
| A8 | Echte Angebote automatisch (eBay Browse API) | ⏳ | Jefrey: eBay-Entwicklerkonto + Produktivfreigabe bei eBay beantragen. Bis dahin nur eigene Listen (A4). |
| A9 | Preisverlauf, Benachrichtigungen, Konto | 💤 | Bewusst nicht im MVP (Konzept S-000) |

## B. Offene Pull Requests

| PR | Inhalt | Status | Nachweis / Empfehlung |
| --- | --- | --- | --- |
| #9 | Agentenstatus fail-closed | ✅ | gemergt 22.10. 10:35 |
| #6 | MASTER-Konzepte S-000–S-006 | ⏳ | **Konflikt mit main seit #9** in `team/agent.py`; getestete Lösung im Kommentar an #6 |
| #12 | Test-Fix für #6 (+ #7) | ⏳ | Nach #6 mergen; ohne ihn scheitern #6 + #7 zusammen (`platform`) |
| #7 | KI-Team lokal mit Ollama | ⏳ | grün; läuft nur, wenn eigener PC an ist |
| #8 | KI-Team auf Cloudflare (Live-Start gesperrt) | ⏳ | grün inkl. `node --test`; Live-Start nur mit Freigabe |
| #2 | altes lokales KI-Gehirn | ⏳ | **durch #7 überholt, hat Konflikte → schließen** |

**Probe-Merge aller offenen PRs** (main + #9 + #6 aufgelöst + #12 + #7 + #8): **106/106 Tests OK**.
**Empfohlene Reihenfolge:** #6 (Konflikt lösen) → #12 → #7 → #8 · #2 schließen.

## C. KI-Team (LEAD, BRAIN, CHECK, COMMAND)

| Nr | Punkt | Status | Nachweis / nächster Schritt |
| --- | --- | --- | --- |
| C1 | Stündliche Läufe auf GitHub | 🚫 | Seit 21.10. wurde **kein** Lauf ausgeführt. Ursache belegt (Job-Annotation): GitHub-Konto meldet fehlgeschlagene Zahlung / Ausgabenlimit. Workflows laufen seit 108509e absichtlich nur in öffentlichem Repo. |
| C2 | Laufzeit festlegen | ⏳ | Jefrey wählt: **(a)** Repo öffentlich → GitHub kostenlos, läuft ohne eigenes Gerät, Code sichtbar · **(b)** #7 → kostenlos, nur wenn PC an · **(c)** #8 → Cloudflare kostenlos, Freigabe nötig |
| C3 | Nachweis echter stündlicher Ausführung | 🚫 | Folgt erst nach C2 |
| C4 | Socket-Warnung in `tests/test_agenten.py` | 🔨 | `server_close()` ergänzt; strenger Testlauf ohne Warnung |

## D. Entscheidungen, die nur Jefrey treffen kann

1. **GitHub-Abrechnung prüfen** (*Settings → Billing and plans*): Warum ist das Konto gesperrt? Nichts Kostenpflichtiges freischalten.
2. **Laufzeit fürs KI-Team** wählen (C2: a, b oder c).
3. **PRs prüfen und mergen** in der Reihenfolge aus Abschnitt B.
4. **eBay-Zugang** beantragen – ja oder nein (A8).
5. **App öffentlich ins Internet** – ja oder nein (A7).

## E. Kosten
Bisher entstanden: **0 €**. Kein Punkt in diesem Plan erfordert Geld; A7, A8 und C2(c) nutzen nur kostenlose Stufen und brauchen trotzdem vorher deine Freigabe.
