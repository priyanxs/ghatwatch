/* GhatWatch frontend: fetches everything from /api and renders it. No build step, no framework.
   Interface text comes from /api/i18n so English and Hindi live in one place (utils/i18n.py). */
"use strict";

const PHASES = ["Pre-Visarjan", "Post-Visarjan"];
const PHASE_COLOUR = { "Pre-Visarjan": "#60A5FA", "Post-Visarjan": "#FB923C" };
const NO_RECORD = "(no record)";

const state = { lang: localStorage.getItem("gw-lang") || "en", ghat: null, tab: "dive" };
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

const statusClass = { PASS: "pass", BREACH: "breach", "NO DATA": "nodata" };
const readingCell = (raw, status) =>
    `${esc(raw === "" || raw === NO_RECORD ? "-" : raw)} <span class="status ${statusClass[status]}">${esc(label("status", status))}</span>`;

// ---------------------------------------------------------------- page sections
function sidebar() {
    const options = OVERVIEW.ranking
        .map((r, i) => `<option value="${esc(r.ghat)}" ${r.ghat === state.ghat ? "selected" : ""}>#${i + 1}  ${esc(ghatName(r))}</option>`)
        .join("");
    const langButtons = Object.entries(I18N.languages)
        .map(([code, name]) => `<button data-lang="${code}" aria-pressed="${code === state.lang}">${esc(name)}</button>`).join("");
    $("#sidebar").innerHTML = `
        <div class="brand"><img src="/icon.png" alt="GhatWatch logo"><div>
            <div class="brand-name">GhatWatch</div><div class="brand-sub">${esc(t("sb.brand"))}</div></div></div>
        <div class="field"><span class="field-label">${esc(t("sb.lang"))}</span><div class="seg" role="group" aria-label="Language">${langButtons}</div></div>
        <div class="field"><label class="field-label" for="ghat-select">${esc(t("sb.select"))}</label>
            <select id="ghat-select">${options}</select></div>
        <p class="side-note">${esc(t("sb.caption"))}</p>`;
    $("#ghat-select").onchange = (e) => selectGhat(e.target.value);
    document.querySelectorAll("[data-lang]").forEach((b) => (b.onclick = () => setLang(b.dataset.lang)));
}

function header() {
    const o = OVERVIEW;
    const pills = [t("pill.ghats", { n: o.metrics.ghats }), t("pill.cpcb"), t("pill.brief")]
        .map((p) => `<span class="pill">${esc(p)}</span>`).join("") + `<span class="pill warn">${esc(t("pill.hist"))}</span>`;
    const notes = o.notes.length
        ? `<details><summary>${esc(t("notes", { n: o.notes.length }))}</summary><div><ul>${o.notes.map((n) => `<li>${esc(n)}</li>`).join("")}</ul></div></details>` : "";
    return `
        <div class="hero"><img src="/icon.png" alt="GhatWatch logo">
            <div><div class="hero-title">Ghat<span>Watch</span></div><div class="hero-sub">${esc(t("subtitle"))}</div></div>
            <div class="pills">${pills}</div></div>
        <div class="note warn"><b>${esc(o.disclaimer[state.lang])}</b></div>
        ${o.is_mock ? `<div class="note">${t("demo")}</div>` : ""}${notes}`;
}

const card = (k, v, help = "") => `<div class="card" ${help ? `title="${esc(help)}"` : ""}><div class="k">${esc(k)}</div><div class="v">${esc(v)}</div></div>`;

function section(title, subtitle = "", level = "") {
    const chip = level ? `<span class="chip ${level.toLowerCase()}">${esc(label("lvl", level))}</span>` : "";
    return `<div class="section"><h2>${esc(title)}${chip}</h2>${subtitle ? `<p>${esc(subtitle)}</p>` : ""}</div>`;
}

function overview() {
    const m = OVERVIEW.metrics;
    const rows = OVERVIEW.ranking.map((r) => `
        <tr class="click ${r.ghat === state.ghat ? "sel" : ""}" data-ghat="${esc(r.ghat)}" tabindex="0">
            <td class="num">${r.rank}</td><td>${esc(ghatName(r))}</td>
            <td class="lv ${r.risk_level.toLowerCase()}">${esc(label("lvl", r.risk_level))}</td>
            <td><span class="bar"><i style="width:${r.risk_score}%"></i></span>${Math.round(r.risk_score)}</td>
            <td>${r.do_breaches} / ${r.do_tested}</td><td>${r.bod_breaches} / ${r.bod_tested}</td>
            <td class="num">${Math.round(r.gap_pct)}%</td></tr>`).join("");
    return `
        <div class="cards">
            ${card(t("m.ghats"), m.ghats)}${card(t("m.high"), m.high_risk)}
            ${card(t("m.breaches"), m.breaches, t("m.breaches.help"))}${card(t("m.nodata"), `${Math.round(m.no_data_pct)}%`, t("m.nodata.help"))}</div>
        ${section(t("h.ranking"), t("h.ranking.sub"))}
        <div class="table-wrap"><table><thead><tr>
            <th class="num">${esc(t("r.rank"))}</th><th>${esc(t("r.ghat"))}</th><th>${esc(t("r.level"))}</th><th>${esc(t("r.score"))}</th>
            <th>${esc(t("r.do"))}</th><th>${esc(t("r.bod"))}</th><th class="num">${esc(t("r.gap"))}</th></tr></thead>
            <tbody>${rows}</tbody></table></div>
        <p class="caption">${esc(t("r.caption"))}</p>`;
}

