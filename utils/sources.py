"""The published reports GhatWatch's real readings come from (from the Track 2 participant guide).

Each MPPCB report covers one year, and a reading's ``page`` is the page in that year's report,
so a reading's year is enough to link it to its report. Demo data is never linked here: its
numbers are not taken from these reports.
"""
from __future__ import annotations

_MPPCB = "https://www.mppcb.mp.gov.in/proc/mon/"

SOURCE_REPORTS = [
    {"year": 2025, "title": "MPPCB Ganesh and Durga Visarjan Report 2025 (92 pages)",
     "url": _MPPCB + "Ganesh_and_Durga_visarjan_report-2025.pdf"},
    {"year": 2024, "title": "MPPCB Ganesh and Durga Visarjan Report 2024 (118 pages)",
     "url": _MPPCB + "Ganesh_and_Durga_visarjan_report-2024.pdf"},
    {"year": 2023, "title": "MPPCB Idol Immersion Report 2023, CPCB format (87 pages)",
     "url": _MPPCB + "Idol_immer._Report_23_CPCB.pdf"},
]

REFERENCE_LINKS = [
    {"title": "Upper and Lower Lake monthly water quality 2025-26, MPPCB (lake context)",
     "url": "https://xgn.mp.nic.in/File_Upload/MONITORING//Yearly%20Water%20Quality%20Status/2026/July/UPPER%20LAKE-2025-26..pdf"},
    {"title": "Copy of that report in the Track 2 pack",
     "url": "https://github.com/Laaaaksh/bhopal-impact-lab-2026/blob/main/tracks/02-visarjan-ghat-watch/resources/Upper_Lower_Lake_monthly_2025-26_from_xgn.pdf"},
    {"title": "CPCB water quality criteria (the Class B limits used)", "url": "https://cpcb.gov.in/water-quality-criteria/"},
]

_BY_YEAR = {r["year"]: r for r in SOURCE_REPORTS}


def report_for_year(year: int) -> dict | None:
    """The report covering ``year``, or None if it is not one of the known reports."""
    return _BY_YEAR.get(int(year))


# Demo readings are labelled MOCK, but each links to the real published document for its year so the
# table can be explored. The page numbers on demo rows are illustrative, so the page is never opened.
DEMO_LINKS = {
    2023: _MPPCB + "Idol_immer._Report_23_CPCB.pdf",
    2024: _MPPCB + "Ganesh_and_Durga_visarjan_report-2024.pdf",
    2025: _MPPCB + "Ganesh_and_Durga_visarjan_report-2025.pdf",
}
