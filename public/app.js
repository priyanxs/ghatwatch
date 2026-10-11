/* GhatWatch frontend: no framework, no build step. Everything comes from /api.
   Interface text comes from /api/i18n so English and Hindi live in one place (utils/i18n.py). */
"use strict";

const PHASES = ["Pre-Visarjan", "During", "Post-Visarjan"];
const PHASE_STYLE = { "Pre-Visarjan": ["#1F5A8C", "solid"], "During": ["#B7570B", "dash"], "Post-Visarjan": ["#1E7B4F", "dot"] };
const LEVEL_COLOUR = { High: "#B42318", Medium: "#B7570B", Low: "#1E7B4F" };
const NO_RECORD = "(no record)";

const state = { lang: localStorage.getItem("gw-lang") || "en", ghat: null, filter: "all", lakeParam: "do",
    size: localStorage.getItem("gw-size") || "", contrast: localStorage.getItem("gw-contrast") === "1" };
/** Text size and high-contrast preferences (accessibility): applied to the page and remembered. */
function applyPrefs() {
    document.documentElement.classList.remove("fs-lg", "fs-xl");
    if (state.size) document.documentElement.classList.add("fs-" + state.size);
    document.body.classList.toggle("hc", state.contrast);
}
const ink = () => (state.contrast ? "#FFFFFF" : "#1B2733");   // state.ghat is a ghat id (slug)
let I18N, OVERVIEW, WEEKLY;
const detailCache = {};

// ---------------------------------------------------------------- helpers
const $ = (sel) => document.querySelector(sel);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

/** Interface string for `key` in the current language, with {placeholders} filled in. */
function t(key, params = {}) {
    const entry = I18N.strings[key];
    const text = entry ? entry[state.lang] || entry.en : key;
    return text.replace(/\{(\w+)\}/g, (m, name) => (name in params ? params[name] : m));
}
/** Translate a category value such as lvl.High / phase.During; unknown values pass through. */
const label = (prefix, value) => (I18N.strings[`${prefix}.${value}`] ? t(`${prefix}.${value}`) : value);
const ghatName = (row) => (state.lang === "hi" ? row.ghat_hi : row.ghat);
const rowById = (id) => OVERVIEW.ranking.find((r) => r.id === id);

/** Tiny markdown for our own strings: **bold**, `code`, and "- " bullet lines. Input is escaped first. */
function md(text) {
    const inline = (s) => esc(s).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>").replace(/`(.+?)`/g, "<code>$1</code>");
    const lines = text.split("\n");
    if (lines.every((l) => l.startsWith("- "))) return `<ul>${lines.map((l) => `<li>${inline(l.slice(2))}</li>`).join("")}</ul>`;
    return inline(text);
}

async function api(path) {
    const res = await fetch(path);
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    return res.json();
}

const STATUS = { PASS: ["s-pass", "pass", "c-pass"], BREACH: ["s-breach", "breach", "c-breach"], "NO DATA": ["s-nodata", "nodata", "c-nodata"] };
const isBlank = (raw) => raw === "" || raw === NO_RECORD;
const readingCell = (raw, status) =>
    `${esc(isBlank(raw) ? "-" : raw)} <span class="${STATUS[status][0]}">${esc(label("status", status))}</span>`;
const list = (items) => `<ul>${items.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>`;
const phRange = () => `${OVERVIEW.limits.ph_min} to ${OVERVIEW.limits.ph_max}`;

// ---------------------------------------------------------------- page blocks
function siteHeader() {
    const periods = OVERVIEW.periods, mock = OVERVIEW.is_mock, lang = state.lang;
    const asOf = new Date(OVERVIEW.as_of + "T00:00:00").toLocaleDateString(lang === "hi" ? "hi-IN" : "en-IN", { day: "numeric", month: "long", year: "numeric" });
    const langBtns = Object.entries(I18N.languages).map(([code, name]) => `<button class="ubtn" data-lang="${code}" aria-pressed="${code === lang}" lang="${code}">${esc(name)}</button>`).join("");
    const sizeBtns = [["", "A"], ["lg", "A+"], ["xl", "A++"]].map(([v, l]) => `<button class="ubtn" data-size="${v}" aria-pressed="${state.size === v}" aria-label="${esc(t("gov.textsize"))} ${l}">${l}</button>`).join("");
    const nav = [["overview", "nav.overview"], ["ranking", "nav.ranking"], ["compare", "nav.compare"], ["lakes", "nav.lakes"], ["limits", "nav.limits"], ["sources", "nav.sources"]]
        .map(([id, k]) => `<a href="#${id}" data-nav="${id}">${esc(t(k))}</a>`).join("");
    const facts = [
        [t("hdr.prepared"), t("hdr.prepared.v")],
        [t("hdr.data"), mock ? t("hdr.data.demo") : t("hdr.data.v", { from: periods[0].year, to: periods[periods.length - 1].year })],
        [t("hdr.coverage"), t("hdr.coverage.v", { n: OVERVIEW.metrics.ghats, p: periods.length })],
        [t("hdr.standard"), t("hdr.standard.v")],
        [t("hdr.status"), mock ? t("hdr.strip.demo").split(":")[0] : t("hdr.status.v")],
        [t("hdr.asof"), asOf],
        ...(OVERVIEW.days_left != null ? [[t("hdr.event"), t("hdr.event.v", { n: OVERVIEW.days_left })]] : []),
    ].map(([k, v]) => `<div><dt>${esc(k)}</dt><dd>${esc(v)}</dd></div>`).join("");
    return `<a class="skip" href="#main">${esc(t("gov.skip"))}</a>
        <div class="utility"><div class="wrap"><div class="grow"></div>
            <div class="grp" role="group" aria-label="${esc(t("gov.textsize"))}"><span class="lbl">${esc(t("gov.textsize"))}</span>${sizeBtns}</div>
            <div class="grp"><button class="ubtn" id="hc-toggle" aria-pressed="${state.contrast}">${esc(t("gov.contrast"))}</button><button class="ubtn" id="print-btn">${esc(t("gov.print"))}</button></div>
            <div class="grp" role="group" aria-label="Language">${langBtns}</div></div></div>
        <header class="mast"><div class="wrap"><img src="/icon.png" alt="GhatWatch logo">
            <div><div class="org">${esc(t("hdr.prepared.v"))}</div><h1>${esc(t("hdr.title"))}</h1><p class="sub">${esc(t("hdr.sub"))}</p></div>
            <div class="asof">${esc(t("hdr.asof"))}<b>${esc(asOf)}</b></div></div></header>
        <nav class="nav" aria-label="Main">${`<div class="wrap">${nav}</div>`}</nav>
        <div class="wrap crumbs"><a href="#top">${esc(t("crumb.home"))}</a> &rsaquo; ${esc(t("hdr.title"))}</div>
        <div class="wrap" id="top"><div class="proto ${mock ? "demo" : ""}" role="note">${esc(mock ? t("hdr.strip.demo") : t("proto.notice"))}</div>
            <h2 class="heading" style="margin-top:20px" id="overview">${esc(t("doc.title"))}</h2><dl class="docinfo">${facts}</dl></div>`;
}

