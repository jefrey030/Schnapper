# Freigegebene Arbeitsliste (Jefrey, 22.10.2026)
Ein Punkt ist erledigt, wenn er in main ist ODER ein offener Draft-PR des Teams (Branch agent/master/...) ihn laut letztem Bericht vollständig umsetzt. Pro PR genau ein Punkt, klein halten.
F1 Aufräumen (tasks.json S-004/S-005 done, S-006 done "überholt", F2–F6 als S-009–S-013 "open"; docs/SCHNAPPER-MASTERPLAN.md Abschnitt B PR-Tabelle auf GitHub-Stand). Nur team/ und docs/.
F2 Angebot direkt in der App erfassen (Formular, POST-Endpunkt mit X-Schnapper/Größenlimit, CSV-Download, Unit- und Browsertests 390x844).
F3 Merkliste/Preisalarme sichern und wiederherstellen (JSON, MAX_MERK/MAX_ALARME, Browsertest).
F4 Barcode per Kamera (BarcodeDetector, getUserMedia nur auf Knopfdruck, Browsertest mit Simulation).
F5 start-schnapper.sh für Android/Termux + docs/HANDY-START.md, Test startet Skript.
F6 eBay Browse-API-Adapter app/schnapper/ebay.py, gesperrt ohne Env-Schlüssel, docs/EBAY.md, Tests ohne Netz.
Konflikte: fremde PRs (z. B. #19) ändern app/schnapper/web. Vor jedem PR main frisch holen und rebasen/mergen; fremde Branches nie ändern.
Auswahlregel: offenen Team-Draft-PR fortsetzen > Aufgabe "open" in tasks.json > nächster offener Punkt F1–F6; erst wenn alles erledigt: neue Vorschläge "proposed".
Harte Sperren: kein Push auf main, kein Merge, kein Force-Push, kein Branch-Löschen auf GitHub, keine .github/workflows-Änderung, keine Live-Abrufe Open Prices/eBay, keine Secrets, 0 € Budget. Tabu: ZENTNA, JERRY AL, Beatmaster.
