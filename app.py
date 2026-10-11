"""GhatWatch - Visarjan water-quality decision assistant for BMC officers (Bhopal).

Run with:  streamlit run app.py
"""
from __future__ import annotations

import base64
import re
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils import i18n
from utils import risk_engine as engine
from utils.data_loader import NO_RECORD, PHASES, load_data
from utils.pdf_generator import build_pdf, hindi_available

ASSETS = Path(__file__).parent / "assets"

st.set_page_config(page_title="GhatWatch - Bhopal", page_icon=str(ASSETS / "icon.png"), layout="wide")
st.markdown(f"<style>{(ASSETS / 'theme.css').read_text()}</style>", unsafe_allow_html=True)

LEVEL_STYLE = {"High": "background-color:rgba(239,68,68,.18);color:#FCA5A5;font-weight:600",
               "Medium": "background-color:rgba(251,191,36,.16);color:#FCD34D;font-weight:600",
               "Low": "background-color:rgba(52,211,153,.16);color:#6EE7B7;font-weight:600"}
PHASE_COLOUR = {"Pre-Visarjan": "#60A5FA", "Post-Visarjan": "#FB923C"}
GRID_COLOUR = "#1C2632"


def t(key: str, **fmt) -> str:
    """Interface text in the language chosen in the sidebar."""
    return i18n.text(key, st.session_state.get("lang", "en"), **fmt)


def lang() -> str:
    return st.session_state.get("lang", "en")


# ---------------------------------------------------------------- data
@st.cache_data(show_spinner=False)
def get_data():
    """Load, annotate and rank once per session."""
    result = load_data()
    annotated = engine.annotate(result.df)
    return annotated, engine.rank_ghats(result.df), result.is_mock, result.notes


@st.cache_resource
def icon_data_uri() -> str:
    return "data:image/png;base64," + base64.b64encode((ASSETS / "icon.png").read_bytes()).decode()


def reading_text(raw: str, status: str) -> str:
    """Show the value exactly as recorded, with its CPCB result."""
    shown = "-" if raw in ("", NO_RECORD) else raw
    return f"{shown}  {i18n.label('status', status, lang())}"


