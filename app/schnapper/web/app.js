"use strict";
// Alle Inhalte werden per textContent eingesetzt (nie innerHTML), damit Titel aus
// fremden Listen keinen Code einschleusen können.
const $ = (id) => document.getElementById(id);
const euro = new Intl.NumberFormat("de-DE", { style: "currency", currency: "EUR" });
const ZUSTAND = { neu: "neu", wie_neu: "wie neu", gebraucht: "gebraucht", defekt: "defekt", unbekannt: "Zustand unbekannt" };
const MAX_MERK = 200;
const MAX_ALARME = 50;
const MAX_BLITZ = 300;
const BROWSER_STATE_KEY = "schnapper.browser-state.v1";
const BROWSER_STATE_FORMAT = "schnapper-browser-backup";
const BROWSER_STATE_KEYS = ["merkliste", "alarme", "vergleich-auswahl", "blitz",
  "mission-ergebnisse", "mission-laeufe"];
let timer = null;
let anfrageNr = 0;
let missionen = [];
const laufendeMissionen = new Set();

// ---------- Speicher (nur auf diesem Gerät) ----------
// Ein einzelner localStorage-Schlüssel hält den Browserzustand atomar. Dadurch
// kann ein fehlgeschlagener Restore nicht mehrere alte Schlüssel halb ersetzen.
function browserStateValide(wert) {
  if (!wert || typeof wert !== "object" || Array.isArray(wert)
      || wert.format !== BROWSER_STATE_FORMAT || wert.version !== 1
      || !wert.values || typeof wert.values !== "object" || Array.isArray(wert.values)
      || !wert.corrupt || typeof wert.corrupt !== "object" || Array.isArray(wert.corrupt)) return false;
  const erlaubt = new Set(BROWSER_STATE_KEYS);
  return Object.keys(wert.values).every((k) => erlaubt.has(k))
    && Object.keys(wert.corrupt).every((k) => erlaubt.has(k) && typeof wert.corrupt[k] === "string");
}

function browserStateLeer() {
  return { format: BROWSER_STATE_FORMAT, version: 1, values: Object.create(null), corrupt: Object.create(null) };
}

function speicherHinweis(text = "Lokale Speicherung ist nicht verfügbar oder beschädigt.") {
  $("speicher-hinweis").hidden = false;
  $("speicher-hinweis").textContent = text;
}

const speicher = {
  ersatz: {},
  beschaedigt: new Set(),
  blockiert: false,
  _laden() {
    let roh;
    try { roh = window.localStorage.getItem(BROWSER_STATE_KEY); }
    catch { speicherHinweis(); return null; }
    if (roh !== null) {
      try {
        const wert = JSON.parse(roh);
        if (!browserStateValide(wert)) throw new Error("invalid browser state");
        for (const name of Object.keys(wert.corrupt)) this.beschaedigt.add(name);
        return wert;
      } catch {
        this.blockiert = true;
        for (const name of BROWSER_STATE_KEYS) this.beschaedigt.add(name);
        speicherHinweis("Der zusammengefasste Browserdatensatz ist beschädigt und bleibt unverändert erhalten.");
        return null;
      }
    }
    const wert = browserStateLeer();
    let vorhanden = false;
    try {
      for (const name of BROWSER_STATE_KEYS) {
        const alt = window.localStorage.getItem("schnapper." + name);
        if (alt === null) continue;
        vorhanden = true;
        try { wert.values[name] = JSON.parse(alt); }
        catch { wert.corrupt[name] = alt; this.beschaedigt.add(name); }
      }
      if (vorhanden) {
        // Erst die vollständige Migration schreiben. Alte Schlüssel bleiben
        // als unveränderte Rückfallebene erhalten.
        window.localStorage.setItem(BROWSER_STATE_KEY, JSON.stringify(wert));
      }
    } catch {
      speicherHinweis("Alte Browserdaten wurden gelesen, aber ihre Migration konnte nicht gespeichert werden.");
      this.ersatz._state = wert;
    }
    return wert;
  },
  lesen(name, standard) {
    const state = this._laden() || this.ersatz._state;
    if (this.blockiert || !state) return name in this.ersatz ? this.ersatz[name] : standard;
    if (Object.hasOwn(state.corrupt, name)) {
      this.beschaedigt.add(name);
      speicherHinweis("Ein lokaler Datensatz ist fehlerhaft und bleibt unverändert erhalten. Für diesen Bereich sind Änderungen gesperrt.");
      return standard;
    }
    if (Object.hasOwn(state.values, name)) return state.values[name];
    if (name in this.ersatz) return this.ersatz[name];
    return standard;
  },
  schreiben(name, wert) {
    if (this.beschaedigt.has(name) || this.blockiert) {
      speicherHinweis("Lokale Speicherung fehlgeschlagen: Der Browserdatensatz ist beschädigt oder schreibgeschützt.");
      return false;
    }
    const state = this._laden() || this.ersatz._state || browserStateLeer();
    if (Object.hasOwn(state.corrupt, name)) {
      speicherHinweis("Lokale Speicherung fehlgeschlagen: Der betroffene Browserdatensatz ist beschädigt und schreibgeschützt.");
      return false;
    }
    const next = {
      format: BROWSER_STATE_FORMAT,
      version: 1,
      values: { ...state.values, [name]: wert },
      corrupt: { ...state.corrupt },
    };
    this.ersatz[name] = wert;
    try {
      window.localStorage.setItem(BROWSER_STATE_KEY, JSON.stringify(next));
      delete this.ersatz._state;
      return true;
    } catch {
      speicherHinweis();
      return false;
    }
  },
  exportdaten() {
    const state = this._laden() || this.ersatz._state;
    if (this.blockiert || !state) throw new Error("Browserdaten sind beschädigt oder nicht lesbar.");
    return JSON.parse(JSON.stringify(state));
  },
  wiederherstellen(wert) {
    if (!browserStateValide(wert)) throw new Error("Browserteil der Sicherung ist ungültig.");
    const safe = JSON.parse(JSON.stringify(wert));
    // Ein Schlüssel und ein synchroner setItem: bei Quota-/I/O-Fehlern bleibt
    // der bisherige Zustand vollständig erhalten.
    window.localStorage.setItem(BROWSER_STATE_KEY, JSON.stringify(safe));
    this.ersatz = {};
    this.ersatz._state = safe;
    this.blockiert = false;
    this.beschaedigt = new Set(Object.keys(safe.corrupt));
  },
};

