# Freigegebene Arbeitsliste (Jefrey, 22.10.2026)
Ein Punkt ist erledigt, wenn er in main ist ODER ein offener Draft-PR des Teams (Branch agent/master/...) ihn laut letztem Bericht vollständig umsetzt. Pro PR genau ein Punkt, klein halten.
F1 Aufräumen: team/tasks.json S-004/S-005 done, S-006 done "überholt"; F2–F6 als S-009..S-013 "open"; docs/SCHNAPPER-MASTERPLAN.md Abschnitt B (PR-Tabelle) auf echten GitHub-Stand. Nur team/ und docs/.
F2 Angebot direkt in der App erfassen (Formular, Quelle "eigene", serverseitige Prüfung, nur Arbeitsspeicher, CSV-Download, POST mit X-Schnapper + Größenlimit, textContent). Unit- + Browsertest 390x844.
F3 Merkliste/Preisalarme sichern/wiederherstellen (JSON), MAX_MERK/MAX_ALARME prüfen, ungültige melden.
F4 Barcode per Kamera (BarcodeDetector ean_13/ean_8/upc_a + getUserMedia), nur auf Knopfdruck, sofort stoppen, CSP minimal.
F5 start-schnapper.sh für Termux, docs/HANDY-START.md, "auf echtem Gerät ungetestet".
F6 eBay-Adapter (Browse API, OAuth Client-Credentials aus Umgebungsvariablen, Sandbox Standard, gesperrt ohne Schalter+Schlüssel), docs/EBAY.md. Keine echten Netzaufrufe in Tests.
Harte Sperren: kein Push auf main, kein Merge, kein Force-Push, keine Branch-Löschung, kein Deploy, keine Änderung an .github/workflows, keine Repo-Einstellungen, keine Live-Abrufe externer Preisquellen, keine Secrets, 0 € Budget. Fremde Branches nie ändern. Tabu: ZENTNA, JERRY AL, Beatmaster.
Auswahlregel: offener Team-Draft-PR fortsetzen > Aufgabe "open" in tasks.json > nächster offener Punkt F1–F6; erst wenn alles erledigt: neue Vorschläge "proposed".
