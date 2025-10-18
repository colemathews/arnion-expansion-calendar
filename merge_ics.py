#!/usr/bin/env python3
import os, re, sys, io, requests, pytz, yaml
from datetime import datetime, timedelta
from ics import Calendar, Event, Alarm
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Los_Angeles")

GIST_TOKEN = os.environ.get("GIST_TOKEN")
GIST_ID = os.environ.get("GIST_ID")
GIST_FILENAME = os.environ.get("GIST_FILENAME", "Arnion_Expansion_Calendar.ics")

def load_sources(path="sources.txt"):
    urls = []
    if os.path.exists(path):
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"): 
                    continue
                urls.append(line)
    return urls

def load_top_tier(path="top_tier.yml"):
    if os.path.exists(path):
        with open(path, "r") as f:
            return yaml.safe_load(f) or {}
    return {"top_tier": []}

def fetch_ics(url):
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"[warn] failed to fetch {url}: {e}", file=sys.stderr)
        return ""

def norm_dt(dt):
    # Ensure timezone-aware and convert to Pacific
    if dt is None:
        return None
    if dt.tzinfo is None:
        # Assume UTC if no tz; convert to PT
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))
    return dt.astimezone(TZ)

def build_leo_alarms(boost_type):
    alarms = []
    # 30-min pre Leo Boost
    alarms.append(Alarm(display_text="🦁 Leo Boost (30 min prior)", trigger=timedelta(minutes=-30)))
    # 10-min pre tactical
    texts = {
        "investor": "You’re not seeking approval—you’re offering opportunity. Lead with legacy, not logistics. Calm power. Strategic confidence.",
        "networking": "Goal: one real connection that lasts. Ask vision questions. Smile first, listen hard, connect two people before you leave.",
        "learning": "Empty your cup. Capture 3 takeaways you’ll apply within 48 hours. Speed of application beats volume of notes.",
        "leadership": "Raise the room’s temperature. Speak precisely, serve generously, leave people better by proximity.",
        "vision": "Recalibrate to your 5Fs. Let conviction be felt in your posture, not just your words.",
    }
    alarms.append(Alarm(display_text=texts.get(boost_type, "Walk in like you belong. Transmit conviction."), trigger=timedelta(minutes=-10)))
    # 15-min post follow-up
    alarms.append(Alarm(display_text="Post-Event: Send 5 follow-ups, add to CRM, schedule coffees.", trigger=timedelta(minutes=15), trigger_rel="END"))
    return alarms

def merge_calendars(source_urls, top_tier_cfg):
    master = Calendar()
    patterns = [(re.compile(item["pattern"]), item.get("boost","networking")) for item in top_tier_cfg.get("top_tier", [])]

    for url in source_urls:
        data = fetch_ics(url)
        if not data:
            continue
        try:
            c = Calendar(data)
        except Exception as e:
            print(f"[warn] parse failed for {url}: {e}", file=sys.stderr)
            continue
        for ev in list(c.events):
            # Normalize times
            ev.begin = norm_dt(ev.begin.datetime)
            if ev.end:
                ev.end = norm_dt(ev.end.datetime)
            # Tag tier via simple heuristics
            title = (ev.name or "").strip()
            tier_emoji = "🤝"
            boost_type = None
            # Heuristic keywords
            title_lower = title.lower()
            if any(k in title_lower for k in ["workshop", "masterclass", "training", "bootcamp", "summit", "school"]):
                tier_emoji = "🧠"
            if any(k in title_lower for k in ["mixer", "network", "happy hour", "meetup", "connect"]):
                tier_emoji = "🚀"
            # Top-tier via patterns
            for rx, btype in patterns:
                if rx.search(title or ""):
                    tier_emoji = "💎"
                    boost_type = btype
                    break

            # Prefix summary
            if tier_emoji and not title.startswith(tier_emoji):
                ev.name = f"{tier_emoji} {title}"

            # Leo alarms for 💎
            if tier_emoji == "💎":
                for a in build_leo_alarms(boost_type):
                    ev.alarms.append(a)

            master.events.add(ev)
    return master

def upload_to_gist(calendar_text):
    if not GIST_TOKEN or not GIST_ID:
        raise RuntimeError("Missing GIST_TOKEN or GIST_ID")
    url = f"https://api.github.com/gists/{GIST_ID}"
    payload = {
        "files": {
            GIST_FILENAME: {
                "content": calendar_text
            }
        }
    }
    headers = {
        "Authorization": f"Bearer {GIST_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    r = requests.patch(url, json=payload, headers=headers, timeout=30)
    if r.status_code not in (200, 201):
        raise RuntimeError(f"Gist update failed: {r.status_code} {r.text}")
    print("[ok] Gist updated.")

def main():
    srcs = load_sources()
    cfg = load_top_tier()
    cal = merge_calendars(srcs, cfg)
    # Ensure calendar has a name/timezone metadata
    cal.creator = "Arnion Expansion Calendar — Auto"
    cal.extra.append(("X-WR-CALNAME", "Arnion Expansion Calendar 🦁"))
    cal.extra.append(("X-WR-TIMEZONE", "America/Los_Angeles"))
    text = cal.serialize()
    upload_to_gist(text)

if __name__ == "__main__":
    main()