function merkliste() {
  const m = speicher.lesen("merkliste", {});
  if (!m || typeof m !== "object" || Array.isArray(m)) {
    speicher.beschaedigt.add("merkliste");
    $("speicher-hinweis").hidden = false;
    return Object.create(null);
  }
  const sauber = Object.create(null);
  for (const [id, wert] of Object.entries(m)) {
    if (["__proto__", "constructor", "prototype"].includes(id) || !wert || typeof wert !== "object"
        || typeof wert.titel !== "string" || !Number.isFinite(Number(wert.gesamtpreis))
        || Number(wert.gesamtpreis) <= 0) {
      speicher.beschaedigt.add("merkliste");
      $("speicher-hinweis").hidden = false;
      continue;
    }
    if (wert.gemerkt_am !== undefined && typeof wert.gemerkt_am !== "string") {
      speicher.beschaedigt.add("merkliste");
      $("speicher-hinweis").hidden = false;
      continue;
    }
    sauber[id] = wert;
  }
  return sauber;
}
function alarme() {
  const a = speicher.lesen("alarme", []);
  if (!Array.isArray(a) || a.some((x) => !x || typeof x !== "object" || typeof x.text !== "string")) {
    speicher.beschaedigt.add("alarme");
    $("speicher-hinweis").hidden = false;
    return [];
  }
  return a;
}
function el(tag, text, klasse) {
  const e = document.createElement(tag);
  if (text !== undefined) e.textContent = text;
  if (klasse) e.className = klasse;
  return e;
}
function zahl(x) { return Number(x).toLocaleString("de-DE"); }

// ---------- Suche ----------
function query() {
  const p = new URLSearchParams();
  for (const [k, v] of new FormData($("filter"))) if (String(v).trim()) p.set(k, String(v).trim());
  return p.toString();
}

function warnText(w) {
  if (w.startsWith("veraltet")) return { text: "Preis evtl. veraltet", gefahr: false, titel: w };
  if (w.startsWith("betrugsverdacht")) return { text: "Vorsicht: zu billig für Neuware", gefahr: true, titel: w };
  if (w.startsWith("kein Referenzpreis")) return { text: "Ersparnis unbekannt", gefahr: false, titel: w };
  if (w.startsWith("teurer")) return { text: "Teurer als üblich", gefahr: true, titel: w };
  if (w.startsWith("referenzpreis fragwürdig")) return { text: "„Statt“-Preis fragwürdig", gefahr: true, titel: w };
  return { text: w, gefahr: false, titel: w };
}

function merkKnopf(knopf, t) {
  const setzen = () => {
    const an = Object.hasOwn(merkliste(), t.id);
    knopf.textContent = an ? "★" : "☆";
    knopf.setAttribute("aria-pressed", String(an));
    knopf.setAttribute("aria-label", an ? "Von der Merkliste nehmen" : "Merken");
    knopf.title = an ? "Gemerkt" : "Merken";
  };
  knopf.addEventListener("click", () => {
    const m = merkliste();
    if (Object.hasOwn(m, t.id)) delete m[t.id];
    else {
      if (Object.keys(m).length >= MAX_MERK) { $("status").textContent = `Merkliste ist voll (max. ${MAX_MERK}).`; return; }
      m[t.id] = { titel: t.titel, preis: t.preis, versand: t.versand, gesamtpreis: t.gesamtpreis,
                  referenzpreis: t.referenzpreis, rabatt_prozent: t.rabatt_prozent, url: t.url,
                  quelle: t.quelle, zustand: t.zustand, region: t.region,
                  entfernung_km: t.entfernung_km, erfasst_am: t.erfasst_am,
                  warnungen: Array.isArray(t.warnungen) ? t.warnungen.slice(0, 20) : [],
                  verlauf: t.verlauf || null, gemerkt_am: new Date().toISOString() };
    }
    speicher.schreiben("merkliste", m);
    setzen();
    zaehler();
  });
  setzen();
}

