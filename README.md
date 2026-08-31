# Revision Planner 📚

An automated, data-driven revision planner written in Python that dynamically schedules topics based on a custom mathematical urgency formula. It balances forward progress with a global revision backlog, tracking your confidence via ratings and saving timestamps directly back to a local storage file.

## Features

* **Custom Priority Formula:** Automatically calculates which topic needs your attention most based on days elapsed, rating, and a 6-month exam deadline.
* **Bi-Weekly Interleaving Timetable:** Alternates between Week 1 and Week 2 grids to prevent subject clustering.
* **Smart Study Rules:** Handles new topic introductions on weekdays and mixes in high-priority review topics across all subjects on weekends.
* **Interactive Pomodoro Engine:** Built-in focus and break timers with clickable terminal hyperlinks and keyboard shortcut support (`Ctrl + C` to skip).
* **Crash-Safe Data Handling:** Safely checks for missing keys, empty strings, and `null` values without breaking, and automatically creates a backup file (`topics_backup.json`) before saving changes.

## File Structure

* `main.py`: The core script containing the scheduling logic, terminal user interface, and Pomodoro timer.
* `topics.json`: Your local database storing subjects, topics, study steps, last-revised dates, and confidence ratings.
* `topics_backup.json`: Automatic safety backup created every time you log a completed session.

## Getting Started

1. Ensure you have Python installed.
2. Place `main.py` and your `topics.json` file in the same directory.
3. Run the script from your terminal:
   ```bash
   python main.py
