# Data

Put the historical records in `bhopal_water_quality.csv` in this folder and redeploy.
Until that file exists, GhatWatch shows clearly labelled **demo data**.

One row per ghat / year / phase:

| column | meaning |
| --- | --- |
| `ghat` | ghat name |
| `year` | e.g. `2023` |
| `phase` | `Pre-Visarjan` or `Post-Visarjan` (also accepts `pre` / `post`) |
| `do_mg_l` | dissolved oxygen, mg/L |
| `bod_mg_l` | BOD, mg/L |
| `source` | report the value came from (shown in the evidence trail) |
| `page` | PDF page number in that report |
| `source_url` | optional: web link to the report (`https://…`). Shown as a clickable link in the evidence table; for `.pdf` links it opens at the cited `page`. Anything that is not an `http(s)` link is ignored. |

`do_mg_l` and `bod_mg_l` may contain lab strings: `<2` (below detection limit), `BDL`, `NA`, blanks.
Unreadable or missing values are never counted as clean water.
