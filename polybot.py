import requests
import schedule
import time
import json
import os

# ── CONFIGURE THESE ─────────────────────────────────────────────────────
TELEGRAM_TOKEN  = "8523781401:AAHRFq5LsS337LtxKTrgsLTAeeRQ2Ij8CXk"
TELEGRAM_CHAT_ID = "1284452829"
REFERRAL        = "?via=FwZsxtf"
POLL_MINUTES    = 30        # change to 15 or 30 to poll less often
# ────────────────────────────────────────────────────────────────────────

KNOWN_FILE = "known_markets.json"
API_URL    = "https://gamma-api.polymarket.com/events"
KEYWORDS   = ["fdv", "launch", "pre-market", "sale", "commitments", "listing", "ipo", "token", "clearing_price", "IPO", "hit"]

def is_premarket(event):
    title = event.get("title", "").lower()
    return any(kw in title for kw in KEYWORDS)

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    })

def fetch_events():
    params = {
        "tag_id": 21,
        "related_tags": "true",
        "closed": "false",
        "order": "startDate",
        "ascending": "false",
        "limit": 100
    }
    return requests.get(API_URL, params=params, timeout=10).json()

def load_known():
    if os.path.exists(KNOWN_FILE):
        return set(json.load(open(KNOWN_FILE)))
    return set()

def save_known(slugs):
    json.dump(list(slugs), open(KNOWN_FILE, "w"))

def check():
    print(f"[{time.strftime('%H:%M:%S')}] Checking...")
    try:
        events  = fetch_events()
        known   = load_known()

        new = [e for e in events if e["slug"] not in known and is_premarket(e)]

        for e in new:
            title = e.get("title", "New market")
            slug  = e["slug"]
            link  = f"https://polymarket.com/event/{slug}{REFERRAL}"
            msg   = (
                f"🔔 <b>New pre-market just dropped!</b>\n\n"
                f"📌 <b>{title}</b>\n\n"
                f"🔗 {link}"
            )
            send_telegram(msg)
            print(f"  ✅ Alerted: {title}")

        if not new:
            print("  No new pre-market events.")

        all_slugs = {e["slug"] for e in events}
        save_known(known | all_slugs)

    except Exception as ex:
        print(f"  ⚠️  Error: {ex}")

check()
schedule.every(POLL_MINUTES).minutes.do(check)
print(f"Bot running — checking every {POLL_MINUTES} min. Ctrl+C to stop.")
while True:
    schedule.run_pending()
    time.sleep(30)
