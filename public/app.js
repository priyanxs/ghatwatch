/* GhatWatch frontend: one page, no framework, no build step. Everything comes from /api.
   Interface text comes from /api/i18n so English and Hindi live in one place (utils/i18n.py). */
"use strict";

const PHASES = ["Pre-Visarjan", "Post-Visarjan"];
const PHASE_COLOUR = { "Pre-Visarjan": "#2563EB", "Post-Visarjan": "#EA580C" };
const NO_RECORD = "(no record)";

const state = { lang: localStorage.getItem("gw-lang") || "en", ghat: null };
let I18N, OVERVIEW;
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
/** Translate a category value such as lvl.High / phase.Post-Visarjan; unknown values pass through. */
const label = (prefix, value) => (I18N.strings[`${prefix}.${value}`] ? t(`${prefix}.${value}`) : value);
const ghatName = (row) => (state.lang === "hi" ? row.ghat_hi : row.ghat);

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

const statusClass = { PASS: "s-pass", BREACH: "s-breach", "NO DATA": "s-nodata" };
const readingCell = (raw, status) =>
    `${esc(raw === "" || raw === NO_RECORD ? "-" : raw)} <span class="${statusClass[status]}">${esc(label("status", status))}</span>`;
const list = (items) => `<ul>${items.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>`;

// ---------------------------------------------------------------- sections
function topBar() {
    const buttons = Object.entries(I18N.languages)
        .map(([code, name]) => `<button data-lang="${code}" aria-pressed="${code === state.lang}">${esc(name)}</button>`).join("");
    return `<div class="top"><img src="/icon.png" alt="GhatWatch logo"><div><div class="name">GhatWatch</div>
        <div class="sub">${esc(t("subtitle"))}</div></div><div class="lang" role="group" aria-label="Language">${buttons}</div></div>`;
}

function notices() {
    const o = OVERVIEW;
    const demo = o.is_mock ? `<div class="notice info">${t("demo")}</div>` : "";
    return `<div class="notice">${esc(o.disclaimer[state.lang])}</div>${demo}`;
}

function ranking() {
    const m = OVERVIEW.metrics;
    const rows = OVERVIEW.ranking.map((r) => {
        const lvl = r.risk_level.toLowerCase();
        return `<button class="ghat" data-ghat="${esc(r.ghat)}" aria-current="${r.ghat === state.ghat}">
            <span class="rank">${r.rank}</span><span class="gname">${esc(ghatName(r))}</span>
            <span class="badge ${lvl}">${esc(label("lvl", r.risk_level))}</span>
            <span class="meter" role="img" aria-label="${esc(t("r.score"))}: ${Math.round(r.risk_score)} / 100"><i class="${lvl}" style="width:${r.risk_score}%"></i></span>
            <span class="detail">${esc(t("r.line", { do: r.do_breaches, dt: r.do_tested, bod: r.bod_breaches, bt: r.bod_tested, gap: Math.round(r.gap_pct) }))}</span></button>`;
    }).join("");
    return `<h2 class="title">${esc(t("h.ranking"))}</h2>
        <p class="summary">${t("top.summary", { high: m.high_risk, n: m.ghats, breaches: m.breaches, gap: Math.round(m.no_data_pct) })}</p>
        <div class="ghats">${rows}</div><p class="hint">${esc(t("h.pick"))}</p>`;
}

function readingsTable(d) {
    const rows = d.readings.map((r) => `<tr><td>${r.year}</td><td>${esc(label("phase", r.phase))}</td>
        <td>${readingCell(r.do_raw, r.do_status)}</td><td>${readingCell(r.bod_raw, r.bod_status)}</td>
        <td>${esc(label("val", r.source))}</td><td>${esc(label("val", r.page))}</td></tr>`).join("");
    return `<div class="table-wrap"><table><thead><tr><th>${esc(t("c.year"))}</th><th>${esc(t("c.phase"))}</th>
        <th>${esc(t("c.do"))}</th><th>${esc(t("c.bod"))}</th><th>${esc(t("e.source"))}</th><th>${esc(t("e.page"))}</th></tr></thead>
        <tbody>${rows}</tbody></table></div>`;
}

function scoreExplanation(s) {
    const w = OVERVIEW.weights, pct = (n) => `${Math.round(n * 100)}%`, f = (n) => Number(n).toFixed(2);
    return md(t("d.how.body", { w1: pct(w.breach), w2: pct(w.severity), w3: pct(w.deterioration), gw: pct(w.gap),
        br: f(s.breach_rate), sev: f(s.severity), det: f(s.deterioration), hi: w.high_at, mid: w.medium_at }));
}

