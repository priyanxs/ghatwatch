# Security

GhatWatch is a read-only decision-support site: it has no login, no user accounts, no database and accepts no uploads.
Every endpoint is a `GET`, and the only data it serves is the public MPPCB readings in `data/`.

## Reporting a problem

Please open a report at https://github.com/priyanxs/ghatwatch/issues (or use GitHub's private vulnerability reporting on the
repository's Security tab for anything sensitive). Include what you saw and how to reproduce it.

## What is in place

- **Browser protections:** a strict Content-Security-Policy (scripts only from this site, `unpkg.com` and `cdn.plot.ly`, each with a
  Subresource Integrity hash; no inline scripts; no framing), `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`,
  `Permissions-Policy`, and HSTS (from Vercel). The values live in `vercel.json` and are mirrored in `api/index.py` for local runs.
- **No injection paths:** all text from the data is HTML-escaped before it is shown; report links are only used if they start with
  `http://` or `https://`; text placed in PDFs is escaped; the page ignores browser-stored settings it does not recognise.
- **Weekly social posting is off by default.** The cron endpoint is disabled unless `CRON_SECRET` is set, compares it in constant time,
  is never cached, only speaks https (no redirects to other schemes), and never posts demo data. Keys are environment variables only;
  nothing secret is in the repository or its history.
- **Errors:** internal error text is logged, not returned to visitors; the API does not echo the input it was given.
- **Dependencies** are pinned in `requirements.txt` and checked weekly by Dependabot. The last `pip-audit` run found no known vulnerabilities.
- **Availability:** the PDF endpoints, the heaviest responses, are built once per day per instance and cached.

## Known limits

- There is no application-level rate limiting; Vercel's platform protections apply. Heavy responses are cached to keep this cheap.
- The map and charts load libraries and tiles from public CDNs (unpkg, cdn.plot.ly, OpenStreetMap, Google Fonts), so the page needs internet access.
- If the weekly post is enabled and the cron job is retried, a channel without idempotency support (Telegram, generic webhooks) could receive a duplicate.
