/* GhatWatch frontend: no framework, no build step. Everything comes from /api.
   Interface text comes from /api/i18n so English and Hindi live in one place (utils/i18n.py). */
"use strict";

const PHASES = ["Pre-Visarjan", "Post-Visarjan"];
const PHASE_COLOUR = { "Pre-Visarjan": "#0E7490", "Post-Visarjan": "#F59E0B" };
const LEVEL_COLOUR = { High: "#DC2626", Medium: "#D97706", Low: "#059669" };
const NO_RECORD = "(no record)";

const state = { lang: localStorage.getItem("gw-lang") || "en", ghat: null, filter: "all" };
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

const STATUS = { PASS: ["s-pass", "pass", "c-pass"], BREACH: ["s-breach", "breach", "c-breach"], "NO DATA": ["s-nodata", "nodata", "c-nodata"] };
const readingCell = (raw, status) =>
    `${esc(raw === "" || raw === NO_RECORD ? "-" : raw)} <span class="${STATUS[status][0]}">${esc(label("status", status))}</span>`;
const list = (items) => `<ul>${items.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>`;

// ---------------------------------------------------------------- page blocks
function hero() {
    const buttons = Object.entries(I18N.languages)
        .map(([code, name]) => `<button data-lang="${code}" aria-pressed="${code === state.lang}">${esc(name)}</button>`).join("");
    return `<header class="hero"><div class="wrap">
        <div class="bar"><img class="logo" src="/icon.png" alt="GhatWatch logo"><div class="brand">Ghat<span>Watch</span></div>
            <div class="lang" role="group" aria-label="Language">${buttons}</div></div>
        <h1>${esc(t("hero.tag"))}</h1><p class="sub">${esc(t("subtitle"))}</p></div>
        <svg class="wave" viewBox="0 0 1440 56" preserveAspectRatio="none" aria-hidden="true">
            <path fill="#EEF6F7" d="M0 32c120 20 240 24 360 8s240-36 360-32 240 28 360 36 240-8 360-24v36H0z"/></svg></header>`;
}

function notices() {
    const o = OVERVIEW;
    return `<div class="notices"><div class="notice">${esc(o.disclaimer[state.lang])}</div>
        ${o.is_mock ? `<div class="notice info">${t("demo")}</div>` : ""}</div>`;
}

function stats() {
    const m = OVERVIEW.metrics;
    const stat = (k, v, cls = "") => `<div class="stat ${cls}"><div class="k">${esc(k)}</div><div class="v">${esc(v)}</div></div>`;
    return `<div class="stats">${stat(t("m.ghats"), m.ghats)}${stat(t("m.high"), m.high_risk, m.high_risk ? "hot" : "")}
        ${stat(t("m.breaches"), m.breaches)}${stat(t("m.nodata"), `${Math.round(m.no_data_pct)}%`, m.no_data_pct > 10 ? "warm" : "")}</div>`;
}

function rankCard() {
    const filters = ["all", "High", "Medium", "Low"].map((f) =>
        `<button class="chip" data-filter="${f}" aria-pressed="${state.filter === f}">${esc(f === "all" ? t("f.all") : label("lvl", f))}</button>`).join("");
    return `<div class="card"><h2>${esc(t("h.ranking"))}</h2><p class="lede">${esc(t("h.ranking.sub"))}</p>
        <div class="chips" role="group">${filters}</div><div class="ghats" id="rank-list">${rankRows()}</div></div>`;
}