function deepDive(d) {
    const s = d.summary, w = OVERVIEW.weights, lim = OVERVIEW.limits;
    const phase = (p) => esc(label("phase", p));
    const limitRows = d.readings.map((r) => `<tr><td class="num">${r.year}</td><td>${phase(r.phase)}</td>
        <td>${readingCell(r.do_raw, r.do_status)}</td><td>${readingCell(r.bod_raw, r.bod_status)}</td></tr>`).join("");
    const evidenceRows = d.readings.map((r) => `<tr><td class="num">${r.year}</td><td>${phase(r.phase)}</td>
        <td>${esc(label("val", r.source))}</td><td>${esc(label("val", r.page))}</td>
        <td>${esc(label("val", r.do_raw))}</td><td>${esc(label("val", r.bod_raw))}</td></tr>`).join("");
    const fmt = (n, dp = 2) => Number(n).toFixed(dp);
    const pct = (n) => `${Math.round(n * 100)}%`;
    return `
        <div class="cards">
            ${card(t("d.score"), `${Math.round(s.risk_score)} / 100`)}${card(t("d.level"), label("lvl", s.risk_level))}
            ${card(t("d.breaches"), s.breaches)}${card(t("d.gap"), `${s.gap_pct}%`)}</div>
        ${s.no_data ? `<div class="note warn">${md(t("d.missing", { n: s.no_data, total: s.readings }))}</div>` : ""}
        ${s.floor_applied ? `<div class="note info">${esc(t("d.floor", { m: w.medium_at }))}</div>` : ""}
        <h3 class="sub">${esc(t("d.limit", { do: lim.do_min, bod: lim.bod_max }))}</h3>
        <div class="table-wrap"><table><thead><tr><th class="num">${esc(t("c.year"))}</th><th>${esc(t("c.phase"))}</th>
            <th>${esc(t("c.do"))}</th><th>${esc(t("c.bod"))}</th></tr></thead><tbody>${limitRows}</tbody></table></div>
        <details><summary>${esc(t("d.how"))}</summary><div>${md(t("d.how.body", {
            w1: pct(w.breach), w2: pct(w.severity), w3: pct(w.deterioration), gw: pct(w.gap),
            br: fmt(s.breach_rate), sev: fmt(s.severity), det: fmt(s.deterioration), hi: w.high_at, mid: w.medium_at }))}</div></details>
        <details><summary>${esc(t("d.evidence"))}</summary><div class="table-wrap"><table><thead><tr>
            <th class="num">${esc(t("c.year"))}</th><th>${esc(t("c.phase"))}</th><th>${esc(t("e.source"))}</th>
            <th>${esc(t("e.page"))}</th><th>${esc(t("e.do"))}</th><th>${esc(t("e.bod"))}</th></tr></thead>
            <tbody>${evidenceRows}</tbody></table></div></details>`;
}

function trends() {
    return `<div class="charts"><div class="chart" id="chart-do"></div><div class="chart" id="chart-bod"></div></div>
        <p class="caption">${esc(t("tr.cap"))}</p>`;
}

/** One line per festival phase; a null value breaks the line (no data is never drawn as "clean"). */
function drawChart(el, readings, param, title, limit, limitText) {
    const traces = PHASES.map((phase, i) => {
        const rows = readings.filter((r) => r.phase === phase).sort((a, b) => a.year - b.year);
        const name = label("phase", phase);
        return {
            x: rows.map((r) => r.year), y: rows.map((r) => r[`${param}_value`]), name, mode: "lines+markers", connectgaps: false,
            line: { color: PHASE_COLOUR[phase], width: 2.5, dash: i === 0 ? "solid" : "dash" }, marker: { size: 8 },
            customdata: rows.map((r) => r[`${param}_raw`]), hovertemplate: `<b>${esc(name)}</b><br>%{x}: %{customdata} mg/L<extra></extra>`,
        };
    });
    const grid = "#1C2632";
    Plotly.newPlot(el, traces, {
        title: { text: title, font: { size: 15, color: "#E8EEF5" } }, template: "plotly_dark",
        paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)", font: { family: "Inter, 'Noto Sans Devanagari', sans-serif", color: "#CBD5E1" },
        xaxis: { title: t("c.year"), dtick: 1, gridcolor: grid, zerolinecolor: grid },
        yaxis: { title: "mg/L", rangemode: "tozero", gridcolor: grid, zerolinecolor: grid },
        shapes: [{ type: "line", xref: "paper", x0: 0, x1: 1, y0: limit, y1: limit, line: { color: "#94A3B8", dash: "dot", width: 1.5 } }],
        annotations: [{ xref: "paper", x: 0, y: limit, yanchor: "bottom", xanchor: "left", text: limitText, showarrow: false, font: { color: "#94A3B8", size: 11 } }],
        height: 360, margin: { l: 50, r: 10, t: 50, b: 40 }, legend: { orientation: "h", y: -0.25 }, hovermode: "x unified",
    }, { displayModeBar: false, responsive: true });
}