function stats() {
    const m = OVERVIEW.metrics;
    const stat = (k, v, cls = "", help = "") => `<div class="stat ${cls}" ${help ? `title="${esc(help)}"` : ""}><div class="k">${esc(k)}</div><div class="v">${esc(v)}</div></div>`;
    return `<h2 class="heading" style="margin-top:26px">${esc(t("sec.key"))}</h2><div class="stats">${stat(t("m.ghats"), m.ghats)}${stat(t("m.high"), m.high_risk, m.high_risk ? "hot" : "")}
        ${stat(t("m.breaches"), m.breaches, "", t("m.breaches.help"))}${stat(t("m.nodata"), `${Math.round(m.no_data_pct)}%`, m.no_data_pct > 10 ? "warm" : "", t("m.nodata.help"))}</div>`;
}

function rankCard() {
    const filters = ["all", "High", "Medium", "Low"].map((f) =>
        `<button class="chip" data-filter="${f}" aria-pressed="${state.filter === f}">${esc(f === "all" ? t("f.all") : label("lvl", f))}</button>`).join("");
    return `<div class="card"><h2>${esc(t("h.ranking"))}</h2><p class="lede">${esc(t("h.ranking.sub"))}</p>
        <div class="chips" role="group">${filters}</div><div class="ghats" id="rank-list">${rankRows()}</div>
        <a class="btn small" href="/api/readiness.pdf" download>${esc(t("city.download"))}</a>
        <p class="note" style="margin-top:6px">${esc(t("city.help"))}</p></div>`;
}

function rankRows() {
    return OVERVIEW.ranking.filter((r) => state.filter === "all" || r.risk_level === state.filter).map((r) => {
        const lvl = r.risk_level.toLowerCase();
        return `<button class="ghat" data-ghat="${esc(r.id)}" aria-current="${r.id === state.ghat}">
            <span class="rank">${r.rank}</span><span class="gname">${esc(ghatName(r))}</span>
            <span class="badge ${lvl}">${esc(label("lvl", r.risk_level))}</span>
            <span class="meter" role="img" aria-label="${esc(t("r.score"))}: ${Math.round(r.risk_score)} / 100"><i class="${lvl}" style="width:${r.risk_score}%"></i></span>
            <span class="trend ${r.trend}">${esc(t("trend." + r.trend))}</span>
            <span class="detail">${esc(t("r.line", { do: r.do_breaches, dt: r.do_tested, bod: r.bod_breaches, bt: r.bod_tested, ph: r.ph_breaches, pt: r.ph_tested, gap: Math.round(r.gap_pct) }))}</span></button>`;
    }).join("");
}

function ring(score, level) {
    const r = 48, c = 2 * Math.PI * r;
    return `<div class="ring" role="img" aria-label="${esc(t("d.score"))}: ${Math.round(score)} / 100">
        <svg width="116" height="116" viewBox="0 0 116 116"><circle cx="58" cy="58" r="${r}" fill="none" stroke="#E6F0F2" stroke-width="11"/>
        <circle cx="58" cy="58" r="${r}" fill="none" stroke="${LEVEL_COLOUR[level]}" stroke-width="11" stroke-linecap="round"
            stroke-dasharray="${(score / 100) * c} ${c}"/></svg>
        <div class="num"><div>${Math.round(score)}<small>/ 100</small></div></div></div>`;
}

const needPill = (level) => `<span class="need ${level.toLowerCase()}">${esc(label("lvl", level))}</span>`;
function needsRow(s) {
    return `<div class="needs">${["aeration", "cleaning", "testing"].map((n) =>
        `<span class="need-item">${esc(t("need." + n))} ${needPill(s["need_" + n])}</span>`).join("")}</div>`;
}

