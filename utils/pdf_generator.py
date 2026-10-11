"""Single-page bilingual (English + Hindi) PDF action brief, built with ReportLab.

ReportLab cannot shape Devanagari on its own (matras and conjuncts come out misspelt), so
Hindi lines are shaped with HarfBuzz and drawn as vector glyph outlines. The Hindi text is
therefore not selectable in the PDF, but it is spelt correctly. If HarfBuzz or a
Devanagari font is unavailable, the PDF is produced in English only and says so.
"""
from __future__ import annotations

import io
from datetime import date
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import FILL_NON_ZERO
from reportlab.platypus import Flowable, Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from utils.risk_engine import BREACH, DISCLAIMER_EN, DISCLAIMER_HI, LEVEL_HI

try:
    import uharfbuzz as hb
except ImportError:  # optional dependency, see module docstring
    hb = None

# (path, face index) of fonts with Devanagari + Latin glyphs, checked in order.
# Drop NotoSansDevanagari-Regular.ttf into ./fonts to use the same font on every machine.
_ROOT = Path(__file__).resolve().parent.parent
LOGO = _ROOT / "assets" / "icon.png"
FONT_CANDIDATES = [
    (_ROOT / "fonts" / "NotoSansDevanagari-Regular.ttf", 0),
    (Path("/System/Library/Fonts/Supplemental/Devanagari Sangam MN.ttc"), 0),
    (Path("/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf"), 0),
    (Path("/usr/share/fonts/noto/NotoSansDevanagari-Regular.ttf"), 0),
    (Path("C:/Windows/Fonts/Nirmala.ttf"), 0),
    (Path("C:/Windows/Fonts/mangal.ttf"), 0),
]

LEVEL_COLOUR = {"High": colors.HexColor("#B3261E"), "Medium": colors.HexColor("#B26A00"),
                "Low": colors.HexColor("#1B7F3B")}
INK, MUTED, RULE = colors.HexColor("#1F2933"), colors.HexColor("#52606D"), colors.HexColor("#CBD2D9")


class DevanagariShaper:
    """Shapes Hindi text with HarfBuzz and measures / draws it on a ReportLab canvas."""

    def __init__(self, path: Path, index: int):
        face = hb.Face(hb.Blob.from_file_path(str(path)), index)
        self.font = hb.Font(face)
        self.upem = face.upem
        self._outlines: dict[int, list] = {}
        self._funcs = hb.DrawFuncs()
        self._funcs.set_move_to_func(lambda x, y, ops: ops.append(("M", x, y)))
        self._funcs.set_line_to_func(lambda x, y, ops: ops.append(("L", x, y)))
        self._funcs.set_quadratic_to_func(lambda cx, cy, x, y, ops: ops.append(("Q", cx, cy, x, y)))
        self._funcs.set_cubic_to_func(lambda a, b, c, d, x, y, ops: ops.append(("C", a, b, c, d, x, y)))
        self._funcs.set_close_path_func(lambda ops: ops.append(("Z",)))

    def has_devanagari(self) -> bool:
        return bool(self.font.get_nominal_glyph(0x0939))

    def shape(self, text: str) -> list[tuple[int, int, int, int]]:
        """Return ``(glyph id, x offset, y offset, x advance)`` per glyph, in font units."""
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.font, buf, {"kern": True, "liga": True})
        return [(i.codepoint, p.x_offset, p.y_offset, p.x_advance)
                for i, p in zip(buf.glyph_infos, buf.glyph_positions)]

    def width(self, text: str, size: float) -> float:
        return sum(g[3] for g in self.shape(text)) * size / self.upem

    def _outline(self, gid: int) -> list:
        if gid not in self._outlines:
            ops: list = []
            self.font.draw_glyph(gid, self._funcs, ops)
            self._outlines[gid] = ops
        return self._outlines[gid]

    def draw(self, canv, x: float, y: float, text: str, size: float, colour=INK) -> None:
        """Draw ``text`` with its baseline-left corner at ``(x, y)``."""
        scale = size / self.upem
        pen_x = x
        canv.setFillColor(colour)
        for gid, dx, dy, adv in self.shape(text):
            path = canv.beginPath()
            ox, oy = pen_x + dx * scale, y + dy * scale

            def at(px, py):  # font units -> page coordinates for this glyph
                return ox + px * scale, oy + py * scale

            cur = (0.0, 0.0)  # current point, needed to turn quadratics into cubics
            for op in self._outline(gid):
                if op[0] == "M":
                    path.moveTo(*at(*op[1:3]))
                    cur = op[1:3]
                elif op[0] == "L":
                    path.lineTo(*at(*op[1:3]))
                    cur = op[1:3]
                elif op[0] == "Q":  # TrueType quadratic -> equivalent cubic
                    (qx, qy), (ex, ey) = op[1:3], op[3:5]
                    c1 = (cur[0] + 2 / 3 * (qx - cur[0]), cur[1] + 2 / 3 * (qy - cur[1]))
                    c2 = (ex + 2 / 3 * (qx - ex), ey + 2 / 3 * (qy - ey))
                    path.curveTo(*at(*c1), *at(*c2), *at(ex, ey))
                    cur = (ex, ey)
                elif op[0] == "C":
                    path.curveTo(*at(*op[1:3]), *at(*op[3:5]), *at(*op[5:7]))
                    cur = op[5:7]
                else:
                    path.close()
            canv.drawPath(path, stroke=0, fill=1, fillMode=FILL_NON_ZERO)
            pen_x += adv * scale


