# Revision Planner 📚

An automated, data-driven terminal revision app built in Python, designed to automate GCSE revision.

It dynamically schedules topics using a mathematical priority formula, integrates active-recall AI prompt generation, tracks practice paper scores against realistic grade boundaries, and maintains study streak heatmaps.

---

## Features

- **Dynamic Urgency Algorithm**
  - Calculates topic priority using confidence ratings and days since last revision.
  - Automatically determines what should be studied each day.

- **Bi-Weekly Subject Rotation**
  - Alternates between Week 1 and Week 2 science schedules.
  - Covers Biology, Chemistry, and Physics on weekdays to reduce subject fatigue.

- **Interactive Pomodoro Engine**
  - **Pomodoro 1:** Video & Flashcards
  - **Pomodoro 2:** Past Paper Questions
  - Built-in focus countdown timers.
  - Automated audio notifications using `alarm.mp3`.
  - Keyboard controls during focus sessions:
    - `P` — Pause / Resume timer
    - `M` — Mute / Unmute background music
    - `Up / Down` — Adjust master volume
    - `Ctrl + C` — Skip the current interval

- **ChatGPT Active-Recall Integration**
  - Generates custom AQA Combined Science prompts.
  - Copies prompts directly to the clipboard using `pyperclip`.
  - Automatically opens targeted prompt URLs in Microsoft Edge.

- **Past Paper Grade Evaluation**
  - Evaluates practice paper scores against subject grade boundaries.
  - Supports Biology, Chemistry, Physics, Computer Science, Maths, and English.
  - Automatically adjusts topic confidence ratings from **1–5 stars**.

- **Terminal Heatmap & Streaks**
  - Displays a 14-week GitHub-style study activity heatmap.
  - Tracks both current and longest study streaks.

- **Background Audio Engine**
  - Randomly plays local MP3 tracks.
  - Uses Pygame mixer threads to keep music running without interfering with timer alerts.

---

## File Structure

```text
Revision-Planner/
├── main.py              # Core application logic, scheduler, UI panels & audio threads
├── topics.json          # Database containing subjects, topics, study steps & rating history
├── topics_backup.json   # Automatic safety backup generated after completion logs
├── alarm.mp3            # Alarm sound played at break intervals
└── Music/               # Folder containing background MP3 tracks