function focus(d) {
    const s = d.summary, lim = OVERVIEW.limits, other = state.lang === "en" ? "hi" : "en";
    const brief = d.brief[state.lang], otherBrief = d.brief[other];
    return `<section class="focus">
        <h2>${esc(state.lang === "hi" ? d.ghat_hi : d.ghat)}<span class="badge ${s.risk_level.toLowerCase()}">${esc(label("lvl", s.risk_level))}</span></h2>
        <p class="score">${esc(t("d.score"))}: <b>${Math.round(s.risk_score)} / 100</b> · ${esc(t("g.sub", { r: d.rank, n: OVERVIEW.ranking.length }))}</p>
        ${s.no_data ? `<div class="callout">${md(t("d.missing", { n: s.no_data, total: s.readings }))}</div>` : ""}
        ${s.floor_applied ? `<div class="callout info">${esc(t("d.floor", { m: OVERVIEW.weights.medium_at }))}</div>` : ""}
        <h3>${esc(t("sec.why"))}</h3>${list(brief.findings)}
        <h3>${esc(t("sec.do"))}</h3>${list(brief.actions)}
        <a class="btn" href="/api/ghats/${encodeURIComponent(d.ghat)}/brief.pdf" download>${esc(t("b.download"))}</a>
        <p class="hint">${esc(t("b.note"))}</p>
        <details><summary>${esc(t("b.other"))}</summary><div class="brief" lang="${other}">
            <h3>${esc(otherBrief.headline)}</h3>${list(otherBrief.findings)}${list(otherBrief.actions)}</div></details>
        <h3>${esc(t("sec.trend"))}</h3>
        <div class="charts"><div class="chart" id="chart-do"></div><div class="chart" id="chart-bod"></div></div>
        <p class="legend-note">${esc(t("tr.help"))}</p>
        <details><summary>${esc(t("sec.table"))}</summary><div><p class="muted" style="margin:0 0 8px">${esc(
            t("d.limit", { do: lim.do_min, bod: lim.bod_max }))}</p>${readingsTable(d)}</div></details>
        <details><summary>${esc(t("d.how"))}</summary><div>${scoreExplanation(s)}</div></details>
    </section>`;
}

/** One line per festival phase; a null value breaks the line (no data is never drawn as "clean"). */
function drawChart(el, readings, param, title, limit, limitText) {
    const traces = PHASES.map((phase, i) => {
        const rows = readings.filter((r) => r.phase === phase).sort((a, b) => a.year - b.year);
        const name = label("phase", phase);
        return {
            x: rows.map((r) => r.year), y: rows.map((r) => r[`${param}_value`]), name, mode: "lines+markers", connectgaps: false,
            line: { color: PHASE_COLOUR[phase], width: 2.5, dash: i === 0 ? "solid" : "dash" }, marker: { size: 7 },
            customdata: rows.map((r) => r[`${param}_raw`]), hovertemplate: `<b>${esc(name)}</b><br>%{x}: %{customdata} mg/L<extra></extra>`,
        };
    });
    Plotly.newPlot(el, traces, {
        title: { text: title, font: { size: 14, color: "#111827" }, x: 0.02 }, template: "plotly_white",
        paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)", font: { family: "Inter, 'Noto Sans Devanagari', sans-serif", color: "#374151", size: 12 },
        xaxis: { dtick: 1, gridcolor: "#F3F4F6", fixedrange: true }, yaxis: { title: "mg/L", rangemode: "tozero", gridcolor: "#F3F4F6", fixedrange: true },
        shapes: [{ type: "line", xref: "paper", x0: 0, x1: 1, y0: limit, y1: limit, line: { color: "#111827", dash: "dot", width: 1.5 } }],
        annotations: [{ xref: "paper", x: 1, y: limit, yanchor: "bottom", xanchor: "right", text: limitText, showarrow: false, font: { size: 11, color: "#111827" } }],
        height: 320, margin: { l: 44, r: 8, t: 44, b: 40 }, legend: { orientation: "h", y: -0.2 }, hovermode: "x unified",
    }, { displayModeBar: false, responsive: true });
}

// ---------------------------------------------------------------- rendering + events
async function loadFocus() {
    const slot = $("#focus");
    try {
        detailCache[state.ghat] ||= await api(`/api/ghats/${encodeURIComponent(state.ghat)}`);
    } catch (err) {
        slot.innerHTML = `<div class="notice error">${esc(t("err.load", { e: err.message }))}</div>`;
        return;
    }
    const d = detailCache[state.ghat], lim = OVERVIEW.limits;
    slot.innerHTML = focus(d);
    drawChart($("#chart-do"), d.readings, "do", t("tr.do"), lim.do_min, t("tr.lim.do", { v: lim.do_min }));
    drawChart($("#chart-bod"), d.readings, "bod", t("tr.bod"), lim.bod_max, t("tr.lim.bod", { v: lim.bod_max }));
}

function render() {
    document.documentElement.lang = state.lang;
    $("#app").innerHTML = `${topBar()}${notices()}${ranking()}<div id="focus"></div>`;
    document.querySelectorAll("[data-lang]").forEach((b) => (b.onclick = () => { state.lang = b.dataset.lang; localStorage.setItem("gw-lang", state.lang); render(); }));
    document.querySelectorAll("[data-ghat]").forEach((b) => (b.onclick = () => {
        state.ghat = b.dataset.ghat; location.hash = encodeURIComponent(state.ghat); render();
        $("#focus").scrollIntoView({ behavior: "smooth", block: "start" });
    }));
    return loadFocus();
}

async function init() {
    try {
        [I18N, OVERVIEW] = await Promise.all([api("/api/i18n"), api("/api/overview")]);
    } catch (err) {
        $("#app").innerHTML = `<div class="notice error">Could not load GhatWatch data (${esc(err.message)}). Please refresh.</div>`;
        return;
    }
    const fromHash = decodeURIComponent(location.hash.slice(1));
    state.ghat = OVERVIEW.ranking.some((r) => r.ghat === fromHash) ? fromHash : OVERVIEW.ranking[0].ghat;
    render();
}

init();