def _load_shaper() -> DevanagariShaper | None:
    """First usable shaper, or None (HarfBuzz missing / no Devanagari font found)."""
    if hb is None:
        return None
    for path, index in FONT_CANDIDATES:
        try:
            if path.exists():
                shaper = DevanagariShaper(path, index)
                if shaper.has_devanagari():
                    return shaper
        except Exception:
            continue
    return None


_SHAPER = _load_shaper()


def hindi_available() -> bool:
    """True when the PDF can include correctly shaped Hindi."""
    return _SHAPER is not None


class HindiText(Flowable):
    """Word-wrapped Hindi paragraph, optionally with a bullet, drawn from shaped glyphs."""

    def __init__(self, text: str, size: float = 9.5, bullet: bool = False,
                 bold: bool = False, colour=INK):
        super().__init__()
        self.text, self.size, self.bullet, self.bold, self.colour = text, size, bullet, bold, colour
        self.leading = size * 1.55
        self.lines: list[str] = []

    def wrap(self, avail_w, avail_h):
        indent = 10 if self.bullet else 0
        self._indent = indent
        self.lines, line = [], ""
        for word in self.text.split():
            trial = f"{line} {word}".strip()
            if line and _SHAPER.width(trial, self.size) > avail_w - indent:
                self.lines.append(line)
                line = word
            else:
                line = trial
        if line:
            self.lines.append(line)
        self.width, self.height = avail_w, self.leading * len(self.lines)
        return self.width, self.height

    def draw(self):
        for i, line in enumerate(self.lines):
            base = self.height - i * self.leading - self.size * 1.1
            if self.bullet and i == 0:
                self.canv.setFillColor(self.colour)
                self.canv.circle(3, base + self.size * 0.3, 1.3, stroke=0, fill=1)
            # Pseudo-bold: a hairline stroke-free second pass offset by a fraction of a point.
            for shift in ((0, 0.25) if self.bold else (0,)):
                _SHAPER.draw(self.canv, self._indent + shift, base, line, self.size, self.colour)


_PHASE_LABEL = {"Pre-Visarjan": "Before", "During": "During", "Post-Visarjan": "1 week after"}
_PHASE_ORDER = {"Pre-Visarjan": 0, "During": 1, "Post-Visarjan": 2}


def _breach_rows(readings: pd.DataFrame, limit: int) -> tuple[list[list[str]], int]:
    """Most recent breaching readings as table rows, plus how many were left out."""
    hit = readings[(readings.do_status == BREACH) | (readings.bod_status == BREACH) | (readings.ph_status == BREACH)].copy()
    hit["_ph"] = hit["phase"].map(_PHASE_ORDER)
    hit = hit.sort_values(["p_order", "_ph"], ascending=[False, True])
    rows = []
    for _, r in hit.head(limit).iterrows():
        flags = [name for name, st in (("DO below 5", r.do_status), ("BOD above 3", r.bod_status), ("pH outside 6.5-8.5", r.ph_status))
                 if st == BREACH]
        rows.append([r.period, _PHASE_LABEL.get(r.phase, r.phase), r.do_raw, r.bod_raw, r.ph_raw, ", ".join(flags)])
    return rows, max(len(hit) - limit, 0)