/** Latest period that has numbers for this ghat, all three phases, DO / BOD / pH: what an officer looks at first. */
function latestTiles(d) {
    const periods = OVERVIEW.periods.map((p) => p.key), overallLatest = periods[periods.length - 1];
    const hasNumbers = (key) => d.readings.some((r) => r.period === key && ["do", "bod", "ph"].some((p) => r[`${p}_value`] != null));
    const period = [...periods].reverse().find(hasNumbers) || overallLatest, lim = OVERVIEW.limits;
    const limitText = { do: t("latest.limit.do", { v: lim.do_min }), bod: t("latest.limit.bod", { v: lim.bod_max }), ph: t("latest.limit.ph", { v: phRange() }) };
    const tiles = ["do", "bod", "ph"].flatMap((p) => PHASES.map((phase) => {
        const r = d.readings.find((x) => x.period === period && x.phase === phase);
        const status = r ? r[`${p}_status`] : "NO DATA", raw = r ? r[`${p}_raw`] : "";
        return `<div class="tile ${STATUS[status][1]}"><div class="t1">${esc(t(`latest.${p}`))} · ${esc(label("phase", phase))}</div>
            <div class="t2">${esc(isBlank(raw) ? "—" : raw)} <span class="t3">${p === "ph" ? "" : "mg/L"}</span></div>
            <div class="t3">${esc(limitText[p])} · ${esc(label("status", status))}</div></div>`;
    }));
    const fallback = period !== overallLatest ? `<p class="callout info">${esc(t("latest.fallback", { p: overallLatest }))}</p>` : "";
    return `<div class="card"><h2>${esc(t("sec.latest", { y: period }))}</h2><div class="tiles">${tiles.join("")}</div>${fallback}</div>`;
}

