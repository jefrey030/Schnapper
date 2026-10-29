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
const alarmFunction = section("async function alarmAnlegen(", "function alarmQuery(");
const apiErrorFunctions = source.includes("function apiFehler(")
  ? section("function apiFehler(", "async function apiGet(")
  : section("async function apiPost(", "async function apiGet(");
const missionConflictFunctions = [
  source.includes("async function apiFehlerMeldung(")
    ? section("async function apiFehlerMeldung(", "async function missionAktion(") : "",
  section("async function missionSpeichern(", "function blitzMeldungen("),
].filter(Boolean).join("\n\n");

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

test("failed alarm persistence is never reported as created", async () => {
  const fields = new Map();
  let writes = 0;
  let checks = 0;
  const context = {
    $: (id) => {
      if (!fields.has(id)) fields.set(id, { textContent: "" });
      return fields.get(id);
    },
    aktuellerWunsch: () => ({ text: "synthetic search" }),
    alarme: () => [],
    wunschText: (value) => value.text,
    alarmQuery: () => "",
    MAX_ALARME: 10,
    fetch: async () => ({ ok: true }),
    speicher: {
      schreiben(name, value) {
        assert.equal(name, "alarme");
        assert.equal(value.length, 1);
        writes += 1;
        return false;
      },
    },
    alarmePruefen: () => { checks += 1; },
  };
  await vm.runInNewContext(`(async()=>{${alarmFunction}\nawait alarmAnlegen();})()`, context);
  const status = fields.get("status")?.textContent;
  assert.equal(writes, 1);
  assert.equal(checks, 0);
  assert.match(status, /Preisalarm nicht angelegt/);
  assert.match(status, /Speicherung fehlgeschlagen/);
  assert.doesNotMatch(status, /Preisalarm angelegt:/);
});

test("409 refreshes mission list, preserves form data, and never retries mutation", async () => {
  const fields = new Map();
  const formData = { id: "synthetic-mission", name: "Keep this input", suche: "synthetic search" };
  const originalFormData = structuredClone(formData);
  let postCount = 0;
  let refreshCount = 0;
  let resetCount = 0;
  const context = {
    $: (id) => {
      if (!fields.has(id)) fields.set(id, { textContent: "" });
      return fields.get(id);
    },
    fetch: async (path) => {
      assert.equal(path, "/api/missionen");
      postCount += 1;
      return {
        ok: false,
        status: 409,
        json: async () => ({ fehler: "synthetic conflict", aktualisieren: true }),
      };
    },
    missionDatenAusForm: () => formData,
    missionFormZuruecksetzen: () => { resetCount += 1; },
    missionenLaden: async () => { refreshCount += 1; return true; },
    renderMissionen: () => {},
    JSON,
  };
  await vm.runInNewContext(
    `${apiErrorFunctions}\n${missionConflictFunctions}\n;(async()=>{await missionSpeichern({preventDefault(){}});})()`,
    context,
  );
  const status = fields.get("mission-form-status")?.textContent;
  assert.equal(postCount, 1);
  assert.equal(refreshCount, 1);
  assert.equal(resetCount, 0);
  assert.deepEqual(formData, originalFormData);
  assert.match(status, /synthetic conflict/);
  assert.match(status, /Missionsliste wurde aktualisiert/);
  assert.match(status, /Eingaben bleiben erhalten/);
  assert.match(status, /nichts automatisch wiederholt/);
});
