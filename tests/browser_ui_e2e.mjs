import assert from "node:assert/strict";
import { mkdir, readdir, readFile, rm, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";

const baseUrl = process.env.SCHNAPPER_TEST_URL || "http://127.0.0.1:8791";
const cdpUrl = process.env.SCHNAPPER_CDP_URL || "http://127.0.0.1:9222";
const fixturePath = path.join(os.tmpdir(), "schnapper-browser-ui-fixture.json");
const downloadDir = process.env.SCHNAPPER_DOWNLOAD_DIR
  || path.join(os.tmpdir(), "schnapper-browser-ui-downloads");

const offer = [{
  id: "ui-camera",
  titel: "Synthetische Kamera",
  preis: "80",
  versand: "4",
  url: "https://offers.example/ui-camera",
  quelle: "eigene",
  erfasst_am: new Date().toISOString(),
  region: "Berlin",
  entfernung_km: "12",
  referenzpreis: "100",
}];
await writeFile(fixturePath, JSON.stringify(offer));
await rm(downloadDir, { recursive: true, force: true });
await mkdir(downloadDir, { recursive: true });

const targetResponse = await fetch(`${cdpUrl}/json/new?${encodeURIComponent(baseUrl)}`, { method: "PUT" });
assert.equal(targetResponse.status, 200, "Chrome DevTools endpoint must be available.");
const target = await targetResponse.json();
const socket = new WebSocket(target.webSocketDebuggerUrl);
const pending = new Map();
const observedEvents = [];
let nextId = 0;
let auxiliaryPage;

await new Promise((resolve, reject) => {
  socket.addEventListener("open", resolve, { once: true });
  socket.addEventListener("error", reject, { once: true });
});
socket.addEventListener("message", ({ data }) => {
  const message = JSON.parse(data);
  if (message.id && pending.has(message.id)) {
    const waiter = pending.get(message.id);
    pending.delete(message.id);
    if (message.error) waiter.reject(new Error(message.error.message));
    else waiter.resolve(message.result);
  } else observedEvents.push(message);
});

function cdp(method, params = {}) {
  const id = ++nextId;
  return new Promise((resolve, reject) => {
    pending.set(id, { resolve, reject });
    socket.send(JSON.stringify({ id, method, params }));
  });
}

async function evaluate(expression) {
  const result = await cdp("Runtime.evaluate", {
    expression,
    awaitPromise: true,
    returnByValue: true,
    userGesture: true,
  });
  if (result.exceptionDetails) {
    throw new Error(result.exceptionDetails.exception?.description
      || result.exceptionDetails.text);
  }
  return result.result.value;
}

async function waitFor(expression, predicate, description, timeoutMs = 10_000) {
  const deadline = Date.now() + timeoutMs;
  let value;
  while (Date.now() < deadline) {
    value = await evaluate(expression);
    if (predicate(value)) return value;
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  throw new Error(`Timed out waiting for ${description}; last value: ${JSON.stringify(value)}`);
}

async function uploadFixture(selector, filePath = fixturePath) {
  const { root } = await cdp("DOM.getDocument", { depth: -1 });
  const { nodeId } = await cdp("DOM.querySelector", { nodeId: root.nodeId, selector });
  assert.ok(nodeId, `file input ${selector} exists`);
  await cdp("DOM.setFileInputFiles", { files: [filePath], nodeId });
  await evaluate(`document.querySelector(${JSON.stringify(selector)}).dispatchEvent(new Event("change", { bubbles: true }))`);
}

async function openAuxiliaryPage(url) {
  const response = await fetch(`${cdpUrl}/json/new?${encodeURIComponent(url)}`, { method: "PUT" });
  assert.equal(response.status, 200, "Chrome must create a second isolated browser tab.");
  const auxiliaryTarget = await response.json();
  const auxiliarySocket = new WebSocket(auxiliaryTarget.webSocketDebuggerUrl);
  const auxiliaryPending = new Map();
  const auxiliaryEvents = [];
  let auxiliaryId = 0;
  await new Promise((resolve, reject) => {
    auxiliarySocket.addEventListener("open", resolve, { once: true });
    auxiliarySocket.addEventListener("error", reject, { once: true });
  });
  auxiliarySocket.addEventListener("message", ({ data }) => {
    const message = JSON.parse(data);
    if (message.id && auxiliaryPending.has(message.id)) {
      const waiter = auxiliaryPending.get(message.id);
      auxiliaryPending.delete(message.id);
      if (message.error) waiter.reject(new Error(message.error.message));
      else waiter.resolve(message.result);
    } else auxiliaryEvents.push(message);
  });
  function auxiliaryCdp(method, params = {}) {
    const id = ++auxiliaryId;
    return new Promise((resolve, reject) => {
      auxiliaryPending.set(id, { resolve, reject });
      auxiliarySocket.send(JSON.stringify({ id, method, params }));
    });
  }
  async function auxiliaryEvaluate(expression) {
    const result = await auxiliaryCdp("Runtime.evaluate", {
      expression,
      awaitPromise: true,
      returnByValue: true,
      userGesture: true,
    });
    if (result.exceptionDetails) {
      throw new Error(result.exceptionDetails.exception?.description || result.exceptionDetails.text);
    }
    return result.result.value;
  }
  await auxiliaryCdp("Page.enable");
  await auxiliaryCdp("Runtime.enable");
  await auxiliaryCdp("Network.enable");
  await auxiliaryCdp("Page.navigate", { url });
  const deadline = Date.now() + 10_000;
  while (Date.now() < deadline) {
    if (await auxiliaryEvaluate("document.readyState") === "complete") break;
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  return {
    target: auxiliaryTarget,
    socket: auxiliarySocket,
    events: auxiliaryEvents,
    cdp: auxiliaryCdp,
    evaluate: auxiliaryEvaluate,
  };
}

async function clickView(name) {
  await evaluate(`document.querySelector('[data-ansicht="${name}"]').click()`);
}

try {
  await cdp("Page.enable");
  await cdp("Runtime.enable");
  await cdp("DOM.enable");
  await cdp("Storage.clearDataForOrigin", {
    origin: new URL(baseUrl).origin,
    storageTypes: "all",
  });
  await cdp("Emulation.setDeviceMetricsOverride", {
    width: 360, height: 800, deviceScaleFactor: 1, mobile: true,
  });
  await cdp("Browser.setDownloadBehavior", { behavior: "allow", downloadPath: downloadDir });
  await cdp("Page.navigate", { url: baseUrl });
  await waitFor("document.readyState", (v) => v === "complete", "page load");

  const modules = await evaluate(
    `[...document.querySelectorAll(".ansichten button")].map((b) => b.textContent.trim().split(" ")[0])`,
  );
  for (const moduleName of ["LUPE", "WARENKORB", "PREISDETEKTIV", "BLITZ", "MISSION"]) {
    assert.ok(modules.includes(moduleName), `UI module ${moduleName} is present`);
  }
  console.log("PASS browser UI exposes LUPE, WARENKORB, PREISDETEKTIV, BLITZ, MISSION at 360x800");

  await uploadFixture("#datei");
  await waitFor(
    "document.querySelector('#status').textContent",
    (v) => v.includes("1 Treffer aus 1 Angeboten"),
    "synthetic offer upload",
  );
  await evaluate("document.querySelector('#treffer .merken').click()");
  await waitFor(
    "JSON.parse(localStorage.getItem('schnapper.browser-state.v1')).values.merkliste",
    (v) => v && Object.keys(v).length === 1,
    "local WARENKORB persistence",
  );
  await clickView("merkliste");
  await waitFor(
    "document.querySelectorAll('#merk-liste > li').length",
    (v) => v === 1,
    "WARENKORB card",
  );
  await evaluate("document.querySelector('#merk-liste .vergleich-check').click(); document.querySelector('#vergleich-starten').click()");
  await waitFor(
    "document.querySelectorAll('#preisvergleich article').length",
    (v) => v === 1,
    "PREISDETEKTIV result",
  );
  console.log("PASS LUPE upload/search, WARENKORB save, PREISDETEKTIV comparison");

  async function createMission(name, maxPrice, automatic = false) {
    const expectedCount = await evaluate("document.querySelectorAll('#mission-liste .mission-karte').length") + 1;
    await clickView("missionen");
    await evaluate(`(() => {
      const form = document.querySelector('#mission-form');
      form.elements.name.value = ${JSON.stringify(name)};
      form.elements.suche.value = "Synthetische Kamera";
      form.elements.max_preis.value = ${JSON.stringify(String(maxPrice))};
      form.elements.region.value = "Berlin";
      form.elements.entfernung_km.value = "20";
      form.elements.automatisch.checked = ${JSON.stringify(automatic)};
      form.dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
    })()`);
    await waitFor(
      "document.querySelectorAll('#mission-liste .mission-karte').length",
      (v) => v === expectedCount,
      `mission ${name} save`,
    );
  }

  async function runMission(cardIndex = 0) {
    await evaluate(`document.querySelectorAll('#mission-liste .mission-karte')[${cardIndex}]`
      + `.querySelector('button').click()`);
    return waitFor(
      "document.querySelector('#mission-form-status').textContent",
      (v) => v.startsWith("Lauf "),
      "mission run result",
    );
  }

  await createMission("Synthetic mission A", 100);
  const firstRun = await runMission(0);
  assert.match(firstRun, /\(lokal gespeichert\)/);
  await clickView("blitz");
  await waitFor(
    "document.querySelectorAll('#blitz-liste .blitz-karte').length",
    (v) => v === 1,
    "BLITZ queue item",
  );
  console.log("PASS MISSION run, BLITZ queue and local run result");

  await clickView("einstellungen");
  await evaluate("document.querySelector('#backup-erstellen').click()");
  await waitFor(
    "document.querySelector('#backup-status').textContent",
    (v) => v.includes("Sicherung heruntergeladen"),
    "backup download status",
  );
  let downloadName;
  const downloadDeadline = Date.now() + 5_000;
  while (Date.now() < downloadDeadline) {
    const names = await readdir(downloadDir);
    downloadName = names.find((name) => name.endsWith(".json"));
    if (downloadName) break;
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  assert.ok(downloadName, "UI backup file was downloaded");
  const backupPath = path.join(downloadDir, downloadName);
  const backup = JSON.parse(await readFile(backupPath, "utf8"));
  assert.equal(backup.format, "schnapper-complete-backup");
  assert.equal(backup.server.missionen.length, 1);
  assert.equal(Object.keys(backup.server.blitz_gesehen).length, 1);
  assert.ok(backup.browser.values["mission-ergebnisse"]);
  assert.ok(backup.browser.values["mission-laeufe"]);
  assert.ok(backup.browser.values.blitz);
  console.log("PASS UI backup includes one consistent MISSION/BLITZ snapshot and browser run state");

  await createMission("Synthetic mission B", 101);
  await evaluate(`(() => {
    const original = Storage.prototype.setItem;
    window.__originalStorageSetItem = original;
    Storage.prototype.setItem = function(key, value) {
      if (key === "schnapper.browser-state.v1") {
        throw new DOMException("synthetic quota failure", "QuotaExceededError");
      }
      return original.call(this, key, value);
    };
  })()`);
  const failedRun = await runMission(1);
  assert.match(failedRun, /Speicherung fehlgeschlagen/);
  assert.match(failedRun, /Ergebnisse/);
  assert.match(failedRun, /BLITZ-Queue/);
  assert.match(failedRun, /Laufprotokoll/);
  assert.doesNotMatch(failedRun, /\(lokal gespeichert\)/);
  console.log("PASS browser quota failure stays visible for results, BLITZ queue and run log");

  await evaluate(`(() => {
    Storage.prototype.setItem = window.__originalStorageSetItem;
    window.confirm = () => true;
  })()`);
  await uploadFixture("#backup-datei", backupPath);
  await waitFor(
    "document.querySelector('#backup-status').textContent",
    (v) => v.includes("Wiederherstellung abgeschlossen"),
    "backup restore",
  );
  await waitFor(
    "document.querySelectorAll('#mission-liste .mission-karte').length",
    (v) => v === 1,
    "restored MISSION list",
  );
  const restoredServer = await fetch(`${baseUrl}/api/backup`).then((r) => r.json());
  assert.equal(restoredServer.missionen.length, 1);
  assert.equal(Object.keys(restoredServer.blitz_gesehen).length, 1);
  assert.equal(await evaluate("blitzQueue().length"), 1);
  console.log("PASS UI restore rolls server and browser state back to the downloaded snapshot");

  await createMission("Synthetic automatic mission", 102, true);
  console.log("INFO automatic readiness " + JSON.stringify(await evaluate(
    "({visibility: document.visibilityState, locks: typeof navigator.locks?.request, missions: missionen.map((m) => ({name:m.name, automatic:m.automatisch, status:m.status, last:m.letzter_lauf_am}))})",
  )));
  await cdp("Network.enable");
  await evaluate(`(() => {
    const original = window.fetch.bind(window);
    window.__automaticRunGateStarted = false;
    window.fetch = async (resource, options = {}) => {
      if (String(resource).includes("/api/missionen/") && String(resource).endsWith("/lauf")) {
        window.__automaticRunGateStarted = true;
        await new Promise((resolve) => setTimeout(resolve, 700));
      }
      return original(resource, options);
    };
  })()`);
  const firstTabRun = evaluate("missionenAutomatischPruefen()");
  await waitFor(
    "window.__automaticRunGateStarted",
    (v) => v === true,
    "first tab holding the automatic-run lock",
  );
  auxiliaryPage = await openAuxiliaryPage(baseUrl);
  await waitFor(
    "document.querySelectorAll('#mission-liste .mission-karte').length",
    (v) => v === 2,
    "two-tab shared server state",
  );
  assert.equal(await auxiliaryPage.evaluate("document.querySelectorAll('#mission-liste .mission-karte').length"), 2);
  assert.equal(await auxiliaryPage.evaluate("typeof navigator.locks?.request"), "function");
  await auxiliaryPage.cdp("Network.enable");
  await auxiliaryPage.evaluate("missionenAutomatischPruefen()");
  await new Promise((resolve) => setTimeout(resolve, 100));
  const secondTabRuns = auxiliaryPage.events.filter((event) =>
    event.method === "Network.requestWillBeSent"
    && event.params.request.method === "POST"
    && event.params.request.url.includes("/api/missionen/")
    && event.params.request.url.endsWith("/lauf"),
  );
  assert.equal(secondTabRuns.length, 0, "second visible tab must not start a duplicate run while lock is held");
  await firstTabRun;
  const firstTabRuns = observedEvents.filter((event) =>
    event.method === "Network.requestWillBeSent"
    && event.params.request.method === "POST"
    && event.params.request.url.includes("/api/missionen/")
    && event.params.request.url.endsWith("/lauf"),
  );
  assert.equal(firstTabRuns.length, 1);
  console.log("PASS simultaneous visible tabs share Web Lock; second tab sends no duplicate mission run");
} finally {
  socket.close();
  auxiliaryPage?.socket.close();
  if (auxiliaryPage) await fetch(`${cdpUrl}/json/close/${auxiliaryPage.target.id}`);
  await fetch(`${cdpUrl}/json/close/${target.id}`);
}