/** Source report name; a link when the CSV or the report register gave a web address, jumping to the cited page for PDFs. */
function sourceCell(r) {
    const name = esc(label("val", r.source));
    if (!/^https?:\/\//i.test(r.source_url || "")) return name;
    const demo = /^MOCK/.test(r.source);  // demo page numbers are illustrative, so never jump to them
    const page = !demo && /^\d+$/.test(String(r.page)) && /\.pdf($|\?)/i.test(r.source_url) ? `#page=${r.page}` : "";
    return `<a href="${esc(r.source_url + page)}" target="_blank" rel="noopener noreferrer" title="${esc(t(demo ? "e.open.demo" : "e.open"))}">${name} ↗</a>`;
}

/** Lake monitoring (Apr 2025 to Mar 2026): the newest data in the pack. Context beside the ghat, never part of its score. */
const shortStation = (n) => n.replace(/^(Upper|Lower) Lake\s*(at|near)?\s*(Bhopal)?\s*/i, "").replace(/\s*,?\s*Spill Out Let.*$/i, "").trim() || n;
function lakesCard(d) {
    const stations = OVERVIEW.lakes.stations.filter((s) => s.lake === d.lake);
    if (!d.lake || !stations.length) return `<div class="card"><h2>${esc(t("sec.lakes"))}</h2><p class="note" style="margin-top:6px">${esc(t("lakes.none"))}</p></div>`;
    const range = (a, b, n) => (a == null ? "—" : `${a}–${b} · <b>${n}</b>`);
    const rows = stations.map((s) => `<tr class="${s.id === d.nearest_station ? "near" : ""}"><td class="name">${esc(s.name)}${s.id === d.nearest_station
        ? ` <span class="tagnear">${esc(t("lakes.nearest"))}</span>` : ""}</td><td>${s.months_measured}</td><td>${range(s.do_min, s.do_max, s.do_months_below)}</td>
        <td>${range(s.ph_min, s.ph_max, s.ph_months_outside)}</td><td>${s.bod3_max ?? "—"}</td></tr>`).join("");
    return `<div class="card"><h2>${esc(t("sec.lakes"))}</h2><p class="note" style="margin:4px 0 8px">${esc(t("lakes.help"))}</p>
        <div id="chart-lake" class="chart" style="min-height:300px"></div>
        <div class="table-wrap"><table><thead><tr><th>${esc(t("lakes.station"))}</th><th>${esc(t("lakes.months"))}</th><th>${esc(t("lakes.do"))}</th>
        <th>${esc(t("lakes.ph"))}</th><th>${esc(t("lakes.bod"))}</th></tr></thead><tbody>${rows}</tbody></table></div>
        <p class="note" style="margin-top:8px">${esc(t("lakes.bodnote"))}</p></div>`;
}

function readingsTable(d) {
    const rows = d.readings.map((r) => `<tr><td>${esc(r.period)}</td><td>${esc(label("phase", r.phase))}</td>
        <td>${readingCell(r.do_raw, r.do_status)}</td><td>${readingCell(r.bod_raw, r.bod_status)}</td><td>${readingCell(r.ph_raw, r.ph_status)}</td>
        <td>${sourceCell(r)}</td><td>${esc(label("val", r.page))}</td></tr>`).join("");
    return `<div class="table-wrap"><table><thead><tr><th>${esc(t("c.period"))}</th><th>${esc(t("c.phase"))}</th><th>${esc(t("c.do"))}</th>
        <th>${esc(t("c.bod"))}</th><th>${esc(t("c.ph"))}</th><th>${esc(t("e.source"))}</th><th>${esc(t("e.page"))}</th></tr></thead><tbody>${rows}</tbody></table></div>`;
}

function scoreExplanation(s) {
    const w = OVERVIEW.weights, pct = (n) => `${Math.round(n * 100)}%`, f = (n) => Number(n).toFixed(2);
    return md(t("d.how.body", { w1: pct(w.breach), w2: pct(w.severity), w3: pct(w.deterioration), gw: pct(w.gap),
        br: f(s.breach_rate), sev: f(s.severity), det: f(s.deterioration), hi: w.high_at, mid: w.medium_at }));
}

/** A short, forwardable message: headline, first finding, first action, and a link to this ghat. */
function whatsappLink(d) {
    const b = d.brief[state.lang];
    const msg = `*${b.headline}*\n• ${b.findings[0]}\n• ${b.actions[0]}\n${location.origin}/#${d.id}`;
    return `https://wa.me/?text=${encodeURIComponent(msg)}`;
}

function briefCard(d) {
    const cols = [["en", "English", ["Findings", "Recommended actions"]], ["hi", "हिन्दी", ["निष्कर्ष", "अनुशंसित कार्रवाई"]]]
        .map(([code, title, heads]) => `<div class="brief" lang="${code}"><span class="tag">${title}</span>
            <h3>${esc(d.brief[code].headline)}</h3><h4>${heads[0]}</h4>${list(d.brief[code].findings)}
            <h4>${heads[1]}</h4>${list(d.brief[code].actions)}</div>`).join("");
    return `<div class="card"><h2>${esc(t("sec.brief"))}</h2><div class="briefs">${cols}</div>
        <a class="btn" href="/api/ghats/${d.id}/brief.pdf" download>${esc(t("b.download"))}</a>
        <a class="btn wa" href="${whatsappLink(d)}" target="_blank" rel="noopener noreferrer">${esc(t("share.wa"))}</a>
        <p class="note" style="margin-top:8px">${esc(t("b.note"))}</p></div>`;
}

function detail(d) {
    const s = d.summary, lim = OVERVIEW.limits, brief = d.brief[state.lang], row = rowById(d.id);
    const place = [d.water_body, d.confidence && d.confidence !== "high" ? `match: ${d.confidence}` : ""].filter(Boolean).join(" · ");
    return `<div class="card top-card"><div>
            <h2>${esc(ghatName(row))}<span class="badge ${s.risk_level.toLowerCase()}">${esc(label("lvl", s.risk_level))}</span></h2>
            <p class="rankline">${esc(t("g.sub", { r: d.rank, n: OVERVIEW.ranking.length }))}${place ? ` · ${esc(place)}` : ""}</p>
            <p class="verdict">${esc(brief.headline)}</p>${needsRow(s)}
            ${s.no_data ? `<div class="callout">${md(t("d.missing", { n: s.no_data, total: s.readings }))}</div>` : ""}
            ${s.floor_applied ? `<div class="callout info">${esc(t("d.floor", { m: OVERVIEW.weights.medium_at }))}</div>` : ""}</div>
            ${ring(s.risk_score, s.risk_level)}</div>
        ${latestTiles(d)}
        ${lakesCard(d)}
        <div class="two" style="margin-top:18px"><div class="card why" style="margin:0"><h3>${esc(t("sec.why"))}</h3>${list(brief.findings)}</div>
            <div class="card do" style="margin:0"><h3>${esc(t("sec.do"))}</h3>${list(brief.actions)}</div></div>
        <div class="card"><h2>${esc(t("sec.trend"))}</h2><div class="charts"><div class="chart" id="chart-do"></div><div class="chart" id="chart-bod"></div><div class="chart" id="chart-ph"></div></div>
            <p class="note">${esc(t("tr.help"))}</p></div>
        ${briefCard(d)}
        <details><summary>${esc(t("sec.table"))}</summary><div><p class="note" style="margin-bottom:8px">${esc(
            t("d.limit", { do: lim.do_min, bod: lim.bod_max, phmin: lim.ph_min, phmax: lim.ph_max }))}</p>${readingsTable(d)}</div></details>
        <details><summary>${esc(t("d.how"))}</summary><div>${scoreExplanation(s)}</div></details>`;
}

function compareSection() {
    const periods = OVERVIEW.periods, head = periods.map((p) => `<th>${esc(p.key)}</th>`).join("");
    const grid = OVERVIEW.ranking.map((r) => {
        const cells = periods.map((p) => {
            const cell = (OVERVIEW.timeline[r.ghat] || {})[p.key] || {};
            const trio = PHASES.map((ph) => {
                const s = cell[ph];
                const title = `${ghatName(r)} · ${p.key} · ${label("phase", ph)}: ${s ? label("status", s) : "—"}`;
                return `<i class="${s ? STATUS[s][2] : "c-none"}" title="${esc(title)}"></i>`;
            }).join("");
            return `<td><div class="cellpair">${trio}</div></td>`;
        }).join("");
        return `<tr class="click ${r.id === state.ghat ? "sel" : ""}" data-ghat="${esc(r.id)}" tabindex="0"><td class="name">${esc(ghatName(r))}</td>${cells}</tr>`;
    }).join("");
    const plan = OVERVIEW.ranking.map((r) => `<tr class="click" data-ghat="${esc(r.id)}" tabindex="0"><td class="name">${esc(ghatName(r))}</td>
        ${["aeration", "cleaning", "testing"].map((n) => `<td>${needPill(r["need_" + n])}</td>`).join("")}</tr>`).join("");
    const legend = [["c-pass", "lg.pass"], ["c-breach", "lg.breach"], ["c-nodata", "lg.nodata"]]
        .map(([c, k]) => `<span><i class="${c}"></i>${esc(t(k))}</span>`).join("");
    return `<h2 class="section-title" id="compare">${esc(t("sec.compare"))}</h2>
        ${mapSection()}
        <div class="two" style="margin-top:18px"><div class="card" style="margin:0"><h3>${esc(t("cmp.score"))}</h3><div id="chart-compare" style="min-height:320px"></div></div>
        <div class="card" style="margin:0"><h3>${esc(t("sec.plan"))}</h3><p class="note" style="margin-bottom:8px">${esc(t("plan.help"))}</p>
            <div class="table-wrap"><table class="plan"><thead><tr><th class="name"></th><th>${esc(t("need.aeration"))}</th><th>${esc(t("need.cleaning"))}</th><th>${esc(t("need.testing"))}</th></tr></thead>
            <tbody>${plan}</tbody></table></div></div></div>
        <div class="card"><h3>${esc(t("sec.matrix"))}</h3><p class="note" style="margin-bottom:6px">${esc(t("matrix.help"))}</p>
            <div class="table-wrap"><table class="matrix"><thead><tr><th class="name"></th>${head}</tr></thead><tbody>${grid}</tbody></table></div>
            <div class="legend">${legend}</div></div>`;
}

function caveatsSection() {
    const sum = (k) => OVERVIEW.ranking.reduce((a, r) => a + r[k], 0);
    const verified = OVERVIEW.is_mock ? "" : `<p class="verified">✔ ${esc(t("sec.verified", { do: sum("do_breaches"), dt: sum("do_tested"), bod: sum("bod_breaches"), bt: sum("bod_tested") }))}</p>`;
    return `<div class="card" id="limits" style="margin-top:28px"><h2>${esc(t("sec.caveats"))}</h2><p class="note" style="margin:4px 0 10px">${esc(t("caveats.help"))}</p>
        ${verified}<ul class="caveats">${OVERVIEW.caveats.map((c) => `<li>${esc(c[state.lang])}</li>`).join("")}</ul></div>`;
}

/** Every lake station and month for one parameter. Red = outside the CPCB Class B limit; hatched = no reading. */
function lakeDataTable() {
    const L = OVERVIEW.lakes, lim = OVERVIEW.limits, p = state.lakeParam;
    const outside = (v) => (p === "do" ? v < lim.do_min : p === "ph" ? v < lim.ph_min || v > lim.ph_max : false);   // BOD (3 days) has no limit to judge against
    const body = ["Upper Lake", "Lower Lake"].map((lake) => {
        const rows = L.stations.filter((s) => s.lake === lake).map((s) => `<tr><td class="name">${esc(s.name)}</td>${L.months.map((m, i) => {
            const v = s.series[p]?.[i];
            return v == null ? `<td class="lk none" title="${esc(t("lakes.nodata"))}">–</td>` : `<td class="lk ${outside(v) ? "bad" : ""}" title="${esc(s.dates[m] || m)}">${v}</td>`;
        }).join("")}</tr>`).join("");
        return rows ? `<tr class="lakehead"><td colspan="${L.months.length + 1}">${esc(lake)}</td></tr>${rows}` : "";
    }).join("");
    return `<div class="table-wrap"><table class="lakedata"><thead><tr><th class="name">${esc(t("lakes.station"))}</th>${L.months.map((m) => `<th>${m}</th>`).join("")}</tr></thead><tbody>${body}</tbody></table></div>`;
}

function lakeDataSection() {
    if (!OVERVIEW.lakes.stations.length) return "";
    const tabs = ["do", "ph", "bod3"].map((p) => `<button class="chip" data-lakeparam="${p}" aria-pressed="${state.lakeParam === p}">${esc(t("lakedata." + p))}</button>`).join("");
    return `<div class="card" id="lakes" style="margin-top:28px"><h2>${esc(t("sec.lakedata"))}</h2><p class="note" style="margin:4px 0 6px">${esc(t("lakedata.help"))}</p>
        <div class="chips" role="group">${tabs}</div><div id="lakedata">${lakeDataTable()}</div>
        <p class="note" style="margin-top:8px">${esc(t("lakes.bodnote"))}</p></div>`;
}

function weeklySection() {
    const w = WEEKLY, a = w.auto_post;
    const status = a.blocked_demo ? t("weekly.demo") : a.enabled && a.channels.length ? t("weekly.on", { ch: a.channels.join(", ") }) : t("weekly.off");
    const box = (code, title) => `<div class="caption-box" lang="${code}"><div class="cap-head"><b>${title}</b>
        <button class="copy" data-copy="${code}">${esc(t("weekly.copy"))}</button></div><pre>${esc(w["caption_" + code])}</pre></div>`;
    return `<div class="card" style="margin-top:28px"><h2>${esc(t("weekly.title"))}</h2>
        <p class="note" style="margin:4px 0 12px">${esc(t("weekly.lede"))}</p>
        <div class="two" style="margin:0">${box("en", "English")}${box("hi", "हिन्दी")}</div>
        <p class="note" style="margin-top:10px"><b>${esc(status)}</b></p></div>`;
}

function sourcesSection() {
    const src = OVERVIEW.sources, link = (x) => `<li><a href="${esc(x.url)}" target="_blank" rel="noopener noreferrer">${esc(x.title)} ↗</a></li>`;
    return `<div class="card" id="sources" style="margin-top:28px"><h2>${esc(t("src.title"))}</h2>
        <p class="note" style="margin:4px 0 10px">${esc(t(OVERVIEW.is_mock ? "src.demo" : "src.live"))}</p>
        <ul class="links">${src.reports.map(link).join("")}${src.references.map(link).join("")}</ul></div>`;
}

// ---------------------------------------------------------------- map
let MAP = null;
function mapSection() {
    const unmapped = OVERVIEW.ranking.filter((r) => !r.location).map((r) => ghatName(r));
    return `<div class="card map-card"><div class="map-head"><div><h2>${esc(t("sec.map"))}</h2><p class="lede">${esc(t("map.help"))}</p></div></div>
        <div id="map" role="img" aria-label="${esc(t("sec.map"))}"></div>
        ${unmapped.length ? `<p class="note" style="margin-top:8px">${esc(t("map.unmapped", { names: unmapped.join(", ") }))}</p>` : ""}</div>`;
}

/** Ghats that share a point (two sites on the same lake) are fanned out slightly so both stay visible. */
function spreadPoints(rows) {
    const groups = {};
    rows.forEach((r) => (groups[`${r.location.lat.toFixed(3)},${r.location.lon.toFixed(3)}`] ||= []).push(r));
    return rows.map((r) => {
        const g = groups[`${r.location.lat.toFixed(3)},${r.location.lon.toFixed(3)}`], i = g.indexOf(r);
        if (g.length === 1) return [r.location.lat, r.location.lon];
        const angle = (2 * Math.PI * i) / g.length, d = 0.004;   // about 400 m
        return [r.location.lat + d * Math.sin(angle), r.location.lon + d * Math.cos(angle) * 1.1];
    });
}

function drawMap() {
    const el = $("#map");
    if (MAP) { MAP.remove(); MAP = null; }
    if (typeof L === "undefined") { el.innerHTML = `<p class="note" style="padding:20px">${esc(t("map.offline"))}</p>`; return; }
    const rows = OVERVIEW.ranking.filter((r) => r.location);
    if (!rows.length) { el.remove(); return; }
    MAP = L.map(el, { scrollWheelZoom: false, zoomControl: true });
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 18, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' }).addTo(MAP);
    const points = spreadPoints(rows);
    rows.forEach((r, i) => {
        const size = 34 + Math.round(r.risk_score / 100 * 22), lvl = r.risk_level.toLowerCase();
        const icon = L.divIcon({ className: "", iconSize: [size, size], iconAnchor: [size / 2, size / 2], popupAnchor: [0, -size / 2],
            html: `<div class="gw-pin ${lvl} ${r.id === state.ghat ? "sel" : ""}" style="width:${size}px;height:${size}px">${lvl === "high" ? '<span class="pulse"></span>' : ""}<b>${Math.round(r.risk_score)}</b></div>` });
        const note = r.location.precision === "exact" ? t("map.exact") : t("map.approx");
        const needs = ["aeration", "cleaning", "testing"].map((n) => `<span class="need-item">${esc(t("need." + n))} ${needPill(r["need_" + n])}</span>`).join("");
        const popup = `<div class="pop"><b>${esc(ghatName(r))}</b><div class="pop-row"><span class="badge ${lvl}">${esc(label("lvl", r.risk_level))}</span>
            <span>${Math.round(r.risk_score)} / 100</span></div><div class="needs" style="margin:6px 0">${needs}</div>
            <p class="pop-note">${esc(note)}</p><button class="pop-btn" data-open="${esc(r.id)}">${esc(t("map.open"))} →</button></div>`;
        L.marker(points[i], { icon, title: ghatName(r), riseOnHover: true }).addTo(MAP).bindPopup(popup, { maxWidth: 260 });
    });
    MAP.fitBounds(L.latLngBounds(points), { padding: [50, 50], maxZoom: 14 });
    MAP.on("popupopen", (e) => e.popup.getElement().querySelector("[data-open]")?.addEventListener("click", (ev) => selectGhat(ev.target.dataset.open)));
    el.addEventListener("click", () => MAP.scrollWheelZoom.enable(), { once: true });   // wheel zoom only after the first click, so page scrolling is not hijacked
}

// ---------------------------------------------------------------- charts
const axis = () => ({ gridcolor: state.contrast ? "#555555" : "#DDE3EA", linecolor: state.contrast ? "#FFFFFF" : "#8A99AB", fixedrange: true });
const plotBase = () => ({ paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)", template: state.contrast ? "plotly_dark" : "plotly_white",
    font: { family: "'Noto Sans', 'Noto Sans Devanagari', sans-serif", color: ink(), size: 12 } });
