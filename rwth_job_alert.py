import json
import os
import re
import time
from datetime import datetime
from urllib.parse import urljoin, urldefrag

import requests
from bs4 import BeautifulSoup

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_IDS = os.getenv("TELEGRAM_CHAT_IDS", "").split(",")

RWTH_URL = "https://www.rwth-aachen.de/go/id/buym/lidx/1"
SEEN_FILE = "seen_jobs.json"

HEADERS = {"User-Agent": "Mozilla/5.0"}

JOB_CODE_RE = re.compile(r"\[?(V\d{9})\]?", re.IGNORECASE)

STUDENT_TERMS = [
    "studentische hilfskraft",
    "student assistant",
]

KEYWORDS = [
    "machine learning", "ml", "artificial intelligence", "ai",
    "deep learning", "reinforcement learning", "neural network",
    "computer vision", "image processing", "perception",
    "robot", "robots", "robotics", "ros", "autonomous",
    "autonomous driving", "navigation", "localization", "mapping",
    "slam", "path planning", "motion planning",
    "python", "programming", "software", "algorithm", "data science",
    "data analysis", "simulation", "matlab", "simulink",
    "mechanical", "mechatronics", "cad", "fem", "fea",
    "finite element", "finite element method", "ansys",
    "structural", "vibration", "dynamics", "kinematics",
    "automotive", "vehicle", "control", "automation",
    "maschinelles lernen", "künstliche intelligenz", "ki",
    "bildverarbeitung", "robotik", "roboter", "autonomes fahren",
    "lokalisierung", "kartierung", "regelung",
    "automatisierung", "sensorik", "wahrnehmung",
    "maschinenbau", "mechanik", "mechatronik", "simulation",
    "finite-elemente", "finite elemente", "struktur",
    "strukturanalyse", "schwingung", "dynamik", "kinematik",
    "fahrzeugtechnik", "automobil", "automotiv", "ika", "kraftfahrzeug"
]


def fetch(url):
    for attempt in range(3):
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            r.raise_for_status()
            return r.text
        except Exception as e:
            print(f"Attempt {attempt + 1}/3 failed for {url}: {e}")
            if attempt < 2:
                time.sleep(20)
    return ""


def load_seen():
    if not os.path.exists(SEEN_FILE):
        return set()
    try:
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    except Exception:
        return set()


def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(sorted(seen), f, indent=2)


def send_telegram(message):
    if not BOT_TOKEN or not CHAT_IDS:
        raise ValueError("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_IDS")

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    for chat_id in CHAT_IDS:
        chat_id = chat_id.strip()
        if not chat_id:
            continue

        r = requests.post(
            url,
            data={
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": False,
            },
            timeout=20,
        )
        r.raise_for_status()


def clean_url(url):
    return urldefrag(url)[0]


def keyword_matches(text):
    text = text.lower()
    found = []
    for kw in KEYWORDS:
        if re.search(r"\b" + re.escape(kw.lower()) + r"\b", text):
            found.append(kw)
    return sorted(set(found))


def is_student_job(text):
    text = text.lower()
    return any(term in text for term in STUDENT_TERMS)


def extract_title(text, job_code):
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    for line in lines:
        if job_code in line and not line.lower().startswith("rwth jobs portal"):
            return line[:180]

    for line in lines:
        if is_student_job(line):
            return line[:180]

    return "RWTH Student Assistant Job"


def get_candidate_jobs():
    html = fetch(RWTH_URL)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    candidates = {}

    for tag in soup.find_all(string=JOB_CODE_RE):
        job_code = JOB_CODE_RE.search(tag).group(1).upper()

        container = tag.find_parent(["tr", "li", "article", "div", "section"])
        if not container:
            continue

        context_text = container.get_text("\n", strip=True)

        if not is_student_job(context_text):
            continue

        link = None
        for a in container.find_all("a", href=True):
            href = clean_url(urljoin(RWTH_URL, a["href"]))

            if href == clean_url(RWTH_URL):
                continue

            if "rwth-aachen.de" not in href:
                continue

            link = href
            break

        if not link:
            continue

        candidates[job_code] = {
            "job_code": job_code,
            "url": link,
            "context": context_text,
        }

    return list(candidates.values())


def main():
    print("Checking URL:", RWTH_URL)

    seen = load_seen()
    jobs = get_candidate_jobs()

    print(f"Found {len(jobs)} real student-assistant job candidates.")

    sent = 0

    for job in jobs:
        job_code = job["job_code"]
        url = job["url"]

        if job_code in seen:
            continue

        detail_html = fetch(url)
        detail_text = ""

        if detail_html:
            detail_soup = BeautifulSoup(detail_html, "html.parser")
            detail_text = detail_soup.get_text("\n", strip=True)

        full_text = job["context"] + "\n" + detail_text

        if not is_student_job(full_text):
            continue

        matches = keyword_matches(full_text)

        if not matches:
            continue

        title = extract_title(full_text, job_code)

        message = f"""🚨 <b>New RWTH Student Assistant Job Match</b>

<b>{title}</b>

Job code:
<b>{job_code}</b>

Matched keywords:
{", ".join(matches[:20])}

Direct job link:
{url}
"""

        send_telegram(message)
        print(f"Sent alert for {job_code}: {title}")

        seen.add(job_code)
        sent += 1

    save_seen(seen)
    print(f"New matching student assistant jobs sent: {sent}")


if __name__ == "__main__":
    try:
        print("=" * 50)
        print("Checking RWTH jobs at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        main()
        print("Done.")
        print("=" * 50)
    except Exception as e:
        print("ERROR:", e)
        raise
