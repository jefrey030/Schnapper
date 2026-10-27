import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import vm from "node:vm";

const appPath = new URL("../app/schnapper/web/app.js", import.meta.url);
const source = await readFile(appPath, "utf8");

function section(start, end) {
  const from = source.indexOf(start);
  const to = source.indexOf(end, from);
  assert.notEqual(from, -1, `missing source marker: ${start}`);
  assert.notEqual(to, -1, `missing source marker: ${end}`);
  return source.slice(from, to).trim();
}

const functions = [
  section("function blitzMeldungen(", "function renderBlitz("),
  section("async function missionLauf(", "function renderMissionLaeufe("),
].join("\n\n");

async function runWithFailedWrites(failedNames) {
  const fields = new Map();
  const saved = [];
  const context = {
    $: (id) => {
      if (!fields.has(id)) fields.set(id, { textContent: "", hidden: false });
      return fields.get(id);
    },
    apiPost: async () => ({
      job_id: "synthetic-job",
      abgeschlossen_am: "2026-10-27T12:00:00.000Z",
      treffer: [{ id: "synthetic-offer" }],
      meldungen: [{
        id: "a".repeat(64),
        titel: "Synthetic offer",
        wunsch: "Synthetic",
        gesamtpreis: 12,
        url: "https://offers.example/item",
        quelle: "synthetic",
        erstellt_am: "2026-10-27T12:00:00.000Z",
      }],
      beispieldaten: true,
    }),
    gespeicherteErgebnisse: () => ({}),
    blitzQueue: () => [],
    euro: { format: (value) => String(value) },
    speicher: {
      schreiben(name, value) {
        saved.push({ name, value });
        return !failedNames.has(name);
      },
    },
    missionLaeufe: () => [],
    missionenLaden: async () => {},
    renderMissionLaeufe: () => {},
    laufendeMissionen: new Set(),
    MAX_BLITZ: 300,
    window: { Notification: { permission: "default" } },
    Date,
    Set,
    Boolean,
    Number,
    Error,
    encodeURIComponent,
  };
  vm.runInNewContext(`${functions}\nmissionLauf("synthetic-mission", false);`, context);
  await new Promise((resolve) => setImmediate(resolve));
  return { status: fields.get("mission-form-status")?.textContent, saved };
}

for (const failedName of ["mission-ergebnisse", "blitz", "mission-laeufe"]) {
  test(`failed ${failedName} persistence is never reported as saved`, async () => {
    const { status, saved } = await runWithFailedWrites(new Set([failedName]));
    assert.ok(saved.some((entry) => entry.name === failedName));
    assert.match(status, /Speicherung fehlgeschlagen/);
    assert.doesNotMatch(status, /\(lokal gespeichert\)/);
    assert.match(status, new RegExp(failedName === "mission-ergebnisse"
      ? "Ergebnisse" : failedName === "mission-laeufe" ? "Laufprotokoll" : "BLITZ"));
  });
}

test("success is reported only after all three browser stores succeed", async () => {
  const { status, saved } = await runWithFailedWrites(new Set());
  assert.deepEqual(saved.map((entry) => entry.name),
    ["mission-ergebnisse", "blitz", "mission-laeufe"]);
  assert.match(status, /\(lokal gespeichert\)/);
});
