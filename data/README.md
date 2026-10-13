# PH Archive source data

This directory retains **public RSS metadata, not full news article bodies**. Index entries are keyed by normalized original publisher URL. Daily GitHub Actions runs create dated snapshots. All entries default to `editorialStatus: pending`; allegations and legal proceedings are not independently established findings.

Initial October 13, 2026 seed: 22 source links from GMA News, The Philippine Star and Rappler. One unrelated local crime story from the prior public snapshot was excluded from the government-specific archive.

- `data/index.json` — deduplicated source-link catalog.
- `data/snapshots/YYYY-MM-DD.json` — daily captures.
- Failed or delayed feed collection never indicates an absence of published reporting.
