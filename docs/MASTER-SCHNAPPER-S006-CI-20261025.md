# SCHNAPPER – MASTER 7: Vollständige Branch-Abnahme S-006 ohne versteckten SKIP

**Stand:** 25.10.2026  
**Auftrag:** Bestehende S-006-Abnahme zuverlässig ausführen und verdeckte Lücken in der CI-Prüfung beseitigen.  
**Bezug:** Issue #82 (MASTER 75), Issue #56 (P0-Review), Sicherheitsentwurf #55.  
**Budget:** 0 € Zusatzkosten.  
**Modus:** Nur isolierter Branch, GitHub-CI/Offline-Tests. Keine Zusammenführung, kein Deployment.

## 1. Vor der Umsetzung geprüft

- Der Integrationsbranch enthält bisher `.github/workflows/tests.yml` ohne gesicherte volle Git-Historie oder Remote-Refs.
- `tests/test_branches_s006.py` überspringt die Branch-Prüfung bei fehlendem `origin/main`, ignoriert außerdem fehlende einzelne Kandidaten-Branches durch `continue`.
- CI kann dadurch `OK (skipped=1)` berichten, obwohl keine der vier Branch-Hygieneaussagen tatsächlich getestet wurde.
- Die vier in S-006 genannten Kandidaten-Branches wurden bei GitHub einzeln durch Branch-Suche nachgewiesen.
- Es besteht bereits Issue #82 mit dieser Aufgabe. **Kein neues paralleles Aufgaben-Issue nötig.** Der separate CI-Entwurf `fix/master75-ci-node24-ubuntu24-20261025` ändert die Actions-Version und Runnerumgebung, behebt aber nicht die Referenzversorgung oder die Skip-Logik; diese Arbeit erfolgt isoliert und greift nicht in dessen Branch ein.

## 2. Auf dem eigenen Branch implementiert

**Arbeitsbranch:** `fix/schnapper-s006-ci-refs-master7-20261025`, Basis `integration/schnapper-p0-mainbased-20261025`.

1. Python-CI checkt mit `fetch-depth: 0` die notwendige historische Commitkette aus.
2. Python-CI führt einen gezielten Git-Fetch für `origin/main` und exakt vier benötigte alte Branches aus; keine Abhängigkeit von einem zufällig vorhandenen lokalen Remote-Ref.
3. Checkout mit `persist-credentials: false`; keine neuen Tokens/Secrets/Berechtigungen.
4. S-006-Test sammelt alle benötigten Referenzen einschließlich Vergleichs-SHA `5343009`. Sobald eine Referenz in GitHub Actions fehlt, zählt das als FAIL anstatt SKIP oder Teil-PASS.
5. Ein Positivresultat erfordert die Prüfung aller vier Kandidaten.
6. Außerhalb der CI darf ein unvollständiger lokaler Checkout weiterhin ehrlich als `SKIP` ausgewiesen werden.
7. Zwei Regressionen prüfen, dass CI sowohl eine fehlende `origin/main` als auch eine fehlende Kandidatenreferenz ablehnt.

## 3. Abnahme

- `python -m unittest discover -s tests -v` auf exakt der finalen SHA ausführen.
- `cd cloudflare && node --test test/*.test.mjs` unverändert als Sicherheitsregression ausführen.
- `test_kandidaten_sind_vollstaendig_in_main` muss in GitHub-CI tatsächlich `ok` melden, ohne `skipped`.
- Die beiden neuen CI-Negativtests müssen `ok` melden.
- Keine Branch-Löschung, kein tatsächlicher Merge, kein Preisquellen- oder KI-Providerzugriff.
- Erfolg nur mit GitHub-Run-ID, Job-IDs, Testzahlen, HEAD-SHA und Rohlog; bis dahin `NOT_VERIFIED`.

## 4. Weitergeltende Freigabegrenzen

- Diese Branch-Hygieneprüfung bestätigt ausschließlich, dass die vier Kandidatenbranches unter den Testkriterien bereits Teil einer `main`-Historie bzw. inhaltlich redundant sind. Sie **löscht keine Branches** und erteilt keine Zustimmung dazu.
- Der Integrationsbranch ist weiterhin Draft. Die eigentliche KI-Laufzeit ist nicht live abgenommen. Secret-, Kosten-, Not-Aus-, Berechtigungs- und Datenschutzgates aus #55, #69, #74 bleiben unabhängig.
- Replit erhält diesen Auftrag nicht automatisch; GitHub-Issue/PR sind nur nachprüfbare Übergabepunkte.
- **NO-GO** für Merge, Produktion, Veröffentlichung, kostenpflichtige Dienste, Budgeterhöhung oder autonome Agenten bis ausdrücklicher Freigabe.
