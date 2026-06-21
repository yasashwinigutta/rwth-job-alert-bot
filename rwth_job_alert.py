import requests
from bs4 import BeautifulSoup
import json
import os
import re
import time
from datetime import datetime
from urllib.parse import urljoin

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

RWTH_URL = "https://www.rwth-aachen.de/go/id/buym/lidx/1"
SEEN_FILE = "seen_jobs.json"

JOB_CODE_PATTERN = re.compile(r"\[?V\d{9}\]?", re.IGNORECASE)

STUDENT_JOB_WORDS = [
    "Studentische Hilfskraft",
    "Student Assistant",
]

KEYWORDS = [
    "machine learning", "ml", "artificial intelligence", "ai",
    "deep learning", "reinforcement learning", "neural network",
    "computer vision", "image processing", "perception",
    "robot", "robots", "robotics", "ros", "ros2", "autonomous",
    "autonomous driving", "navigation", "localization", "mapping",
    "slam", "path planning", "motion planning",
    "python", "programming", "software", "algorithm", "data science",
    "data analysis", "simulation", "matlab", "simulink",
    "mechanical", "mechatronics", "cad", "fem", "fea",
    "finite element", "finite element method", "ansys",
    "structural", "vibration", "dynamics", "kinematics",
    "automotive", "vehicle", "control", "automation", "python"

    "maschinelles lernen", "künstliche intelligenz", "ki",
    "bildverarbeitung", "robotik", "roboter", "autonomes fahren",
    "navigation", "lokalisierung", "kartierung", "regelung",
    "automatisierung", "sensorik", "wahrnehmung",
    "maschinenbau", "mechanik", "mechatronik", "simulation",
    "finite-elemente", "finite elemente", "fem", "struktur",
    "strukturanalyse", "schwingung", "dynamik", "kinematik",
    "fahrzeugtechnik", "automobil", "automotive", "cad",
    "ansys", "matlab"
]

HEADERS = {"User-Agent": "Mozilla/5.0"}


def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(sorted(list(seen)), f, indent=2)


def fetch_url(url):
    for i in range(3):
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            r.raise_for_status()
            return r.text
        except Exception as e:
            print(f"Attempt {i+1}/3 failed for {url}")
            print(e)
            if i < 2:
                time.sleep(30)
    return ""


def send_telegram(message):
    if not BOT_TOKEN or not CHAT_ID:
        raise ValueError("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID")

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    r = requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }, timeout=20)
    r.raise_for_status()


def keyword_matches(text):
    text_lower = text.lower()
    matches = []

    for kw in KEYWORDS:
        pattern = r"\b" + re.escape(kw.lower()) + r"\b"
        if re.search(pattern, text_lower):
            matches.append(kw)

    return matches


def is_student_assistant_job(text):
    has_student_word = any(word.lower() in text.lower() for word in STUDENT_JOB_WORDS)
    has_job_code = bool(JOB_CODE_PATTERN.search(text))
    return has_student_word and has_job_code


def extract_job_code(text):
    match = JOB_CODE_PATTERN.search(text)
    return match.group(0).strip("[]") if match else None


def extract_title(soup, fallback):
    h1 = soup.find("h1")
    if h1:
        return h1.get_text(" ", strip=True)

    title = soup.find("title")
    if title:
        return title.get_text(" ", strip=True)

    return fallback


def get_candidate_links():
    html = fetch_url(RWTH_URL)
    if not html:
        print("Could not fetch RWTH job portal.")
        return []

    soup = BeautifulSoup(html, "html.parser")
    links = []

    for a in soup.find_all("a", href=True):
        href = urljoin(RWTH_URL, a["href"])
        text = a.get_text(" ", strip=True)

        if "rwth-aachen.de" not in href:
            continue

        links.append((text, href))

    return list(dict.fromkeys(links))


def main():
    print("Checking URL:", RWTH_URL)

    seen = load_seen()
    candidate_links = get_candidate_links()

    print(f"Found {len(candidate_links)} candidate links on portal page.")

    new_matches_count = 0

    for link_text, href in candidate_links:
        html = fetch_url(href)
        if not html:
            continue

        soup = BeautifulSoup(html, "html.parser")
        page_text = soup.get_text(" ", strip=True)
        full_text = link_text + " " + page_text

        # Rule 1: only real student assistant jobs with job code
        if not is_student_assistant_job(full_text):
            continue

        job_code = extract_job_code(full_text)
        job_id = job_code if job_code else href

        if job_id in seen:
            continue

        # Rule 2: keyword must appear in title OR description
        matches = keyword_matches(full_text)

        if not matches:
            continue

        title = extract_title(soup, link_text)

        message = f"""🚨 <b>New RWTH Student Assistant Job Match</b>

<b>{title}</b>

Job code:
<b>{job_code}</b>

Matched keywords:
{", ".join(matches[:20])}

Direct job link:
{href}
"""

        send_telegram(message)
        print(f"Sent alert for {job_code}: {title}")

        seen.add(job_id)
        new_matches_count += 1

    save_seen(seen)

    print(f"New matching student assistant jobs sent: {new_matches_count}")


if __name__ == "__main__":
    try:
        print("=" * 50)
        print("Checking RWTH jobs at",
              datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        main()

        print("Done.")
        print("=" * 50)

    except Exception as e:
        print("ERROR:", e)
