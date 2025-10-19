#!/usr/bin/env python3
import os, re, sys, requests, yaml
from datetime import timedelta
from ics import Calendar, Event
from ics.alarm import DisplayAlarm
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
        r = requests.get(url, timeout=30, headers={"User-Agent": "ArnionCalendarBot/1.0"})
        r.raise_for_status()
        text = r.text
        if not text.startswith("BEGIN:VCALENDAR"):
            raise ValueError("Not a valid .ics feed")
        return text
    except Exception as e:
        print(f"[warn] failed to fetch or parse {url}: {e}", file=sys.stderr)
        return ""

def norm_dt(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))
    return dt.astimezone(TZ)

def build_leo_alarms(boost_type):
    alarms = []
    alarms.append(DisplayAlarm(trigger=timedelta(minutes=-30),
                               display_text="🦁 Leo Boost (30 min prior)"))
    texts = {
        "investor": "You’re not seeking approval—you’re offering opportunity. Lead with legacy, not logistics. Calm power. Strategic confidence.",
        "networking": "Goal: one real connection that lasts. Ask vision questions. Smile first, listen hard, connect two people before you leave.",
        "learning": "Empty your cup. Capture 3 takeaways you’ll apply within 48 hours. Speed of application beats volume of notes.",
        "leadership": "Raise the room’s temperature. Speak precisely, serve generously, leave people better by proximity.",
        "vision": "Recalibrate to your 5 Fs. Let conviction be felt in your posture, not just your words.",
    }
    alarms.append(DisplayAlarm(trigger=timedelta(minutes=-10),
                               display_text=texts.get(boost_type, "Walk in like you belong. Transmit conviction.")))
    return alarms

def merge_calendars(source_urls, top_tier_cfg):
    master = Calendar()
    patterns = [(re.compile(item["pattern"]), item.get("boost", "networking"))
                for item in top_tier_cfg.get("top_tier", [])]

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
            ev.begin = norm_dt(ev.begin.datetime)
            if ev.end:
                ev.end = norm_dt(ev.end.datetime)
            title = (ev.name or "").strip()
            tier_emoji = "🤝"
            boost_type = None
            title_lower = title.lower()
            if any(k in title_lower for k in ["workshop", "masterclass", "training", "bootcamp", "summit", "school"]):
                tier_emoji = "🧠"
            if any(k in title_lower for k in ["mixer", "network", "happy hour", "meetup", "connect"]):
                tier_emoji = "🚀"
            for rx, btype in patterns:
                if rx.search(title or ""):
                    tier_emoji = "💎"
                    boost_type = btype
                    break
            if tier_emoji and not title.startswith(tier_emoji):
                ev.name = f"{tier_emoji} {title}"
            if tier_emoji == "💎":
                for a in build_leo_alarms(boost_type):
                    ev.alarms.append(a)
            master.events.add(ev)
    return master

def upload_to_gist(calendar_text):
    if not GIST_TOKEN or not GIST_ID:
        raise RuntimeError("Missing GIST_TOKEN or GIST_ID")
    url = f"https://api.github.com/gists/{GIST_ID}"
    payload = {"files": {GIST_FILENAME: {"content": calendar_text}}}
    headers = {
        "Authorization": f"Bearer {GIST_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    r = requests.patch(url, json=payload, headers=headers, timeout=30)
    if r.status_code not in (200, 201):
        raise RuntimeError(f"Gist update failed: {r.status_code} {r.text}")
    print("[ok] Gist updated.")

def main():
    srcs = load_sources()
    cfg = load_top_tier()
    cal = merge_calendars(srcs, cfg)
    cal.creator = "Arnion Expansion Calendar — Auto"
    cal.extra.append(("X-WR-CALNAME", "Arnion Expansion Calendar 🦁"))
    cal.extra.append(("X-WR-TIMEZONE", "America/Los_Angeles"))
    # The fix: convert Calendar to string directly
    text = str(cal)
    upload_to_gist(text)

if __name__ == "__main__":
    main()
