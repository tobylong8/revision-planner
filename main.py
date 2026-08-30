import json
import os
import random
import subprocess
import time
import sys
from datetime import date, datetime

# Load topics from configuration file
with open("topics.json", "r") as f:
    topics_data = json.load(f)

def make_link(url, text):
    return f"\x1b]8;;{url}\x1b\\{text}\x1b]8;;\x1b\\"

def clear():
    subprocess.run("cls" if os.name == "nt" else "clear", shell=True)

def calculate_priority(rating, last_revised_str):
    current_date = date.today()
    if last_revised_str:
        last_revised_dt = datetime.strptime(last_revised_str, "%Y-%m-%d").date()
        days_since_last_revised = (current_date - last_revised_dt).days
        days_elapsed = days_since_last_revised
    else:
        days_since_last_revised = 180
        days_elapsed = 180

    rating = max(1, rating)
    part1 = (days_since_last_revised + 1) / (rating * rating)
    part2 = (days_elapsed / 180) * (6 - rating)
    return part1 + part2

def get_plan(subject, topic):
    steps = topics_data[subject][topic]["plan"]
    formatted_steps = []
    for item in steps:
        if item["url"]:
            formatted_steps.append(f"• {make_link(item['url'], item['text'])}")
        else:
            formatted_steps.append(f"• {item['text']}")
    return "\n".join(formatted_steps)

def get_best_topic(topic_pool):
    """Calculates scores and handles randomized ties for the highest priority score."""
    if not topic_pool:
        return None
    scored_pool = []
    for sub, top, meta in topic_pool:
        score = calculate_priority(meta["rating"], meta["last_revised"])
        scored_pool.append((score, sub, top))
    
    # 1. Look ONLY at the numeric score value (index 0) to find the maximum
    max_score = max(item[0] for item in scored_pool)
    
    # 2. Compare ONLY the score value (item[0]) against the max_score
    highest_scored_topics = [item for item in scored_pool if abs(item[0] - max_score) < 1e-9]
    return random.choice(highest_scored_topics)

def run_countdown_timer(duration_minutes=60):
    """Displays a ticking countdown clock that can be completed early via Ctrl+C."""
    total_seconds = duration_minutes * 60
    print(f"\033[1;33m⏱️  Starting your {duration_minutes}-minute study session now...")
    print("👉 Press [Ctrl + C] at any time if you finish studying early!\033[0m\n")
    
    try:
        while total_seconds > 0:
            mins, secs = divmod(total_seconds, 60)
            timer_format = f"Time Remaining: {mins:02d}:{secs:02d}"
            sys.stdout.write(f"\r\033[1;36m⏳ {timer_format}\033[0m")
            sys.stdout.flush()
            time.sleep(1)
            total_seconds -= 1
        print("\n\n\033[1;32m🎉 Time's up! Brilliant job finishing your session.\033[0m")
    except KeyboardInterrupt:
        print("\n\n\033[1;32m▶️  Timer stopped. Let's record your progress.\033[0m")

def save_completion(subject, topic):
    """Updates revision date and asks the user to adjust their confidence rating."""
    print(f"\nLogging completion for: \033[1m{topic}\033[0m")
    
    # 1. Update the date timestamp
    topics_data[subject][topic]["last_revised"] = date.today().strftime("%Y-%m-%d")
    
    # 2. Grab current rating for reference
    current_rating = topics_data[subject][topic].get("rating", 1)
    print(f"Your current confidence rating for this topic is: {'★' * current_rating}")
    
    # 3. Request a new rating profile input
    while True:
        new_rating_input = input("Enter your new rating (1-5, or press Enter to keep current): ").strip()
        if new_rating_input == "":
            break # Keep the current rating intact
        if new_rating_input.isdigit() and 1 <= int(new_rating_input) <= 5:
            topics_data[subject][topic]["rating"] = int(new_rating_input)
            break
        print("\033[91mInvalid entry! Please enter a number between 1 and 5.\033[0m")

    # 4. Flush changes out to disk space storage
    with open("topics.json", "w") as f:
        json.dump(topics_data, f, indent=2)
    print(f"\n\033[92mSuccessfully saved! '{topic}' database metrics updated.\033[0m")

