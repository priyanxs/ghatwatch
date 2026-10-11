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


# Every document the Track 2 guide lists. "role" says honestly what GhatWatch does with it. The pack holds a copy of each PDF.
_PACK = "https://github.com/Laaaaksh/bhopal-impact-lab-2026/blob/main/tracks/02-visarjan-ghat-watch/resources/"
SOURCE_DOCUMENTS = [
    {"title": "MPPCB Ganesh and Durga Visarjan Report 2025", "pages": 92, "role": "readings", "url": _MPPCB + "Ganesh_and_Durga_visarjan_report-2025.pdf", "pack": _PACK + "Ganesh_and_Durga_visarjan_report-2025.pdf"},
    {"title": "MPPCB Ganesh and Durga Visarjan Report 2024", "pages": 118, "role": "readings", "url": _MPPCB + "Ganesh_and_Durga_visarjan_report-2024.pdf", "pack": _PACK + "Ganesh_and_Durga_visarjan_report-2024.pdf"},
    {"title": "MPPCB Idol Immersion Report 2023 (CPCB format)", "pages": 87, "role": "readings", "url": _MPPCB + "Idol_immer._Report_23_CPCB.pdf", "pack": _PACK + "Idol_immer._Report_23_CPCB.pdf"},
    {"title": "Upper and Lower Lake monthly water quality 2025-26", "pages": 12, "role": "lakes",
     "url": "https://xgn.mp.nic.in/File_Upload/MONITORING//Yearly%20Water%20Quality%20Status/2026/July/UPPER%20LAKE-2025-26..pdf", "pack": _PACK + "Upper_Lower_Lake_monthly_2025-26_from_xgn.pdf"},
    {"title": "Upper Lake water quality 2023-24", "pages": None, "role": "unused", "url": _MPPCB + "Bhopal-2023-24_upper_lake.pdf", "pack": _PACK + "Bhopal-2023-24_upper_lake.pdf"},
    {"title": "Upper Lake water quality by station, 2003-04 to 2022-23", "pages": None, "role": "unused", "url": _MPPCB + "comparatives-uppe-lak-lower-lake-2003-2023.pdf", "pack": _PACK + "comparatives-uppe-lak-lower-lake-2003-2023.pdf"},
    {"title": "CPCB water quality criteria (Class B limits)", "pages": None, "role": "limits", "url": "https://cpcb.gov.in/water-quality-criteria/", "pack": ""},
    {"title": "NGT immersion ban and new BMC ghats, Free Press Journal, 26 Feb 2026", "pages": None, "role": "context",
     "url": "https://www.freepressjournal.in/amp/bhopal/mp-news-idol-immersion-to-shift-from-lakes-to-safer-sites-ngt-ban-pushes-bmc-to-build-4-dedicated-ghats", "pack": ""},
    {"title": "Durga visarjan date, 20 October 2026, Drik Panchang", "pages": None, "role": "context",
     "url": "https://www.drikpanchang.com/navratri/durga-puja/durga-visarjan-date-time.html?year=2026", "pack": ""},
]