const PLOT_CFG = { displayModeBar: false, responsive: true };

/** Plotly comes from a CDN; if it is blocked, say so in place of the charts and keep everything else working. */
function chartsAvailable() {
    if (typeof Plotly !== "undefined") return true;
    document.querySelectorAll(".chart, #chart-compare").forEach((el) => (el.innerHTML = `<p class="note">${esc(t("tr.offline"))}</p>`));
    return false;
}

/** Monthly DO at each station of the ghat's lake, with the 5 mg/L limit. A gap (May) is a gap, not a pass. */
function drawLakeChart(d) {
    const el = $("#chart-lake");
    if (!el) return;
    const L = OVERVIEW.lakes, stations = L.stations.filter((s) => s.lake === d.lake), colours = ["#1F5A8C", "#B7570B", "#1E7B4F", "#6B3FA0", "#B42318"];
    const traces = stations.map((s, i) => ({ x: L.months, y: s.series.do, name: shortStation(s.name), mode: "lines+markers", connectgaps: false,
        line: { color: colours[i % colours.length], width: s.id === d.nearest_station ? 4 : 2.2 }, marker: { size: 6 },
        customdata: L.months.map((m) => s.dates[m] || ""), hovertemplate: "<b>%{fullData.name}</b><br>%{x} (%{customdata}): %{y} mg/L<extra></extra>" }));
    Plotly.newPlot(el, traces, { ...plotBase(), title: { text: t("lakes.chart"), font: { size: 14 }, x: 0.02 },
        xaxis: { ...axis(), type: "category", categoryorder: "array", categoryarray: L.months }, yaxis: { ...axis(), title: "mg/L", rangemode: "tozero" },
        shapes: [hline(OVERVIEW.limits.do_min)], annotations: [{ xref: "paper", x: 1, y: 1, yref: "paper", yanchor: "bottom", xanchor: "right", text: t("tr.lim.do", { v: OVERVIEW.limits.do_min }), showarrow: false, font: { size: 11 } }],
        height: 300, margin: { l: 44, r: 8, t: 50, b: 40 }, legend: { orientation: "h", y: -0.2 }, hovermode: "x unified" }, PLOT_CFG);
}

