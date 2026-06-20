import requests
from bs4 import BeautifulSoup
import json
import os
import re

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

RWTH_URL = "https://www.rwth-aachen.de/go/id/buym/lidx/1"
SEEN_FILE = "seen_jobs.json"

KEYWORDS = [
    # AI / ML / robotics
    "machine learning", "ml", "artificial intelligence", "ai",
    "deep learning", "reinforcement learning", "neural network",
    "computer vision", "image processing", "perception",
    "robot", "robots", "robotics", "ros", "autonomous",
    "autonomous driving", "navigation", "localization", "mapping",
    "slam", "path planning", "motion planning",

    # programming
    "python", "programming", "software", "algorithm", "data science",
    "data analysis", "simulation", "matlab", "simulink",

    # mechanical / automotive / FEM
    "mechanical", "mechatronics", "cad", "fem", "fea",
    "finite element", "finite element method", "ansys",
    "structural", "vibration", "dynamics", "kinematics",
    "automotive", "vehicle", "control", "automation",

    # German AI / robotics
    "maschinelles lernen", "künstliche intelligenz", "ki",
    "bildverarbeitung", "robotik", "roboter", "autonomes fahren",
    "navigation", "lokalisierung", "kartierung", "regelung",
    "automatisierung", "sensorik", "wahrnehmung",

    # German mechanical / simulation
    "maschinenbau", "mechanik", "mechatronik", "simulation",
    "finite-elemente", "finite elemente", "fem", "struktur",
    "strukturanalyse", "schwingung", "dynamik", "kinematik",
    "fahrzeugtechnik", "automobil", "automotive", "cad",
    "ansys", "matlab"
]

def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    })

def keyword_matches(text):
    text = text.lower()
    matches = []
    for kw in KEYWORDS:
        pattern = r"\b" + re.escape(kw.lower()) + r"\b"
        if re.search(pattern, text):
            matches.append(kw)
    return matches

import time

def get_page_text(url):

    for i in range(3):

        try:
            r = requests.get(
                url,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=20
            )

            soup = BeautifulSoup(r.text, "html.parser")
            return soup.get_text(" ", strip=True)

        except Exception as e:

            print(f"Attempt {i+1}/3 failed for {url}")
            print(e)

            if i < 2:
                print("Retrying in 30 seconds...")
                time.sleep(30)

    return ""

def main():
    #if not BOT_TOKEN or not CHAT_ID:
     #   raise ValueError("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID first.")

    seen = load_seen()

    r = requests.get(RWTH_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
    soup = BeautifulSoup(r.text, "html.parser")

    links = soup.find_all("a", href=True)

    for link in links:
        title = link.get_text(" ", strip=True)
        href = link["href"]

        if not title:
            continue

        if href.startswith("/"):
            href = "https://www.rwth-aachen.de" + href

        if "rwth-aachen.de" not in href:
            continue

        job_id = href

        if job_id in seen:
            continue

        description_text = get_page_text(href)
        full_text = title + " " + description_text

        matches = keyword_matches(full_text)

        if matches:
            message = f"""🚨 <b>New RWTH Job Match</b>

<b>{title}</b>

Matched keywords:
{", ".join(matches[:15])}

{href}
"""
            send_telegram(message)

        seen.add(job_id)

    save_seen(seen)

from datetime import datetime

if __name__ == "__main__":
    try:
        print("="*50)
        print("Checking RWTH jobs at",
              datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        main()

        print("Done.")
        print("="*50)

    except Exception as e:
        print("ERROR:", e)
