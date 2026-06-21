# RWTH HiWi Job Alert Bot

A Telegram bot that automatically monitors the RWTH Aachen University Job Portal and sends Telegram alerts only for newly posted **Student Assistant / Studentische Hilfskraft** jobs that match my interests.

---

## Features

* Monitors the RWTH Job Portal automatically every hour using GitHub Actions.
* Sends Telegram notifications instantly.
* Only considers **official student assistant jobs**, i.e. postings containing:

  * `Studentische Hilfskraft` or `Student Assistant`
  * Official RWTH job codes such as `[V000010954]`
* Filters jobs using keywords from:

  * Machine Learning
  * Artificial Intelligence
  * Reinforcement Learning
  * Computer Vision
  * Robotics / ROS
  * Autonomous Driving
  * Mechanical Engineering
  * FEM / FEA / ANSYS
  * Dynamics / Kinematics
  * CAD / Simulation
  * Automotive Engineering
* Searches both **English and German** keywords.
* Avoids duplicate notifications by storing previously seen job IDs in `seen_jobs.json`.
* Runs completely in the cloud using **GitHub Actions**, so it continues working even when the laptop is turned off.

---

## Workflow

```text
RWTH Job Portal
        ↓
Download webpage
        ↓
Extract candidate links
        ↓
Check:
    - Studentische Hilfskraft OR Student Assistant
    - Official RWTH job code [VXXXXXXXXX]
    - Relevant keywords in title or description
        ↓
New match?
    ├── No → Ignore
    └── Yes
            ↓
    Send Telegram Alert
            ↓
    Save job ID to seen_jobs.json
```

---

## Technologies Used

* Python 3.12
* Requests
* BeautifulSoup4
* Telegram Bot API
* GitHub Actions
* JSON for persistence

---

## Repository Structure

```text
rwth_job_bot/
│
├── rwth_job_alert.py          # Main bot script
├── requirements.txt          # Python dependencies
├── seen_jobs.json            # Stores already notified jobs
├── .gitignore
│
└── .github/
    └── workflows/
        └── rwth_job_alert.yml   # GitHub Actions workflow
```

---

## Telegram Notification Example

```text
🚨 New RWTH Student Assistant Job Match

Studentische Hilfskraft (w/m/d) –
Machine Learning for Autonomous Robots

Job code:
V000010954

Matched keywords:
machine learning, robotics, autonomous, python

Direct job link:
https://www.rwth-aachen.de/...
```

---

## Future Improvements

* Add support for:

  * Fraunhofer Institutes Aachen
  * DLR
  * WZL
  * IKV
  * IMA/ZLW
  * FIA
  * Bosch Aachen
  * FEV
  * Ford Aachen
* Add fuzzy keyword matching.
* Add daily summary mode.
* Add support for multiple job portals.
* Use Playwright for more robust dynamic page scraping.

---

## Motivation

As a Master's student in **Robotic Systems Engineering at RWTH Aachen University**, I wanted an automated assistant that continuously monitors relevant HiWi opportunities in AI, Robotics, Mechanical Engineering and Autonomous Systems, and notifies me instantly without requiring manual searches and save some of my time.