/** One line per phase over every period. A null value breaks the line: no data is never drawn as "clean". */
function drawTrend(el, readings, param, title, limitShapes, limitText) {
    const keys = OVERVIEW.periods.map((p) => p.key);
    const traces = PHASES.map((phase) => {
        const byPeriod = Object.fromEntries(readings.filter((r) => r.phase === phase).map((r) => [r.period, r]));
        const name = label("phase", phase);
        return {
            x: keys, y: keys.map((k) => byPeriod[k]?.[`${param}_value`] ?? null), name, mode: "lines+markers", connectgaps: false,
            line: { color: PHASE_STYLE[phase][0], width: 2.5, dash: PHASE_STYLE[phase][1] }, marker: { size: 7 },
            customdata: keys.map((k) => (byPeriod[k] && !isBlank(byPeriod[k][`${param}_raw`]) ? byPeriod[k][`${param}_raw`] : "no data")),
            hovertemplate: `<b>${esc(name)}</b><br>%{x}: %{customdata}<extra></extra>`,
        };
    });
    Plotly.newPlot(el, traces, { ...plotBase(), title: { text: title, font: { size: 14 }, x: 0.02 },
        xaxis: { ...axis(), type: "category", categoryorder: "array", categoryarray: keys, tickangle: -30 },
        yaxis: { ...axis(), title: param === "ph" ? "pH" : "mg/L", rangemode: param === "ph" ? "normal" : "tozero" },
        shapes: limitShapes, annotations: [{ xref: "paper", x: 1, y: 1, yref: "paper", yanchor: "bottom", xanchor: "right", text: limitText, showarrow: false, font: { size: 11 } }],
        height: 320, margin: { l: 44, r: 8, t: 50, b: 70 }, legend: { orientation: "h", y: -0.35 }, hovermode: "x unified" }, PLOT_CFG);
}
const hline = (y) => ({ type: "line", xref: "paper", x0: 0, x1: 1, y0: y, y1: y, line: { color: ink(), dash: "dot", width: 1.5 } });

