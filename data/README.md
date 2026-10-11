# Data

`bhopal_ghats_2023_2025.csv` is the Track 2 dataset: every reading at the 7 Bhopal ghats, 2023 to 2025, Ganesh and Durga,
before / during / one week after immersion. One row per site / year / festival / phase / parameter, with
`value`, `flag` (why a value is empty: `BDL`, `not sampled`, `*`, `**`), `value_as_printed` and `source_page`.
GhatWatch scores three parameters: Dissolved oxygen, BOD and pH.

Replace the file with newer data in the same format to update the site. If it is missing or unreadable, labelled demo data is shown.

| value | treated as |
| --- | --- |
| a number | checked against the CPCB Class B limit |
| `<2` | below 2: a pass for BOD (provably under 3), no data for DO |
| `BDL`, `ND` | below detection / not detected, "very low": a pass for BOD, no data for DO and pH |
| blank, `NA`, `_`, `-`, `*`, `**`, `not sampled` | missing: **never** counted as clean water |
| a whole festival table absent from a report | missing, shown as a gap |

`ghat_locations.csv` gives each ghat's map position (`lat`, `lon`, `precision` = `exact` or `approximate`, `basis`).
A row without coordinates keeps that ghat off the map.

`lake_monitoring_2025_26.csv` is the pack's monthly lake report (Upper Lake: 4 stations, Lower Lake: Kalighat), April 2025 to March 2026: DO, pH and BOD (3 days, 27°C), one row per station / month / parameter, with the PDF page. It is context only and is not scored.

The site's **All readings** section and `/api/readings.csv` expose every row of `bhopal_ghats_2023_2025.csv` (all 13 parameters), not just the three that are scored.
