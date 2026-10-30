# SCHNAPPER MASTER 30 — unabhängiges Release-Gate (30.10.2026)

Basis: PR #143, SHA `2be8e73e2d5e8d75c995780b4373609e8e298e39`, gestapelt auf #142 → #139. Dieser Branch ist ausschließlich eine Prüf-/Dokumentationsbasis, kein Release.

## Belegte Nachweise
- GitHub Actions https://github.com/jefrey030/Schnapper/actions/runs/40925465386 : python-tests Job 123629657963 **success**; cloudflare-tests Job 123629657640 **success**.
- PR #143 dokumentiert 690 Python-Tests, 32 CI-SKIPs, 25 Worker- und 6 UI-Speichertests; die Jobs sind über die GitHub-API als erfolgreich bestätigt. Keine Actions-Artefakte vorhanden.
- Main: `6dbe114271b332ed9d4c282b50c4ce02b112ac49`. PR #134 ist geschlossen, nicht gemergt.
- Legacy `.github/workflows/schnapper-hourly.yml` auf main: schedule, contents:write, model read, automatischer Push und Kosten-/Sichtbarkeits-Gate. Unverändert.

## Noch offene Freigabegates
| Gate | Status | Erforderlicher Beleg |
|---|---|---|
| Offline-Python/Worker/UI-Speicher | PASS (CI) | Exakter SHA und Job-Logs wie oben |
| LEAD/BRAIN/CHECK/COMMAND | BLOCKED | Vier echte, getrennte Modellantworten und Job-IDs, ohne Kosten |
| Browser-E2E | SKIP | Playwright/Chromium und vollständiger erfolgreicher Lauf |
| Android-E2E | BLOCKED | Echter Gerät-/Emulatorlauf |
| eBay-Live-/Sandbox-API | BLOCKED | Autorisierter Test ohne neue Kosten/Secrets |
| Unabhängiges Sicherheitsreview | BLOCKED | Signiertes/zuordenbares Review aller integrierten Änderungen |
| Repository-Sichtbarkeit | BLOCKED | Berechtigte Betreiberprüfung; niemals eigenmächtig ändern |
| ZENTNA #80/#82 | SKIP | Erst zulässige kostenlose read-only Voraussetzungen |
| Release/Merge/Deployment | NO-GO | Alle Gates und ausdrückliche Freigabe |

## Technische Reihenfolge
1. Prüfen, ob der gestapelte Branch alle fünf Module und die Sicherheitskorrekturen enthält; Konflikte gegen main separat auflisten.
2. Vollständige Regression auf exakt dem finalen Branch-HEAD erneut ausführen; keine übersprungenen Browser-/Android-Tests als PASS zählen.
3. Echte KI-Ausführung ausschließlich bei kostenloser, nachgewiesener und autorisierter Laufzeit; ansonsten BLOCKED.
4. Unabhängige Sicherheits- und Plattformabnahme; erst danach Betreiberentscheidung.

Keine Secrets, keine Kosten, keine Rechte-/Sichtbarkeitsänderung, kein Merge, kein Deployment, keine produktiven Daten.