/** Horizontal bars, one per ghat, coloured by risk level. Clicking a bar opens that ghat. */
function drawCompare() {
    if (!chartsAvailable()) return;
    const rows = OVERVIEW.ranking, el = $("#chart-compare");
    Plotly.newPlot(el, [{
        type: "bar", orientation: "h", x: rows.map((r) => r.risk_score), y: rows.map(ghatName), customdata: rows.map((r) => r.id),
        marker: { color: rows.map((r) => LEVEL_COLOUR[r.risk_level]) }, text: rows.map((r) => Math.round(r.risk_score)),
        textposition: "outside", cliponaxis: false, hovertemplate: "%{y}: %{x:.0f} / 100<extra></extra>",
    }], { ...plotBase(), xaxis: { ...axis(), range: [0, 100] }, yaxis: { autorange: "reversed", fixedrange: true, automargin: true },
        height: 320, margin: { l: 10, r: 30, t: 8, b: 30 }, bargap: 0.35 }, PLOT_CFG);
    el.on("plotly_click", (e) => selectGhat(e.points[0].customdata));
}

// ---------------------------------------------------------------- rendering + events
async function loadDetail() {
    const slot = $("#detail"), wanted = state.ghat, lang = state.lang;
    try {
        detailCache[wanted] ||= await api(`/api/ghats/${wanted}`);
    } catch (err) {
        if (wanted !== state.ghat) return;
        slot.innerHTML = `<div class="notice error">${esc(t("err.load", { e: err.message }))}</div>`;
        return;
    }
    if (wanted !== state.ghat || lang !== state.lang) return;  // a newer selection or language took over
    const d = detailCache[wanted], lim = OVERVIEW.limits;
    slot.innerHTML = detail(d);
    if (!chartsAvailable()) return;
    drawTrend($("#chart-do"), d.readings, "do", t("tr.do"), [hline(lim.do_min)], t("tr.lim.do", { v: lim.do_min }));
    drawTrend($("#chart-bod"), d.readings, "bod", t("tr.bod"), [hline(lim.bod_max)], t("tr.lim.bod", { v: lim.bod_max }));
    drawLakeChart(d);
    drawTrend($("#chart-ph"), d.readings, "ph", t("tr.ph"), [{ type: "rect", xref: "paper", x0: 0, x1: 1, y0: lim.ph_min, y1: lim.ph_max, fillcolor: "rgba(30,123,79,.14)", line: { width: 0 } }],
        t("tr.lim.ph", { v: phRange() }));
}