def generate_schedule():
    schedule_week_1 = {
        "Monday": "Maths", "Tuesday": "Biology", "Wednesday": "Computer Science",
        "Thursday": "English", "Friday": "Spanish", "Saturday": "Geography", "Sunday": "Chemistry"
    }
    schedule_week_2 = {
        "Monday": "English", "Tuesday": "Spanish", "Wednesday": "Maths",
        "Thursday": "Physics", "Friday": "Computer Science", "Saturday": "Geography", "Sunday": "Maths"
    }
    
    current_date = date.today()
    current_day = current_date.strftime("%A")
    is_weekend = current_day in ["Saturday", "Sunday"]
    
    # Fixed tuple index lookup [1] for extracting calendar week integer cleanly
    week_number = current_date.isocalendar()[1]
    is_week_1 = (week_number % 2 != 0)
    
    today_subject = schedule_week_1.get(current_day) if is_week_1 else schedule_week_2.get(current_day)
    week_label = "WEEK 1" if is_week_1 else "WEEK 2"
    
    clear()
    print(f"\033[1;4mAUTOMATED REVISION SCHEDULE ({week_label} - {current_day.upper()})\033[0m")
    print(f"\033[1;32mToday's Scheduled Subject for New Content: {today_subject}\033[0m\n")

    selected_tasks = []

    # --- POOL 1: NEW TOPIC FOR TODAY'S SUBJECT ---
    if today_subject in topics_data:
        new_pool = []
        for topic_name, meta in topics_data[today_subject].items():
            if meta["last_revised"] is None:
                new_pool.append((today_subject, topic_name, meta))
        best_new = get_best_topic(new_pool)
        if best_new: selected_tasks.append(best_new)
    
    # --- POOL 2: OLD TOPIC FROM ANY SUBJECT (WEEKENDS ONLY) ---
    if is_weekend:
        global_old_pool = []
        for subject, sub_dict in topics_data.items():
            for topic_name, meta in sub_dict.items():
                if meta["last_revised"] is not None:
                    global_old_pool.append((subject, topic_name, meta))
        best_old = get_best_topic(global_old_pool)
        if best_old: selected_tasks.append(best_old)

    if not selected_tasks:
        print("No matches available in the database for today's rules.")
        return

    # Print out targets instantly
    for idx, (score, sub, top) in enumerate(selected_tasks, 1):
        type_label = "OLD REVISION REVIEW" if topics_data[sub][top]["last_revised"] else "NEW TOPIC STUDY"
        print(f"\033[1;4mTARGET TASK {idx} ({type_label}):\033[0m")
        print(f"\033[1mSubject:\033[0m {sub} | \033[1mTopic:\033[0m {top}\n")
        print(get_plan(sub, top))
        print("-" * 40 + "\n")

    # --- DYNAMIC AUTOMATIC TIMING BLOCK ---
    # Assign 120 minutes on Saturday/Sunday, otherwise 60 minutes
    timer_duration = 120 if is_weekend else 60
    run_countdown_timer(duration_minutes=timer_duration)
    
    # --- COMPLETION LOGGING TREE (TRIGGERED AFTER TIMER FINISHES/CANCELLED) ---
    print("\n" + "="*40)
    print("\033[1;4mSESSION COMPLETION INTERFACE\033[0m")
    print("1. Log a completed topic and update confidence score")
    print("2. Close program without updating logs")
    
    action = input("\nChoose an option: ").strip()
    
    if action == "1":
        if len(selected_tasks) == 1:
            # Weekdays: Instantly logs the single available topic
            _, s, t = selected_tasks[0]
            save_completion(s, t)
        else:
            # Weekends: Lets you pick which of the two active slots you finished working on
            print("\nWhich topic did you work on or finish?")
            for idx, (_, _, top) in enumerate(selected_tasks, 1):
                print(f"{idx}. {top}")
            choice = input("Enter number: ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(selected_tasks):
                _, s, t = selected_tasks[int(choice) - 1]
                save_completion(s, t)
    else:
        print("\nExiting. Keep up the hard work next time!")

if __name__ == "__main__":
    generate_schedule()