function briefTab(d) {
    const cols = [
        ["en", "English", OVERVIEW.disclaimer.en, ["Findings", "Recommended actions"]],
        ["hi", "हिन्दी", OVERVIEW.disclaimer.hi, ["निष्कर्ष", "अनुशंसित कार्रवाई"]],
    ].map(([code, title, disclaimer, heads]) => `
        <div class="brief" lang="${code}"><div class="lang">${title}</div>
            <h3>${esc(d.brief[code].headline)}</h3><div class="disc">${esc(disclaimer)}</div>
            <h4>${heads[0]}</h4><ul>${d.brief[code].findings.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>
            <h4>${heads[1]}</h4><ul>${d.brief[code].actions.map((x) => `<li>${esc(x)}</li>`).join("")}</ul></div>`).join("");
    return `<div class="brief-grid">${cols}</div><p class="caption">${esc(t("b.note"))}</p>
        <a class="btn" href="/api/ghats/${encodeURIComponent(d.ghat)}/brief.pdf" download>${esc(t("b.download"))}</a>`;
}

// ---------------------------------------------------------------- rendering + events
async function renderGhat() {
    const panel = $("#ghat-panel");
    try {
        detailCache[state.ghat] ||= await api(`/api/ghats/${encodeURIComponent(state.ghat)}`);
    } catch (err) {
        panel.innerHTML = `<div class="note error">${esc(t("err.load", { e: err.message }))}</div>`;
        return;
    }
    const d = detailCache[state.ghat];
    panel.innerHTML = state.tab === "dive" ? deepDive(d) : state.tab === "trends" ? trends() : briefTab(d);
    if (state.tab === "trends") {
        const lim = OVERVIEW.limits;
        drawChart($("#chart-do"), d.readings, "do", t("tr.do"), lim.do_min, t("tr.lim.do", { v: lim.do_min }));
        drawChart($("#chart-bod"), d.readings, "bod", t("tr.bod"), lim.bod_max, t("tr.lim.bod", { v: lim.bod_max }));
    }
}

function render() {
    document.documentElement.lang = state.lang;
    const row = OVERVIEW.ranking.find((r) => r.ghat === state.ghat);
    const tabs = [["dive", "tab.dive"], ["trends", "tab.trends"], ["brief", "tab.brief"]]
        .map(([id, key]) => `<button role="tab" data-tab="${id}" aria-selected="${state.tab === id}">${esc(t(key))}</button>`).join("");
    sidebar();
    $("#main").innerHTML = `${header()}${overview()}
        ${section(ghatName(row), t("g.sub", { r: row.rank, n: OVERVIEW.ranking.length }), row.risk_level)}
        <div class="tabs" role="tablist">${tabs}</div><div id="ghat-panel"></div>`;
    document.querySelectorAll("tr.click").forEach((tr) => {
        tr.onclick = () => selectGhat(tr.dataset.ghat);
        tr.onkeydown = (e) => (e.key === "Enter" || e.key === " ") && (e.preventDefault(), selectGhat(tr.dataset.ghat));
    });
    document.querySelectorAll("[data-tab]").forEach((b) => (b.onclick = () => { state.tab = b.dataset.tab; render(); }));
    return renderGhat();
}

function selectGhat(name) { state.ghat = name; location.hash = encodeURIComponent(name); render(); }
function setLang(code) { state.lang = code; localStorage.setItem("gw-lang", code); render(); }

async function init() {
    try {
        [I18N, OVERVIEW] = await Promise.all([api("/api/i18n"), api("/api/overview")]);
    } catch (err) {
        $("#main").innerHTML = `<div class="note error">Could not load GhatWatch data (${esc(err.message)}). Please refresh.</div>`;
        return;
    }
    const fromHash = decodeURIComponent(location.hash.slice(1));
    state.ghat = OVERVIEW.ranking.some((r) => r.ghat === fromHash) ? fromHash : OVERVIEW.ranking[0].ghat;
    render();
}

init();