def section(title: str, subtitle: str = "", chip_level: str | None = None) -> None:
    """Section heading with optional muted subtitle and risk-level chip."""
    chip = (f'<span class="gw-chip {chip_level.lower()}">{i18n.label("lvl", chip_level, lang())}</span>'
            if chip_level else "")
    sub = f"<p>{subtitle}</p>" if subtitle else ""
    st.markdown(f'<div class="gw-section"><h2>{title}{chip}</h2>{sub}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------- page sections
def sidebar(ranking: pd.DataFrame) -> str:
    """Brand, language switch and ghat selector. Returns the selected ghat (English record name)."""
    st.sidebar.markdown(
        f'<div class="gw-brand"><img src="{icon_data_uri()}" alt="GhatWatch logo"><div>'
        f'<div class="gw-brand-name">GhatWatch</div><div class="gw-brand-sub">{t("sb.brand")}</div>'
        '</div></div>', unsafe_allow_html=True)
    # Streamlit applies a widget's new value before the rerun, so t() already sees the new language.
    st.sidebar.radio(i18n.text("sb.lang", "en"), list(i18n.LANGUAGES), key="lang", horizontal=True,
                     format_func=i18n.LANGUAGES.get)
    ghats = ranking["ghat"].tolist()  # highest risk first
    ghat = st.sidebar.selectbox(
        t("sb.select"), ghats,
        format_func=lambda n: f"#{ghats.index(n) + 1}  {i18n.ghat_name(n, lang())}")
    st.sidebar.caption(t("sb.caption"))
    return ghat


def header(is_mock: bool, notes: list[str], n_ghats: int) -> None:
    pills = [t("pill.ghats", n=n_ghats), t("pill.cpcb"), t("pill.brief")]
    pill_html = "".join(f'<span class="gw-pill">{p}</span>' for p in pills)
    # Not live data, so say so in the header itself.
    pill_html += f'<span class="gw-pill warn">{t("pill.hist")}</span>'
    st.markdown(
        f'<div class="gw-hero"><img src="{icon_data_uri()}" alt="GhatWatch logo">'
        '<div><div class="gw-title">Ghat<span>Watch</span></div>'
        f'<div class="gw-sub">{t("subtitle")}</div></div>'
        f'<div class="gw-pills">{pill_html}</div></div>', unsafe_allow_html=True)
    disclaimer = engine.DISCLAIMER_HI if lang() == "hi" else engine.DISCLAIMER_EN
    st.markdown(f'<div class="gw-note warn"><b>{disclaimer}</b></div>', unsafe_allow_html=True)
    if is_mock:
        st.markdown(f'<div class="gw-note">{t("demo")}</div>', unsafe_allow_html=True)
    st.write("")
    if notes:
        with st.expander(t("notes", n=len(notes))):
            for note in notes:
                st.write("•", note)


def overview(data: pd.DataFrame, ranking: pd.DataFrame) -> None:
    total_readings = len(data) * 2
    gaps = int((data.do_status == engine.NO_DATA).sum() + (data.bod_status == engine.NO_DATA).sum())
    breaches = int((data.do_status == engine.BREACH).sum() + (data.bod_status == engine.BREACH).sum())
    cols = st.columns(4)
    cols[0].metric(t("m.ghats"), len(ranking))
    cols[1].metric(t("m.high"), int((ranking.risk_level == "High").sum()))
    cols[2].metric(t("m.breaches"), breaches, help=t("m.breaches.help"))
    cols[3].metric(t("m.nodata"), f"{100 * gaps / total_readings:.0f}%", help=t("m.nodata.help"))

    section(t("h.ranking"), t("h.ranking.sub"))
    col = {k: t(k) for k in ("r.rank", "r.ghat", "r.level", "r.score", "r.do", "r.bod", "r.gap")}
    view = pd.DataFrame({
        col["r.rank"]: ranking["rank"],
        col["r.ghat"]: [i18n.ghat_name(g, lang()) for g in ranking["ghat"]],
        col["r.level"]: [i18n.label("lvl", lv, lang()) for lv in ranking["risk_level"]],
        col["r.score"]: ranking["risk_score"],
        col["r.do"]: ranking.do_breaches.astype(str) + " / " + ranking.do_tested.astype(str),
        col["r.bod"]: ranking.bod_breaches.astype(str) + " / " + ranking.bod_tested.astype(str),
        col["r.gap"]: ranking["gap_pct"],
    })
    levels = ranking["risk_level"].tolist()
    st.dataframe(
        view.style.apply(lambda s: [LEVEL_STYLE[lv] for lv in levels], subset=[col["r.level"]]),
        hide_index=True, width="stretch",
        column_config={
            col["r.score"]: st.column_config.ProgressColumn(col["r.score"], min_value=0, max_value=100, format="%.0f"),
            col["r.gap"]: st.column_config.NumberColumn(format="%.0f%%"),
        })
    st.caption(t("r.caption"))


def deep_dive(g: pd.DataFrame, summary: dict) -> None:
    c = st.columns(4)
    c[0].metric(t("d.score"), f"{summary['risk_score']:.0f} / 100")
    c[1].metric(t("d.level"), i18n.label("lvl", summary["risk_level"], lang()))
    c[2].metric(t("d.breaches"), summary["breaches"])
    c[3].metric(t("d.gap"), f"{summary['gap_pct']:g}%")

    if summary["no_data"]:
        st.warning(t("d.missing", n=summary["no_data"], total=summary["readings"]))
    if summary["floor_applied"]:
        st.info(t("d.floor", m=engine.MEDIUM_AT))

    st.markdown(f"##### {t('d.limit', do=f'{engine.DO_MIN:g}', bod=f'{engine.BOD_MAX:g}')}")
    table = g.sort_values(["year", "phase"], ascending=[False, False])
    phases = [i18n.label("phase", p, lang()) for p in table.phase]
    st.dataframe(pd.DataFrame({
        t("c.year"): table.year, t("c.phase"): phases,
        t("c.do"): [reading_text(r, s) for r, s in zip(table.do_raw, table.do_status)],
        t("c.bod"): [reading_text(r, s) for r, s in zip(table.bod_raw, table.bod_status)],
    }), hide_index=True, width="stretch")

    with st.expander(t("d.how")):
        st.markdown(t("d.how.body", w1=f"{engine.W_BREACH:.0%}", w2=f"{engine.W_SEVERITY:.0%}",
                      w3=f"{engine.W_DETERIORATION:.0%}", gw=f"{engine.GAP_WEIGHT:.0%}",
                      br=f"{summary['breach_rate']:.2f}", sev=f"{summary['severity']:.2f}",
                      det=f"{summary['deterioration']:.2f}", hi=engine.HIGH_AT, mid=engine.MEDIUM_AT))

    with st.expander(t("d.evidence")):
        st.dataframe(pd.DataFrame({
            t("c.year"): table.year, t("c.phase"): phases,
            t("e.source"): [i18n.label("val", v, lang()) for v in table.source],
            t("e.page"): [i18n.label("val", v, lang()) for v in table.page],
            t("e.do"): [i18n.label("val", v, lang()) for v in table.do_raw],
            t("e.bod"): [i18n.label("val", v, lang()) for v in table.bod_raw],
        }), hide_index=True, width="stretch")


def trend_chart(g: pd.DataFrame, param: str, label: str, limit: float, limit_text: str) -> go.Figure:
    """Line chart of one parameter by year, one line per festival phase, with the CPCB limit."""
    fig = go.Figure()
    for phase in PHASES:
        p = g[g.phase == phase].sort_values("year")
        name = i18n.label("phase", phase, lang())
        fig.add_scatter(
            x=p.year, y=p[f"{param}_value"], name=name, mode="lines+markers",
            line=dict(color=PHASE_COLOUR[phase], width=2.5, dash="solid" if phase == PHASES[0] else "dash"),
            marker=dict(size=8), connectgaps=False,   # a gap in the line = no data, not "clean"
            customdata=p[f"{param}_raw"],
            hovertemplate=f"<b>{name}</b><br>%{{x}}: %{{customdata}} mg/L<extra></extra>")
    fig.add_hline(y=limit, line=dict(color="#94A3B8", dash="dot"), annotation_text=limit_text,
                  annotation_position="top left", annotation_font_color="#94A3B8")
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      title=dict(text=label, font=dict(size=15, color="#E8EEF5")),
                      xaxis=dict(title=t("c.year"), dtick=1, gridcolor=GRID_COLOUR, zerolinecolor=GRID_COLOUR),
                      yaxis=dict(title="mg/L", rangemode="tozero", gridcolor=GRID_COLOUR, zerolinecolor=GRID_COLOUR),
                      height=360, margin=dict(l=10, r=10, t=50, b=10), legend=dict(orientation="h", y=-0.25),
                      hovermode="x unified")
    return fig