def _story(summary, brief, readings, rank, n_ghats, is_mock, k):
    """Build the page content. ``k`` scales font sizes so the brief can be shrunk to one page."""
    def st(**kw):
        return ParagraphStyle("s", **{"fontName": "Helvetica", "textColor": INK, "alignment": TA_LEFT, **kw})

    body = st(fontSize=9.5 * k, leading=13 * k)
    bullet = st(fontSize=9.5 * k, leading=13 * k, leftIndent=10, bulletIndent=0, spaceAfter=1)
    small = st(fontSize=8 * k, leading=10.5 * k, textColor=MUTED)
    h2 = st(fontName="Helvetica-Bold", fontSize=11 * k, leading=14 * k, spaceBefore=6 * k, spaceAfter=2 * k)
    level = summary["risk_level"]
    hindi = hindi_available()
    s: list = []

    titles = [Paragraph("GhatWatch - Visarjan Water-Quality Action Brief", st(
        fontName="Helvetica-Bold", fontSize=16 * k, leading=20 * k))]
    if hindi:
        titles.append(HindiText("घाटवॉच - विसर्जन जल-गुणवत्ता कार्य-सार", size=12 * k, bold=True))
    titles.append(Paragraph(f"Bhopal Municipal Corporation &nbsp;|&nbsp; Prepared {date.today():%d %b %Y}", small))
    if LOGO.exists():
        logo_size = 20 * mm * k
        head = Table([[Image(str(LOGO), logo_size, logo_size, mask="auto"), titles]],
                     colWidths=[logo_size + 4 * mm, None], hAlign="LEFT")
        head.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                                  ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
        s.append(head)
    else:
        s += titles
    s.append(Spacer(1, 4 * k))

    # Status banner
    banner = Table([[Paragraph(f"<b>{brief['en']['headline']}</b>", st(
        fontSize=11 * k, leading=14 * k, textColor=colors.white)),
        Paragraph(f"Rank {rank} of {n_ghats}<br/>Data gap {summary['gap_pct']:g}%", st(
            fontSize=9 * k, leading=12 * k, textColor=colors.white))]], colWidths=[None, 38 * mm])
    banner.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LEVEL_COLOUR[level]), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    s += [banner, Spacer(1, 3 * k), Paragraph(f"<i>{DISCLAIMER_EN}</i>", small)]
    if hindi:
        s.append(HindiText(DISCLAIMER_HI, size=8 * k, colour=MUTED))
    if is_mock:
        s.append(Paragraph("<b>DEMO DATA:</b> values are generated for demonstration, not real measurements.",
                           st(fontSize=8 * k, leading=10.5 * k, textColor=LEVEL_COLOUR["High"])))

    # CPCB breaches
    s.append(Paragraph("CPCB Class B breaches (DO >= 5 mg/L, BOD <= 3 mg/L, pH 6.5 to 8.5)", h2))
    rows, extra = _breach_rows(readings, limit=8)
    if rows:
        table = Table([["Period", "Phase", "DO mg/L", "BOD mg/L", "pH", "Breach"]] + rows,
                      colWidths=[22 * mm, 24 * mm, 17 * mm, 17 * mm, 13 * mm, 85 * mm], repeatRows=1, hAlign="LEFT")
        table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 8.5 * k),
            ("TEXTCOLOR", (0, 0), (-1, -1), INK), ("LINEBELOW", (0, 0), (-1, 0), 0.8, INK),
            ("LINEBELOW", (0, 1), (-1, -1), 0.3, RULE), ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2), ("LEFTPADDING", (0, 0), (-1, -1), 3)]))
        s.append(table)
        if extra:
            s.append(Paragraph(f"+ {extra} earlier breaching reading(s) not shown.", small))
    else:
        s.append(Paragraph("No CPCB Class B breach among the readings on record.", body))

    # English then Hindi: findings and recommendations
    s.append(Paragraph("Findings", h2))
    s += [Paragraph(t, bullet, bulletText="\u2022") for t in brief["en"]["findings"]]
    s.append(Paragraph("Recommended municipal actions", h2))
    s += [Paragraph(t, bullet, bulletText="\u2022") for t in brief["en"]["actions"]]

    if hindi:
        s.append(Spacer(1, 4 * k))
        s.append(HindiText("निष्कर्ष", size=11 * k, bold=True))
        s += [HindiText(t, size=9.5 * k, bullet=True) for t in brief["hi"]["findings"]]
        s.append(Spacer(1, 2 * k))
        s.append(HindiText("अनुशंसित नगर-निगम कार्रवाई", size=11 * k, bold=True))
        s += [HindiText(t, size=9.5 * k, bullet=True) for t in brief["hi"]["actions"]]
    else:
        s.append(Paragraph("Hindi section unavailable: install 'uharfbuzz' and a Devanagari font.", small))
    return s


def build_pdf(ghat: str, summary: dict, brief: dict, readings: pd.DataFrame,
              rank: int, n_ghats: int, is_mock: bool = False) -> bytes:
    """Render the one-page brief and return the PDF bytes.

    ``readings`` is that ghat's annotated rows (see ``risk_engine.annotate``). Fonts are
    shrunk step by step until everything fits on one page.
    """
    for k in (1.0, 0.92, 0.85, 0.78, 0.7):
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=16 * mm, rightMargin=16 * mm,
                                topMargin=14 * mm, bottomMargin=12 * mm,
                                title=f"GhatWatch brief - {ghat}", author="GhatWatch")
        doc.build(_story(summary, brief, readings, rank, n_ghats, is_mock, k))
        if doc.page <= 1:
            break
    return buf.getvalue()