function rankRows() {
    return OVERVIEW.ranking.filter((r) => state.filter === "all" || r.risk_level === state.filter).map((r) => {
        const lvl = r.risk_level.toLowerCase();
        return `<button class="ghat" data-ghat="${esc(r.ghat)}" aria-current="${r.ghat === state.ghat}">
            <span class="rank">${r.rank}</span><span class="gname">${esc(ghatName(r))}</span>
            <span class="badge ${lvl}">${esc(label("lvl", r.risk_level))}</span>
            <span class="meter" role="img" aria-label="${esc(t("r.score"))}: ${Math.round(r.risk_score)} / 100"><i class="${lvl}" style="width:${r.risk_score}%"></i></span>
            <span class="detail">${esc(t("r.line", { do: r.do_breaches, dt: r.do_tested, bod: r.bod_breaches, bt: r.bod_tested, gap: Math.round(r.gap_pct) }))}</span></button>`;
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

/** Latest year, both phases, DO and BOD: the numbers an officer looks at first. */
function latestTiles(d) {
    const year = Math.max(...OVERVIEW.years), lim = OVERVIEW.limits;
    const tiles = ["do", "bod"].flatMap((p) => PHASES.map((phase) => {
        const r = d.readings.find((x) => x.year === year && x.phase === phase);
        const status = r ? r[`${p}_status`] : "NO DATA", raw = r ? r[`${p}_raw`] : "";
        const shown = status === "NO DATA" && (raw === "" || raw === NO_RECORD) ? "—" : raw;
        return `<div class="tile ${STATUS[status][1]}"><div class="t1">${esc(t(`latest.${p}`))} · ${esc(label("phase", phase))}</div>
            <div class="t2">${esc(shown)} <span class="t3">mg/L</span></div>
            <div class="t3">${esc(t(`latest.limit.${p}`, { v: p === "do" ? lim.do_min : lim.bod_max }))} · ${esc(label("status", status))}</div></div>`;
    }));
    return `<div class="card"><h2>${esc(t("sec.latest", { y: year }))}</h2><div class="tiles">${tiles.join("")}</div></div>`;
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

function briefCard(d) {
    const cols = [["en", "English", ["Findings", "Recommended actions"]], ["hi", "हिन्दी", ["निष्कर्ष", "अनुशंसित कार्रवाई"]]]
        .map(([code, title, heads]) => `<div class="brief" lang="${code}"><span class="tag">${title}</span>
            <h3>${esc(d.brief[code].headline)}</h3><h4>${heads[0]}</h4>${list(d.brief[code].findings)}
            <h4>${heads[1]}</h4>${list(d.brief[code].actions)}</div>`).join("");
    return `<div class="card"><h2>${esc(t("sec.brief"))}</h2><div class="briefs">${cols}</div>
        <a class="btn" href="/api/ghats/${encodeURIComponent(d.ghat)}/brief.pdf" download>${esc(t("b.download"))}</a>
        <p class="note" style="margin-top:8px">${esc(t("b.note"))}</p></div>`;
}

function detail(d) {
    const s = d.summary, lim = OVERVIEW.limits, brief = d.brief[state.lang];
    return `<div class="card top-card"><div>
            <h2>${esc(state.lang === "hi" ? d.ghat_hi : d.ghat)}<span class="badge ${s.risk_level.toLowerCase()}">${esc(label("lvl", s.risk_level))}</span></h2>
            <p class="rankline">${esc(t("g.sub", { r: d.rank, n: OVERVIEW.ranking.length }))}</p>
            <p class="verdict">${esc(brief.headline)}</p>
            ${s.no_data ? `<div class="callout">${md(t("d.missing", { n: s.no_data, total: s.readings }))}</div>` : ""}
            ${s.floor_applied ? `<div class="callout info">${esc(t("d.floor", { m: OVERVIEW.weights.medium_at }))}</div>` : ""}</div>
            ${ring(s.risk_score, s.risk_level)}</div>
        ${latestTiles(d)}
        <div class="two" style="margin-top:18px"><div class="card why" style="margin:0"><h3>${esc(t("sec.why"))}</h3>${list(brief.findings)}</div>
            <div class="card do" style="margin:0"><h3>${esc(t("sec.do"))}</h3>${list(brief.actions)}</div></div>
        <div class="card"><h2>${esc(t("sec.trend"))}</h2><div class="charts"><div class="chart" id="chart-do"></div><div class="chart" id="chart-bod"></div></div>
            <p class="note">${esc(t("tr.help"))}</p></div>
        ${briefCard(d)}
        <details><summary>${esc(t("sec.table"))}</summary><div><p class="note" style="margin-bottom:8px">${esc(
            t("d.limit", { do: lim.do_min, bod: lim.bod_max }))}</p>${readingsTable(d)}</div></details>
        <details><summary>${esc(t("d.how"))}</summary><div>${scoreExplanation(s)}</div></details>`;
}

function compareSection() {
    const years = OVERVIEW.years;
    const head = years.map((y) => `<th>${y}</th>`).join("");
    const rows = OVERVIEW.ranking.map((r) => {
        const cells = years.map((y) => {
            const cell = (OVERVIEW.timeline[r.ghat] || {})[y] || {};
            const pair = PHASES.map((p) => {
                const s = cell[p];
                const title = `${ghatName(r)} · ${y} · ${label("phase", p)}: ${s ? label("status", s) : "—"}`;
                return `<i class="${s ? STATUS[s][2] : "c-none"}" title="${esc(title)}"></i>`;
            }).join("");
            return `<td><div class="cellpair">${pair}</div></td>`;
        }).join("");
        return `<tr class="click ${r.ghat === state.ghat ? "sel" : ""}" data-ghat="${esc(r.ghat)}"><td class="name">${esc(ghatName(r))}</td>${cells}</tr>`;
    }).join("");
    const legend = [["c-pass", "lg.pass"], ["c-breach", "lg.breach"], ["c-nodata", "lg.nodata"]]
        .map(([c, k]) => `<span><i class="${c}"></i>${esc(t(k))}</span>`).join("");
    return `<h2 class="section-title">${esc(t("sec.compare"))}</h2>
        <div class="two"><div class="card" style="margin:0"><h3>${esc(t("cmp.score"))}</h3><div id="chart-compare" style="min-height:320px"></div></div>
        <div class="card" style="margin:0"><h3>${esc(t("sec.matrix"))}</h3><p class="note" style="margin-bottom:6px">${esc(t("matrix.help"))}</p>
            <div class="table-wrap"><table class="matrix"><thead><tr><th class="name"></th>${head}</tr></thead><tbody>${rows}</tbody></table></div>
            <div class="legend">${legend}</div></div></div>`;
}

// ---------------------------------------------------------------- charts
const AXIS = { gridcolor: "#E6F0F2", fixedrange: true };
const PLOT_BASE = { paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)", template: "plotly_white",
    font: { family: "'Plus Jakarta Sans', 'Noto Sans Devanagari', sans-serif", color: "#0F2A33", size: 12 } };
const PLOT_CFG = { displayModeBar: false, responsive: true };

/** One line per festival phase; a null value breaks the line (no data is never drawn as "clean"). */
function drawTrend(el, readings, param, title, limit, limitText) {
    const traces = PHASES.map((phase, i) => {
        const rows = readings.filter((r) => r.phase === phase).sort((a, b) => a.year - b.year);
        const name = label("phase", phase);
        return {
            x: rows.map((r) => r.year), y: rows.map((r) => r[`${param}_value`]), name, mode: "lines+markers", connectgaps: false,
            line: { color: PHASE_COLOUR[phase], width: 3, dash: i === 0 ? "solid" : "dash" }, marker: { size: 8 },
            customdata: rows.map((r) => r[`${param}_raw`]), hovertemplate: `<b>${esc(name)}</b><br>%{x}: %{customdata} mg/L<extra></extra>`,
        };
    });
    Plotly.newPlot(el, traces, { ...PLOT_BASE,
        title: { text: title, font: { size: 14 }, x: 0.02 },
        xaxis: { ...AXIS, dtick: 1 }, yaxis: { ...AXIS, title: "mg/L", rangemode: "tozero" },
        shapes: [{ type: "line", xref: "paper", x0: 0, x1: 1, y0: limit, y1: limit, line: { color: "#0F2A33", dash: "dot", width: 1.5 } }],
        annotations: [{ xref: "paper", x: 1, y: limit, yanchor: "bottom", xanchor: "right", text: limitText, showarrow: false, font: { size: 11 } }],
        height: 320, margin: { l: 44, r: 8, t: 44, b: 40 }, legend: { orientation: "h", y: -0.2 }, hovermode: "x unified" }, PLOT_CFG);
}

/** Horizontal bars, one per ghat, coloured by risk level. Clicking a bar opens that ghat. */
function drawCompare() {
    const rows = OVERVIEW.ranking;
    const el = $("#chart-compare");
    Plotly.newPlot(el, [{
        type: "bar", orientation: "h", x: rows.map((r) => r.risk_score), y: rows.map(ghatName),
        customdata: rows.map((r) => r.ghat), marker: { color: rows.map((r) => LEVEL_COLOUR[r.risk_level]) },
        text: rows.map((r) => Math.round(r.risk_score)), textposition: "outside", cliponaxis: false,
        hovertemplate: "%{y}: %{x:.0f} / 100<extra></extra>",
    }], { ...PLOT_BASE, xaxis: { ...AXIS, range: [0, 100] }, yaxis: { autorange: "reversed", fixedrange: true, automargin: true },
        height: 320, margin: { l: 10, r: 30, t: 8, b: 30 }, bargap: 0.35 }, PLOT_CFG);
    el.on("plotly_click", (e) => selectGhat(e.points[0].customdata));
}

// ---------------------------------------------------------------- rendering + events
async function loadDetail() {
    const slot = $("#detail");
    try {
        detailCache[state.ghat] ||= await api(`/api/ghats/${encodeURIComponent(state.ghat)}`);
    } catch (err) {
        slot.innerHTML = `<div class="notice error">${esc(t("err.load", { e: err.message }))}</div>`;
        return;
    }
    const d = detailCache[state.ghat], lim = OVERVIEW.limits;
    slot.innerHTML = detail(d);
    drawTrend($("#chart-do"), d.readings, "do", t("tr.do"), lim.do_min, t("tr.lim.do", { v: lim.do_min }));
    drawTrend($("#chart-bod"), d.readings, "bod", t("tr.bod"), lim.bod_max, t("tr.lim.bod", { v: lim.bod_max }));
}

function bindRankList() {
    document.querySelectorAll("#rank-list [data-ghat]").forEach((b) => (b.onclick = () => selectGhat(b.dataset.ghat)));
}

function render() {
    document.documentElement.lang = state.lang;
    $("#app").innerHTML = `${hero()}<main class="wrap">${notices()}${stats()}
        <div class="grid"><aside class="rail">${rankCard()}</aside><section id="detail"></section></div>
        ${compareSection()}<footer>${esc(t("foot"))}</footer></main>`;
    document.querySelectorAll("[data-lang]").forEach((b) => (b.onclick = () => { state.lang = b.dataset.lang; localStorage.setItem("gw-lang", state.lang); render(); }));
    document.querySelectorAll("[data-filter]").forEach((b) => (b.onclick = () => {
        state.filter = b.dataset.filter;
        document.querySelectorAll("[data-filter]").forEach((c) => c.setAttribute("aria-pressed", c.dataset.filter === state.filter));
        $("#rank-list").innerHTML = rankRows(); bindRankList();
    }));
    document.querySelectorAll(".matrix tr.click").forEach((tr) => (tr.onclick = () => selectGhat(tr.dataset.ghat)));
    bindRankList();
    drawCompare();
    return loadDetail();
}

function selectGhat(name) {
    state.ghat = name; location.hash = encodeURIComponent(name); render();
    if (window.innerWidth <= 1060) $("#detail").scrollIntoView({ behavior: "smooth", block: "start" });
}

async function init() {
    try {
        [I18N, OVERVIEW] = await Promise.all([api("/api/i18n"), api("/api/overview")]);
    } catch (err) {
        $("#app").innerHTML = `<div class="wrap"><div class="notice error" style="margin-top:30px">Could not load GhatWatch data (${esc(err.message)}). Please refresh.</div></div>`;
        return;
    }
    const fromHash = decodeURIComponent(location.hash.slice(1));
    state.ghat = OVERVIEW.ranking.some((r) => r.ghat === fromHash) ? fromHash : OVERVIEW.ranking[0].ghat;
    render();
}

init();
