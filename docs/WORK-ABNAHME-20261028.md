# SCHNAPPER — unabhängiger Offline-Nachtest, 28.10.2026

Geprüfter Produktcode: #134, `6c66d2a225595267c5e5ce4b593a66bc129dc0cb`.

- Vollständiger Git-Checkout des exakten Heads.
- Erster Python-Lauf: 533 PASS, 1 FAIL. Ursache: flacher Checkout ohne die für S-006 verlangten Remote-Refs, keine Produktassertion fehlgeschlagen.
- Vollständige Historie und Remote-Branchrefs nachgeladen. Unveränderte vollständige Python-Suite erneut ausgeführt: 534 PASS, 0 FAIL, 0 SKIP, `GITHUB_ACTIONS=true`, Python 3.12.14 mit `-X dev -W error`.
- Worker-/UI-Speicherregressionen: 22 PASS, 0 FAIL, 0 SKIP, Node 24.22.1.
- Produktcode unverändert. Neue eigene Rohprotokolle unter `docs/evidence/work-20261028/`.

Die aktuelle Dokumentation ordnet die 13 früheren #130/#132-Speichertests ihren Nachfolgern zu. Im aktuellen Vertrag führen veraltete Revisionen zu einem ausdrücklichen Konflikt; erst bewusstes Neuladen/Retry erhält weitere Änderungen. Es wurde kein älterer Speichercode zurückkopiert.

Keine eigene Browser-/Android-/Livepreis-/Vier-Modell-Abnahme in dieser Runde. Chromium/adb/Emulator und lokale Modellgewichte nicht nachgewiesen. Legacy-Stundenworkflow auf main unverändert; Stilllegung bereits in #131 und diesem Entwicklungszweig vorbereitet. Diese Nachprüfung ist keine Betreiberfreigabe oder Produktionsfreigabe. Kein Merge, Deployment, Provideraufruf oder Budgetwechsel.