function karte(t) {
  const e = $("karte").content.firstElementChild.cloneNode(true);
  const r = e.querySelector(".rabatt");
  if (t.rabatt_prozent !== null) {
    r.textContent = Number(t.rabatt_prozent) >= 0 ? `−${zahl(t.rabatt_prozent)} %` : "teurer";
  } else { r.textContent = "ohne Vergleich"; r.classList.add("ohne"); }
  e.querySelector(".preis").textContent = euro.format(Number(t.gesamtpreis));
  e.querySelector(".titel").textContent = t.titel;
  const teile = [ZUSTAND[t.zustand] || t.zustand, t.quelle];
  if (Number(t.versand) > 0) teile.push(`inkl. ${euro.format(Number(t.versand))} Versand`);
  if (t.referenzpreis) teile.push(`sonst ${euro.format(Number(t.referenzpreis))}`);
  if (t.region) teile.push(`Region ${t.region}`);
  if (t.entfernung_km !== null && t.entfernung_km !== undefined && Number.isFinite(Number(t.entfernung_km))) {
    teile.push(`${zahl(t.entfernung_km)} km`);
  }
  e.querySelector(".details").textContent = teile.join(" · ");
  verlaufZeile(e.querySelector(".verlauf"), t);
  const ul = e.querySelector(".warnungen");
  for (const w of t.warnungen) {
    const info = warnText(w);
    const li = el("li", info.text, info.gefahr ? "gefahr" : "");
    li.title = info.titel;
    ul.appendChild(li);
  }
  const a = e.querySelector(".link");
  if (/^https:\/\//.test(t.url)) a.href = t.url; else a.remove();
  e.querySelector(".vergleich-auswahl").hidden = true;
  merkKnopf(e.querySelector(".merken"), t);
  return e;
}

// Preisverlauf: Tiefstpreis, Spanne der letzten 30 Tage, vorheriger Preis
function verlaufZeile(p, t) {
  const v = t.verlauf;
  if (!v) return;
  const teile = [];
  if (v.ist_tiefstpreis) {
    p.appendChild(el("span", `Tiefstpreis seit ${v.seit_tagen} Tag${v.seit_tagen === 1 ? "" : "en"}`, "tief"));
  }
  if (v.vorher !== null) {
    const diff = Number(t.gesamtpreis) - Number(v.vorher);
    teile.push(`${diff < 0 ? "↓" : "↑"} vorher ${euro.format(Number(v.vorher))}`);
  }
  teile.push(`${euro.format(Number(v.tiefst))}–${euro.format(Number(v.hoechst))} in ${v.seit_tagen} Tagen`);
  p.appendChild(el("span", teile.join(" · ")));
  p.title = `${v.anzahl} Preise beobachtet`;
  p.hidden = false;
}

function probleme(daten) {
  const liste = [...daten.ungueltig.map((f) => "Ungültig – " + f),
                 ...daten.dubletten.map((d) => `Doppelt entfernt: „${d.titel}“`)];
  $("probleme").hidden = liste.length === 0;
  $("probleme-titel").textContent = `${liste.length} Hinweis${liste.length === 1 ? "" : "e"} zur Liste anzeigen`;
  $("probleme-liste").replaceChildren(...liste.map((txt) => el("li", txt)));
}

async function suchen() {
  const nr = ++anfrageNr;
  alarmKnopf();
  try {
    const antwort = await fetch("/api/suche?" + query());
    const daten = await antwort.json();
    if (nr !== anfrageNr) return; // veraltete Antwort ignorieren
    if (!antwort.ok) { $("status").textContent = daten.fehler || "Fehler bei der Suche"; return; }
    // Mock-Angebote bleiben selbst nach dem Import als Testdaten markiert.
    $("beispiel").hidden = !(daten.beispieldaten || daten.enthaelt_testdaten);
    $("treffer").replaceChildren(...daten.treffer.map(karte));
    $("leer").hidden = daten.treffer.length > 0;
    $("leer").textContent = daten.eingelesen === 0
      ? "Noch keine Angebote geladen. Tippe oben rechts auf „Eigene Liste“ und wähle deine CSV- oder JSON-Datei."
      : "Keine Treffer. Lockere die Filter oder suche nach etwas anderem.";
    $("status").textContent = `${daten.treffer.length} Treffer aus ${daten.eingelesen} Angeboten · Liste: ${daten.liste}`;
    probleme(daten);
  } catch {
    if (nr === anfrageNr) $("status").textContent = "Server nicht erreichbar. Läuft SCHNAPPER noch?";
  }
}

function spaeter() { clearTimeout(timer); timer = setTimeout(suchen, 250); }

async function hochladen(ev) {
  const datei = ev.target.files[0];
  ev.target.value = "";
  if (!datei) return;
  if (datei.size > 5 * 1024 * 1024) { $("status").textContent = "Datei ist größer als 5 MB."; return; }
  zeige("suche");
  $("status").textContent = "Lade Liste …";
  try {
    const antwort = await fetch("/api/import", {
      method: "POST", body: datei,
      headers: { "X-Schnapper": "1", "X-Dateiname": datei.name, "Content-Type": "application/octet-stream" },
    });
    const daten = await antwort.json();
    if (!antwort.ok) {
      $("status").textContent = daten.fehler || "Liste konnte nicht geladen werden.";
      if (daten.ungueltig) probleme({ ungueltig: daten.ungueltig, dubletten: [] });
      return;
    }
    await suchen();
    alarmePruefen();
  } catch { $("status").textContent = "Hochladen fehlgeschlagen."; }
}

async function barcodeSuchen(ev) {
  ev.preventDefault();
  const ean = $("barcode").value.trim();
  const status = $("barcode-status");
  const knopf = $("barcode-knopf");
  $("barcode-treffer").replaceChildren();
  $("barcode-lizenz").textContent = "";
  if (!/^[0-9]{8,14}$/.test(ean)) {
    status.textContent = "Bitte einen Barcode mit 8 bis 14 Ziffern eingeben.";
    return;
  }
  knopf.disabled = true;
  status.textContent = "Frage Ladenpreise ab …";
  try {
    const antwort = await fetch("/api/openprices", {
      method: "POST",
      headers: { "X-Schnapper": "1", "Content-Type": "application/json" },
      body: JSON.stringify({ ean }),
    });
    const daten = await antwort.json();
    if (!antwort.ok) {
      status.textContent = daten.fehler || "Ladenpreise konnten nicht abgerufen werden.";
      return;
    }
    // Ladenpreise bleiben getrennt von der eigenen Angebotsliste: nicht merkbar.
    $("barcode-treffer").replaceChildren(...daten.treffer.map((t) => {
      const e = karte(t);
      e.querySelector(".merken")?.remove();
      return e;
    }));
    $("barcode-lizenz").textContent = daten.lizenz || "";
    status.textContent = daten.treffer.length === 0
      ? "Keine passenden gemeldeten Preise gefunden."
      : `${daten.treffer.length} Preise gefunden · ${daten.begrenzung}`;
    if (daten.hinweise.length) status.textContent += ` · ${daten.hinweise.length} Einträge übersprungen`;
  } catch {
    status.textContent = "Server oder Preisquelle nicht erreichbar.";
  } finally {
    knopf.disabled = false;
  }
}

// ---------- Preisalarm ----------
function aktuellerWunsch() {
  const f = new FormData($("filter"));
  const w = { text: String(f.get("text") || "").trim(), max_preis: String(f.get("max_preis") || "").trim(),
              min_rabatt: String(f.get("min_rabatt") || "").trim(), zustand: String(f.get("zustand") || ""),
              region: String(f.get("region") || "").trim(),
              entfernung_km: String(f.get("entfernung_km") || "").trim() };
  return w.text && (w.max_preis || w.min_rabatt) ? w : null;
}

function alarmKnopf() {
  const ok = aktuellerWunsch() !== null;
  $("alarm-anlegen").disabled = !ok;
  $("mission-aus-suche").disabled = !String(new FormData($("filter")).get("text") || "").trim();
  $("alarm-tipp").hidden = ok;
}

function wunschText(w, mitText = true) {
  const teile = mitText ? [`„${w.text}“`] : [];
  if (w.max_preis) teile.push(`bis ${w.max_preis} €`);
  if (w.min_rabatt) teile.push(`ab ${w.min_rabatt} % billiger`);
  if (w.zustand) teile.push(ZUSTAND[w.zustand] || w.zustand);
  if (w.region) teile.push(w.region);
  if (w.entfernung_km) teile.push(`Umkreis ${w.entfernung_km} km`);
  return teile.join(" · ");
}

async function alarmAnlegen() {
  const w = aktuellerWunsch();
  if (!w) return;
  const liste = alarme();
  if (liste.some((x) => wunschText(x) === wunschText(w))) { $("status").textContent = "Diesen Preisalarm gibt es schon."; return; }
  if (liste.length >= MAX_ALARME) { $("status").textContent = `Höchstens ${MAX_ALARME} Preisalarme.`; return; }
  // Erst beim Server prüfen lassen, ob die Zahlen lesbar sind
  const antwort = await fetch("/api/suche?" + alarmQuery(w)).catch(() => null);
  if (!antwort || !antwort.ok) { $("status").textContent = "Preisalarm nicht angelegt: Eingaben prüfen."; return; }
  liste.push({ ...w, angelegt_am: new Date().toISOString() });
  if (!speicher.schreiben("alarme", liste)) {
    $("status").textContent = "Preisalarm nicht angelegt: lokale Speicherung fehlgeschlagen.";
    return;
  }
  $("status").textContent = `Preisalarm angelegt: ${wunschText(w)}`;
  alarmePruefen();
}

function alarmQuery(w) {
  const p = new URLSearchParams({ text: w.text, sortierung: "preis", ohne_veraltet: "1" });
  if (w.max_preis) p.set("max_preis", w.max_preis);
  if (w.min_rabatt) p.set("min_rabatt", w.min_rabatt);
  if (w.zustand) p.set("zustand", w.zustand);
  if (w.region) p.set("region", w.region);
  if (w.entfernung_km) p.set("entfernung_km", w.entfernung_km);
  return p.toString();
}

let alarmTreffer = 0;
async function alarmePruefen() {
  const liste = alarme();
  const karten = await Promise.all(liste.map(async (w, i) => {
    const e = $("karte-alarm").content.firstElementChild.cloneNode(true);
    e.querySelector(".titel").textContent = w.text;
    e.querySelector(".details").textContent = wunschText(w, false);
    e.querySelector(".loeschen").addEventListener("click", () => {
      const neu = alarme().filter((_, j) => j !== i);
      speicher.schreiben("alarme", neu);
      alarmePruefen();
    });
    const marke = e.querySelector(".ausgeloest");
    let treffer = [];
    try {
      const antwort = await fetch("/api/suche?" + alarmQuery(w));
      if (antwort.ok) treffer = (await antwort.json()).treffer;
      else marke.textContent = "Eingabe ungültig";
    } catch { marke.textContent = "Server nicht erreichbar"; }
    if (treffer.length) {
      marke.textContent = `⚡ ${treffer.length} Treffer · ab ${euro.format(Number(treffer[0].gesamtpreis))}`;
      e.classList.add("an");
      const ul = e.querySelector(".alarm-treffer");
      for (const t of treffer.slice(0, 3)) {
        const li = el("li");
        const a = el("a", `${euro.format(Number(t.gesamtpreis))} – ${t.titel}`);
        if (/^https:\/\//.test(t.url)) { a.href = t.url; a.target = "_blank"; a.rel = "noopener noreferrer"; }
        li.append(a, el("span", ` · ${t.quelle}`, "leise"));
        ul.appendChild(li);
      }
    } else if (!marke.textContent) marke.textContent = "noch nichts unter der Grenze";
    return { e, an: treffer.length > 0 };
  }));
  karten.sort((x, y) => Number(y.an) - Number(x.an));
  $("alarm-liste").replaceChildren(...karten.map((k) => k.e));
  $("alarm-leer").hidden = liste.length > 0;
  alarmTreffer = karten.filter((k) => k.an).length;
  zaehler();
}

// ---------- Merkliste ----------
async function merklisteZeigen() {
  const m = merkliste();
  const ids = Object.keys(m);
  let aktuell = Object.create(null);
  try {
    const antwort = await fetch("/api/suche?mit_verdacht=1");
    if (antwort.ok) for (const t of (await antwort.json()).treffer) aktuell[t.id] = t;
  } catch { aktuell = null; }
  const karten = ids.sort((a, b) => (m[b].gemerkt_am || "").localeCompare(m[a].gemerkt_am || "")).map((id) => {
    const alt = m[id];
    const jetzt = aktuell ? aktuell[id] : undefined;
    const e = $("karte").content.firstElementChild.cloneNode(true);
    const r = e.querySelector(".rabatt");
    const preis = Number(jetzt ? jetzt.gesamtpreis : alt.gesamtpreis);
    e.querySelector(".preis").textContent = euro.format(preis);
    e.querySelector(".titel").textContent = alt.titel;
    const details = [ZUSTAND[alt.zustand] || alt.zustand, alt.quelle];
    if (alt.gemerkt_am) details.push("gemerkt am " + new Date(alt.gemerkt_am).toLocaleDateString("de-DE"));
    e.querySelector(".details").textContent = details.filter(Boolean).join(" · ");
    if (aktuell === null) { r.textContent = "Stand unbekannt"; r.classList.add("ohne"); }
    else if (!jetzt) { r.textContent = "nicht mehr in der Liste"; r.classList.add("ohne"); }
    else {
      const diff = Number(jetzt.gesamtpreis) - Number(alt.gesamtpreis);
      if (Math.abs(diff) < 0.005) { r.textContent = "Preis unverändert"; r.classList.add("ohne"); }
      else if (diff < 0) r.textContent = `${euro.format(-diff)} günstiger`;
      else { r.textContent = `${euro.format(diff)} teurer`; r.classList.add("hoch"); }
      for (const w of jetzt.warnungen) {
        const info = warnText(w);
        e.querySelector(".warnungen").appendChild(el("li", info.text, info.gefahr ? "gefahr" : ""));
      }
    }
    const a = e.querySelector(".link");
    if (/^https:\/\//.test(alt.url || "")) a.href = alt.url; else a.remove();
    const check = e.querySelector(".vergleich-check");
    e.querySelector(".vergleich-auswahl").hidden = false;
    check.checked = gespeicherteAuswahl().includes(id);
    check.addEventListener("change", () => {
      const selected = new Set(gespeicherteAuswahl());
      if (check.checked) selected.add(id); else selected.delete(id);
      if (selected.size > MAX_MERK) {
        check.checked = false;
        $("korb-status").textContent = `Höchstens ${MAX_MERK} Angebote für den Vergleich auswählen.`;
        return;
      }
      speicher.schreiben("vergleich-auswahl", [...selected]);
      $("korb-status").textContent = `${selected.size} Angebot(e) für den Vergleich ausgewählt.`;
    });
    const knopf = e.querySelector(".merken");
    merkKnopf(knopf, { id, ...alt });
    knopf.addEventListener("click", () => { if (!Object.hasOwn(merkliste(), id)) e.remove(); $("merk-leer").hidden = Object.keys(merkliste()).length > 0; });
    return e;
  });
  $("merk-liste").replaceChildren(...karten);
  $("merk-leer").hidden = ids.length > 0;
}

// ---------- Dauerhafte, lokale App-Daten ----------
function arrayStorage(name, valid, limit) {
  const wert = speicher.lesen(name, []);
  if (!Array.isArray(wert)) {
    speicher.beschaedigt.add(name);
    $("speicher-hinweis").hidden = false;
    return [];
  }
  const safe = wert.filter(valid).slice(-limit);
  if (safe.length !== wert.length) {
    speicher.beschaedigt.add(name);
    $("speicher-hinweis").hidden = false;
  }
  return safe;
}

function blitzQueue() {
  return arrayStorage("blitz", (x) => x && typeof x === "object"
    && typeof x.id === "string" && /^[a-f0-9]{64}$/.test(x.id)
    && typeof x.titel === "string" && typeof x.wunsch === "string"
    && Number.isFinite(Number(x.gesamtpreis)) && Number(x.gesamtpreis) > 0
    && typeof x.url === "string" && /^https:\/\//.test(x.url)
    && typeof x.quelle === "string" && typeof x.erstellt_am === "string"
    && (x.gesehen === undefined || typeof x.gesehen === "boolean"), MAX_BLITZ);
}

function missionLaeufe() {
  return arrayStorage("mission-laeufe", (x) => x && typeof x === "object"
    && typeof x.job_id === "string" && typeof x.mission_id === "string"
    && typeof x.status === "string" && typeof x.zeit === "string", 50);
}

function gespeicherteErgebnisse() {
  const wert = speicher.lesen("mission-ergebnisse", {});
  if (!wert || typeof wert !== "object" || Array.isArray(wert)) {
    speicher.beschaedigt.add("mission-ergebnisse");
    $("speicher-hinweis").hidden = false;
    return Object.create(null);
  }
  const safe = Object.create(null);
  for (const [id, eintrag] of Object.entries(wert)) {
    if (!/^[A-Za-z0-9_-]{1,64}$/.test(id) || !eintrag || typeof eintrag !== "object"
        || typeof eintrag.zeit !== "string" || !Array.isArray(eintrag.treffer)
        || eintrag.treffer.some((t) => !t || typeof t.titel !== "string"
          || !Number.isFinite(Number(t.gesamtpreis)) || Number(t.gesamtpreis) <= 0)) {
      speicher.beschaedigt.add("mission-ergebnisse");
      $("speicher-hinweis").hidden = false;
      continue;
    }
    safe[id] = { ...eintrag, treffer: eintrag.treffer.slice(0, 12),
      beispieldaten: Boolean(eintrag.beispieldaten) };
  }
  return safe;
}

function apiFehler(antwort, inhalt, pfad) {
  const fehler = new Error(inhalt.fehler || `Anfrage fehlgeschlagen (${antwort.status})`);
  fehler.status = antwort.status;
  fehler.aktualisieren = inhalt.aktualisieren === true;
  fehler.pfad = pfad;
  return fehler;
}

async function apiPost(pfad, daten) {
  const antwort = await fetch(pfad, {
    method: "POST",
    headers: { "X-Schnapper": "1", "Content-Type": "application/json" },
    body: JSON.stringify(daten),
  });
  let inhalt = {};
  try { inhalt = await antwort.json(); } catch { /* verständlicher Fehler unten */ }
  if (!antwort.ok) throw apiFehler(antwort, inhalt, pfad);
  return inhalt;
}

async function apiGet(pfad) {
  const antwort = await fetch(pfad, { headers: { "X-Schnapper": "1" } });
  let inhalt = {};
  try { inhalt = await antwort.json(); } catch { /* verständlicher Fehler unten */ }
  if (!antwort.ok) throw apiFehler(antwort, inhalt, pfad);
  return inhalt;
}

async function sicherungHerunterladen() {
  const status = $("backup-status");
  status.textContent = "Sichere lokale Daten …";
  try {
    const paket = {
      format: "schnapper-complete-backup",
      version: 1,
      erstellt_am: new Date().toISOString(),
      server: await apiGet("/api/backup"),
      browser: speicher.exportdaten(),
    };
    const blob = new Blob([JSON.stringify(paket, null, 2)], { type: "application/json" });
    if (blob.size > 12 * 1024 * 1024) throw new Error("Sicherung überschreitet 12 MB.");
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `schnapper-backup-${new Date().toISOString().slice(0, 10)}.json`;
    document.body.append(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    status.textContent = "Sicherung heruntergeladen. Bewahre die Datei getrennt von diesem Gerät auf.";
  } catch (error) {
    status.textContent = `Sicherung fehlgeschlagen: ${error.message}`;
  }
}

async function sicherungWiederherstellen(ev) {
  const datei = ev.target.files?.[0];
  ev.target.value = "";
  const status = $("backup-status");
  if (!datei) return;
  if (datei.size > 12 * 1024 * 1024) {
    status.textContent = "Sicherung überschreitet 12 MB; es wurde nichts geändert.";
    return;
  }
  let paket;
  try {
    paket = JSON.parse(await datei.text());
    if (!paket || paket.format !== "schnapper-complete-backup" || paket.version !== 1
        || !paket.server || paket.server.format !== "schnapper-server-backup"
        || paket.server.version !== 1 || !Array.isArray(paket.server.missionen)
        || !paket.server.blitz_gesehen || typeof paket.server.blitz_gesehen !== "object"
        || !browserStateValide(paket.browser)) throw new Error("Sicherungsformat oder Daten ungültig.");
  } catch (error) {
    status.textContent = `Sicherung abgelehnt: ${error.message}`;
    return;
  }
  if (!window.confirm("Lokale Missionen, BLITZ-Deduplizierung und Browserdaten durch die Sicherung ersetzen?")) return;
  status.textContent = "Prüfe Sicherung und sichere den aktuellen Stand …";
  let serverVorher;
  let serverErsetzt = false;
  try {
    serverVorher = await apiGet("/api/backup");
    await apiPost("/api/backup", paket.server);
    serverErsetzt = true;
    speicher.wiederherstellen(paket.browser);
    serverErsetzt = false;
    await missionenLaden().catch(() => {});
    try { renderBlitz(); renderMissionLaeufe(); } catch { /* gespeicherte Daten bleiben wiederhergestellt */ }
    status.textContent = "Wiederherstellung abgeschlossen. Die vorherige Sicherung wurde vor dem Austausch geprüft.";
  } catch (error) {
    if (serverErsetzt) {
      try {
        await apiPost("/api/backup", serverVorher);
        status.textContent = `Browser-Wiederherstellung fehlgeschlagen; die vorherigen Serverdaten wurden zurückgesichert. ${error.message}`;
      } catch {
        status.textContent = `Wiederherstellung unvollständig: Browserdaten blieben unverändert; die Serverwiederherstellung muss erneut geprüft werden. ${error.message}`;
      }
    } else {
      status.textContent = `Wiederherstellung fehlgeschlagen; vorhandene Daten blieben unverändert. ${error.message}`;
    }
  }
}

function textButton(text, klasse, aktion) {
  const button = el("button", text, klasse || "knopf sekundaer");
  button.type = "button";
  button.addEventListener("click", aktion);
  return button;
}

function missionDatenAusForm() {
  const form = $("mission-form");
  const f = new FormData(form);
  const zustand = String(f.get("zustand") || "");
  return {
    id: String(f.get("id") || ""),
    name: String(f.get("name") || "").trim(),
    suche: String(f.get("suche") || "").trim(),
    max_preis: String(f.get("max_preis") || "").trim(),
    min_rabatt: String(f.get("min_rabatt") || "").trim(),
    region: String(f.get("region") || "").trim(),
    entfernung_km: String(f.get("entfernung_km") || "").trim(),
    intervall_minuten: Number(f.get("intervall_minuten")),
    zustaende: zustand ? [zustand] : [],
    automatisch: Boolean(form.elements.automatisch.checked),
  };
}

function missionFormZuruecksetzen() {
  $("mission-form").reset();
  $("mission-form").elements.id.value = "";
  $("mission-form-titel").textContent = "Suchauftrag erstellen";
  $("mission-abbrechen").hidden = true;
}

function missionBearbeitenStarten(m) {
  const f = $("mission-form");
  f.elements.id.value = m.id;
  f.elements.name.value = m.name;
  f.elements.suche.value = m.suche;
  f.elements.max_preis.value = m.max_preis || "";
  f.elements.min_rabatt.value = m.min_rabatt || "";
  f.elements.region.value = m.region || "";
  f.elements.entfernung_km.value = m.entfernung_km || "";
  f.elements.intervall_minuten.value = m.intervall_minuten;
  f.elements.zustand.value = (m.zustaende || [])[0] || "";
  f.elements.automatisch.checked = Boolean(m.automatisch);
  $("mission-form-titel").textContent = "Mission bearbeiten";
  $("mission-abbrechen").hidden = false;
  zeige("missionen");
  f.elements.name.focus();
}

function renderMissionErgebnisse(ul, missionId) {
  const daten = gespeicherteErgebnisse();
  const eintrag = daten[missionId];
  if (!eintrag || !Array.isArray(eintrag.treffer)) return;
  if (eintrag.beispieldaten) ul.appendChild(el("li", "DEMO-Beispieldaten – keine echten Angebote", "leise"));
  for (const t of eintrag.treffer.slice(0, 12)) {
    if (!t || typeof t.titel !== "string" || !Number.isFinite(Number(t.gesamtpreis))) continue;
    const li = el("li");
    const a = el("a", `${euro.format(Number(t.gesamtpreis))} · ${t.titel}`);
    if (typeof t.url === "string" && /^https:\/\//.test(t.url)) {
      a.href = t.url; a.target = "_blank"; a.rel = "noopener noreferrer";
    }
    li.append(a);
    ul.appendChild(li);
  }
}

function renderMissionen() {
  const ol = $("mission-liste");
  const ergebnisse = gespeicherteErgebnisse();
  const karten = missionen.map((m) => {
    const k = $("karte-mission").content.firstElementChild.cloneNode(true);
    k.querySelector(".mission-status").textContent =
      `${m.status === "aktiv" ? "Aktiv" : m.status === "pausiert" ? "Pausiert" : "Beendet"}${m.automatisch ? " · Automatik nur im Vordergrund" : ""}`;
    k.querySelector(".titel").textContent = m.name;
    k.querySelector(".details").textContent =
      [m.suche, m.max_preis ? `bis ${m.max_preis} € inkl. Versand` : "",
        m.min_rabatt ? `ab ${m.min_rabatt} % Rabatt` : "",
        m.region || "", m.entfernung_km ? `${m.entfernung_km} km` : "",
        `${m.intervall_minuten} Min.`].filter(Boolean).join(" · ");
    const vorherigerLauf = m.letzter_lauf_am
      ? `Letzter Lauf: ${new Date(m.letzter_lauf_am).toLocaleString("de-DE")}` : "Noch kein Lauf";
    const lokalErgebnis = ergebnisse[m.id];
    k.querySelector(".mission-lauf").textContent = lokalErgebnis
      ? `${vorherigerLauf} · letzter Nachweis: ${lokalErgebnis.treffer?.length || 0} Treffer`
      : vorherigerLauf;
    const actions = k.querySelector(".aktionsreihe");
    if (m.status === "aktiv") actions.append(textButton("Jetzt prüfen", "knopf", () => missionLauf(m.id, false)));
    if (m.status === "aktiv") actions.append(textButton("Pausieren", "knopf sekundaer", () => missionAktion("pausieren", m.id)));
    if (m.status === "pausiert") actions.append(textButton("Fortsetzen", "knopf sekundaer", () => missionAktion("fortsetzen", m.id)));
    actions.append(textButton("Bearbeiten", "knopf sekundaer", () => missionBearbeitenStarten(m)));
    actions.append(textButton("Löschen", "knopf sekundaer", async () => {
      if (!window.confirm(`Mission „${m.name}“ löschen?`)) return;
      await missionAktion("loeschen", m.id);
    }));
    renderMissionErgebnisse(k.querySelector(".mission-ergebnisse"), m.id);
    return k;
  });
  ol.replaceChildren(...karten);
  $("mission-leer").hidden = missionen.length > 0;
  const auto = missionen.some((m) => m.status === "aktiv" && m.automatisch);
  if (auto && !navigator.locks?.request) {
    $("mission-form-status").textContent = "Automatik ist auf diesem Browser deaktiviert: sichere tabübergreifende Sperren werden nicht unterstützt.";
  }
}

async function missionenLaden() {
  try {
    const antwort = await fetch("/api/missionen");
    const daten = await antwort.json();
    if (!antwort.ok) throw new Error(daten.fehler || "Missionen konnten nicht geladen werden");
    missionen = Array.isArray(daten.missionen) ? daten.missionen : [];
    renderMissionen();
    return true;
  } catch (err) {
    $("mission-form-status").textContent = `${err.message}. Starte SCHNAPPER mit lokalem Datenverzeichnis neu.`;
    return false;
  }
}

async function apiFehlerMeldung(err) {
  const meldung = err?.message || "Anfrage fehlgeschlagen.";
  if (err?.status !== 409 || err?.aktualisieren !== true) return meldung;
  const missionsPfad = err.pfad === "/api/missionen";
  const aktualisiert = missionsPfad ? await missionenLaden() : false;
  const hinweis = missionsPfad
    ? (aktualisiert ? "Die Missionsliste wurde aktualisiert." : "Die Missionsliste konnte nicht aktualisiert werden.")
    : "Bitte lade den betroffenen Datenstand neu.";
  return `${meldung}. ${hinweis} Deine Eingaben bleiben erhalten. Es wurde nichts automatisch wiederholt; prüfe den Stand und starte den Vorgang bewusst erneut.`;
}

async function missionAktion(aktion, id) {
  $("mission-form-status").textContent = "Speichere lokal …";
  try {
    await apiPost("/api/missionen", { aktion, id });
    await missionenLaden();
    $("mission-form-status").textContent = aktion === "loeschen" ? "Mission gelöscht." : "Mission aktualisiert.";
  } catch (err) { $("mission-form-status").textContent = await apiFehlerMeldung(err); }
}

async function missionSpeichern(ev) {
  ev.preventDefault();
  const daten = missionDatenAusForm();
  if (!daten.suche) return;
  const aktion = daten.id ? "bearbeiten" : "erstellen";
  $("mission-form-status").textContent = "Speichere lokal …";
  try {
    const antwort = await apiPost("/api/missionen", { ...daten, aktion });
    missionFormZuruecksetzen();
    await missionenLaden();
    $("mission-form-status").textContent = `Mission „${antwort.mission.name}“ lokal gespeichert.`;
  } catch (err) { $("mission-form-status").textContent = await apiFehlerMeldung(err); }
}

function blitzMeldungen(meldungen, beispieldaten) {
  const q = blitzQueue();
  const ids = new Set(q.map((x) => x.id));
  const neu = [];
  for (const m of meldungen) {
    if (!m || typeof m.id !== "string" || ids.has(m.id)
        || typeof m.titel !== "string" || !Number.isFinite(Number(m.gesamtpreis))
        || typeof m.url !== "string" || !/^https:\/\//.test(m.url)) continue;
    const item = { ...m, gesehen: false, beispieldaten: Boolean(beispieldaten) };
    neu.push(item); ids.add(item.id);
  }
  if (neu.length) {
    const gespeichert = [...q, ...neu].slice(-MAX_BLITZ);
    if (!speicher.schreiben("blitz", gespeichert)) {
      $("benachrichtigung-status").textContent =
        "BLITZ-Treffer gefunden, aber der beschädigte lokale Speicher ist schreibgeschützt; bitte Datensicherung erstellen.";
      return false;
    }
    if (window.Notification?.permission === "granted") {
      try {
        const m = neu[0];
        new Notification("SCHNAPPER: neues passendes Angebot", {
          body: `${m.titel} · ${euro.format(Number(m.gesamtpreis))}`,
          tag: m.id,
        });
        $("benachrichtigung-status").textContent =
          "Browser-Benachrichtigung ausgelöst; der Treffer bleibt zusätzlich lokal in BLITZ gespeichert.";
      } catch {
        $("benachrichtigung-status").textContent =
          "Treffer lokal in BLITZ gespeichert; der Browser hat keine Benachrichtigung ausgelöst.";
      }
    }
  }
  return true;
}

function renderBlitz() {
  const q = blitzQueue();
  const ol = $("blitz-liste");
  const karten = q.slice().reverse().map((m) => {
    const k = $("karte-blitz").content.firstElementChild.cloneNode(true);
    k.querySelector(".titel").textContent = m.titel;
    k.querySelector(".details").textContent =
      `${m.wunsch} · ${euro.format(Number(m.gesamtpreis))} · Quelle: ${m.quelle} · ${new Date(m.erstellt_am).toLocaleString("de-DE")}`
      + (m.beispieldaten ? " · DEMO-Beispieldaten" : "");
    k.querySelector(".blitz-status").textContent = m.gesehen ? "Gesehen" : "Neu";
    const a = k.querySelector(".link");
    if (typeof m.url === "string" && /^https:\/\//.test(m.url)) a.href = m.url; else a.remove();
    const button = k.querySelector(".blitz-gesehen");
    button.hidden = Boolean(m.gesehen);
    button.addEventListener("click", () => {
      const next = blitzQueue().map((x) => x.id === m.id ? { ...x, gesehen: true } : x);
      if (speicher.schreiben("blitz", next)) renderBlitz();
    });
    return k;
  });
  ol.replaceChildren(...karten);
  $("blitz-leer").hidden = q.length > 0;
  alarmePruefen();
}

async function missionLauf(id, automatisch) {
  if (laufendeMissionen.has(id)) return;
  laufendeMissionen.add(id);
  $("mission-form-status").textContent = automatisch ? "Fällige Mission läuft im Vordergrund …" : "Mission läuft …";
  try {
    const daten = await apiPost(`/api/missionen/${encodeURIComponent(id)}/lauf`, { automatisch });
    const resultate = (daten.treffer || []).slice(0, 12);
    const safe = gespeicherteErgebnisse();
    safe[id] = { zeit: daten.abgeschlossen_am, treffer: resultate,
      beispieldaten: Boolean(daten.beispieldaten) };
    const speicherFehler = [];
    if (!speicher.schreiben("mission-ergebnisse", safe)) speicherFehler.push("Ergebnisse");
    if (!blitzMeldungen(daten.meldungen || [], daten.beispieldaten)) speicherFehler.push("BLITZ-Queue");
    const eintrag = {
      job_id: daten.job_id, mission_id: id,
      status: daten.blitz_fehler || speicherFehler.length ? "abgeschlossen_mit_fehler" : "abgeschlossen",
      zeit: daten.abgeschlossen_am, anzahl: (daten.treffer || []).length,
      meldungen: (daten.meldungen || []).length,
    };
    const logs = missionLaeufe();
    logs.push(eintrag);
    if (!speicher.schreiben("mission-laeufe", logs.slice(-50))) speicherFehler.push("Laufprotokoll");
    const laufFehler = [];
    if (daten.blitz_fehler) laufFehler.push(daten.blitz_fehler);
    if (speicherFehler.length) laufFehler.push(`Speicherung fehlgeschlagen: ${speicherFehler.join(", ")}.`);
    $("mission-form-status").textContent = laufFehler.length
      ? `Lauf ${daten.job_id}: ${eintrag.anzahl} Treffer; ${laufFehler.join(" ")}`
      : `Lauf ${daten.job_id}: ${eintrag.anzahl} Treffer, ${eintrag.meldungen} neue BLITZ-Einträge (lokal gespeichert).`;
    await missionenLaden();
    renderMissionLaeufe();
  } catch (err) {
    const logs = missionLaeufe();
    logs.push({ job_id: `fehler-${Date.now()}`, mission_id: id, status: "fehlgeschlagen", zeit: new Date().toISOString() });
    const protokollGespeichert = speicher.schreiben("mission-laeufe", logs.slice(-50));
    $("mission-form-status").textContent = `Lauf fehlgeschlagen: ${await apiFehlerMeldung(err)}`
      + (protokollGespeichert ? "" : " Das Laufprotokoll konnte nicht lokal gespeichert werden.");
    renderMissionLaeufe();
  } finally {
    laufendeMissionen.delete(id);
  }
}

function renderMissionLaeufe() {
  const ol = $("mission-laeufe");
  const logs = missionLaeufe().slice().reverse().slice(0, 20);
  ol.replaceChildren(...logs.map((x) => {
    const li = el("li", `${x.zeit ? new Date(x.zeit).toLocaleString("de-DE") : "Zeit unbekannt"} · Job ${x.job_id} · ${x.status}`
      + (Number.isFinite(Number(x.anzahl)) ? ` · ${x.anzahl} Treffer · ${x.meldungen || 0} neue BLITZ-Einträge` : ""), "karte");
    return li;
  }));
}

async function missionenAutomatischPruefen() {
  if (document.visibilityState !== "visible" || !navigator.locks?.request) return;
  const jetzt = Date.now();
  for (const m of missionen) {
    if (m.status !== "aktiv" || !m.automatisch || laufendeMissionen.has(m.id)) continue;
    const letzter = m.letzter_lauf_am ? Date.parse(m.letzter_lauf_am) : 0;
    if (letzter && jetzt < letzter + Number(m.intervall_minuten) * 60000) continue;
    try {
      await navigator.locks.request(`schnapper-mission-${m.id}`, { ifAvailable: true }, async (lock) => {
        if (lock) await missionLauf(m.id, true);
      });
    } catch (err) {
      $("mission-form-status").textContent = `Automatischer Lauf blockiert: ${err.message}`;
    }
  }
}

function gespeicherteAuswahl() {
  const ids = speicher.lesen("vergleich-auswahl", []);
  if (!Array.isArray(ids) || ids.some((x) => typeof x !== "string")) {
    speicher.beschaedigt.add("vergleich-auswahl");
    $("speicher-hinweis").hidden = false;
    return [];
  }
  return [...new Set(ids)].slice(0, MAX_MERK);
}

async function vergleichAnzeigen() {
  const ids = gespeicherteAuswahl();
  const box = $("preisvergleich");
  box.replaceChildren();
  if (!ids.length) {
    $("vergleich-leer").hidden = false;
    return;
  }
  $("vergleich-leer").hidden = true;
  const m = merkliste();
  let live = Object.create(null);
  try {
    const response = await fetch("/api/suche?mit_verdacht=1");
    if (response.ok) {
      const data = await response.json();
      for (const t of data.treffer || []) live[t.id] = t;
    }
  } catch { live = null; }
  const items = ids.filter((id) => m[id]).map((id) => {
    const saved = m[id];
    const current = live ? live[id] : null;
    return { id, saved, current, total: Number(current?.gesamtpreis ?? saved.gesamtpreis) };
  }).filter((x) => Number.isFinite(x.total) && x.total > 0);
  if (!items.length) {
    $("vergleich-leer").hidden = false;
    $("vergleich-leer").textContent = "Die ausgewählten Angebote sind nicht verfügbar. Prüfe die Merkliste oder lade eine Liste.";
    return;
  }
  const lowest = Math.min(...items.map((x) => x.total));
  for (const item of items) {
    const current = item.current;
    const source = current || item.saved;
    const section = el("article", undefined, "karte vergleich-karte");
    const title = el("h3", source.titel, "titel");
    const total = el("p", `Gesamtpreis inkl. angegebener Versandkosten: ${euro.format(item.total)}`, "preis");
    const details = el("p", [
      source.quelle ? `Quelle: ${source.quelle}` : "",
      source.versand !== undefined && source.versand !== null ? `Versand: ${euro.format(Number(source.versand))}` : "",
      current ? "Preis aus aktuell geladener Liste" : "letzter gespeicherter Stand",
      item.total === lowest ? "niedrigster ausgewählter Gesamtpreis" : "",
    ].filter(Boolean).join(" · "), "details");
    section.append(title, total, details);
    const warnings = current?.warnungen || item.saved.warnungen || [];
    if (warnings.length) section.append(el("p", warnings.join(" · "), "warnungen-text"));
    const history = current?.verlauf || item.saved.verlauf;
    if (history) {
      section.append(el("p",
        `${history.anzahl} Beobachtungen · ${euro.format(Number(history.tiefst))}–${euro.format(Number(history.hoechst))} über ${history.seit_tagen} Tage`
        + (history.vorher ? ` · vorher ${euro.format(Number(history.vorher))}` : ""), "details"));
    } else {
      section.append(el("p", "Kein belastbarer lokaler Preisverlauf vorhanden.", "details"));
    }
    if (source.referenzpreis && Number(source.referenzpreis) > 0) {
      section.append(el("p", `Angegebener Referenzpreis: ${euro.format(Number(source.referenzpreis))} — kein unabhängig bestätigter Marktpreis.`, "details"));
    } else {
      section.append(el("p", "Kein Referenzpreis; Rabattbewertung nicht verfügbar.", "details"));
    }
    const a = el("a", "Angebot öffnen ↗", "link");
    if (typeof source.url === "string" && /^https:\/\//.test(source.url)) {
      a.href = source.url; a.target = "_blank"; a.rel = "noopener noreferrer";
    } else a.remove();
    section.append(a);
    box.append(section);
  }
}

async function quellenAnzeigen() {
  try {
    const response = await fetch("/api/quellen");
    const daten = await response.json();
    if (!response.ok) throw new Error(daten.fehler || "Quellenstatus nicht verfügbar");
    $("quellen-status").textContent = (daten.quellen || []).map((q) =>
      `${q.name}: ${q.entscheidung}${q.hinweis ? ` — ${q.hinweis}` : ""}`).join(" · ");
  } catch (err) { $("quellen-status").textContent = `Quellenstatus nicht geladen: ${err.message}`; }
}

async function benachrichtigungenFreigeben() {
  if (!window.Notification) {
    $("benachrichtigung-status").textContent = "Dieser Browser unterstützt keine lokalen Browser-Benachrichtigungen; BLITZ bleibt in der App verfügbar.";
    return;
  }
  try {
    const permission = await Notification.requestPermission();
    $("benachrichtigung-status").textContent = permission === "granted"
      ? "Freigegeben. Eine lokale Browser-Benachrichtigung kann bei neuen Vordergrund-Treffern ausgelöst werden."
      : "Nicht freigegeben. Neue Treffer bleiben in der lokalen BLITZ-Liste.";
  } catch {
    $("benachrichtigung-status").textContent = "Freigabe nicht verfügbar. Treffer bleiben in der lokalen BLITZ-Liste.";
  }
}

async function pwaEinrichten() {
  if (!("serviceWorker" in navigator)) {
    $("pwa-status").textContent = "Dieser Browser unterstützt keinen Service Worker. Suche und lokale Daten funktionieren online weiter.";
    return;
  }
  try {
    await navigator.serviceWorker.register("/sw.js");
    $("pwa-status").textContent = window.isSecureContext
      ? "PWA-Shell registriert: App-Dateien können offline geladen werden; Such-API bleibt onlineabhängig."
      : "Service Worker nicht verfügbar: Für installierbare PWA auf Android ist HTTPS erforderlich.";
  } catch {
    $("pwa-status").textContent = "PWA-Offline-Shell konnte nicht registriert werden. Die normale Weboberfläche bleibt nutzbar.";
  }
}

function missionAusSuche() {
  const filter = new FormData($("filter"));
  const f = $("mission-form");
  f.elements.name.value = String(filter.get("text") || "").trim();
  f.elements.suche.value = String(filter.get("text") || "").trim();
  f.elements.max_preis.value = String(filter.get("max_preis") || "");
  f.elements.min_rabatt.value = String(filter.get("min_rabatt") || "");
  f.elements.region.value = String(filter.get("region") || "");
  f.elements.entfernung_km.value = String(filter.get("entfernung_km") || "");
  f.elements.zustand.value = String(filter.get("zustand") || "");
  f.elements.id.value = "";
  $("mission-form-titel").textContent = "Suchauftrag erstellen";
  $("mission-abbrechen").hidden = true;
  zeige("missionen");
  f.elements.intervall_minuten.focus();
}

// ---------- Ansichten ----------
function zaehler() {
  const n = Object.keys(merkliste()).length;
  $("anzahl-merk").hidden = n === 0;
  $("anzahl-merk").textContent = String(n);
  const neueMeldungen = blitzQueue().filter((x) => !x.gesehen).length;
  const blitze = alarmTreffer + neueMeldungen;
  $("anzahl-alarm").hidden = blitze === 0;
  $("anzahl-alarm").textContent = `⚡${blitze}`;
}

function zeige(ansicht) {
  for (const knopf of document.querySelectorAll(".ansichten button")) {
    knopf.setAttribute("aria-pressed", String(knopf.dataset.ansicht === ansicht));
  }
  for (const name of ["suche", "merkliste", "preisdetektiv", "missionen", "blitz", "einstellungen"]) {
    $("ansicht-" + name).hidden = name !== ansicht;
  }
  if (ansicht === "merkliste") merklisteZeigen();
  if (ansicht === "preisdetektiv") vergleichAnzeigen();
  if (ansicht === "missionen") { missionenLaden(); renderMissionLaeufe(); }
  if (ansicht === "blitz") renderBlitz();
  if (ansicht === "einstellungen") quellenAnzeigen();
  if (ansicht === "suche") suchen();
}

document.addEventListener("DOMContentLoaded", () => {
  $("barcode-form").addEventListener("submit", barcodeSuchen);
  $("filter").addEventListener("input", spaeter);
  $("filter").addEventListener("submit", (e) => { e.preventDefault(); suchen(); });
  $("datei").addEventListener("change", hochladen);
  $("alarm-anlegen").addEventListener("click", alarmAnlegen);
  $("mission-aus-suche").addEventListener("click", missionAusSuche);
  $("mission-form").addEventListener("submit", missionSpeichern);
  $("mission-abbrechen").addEventListener("click", () => {
    missionFormZuruecksetzen();
    $("mission-form-status").textContent = "Bearbeitung abgebrochen.";
  });
  $("vergleich-starten").addEventListener("click", () => zeige("preisdetektiv"));
  $("benachrichtigung-freigeben").addEventListener("click", benachrichtigungenFreigeben);
  $("backup-erstellen").addEventListener("click", sicherungHerunterladen);
  $("backup-datei").addEventListener("change", sicherungWiederherstellen);
  $("filter").addEventListener("input", alarmKnopf);
  $("filter").addEventListener("change", alarmKnopf);
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible") {
      missionenLaden().then(missionenAutomatischPruefen);
    }
  });
  for (const knopf of document.querySelectorAll(".ansichten button")) {
    knopf.addEventListener("click", () => zeige(knopf.dataset.ansicht));
  }
  try { window.localStorage.getItem("schnapper.test"); } catch { $("speicher-hinweis").hidden = false; }
  missionFormZuruecksetzen();
  if (!navigator.locks?.request) {
    $("mission-form").elements.automatisch.disabled = true;
    $("mission-form-status").textContent =
      "Automatik deaktiviert: dieser Browser unterstützt keine sicheren tabübergreifenden Sperren. Manuelle Läufe bleiben verfügbar.";
  }
  zaehler();
  suchen();
  alarmePruefen();
  renderBlitz();
  missionenLaden();
  renderMissionLaeufe();
  quellenAnzeigen();
  pwaEinrichten();
  setInterval(missionenAutomatischPruefen, 30_000);
});