def trends(g: pd.DataFrame) -> None:
    left, right = st.columns(2)
    left.plotly_chart(trend_chart(g, "do", t("tr.do"), engine.DO_MIN,
                                  t("tr.lim.do", v=f"{engine.DO_MIN:g}")), width="stretch")
    right.plotly_chart(trend_chart(g, "bod", t("tr.bod"), engine.BOD_MAX,
                                   t("tr.lim.bod", v=f"{engine.BOD_MAX:g}")), width="stretch")
    st.caption(t("tr.cap"))


def action_brief(ghat: str, summary: dict, g: pd.DataFrame, rank: int, n_ghats: int, is_mock: bool) -> None:
    """Both languages are always previewed side by side; the PDF carries both too."""
    brief = engine.build_brief(ghat, summary)
    en_col, hi_col = st.columns(2)
    for col, code, title, disclaimer, headings in (
            (en_col, "en", "English", engine.DISCLAIMER_EN, ("Findings", "Recommended actions")),
            (hi_col, "hi", "हिन्दी", engine.DISCLAIMER_HI, ("निष्कर्ष", "अनुशंसित कार्रवाई"))):
        with col, st.container(border=True):
            st.markdown(f"**{title}**")
            st.markdown(f"#### {brief[code]['headline']}")
            st.caption(disclaimer)
            st.markdown(f"**{headings[0]}**")
            for line in brief[code]["findings"]:
                st.markdown(f"- {line}")
            st.markdown(f"**{headings[1]}**")
            for line in brief[code]["actions"]:
                st.markdown(f"- {line}")

    st.caption(t("b.note"))
    if not hindi_available():
        st.warning(t("b.nohindi"))
    try:
        pdf = build_pdf(ghat, summary, brief, g, rank, n_ghats, is_mock)
        st.download_button(t("b.download"), data=pdf, mime="application/pdf", type="primary",
                           file_name=f"ghatwatch_{re.sub(r'[^a-z0-9]+', '_', ghat.lower()).strip('_')}.pdf")
    except Exception as exc:  # never let a PDF problem take down the dashboard
        st.error(t("b.error", e=exc))


# ---------------------------------------------------------------- main
def main() -> None:
    data, ranking, is_mock, notes = get_data()
    ghat = sidebar(ranking)  # also draws the language switch, so it runs before any text is drawn
    header(is_mock, notes, len(ranking))
    overview(data, ranking)

    row = ranking[ranking.ghat == ghat].iloc[0]
    summary, g = row.to_dict(), data[data.ghat == ghat]
    rank = int(row["rank"])

    section(i18n.ghat_name(ghat, lang()), t("g.sub", r=rank, n=len(ranking)), chip_level=summary["risk_level"])
    tab_dive, tab_trend, tab_brief = st.tabs([t("tab.dive"), t("tab.trends"), t("tab.brief")])
    with tab_dive:
        deep_dive(g, summary)
    with tab_trend:
        trends(g)
    with tab_brief:
        action_brief(ghat, summary, g, rank, len(ranking), is_mock)


main()
