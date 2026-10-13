# PH Archive — Public News Source Data

A free, publicly inspectable source-link index for [PH Archive](https://ph-archive-public.vercel.app/#/repository). This repository stores **publisher RSS titles, short publisher excerpts, publication dates, and original article URLs**. It does not mirror copyrighted news article bodies.

## Running collector

- **Schedule:** Every day around **12:19 PM Philippine Time** (04:19 UTC), subject to GitHub Actions delays or cancellation.
- **First verified successful run:** October 13, 2026, [Actions run #1](https://github.com/cyriltagalog123-a11y/ph-archive-data/actions/runs/38364167300).
- **Feeds:** GMA News, The Philippine Star, Rappler through the [PH Archive public feed API](https://ph-archive-feed.vercel.app/api/news).
- **Source data:** [data/index.json](data/index.json) and [data/snapshots](data/snapshots).
- **Workflow:** [.github/workflows/collect.yml](.github/workflows/collect.yml).
- **Tests:** `python -m unittest discover -s tests -v`.

The first run committed **39 deduplicated source links**. Counts may change after later runs, corrections and review decisions. The collector is programmed to preserve same-day feed changes as separately named, content-addressed JSON snapshots.

### Editorial status and accuracy

All automated imports are marked **pending review**. Indexing an allegation, investigation or court proceeding does not mean PH Archive independently verifies it, implies wrongdoing by anyone mentioned, or reflects a final legal outcome. This is a **collection of source metadata**, not a complete archive of all Philippine government news since 1980.

Avoid publishing private personal rumors or unsupported allegations. Verify claims against publisher updates and official records; preserve corrections and linked responses separately.

### Free hosting and schedule

The GitHub repository is public and uses standard GitHub Actions, subject to GitHub's current free-use rules. GitHub may delay scheduled jobs, and public-repository schedules may be disabled after 60 days of repository inactivity. Check the [workflow run page](https://github.com/cyriltagalog123-a11y/ph-archive-data/actions/workflows/collect.yml) if daily entries stop changing. No paid API keys, database credentials, or external secrets are required.

### Run offline

```bash
python -m unittest discover -s tests -v
python scheduled_sync.py --input sample-feed.json --root data --day 2026-10-13
```

To collect current feeds manually, omit `--input`:

```bash
python scheduled_sync.py --root data
```

For each publication, PH Archive links readers to the original publisher's website. The code and data are independent from Dex AI and LifeGrid.
