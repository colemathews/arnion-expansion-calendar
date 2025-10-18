# arnion-expansion-calendar
Automated calendar for entrepreneur events in the Bay Area
[README.md](https://github.com/user-attachments/files/22987563/README.md)
# Arnion Expansion Calendar — Auto-Updating Feed

This repo generates a **single master `.ics`** file and pushes it to your **Gist** on a schedule so Google Calendar stays synced automatically.

## How it works
1. **`sources.txt`** lists upstream calendar feeds (ICS) to merge (Meetup groups, chambers, conferences, etc.).
2. **`top_tier.yml`** defines events that should get 💎 tags and **Leo Boost** reminders (by name/regex).
3. **`merge_ics.py`** fetches sources, merges events, normalizes times to *America/Los_Angeles*, adds emoji tags and VALARMs, and uploads to your **Gist** via API.
4. A GitHub Action runs **daily at 7:00 AM PT** and also supports **manual dispatch** and **webhook dispatch**.

## Setup (one-time)
1. Create a **Personal Access Token (classic)** with **gist** scope. Name it `GIST_TOKEN` in repo **Settings → Secrets and variables → Actions → New repository secret**.
2. Add two more secrets:
   - `GIST_ID`: the ID of your Gist (e.g., `f10b313eedf1944ac1aeb06434b2aa2c`)
   - `GIST_FILENAME`: `Arnion_Expansion_Calendar.ics` (or your gist filename)
3. Edit `sources.txt` to include the ICS feeds you want merged.
4. (Optional) Edit `top_tier.yml` to customize 💎 tagging and Leo Boost types.

## Manual run
- Go to **Actions → Update Arnion Expansion Calendar → Run workflow**.

## Webhook (hands-off trigger)
- Use the **repository_dispatch** endpoint to trigger an immediate update:
  ```bash
  curl -X POST -H "Accept: application/vnd.github+json" \
       -H "Authorization: Bearer <YOUR_GH_TOKEN_WITH_REPO_SCOPE>" \
       https://api.github.com/repos/<your-username>/arnion-expansion-calendar/dispatches \
       -d '{"event_type":"update_calendar"}'
  ```

> Google Calendar refresh cadence is controlled by Google (usually hours). This workflow ensures your Gist is always fresh.

---

**Made for Cole by Leo.**