def _city_story(rows: list[dict], is_mock: bool, k: float) -> list:
    """One page ranking every ghat, with the first recommended action, in English then Hindi."""
    def st(**kw):
        return ParagraphStyle("c", **{"fontName": "Helvetica", "textColor": INK, "fontSize": 8.5 * k, "leading": 11 * k, **kw})
    hindi = hindi_available()
    titles = [Paragraph("GhatWatch - Visarjan Readiness Brief (all ghats)", st(fontName="Helvetica-Bold", fontSize=16 * k, leading=20 * k))]
    if hindi:
        titles.append(HindiText("घाटवॉच - विसर्जन तैयारी सार (सभी घाट)", size=12 * k, bold=True))
    titles.append(Paragraph(f"Bhopal Municipal Corporation &nbsp;|&nbsp; Prepared {date.today():%d %b %Y}", st(fontSize=8 * k, textColor=MUTED)))
    story: list = []
    if LOGO.exists():
        size = 18 * mm * k
        head = Table([[Image(str(LOGO), size, size, mask="auto"), titles]], colWidths=[size + 4 * mm, None], hAlign="LEFT")
        head.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
        story.append(head)
    else:
        story += titles
    story += [Spacer(1, 4 * k), Paragraph(f"<i>{DISCLAIMER_EN}</i>", st(fontSize=8 * k, textColor=MUTED))]
    if hindi:
        story.append(HindiText(DISCLAIMER_HI, size=8 * k, colour=MUTED))
    if is_mock:
        story.append(Paragraph("<b>DEMO DATA:</b> values are generated for demonstration, not real measurements.",
                               st(fontSize=8 * k, textColor=LEVEL_COLOUR["High"])))
    story.append(Spacer(1, 5 * k))
    data = [[Paragraph(f"<b>{h}</b>", st()) for h in ("#", "Ghat", "Level", "Score", "Gap", "Needs A / C / T", "First recommended action")]]
    for r in rows:
        col = LEVEL_COLOUR[r["risk_level"]].hexval()[2:]
        data.append([Paragraph(str(r["rank"]), st()), Paragraph(r["ghat"], st()),
                     Paragraph(f'<font color="#{col}"><b>{r["risk_level"]}</b></font>', st()),
                     Paragraph(f'{r["risk_score"]:.0f}', st()), Paragraph(f'{r["gap_pct"]:g}%', st()),
                     Paragraph(" / ".join(r[f"need_{n}"][0] for n in ("aeration", "cleaning", "testing")), st()), Paragraph(r["action_en"], st())])
    table = Table(data, colWidths=[7 * mm, 34 * mm, 15 * mm, 11 * mm, 12 * mm, 22 * mm, 77 * mm], repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, 0), 0.8, INK), ("LINEBELOW", (0, 1), (-1, -1), 0.3, RULE),
                               ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 2),
                               ("BOTTOMPADDING", (0, 0), (-1, -1), 2), ("LEFTPADDING", (0, 0), (-1, -1), 3)]))
    story += [table, Paragraph("Needs: A = aeration (low oxygen), C = cleaning (organic waste), T = extra testing (data gaps). H = high, M = medium, L = low.", st(fontSize=7.5 * k, textColor=MUTED))]
    if hindi:
        story += [Spacer(1, 8 * k), HindiText("घाटों की प्राथमिकता और पहली कार्रवाई", size=11 * k, bold=True)]
        for r in rows:
            story.append(HindiText(f'{r["rank"]}. {r["ghat_hi"]} · {LEVEL_HI[r["risk_level"]]} ({r["risk_score"]:.0f}) — {r["action_hi"]}', size=8.8 * k))
    else:
        story.append(Paragraph("Hindi section unavailable: install 'uharfbuzz' and a Devanagari font.", st(textColor=MUTED)))
    return story


def build_city_pdf(rows: list[dict], is_mock: bool = False) -> bytes:
    """Render the one-page city-wide brief; fonts shrink step by step until it fits one page."""
    for k in (1.0, 0.92, 0.85, 0.78, 0.7):
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=16 * mm, rightMargin=16 * mm, topMargin=14 * mm,
                                bottomMargin=12 * mm, title="GhatWatch - Visarjan readiness brief", author="GhatWatch")
        doc.build(_city_story(rows, is_mock, k))
        if doc.page <= 1:
            break
    return buf.getvalue()