function bindRankList() {
    document.querySelectorAll("#rank-list [data-ghat]").forEach((b) => (b.onclick = () => selectGhat(b.dataset.ghat)));
}

function render() {
    document.documentElement.lang = state.lang;
    $("#app").innerHTML = `${siteHeader()}<main class="wrap" id="main" tabindex="-1">${stats()}
        <div class="grid" id="ranking"><aside class="rail">${rankCard()}</aside><section id="detail"></section></div>
        ${compareSection()}${lakeDataSection()}${caveatsSection()}${weeklySection()}${sourcesSection()}</main>
        <footer class="site"><div class="wrap"><p>${esc(t("foot.formal"))}</p><p>${esc(t("foot"))}</p>
            <div class="flinks"><a href="https://github.com/priyanxs/ghatwatch/issues" target="_blank" rel="noopener noreferrer">${esc(t("foot.feedback"))}</a>
            <a href="https://github.com/priyanxs/ghatwatch" target="_blank" rel="noopener noreferrer">${esc(t("foot.code"))}</a><a href="#top">${esc(t("foot.top"))}</a></div>
            <p>${esc(t("foot.updated", { d: new Date(OVERVIEW.as_of + "T00:00:00").toLocaleDateString(state.lang === "hi" ? "hi-IN" : "en-IN", { day: "numeric", month: "long", year: "numeric" }) }))}</p></div></footer>`;
    document.querySelectorAll("[data-lang]").forEach((b) => (b.onclick = () => { state.lang = b.dataset.lang; localStorage.setItem("gw-lang", state.lang); render(); }));
    document.querySelectorAll("[data-size]").forEach((b) => (b.onclick = () => { state.size = b.dataset.size; localStorage.setItem("gw-size", state.size); applyPrefs(); render(); }));
    $("#hc-toggle").onclick = () => { state.contrast = !state.contrast; localStorage.setItem("gw-contrast", state.contrast ? "1" : "0"); applyPrefs(); render(); };
    $("#print-btn").onclick = () => window.print();
    document.querySelectorAll("[data-filter]").forEach((b) => (b.onclick = () => {
        state.filter = b.dataset.filter;
        document.querySelectorAll("[data-filter]").forEach((c) => c.setAttribute("aria-pressed", c.dataset.filter === state.filter));
        $("#rank-list").innerHTML = rankRows(); bindRankList();
    }));
    document.querySelectorAll("[data-lakeparam]").forEach((b) => (b.onclick = () => {
        state.lakeParam = b.dataset.lakeparam;
        document.querySelectorAll("[data-lakeparam]").forEach((c) => c.setAttribute("aria-pressed", c.dataset.lakeparam === state.lakeParam));
        $("#lakedata").innerHTML = lakeDataTable();
    }));
    document.querySelectorAll("tr.click").forEach((tr) => {
        tr.onclick = () => selectGhat(tr.dataset.ghat);
        tr.onkeydown = (e) => (e.key === "Enter" || e.key === " ") && (e.preventDefault(), selectGhat(tr.dataset.ghat));
    });
    document.querySelectorAll("[data-copy]").forEach((b) => (b.onclick = async () => {
        try { await navigator.clipboard.writeText(WEEKLY["caption_" + b.dataset.copy]); } catch { return; }
        const old = b.textContent; b.textContent = t("weekly.copied"); setTimeout(() => (b.textContent = old), 1500);
    }));
    bindRankList();
    drawMap();
    drawCompare();
    return loadDetail();
}

function selectGhat(id) {
    state.ghat = id; location.hash = id; render();
    // The details sit near the top of the page; picking a ghat from the map, charts or grid further down must show them.
    const top = $("#detail").getBoundingClientRect().top;
    if (top < 0 || top > window.innerHeight * 0.7 || window.innerWidth <= 1060) $("#detail").scrollIntoView({ behavior: "smooth", block: "start" });
}

async function init() {
    try {
        [I18N, OVERVIEW, WEEKLY] = await Promise.all([api("/api/i18n"), api("/api/overview"), api("/api/weekly-report")]);
    } catch (err) {
        $("#app").innerHTML = `<div class="wrap"><div class="notice error" style="margin-top:30px">Could not load GhatWatch data (${esc(err.message)}). Please refresh.</div></div>`;
        return;
    }
    applyPrefs();
    const fromHash = decodeURIComponent(location.hash.slice(1));
    state.ghat = OVERVIEW.ranking.some((r) => r.id === fromHash) ? fromHash : OVERVIEW.ranking[0].id;
    render();
}

init();
