import json
import os
import random
import subprocess
import time
import sys
import shutil
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

def get_plan(subject, topic, phase=None):
    topic_data = topics_data[subject][topic]
    plan_data = topic_data.get("plan", {})
    
    if phase:
        if isinstance(plan_data, list):
            steps = plan_data if phase == "pomodoro_1" else []
        else:
            steps = plan_data.get(phase, [])
    else:
        if isinstance(plan_data, list):
            steps = plan_data
        else:
            steps = plan_data.get("pomodoro_1", []) + plan_data.get("pomodoro_2", [])
            
    formatted_steps = []
    for item in steps:
        url = item.get("url")
        text = item["text"]
        if url:
            formatted_steps.append(f"• {make_link(url, text)}")
        else:
            formatted_steps.append(f"• {text}")
            
    return "\n".join(formatted_steps) if formatted_steps else "• No tasks listed."

def get_best_topic(topic_pool):
    if not topic_pool:
        return None
    scored_pool = []
    for sub, top, meta in topic_pool:
        score = calculate_priority(meta["rating"], meta["last_revised"])
        scored_pool.append((score, sub, top))
    
    max_score = max(item[0] for item in scored_pool)
    highest_scored_topics = [item for item in scored_pool if abs(item[0] - max_score) < 1e-9]
    return random.choice(highest_scored_topics)

def run_countdown_clock(duration_minutes, label, color_code):
    total_seconds = duration_minutes * 60
    try:
        while total_seconds > 0:
            mins, secs = divmod(total_seconds, 60)
            timer_format = f"{label}: {mins:02d}:{secs:02d}"
            sys.stdout.write(f"\r{color_code}{timer_format}\033[0m          ")
            sys.stdout.flush()
            time.sleep(1)
            total_seconds -= 1
        print(f"\n\033[1;32m🔔 {label} complete!\033[0m\n")
    except KeyboardInterrupt:
        print(f"\n\033[1;31m⏩ Skipped the rest of this {label.lower()} block.\033[0m\n")

def run_pomodoro_engine(selected_tasks, week_label, current_day):
    total_cycles = 4 if len(selected_tasks) > 1 else 2
    
    for current_cycle in range(1, total_cycles + 1):
        task_index = 0 if current_cycle <= 2 or len(selected_tasks) == 1 else 1
        if task_index >= len(selected_tasks):
            task_index = 0
            
        sub, top = selected_tasks[task_index][1], selected_tasks[task_index][2]
        type_label = "OLD REVISION REVIEW" if topics_data[sub][top]["last_revised"] else "NEW TOPIC STUDY"
        
        phase = "pomodoro_1" if (current_cycle % 2 != 0) else "pomodoro_2"
        phase_title = "POMODORO 1 (Video & Flashcards)" if phase == "pomodoro_1" else "POMODORO 2 (Past Paper Questions)"
        
        # Display the plan and keep it visible while running the timer on the same page
        clear()
        print(f"\033[1;4mAUTOMATED REVISION SCHEDULE ({week_label} - {current_day.upper()})\033[0m")
        print(f"\033[1mTask: {sub} - {top} ({type_label})\033[0m\n")
        print(f"\033[1m--- {phase_title} ---\033[0m")
        print(get_plan(sub, top, phase))
        print("-" * 40 + "\n")
        print(f"\033[1;35m🍅 CYCLE {current_cycle} OF {total_cycles} ACTIVE 🍅\033[0m")
        print("👉 Press [Ctrl + C] to skip the current block.\n")
        
        run_countdown_clock(duration_minutes=25, label="⏳ Focus Time", color_code="\033[1;36m")
        print("\a")
        
        if current_cycle < total_cycles:
            print("\033[1;33m☕ Break time! Step away from your desk.\033[0m")
            print("")
            run_countdown_clock(duration_minutes=5, label="🧘 Rest Interval", color_code="\033[1;33m")
            print("\a")
            input("Press [Enter] to continue to the next block...")

    print("\n\033[1;32m🎉 All scheduled Pomodoro intervals finished! Ready for logging.\033[0m")

def save_completion(subject, topic):
    print(f"\nLogging completion for: \033[1m{topic}\033[0m")
    
    try:
        shutil.copy("topics.json", "topics_backup.json")
    except Exception as e:
        print(f"\033[93mWarning: Could not create database backup ({e})\033[0m")
        
    topics_data[subject][topic]["last_revised"] = date.today().strftime("%Y-%m-%d")
    
    current_rating = topics_data[subject][topic].get("rating", 1)
    print(f"Your current confidence rating for this topic is: {'★' * current_rating}")
    
    while True:
        new_rating_input = input("Enter your new rating (1-5, or press Enter to keep current): ").strip()
        if new_rating_input == "":
            break 
        if new_rating_input.isdigit() and 1 <= int(new_rating_input) <= 5:
            topics_data[subject][topic]["rating"] = int(new_rating_input)
            break
        print("\033[91mInvalid entry! Please enter a number between 1 and 5.\033[0m")

    with open("topics.json", "w") as f:
        json.dump(topics_data, f, indent=2)
    print(f"\033[92mSuccessfully saved updates for '{topic}'!\033[0m\n")

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
    
    week_number = current_date.isocalendar()[1]
    is_week_1 = (week_number % 2 != 0)
    
    today_subject = schedule_week_1.get(current_day) if is_week_1 else schedule_week_2.get(current_day)
    week_label = "WEEK 1" if is_week_1 else "WEEK 2"
    
    clear()
    print(f"\033[1;4mAUTOMATED REVISION SCHEDULE ({week_label} - {current_day.upper()})\033[0m")
    print(f"\033[1;32mToday's Scheduled Subject for New Content: {today_subject}\033[0m\n")

    selected_tasks = []

    if today_subject in topics_data:
        new_pool = []
        for topic_name, meta in topics_data[today_subject].items():
            if meta["last_revised"] is None:
                new_pool.append((today_subject, topic_name, meta))
        best_new = get_best_topic(new_pool)
        if best_new: selected_tasks.append(best_new)
    
    if is_weekend:
        global_old_pool = []
        for subject, sub_dict in topics_data.items():
            for topic_name, meta in sub_dict.items():
                if meta["last_revised"] is not None:
                    global_old_pool.append((subject, topic_name, meta))
        best_old = get_best_topic(global_old_pool)
        if best_old: 
            selected_tasks.append(best_old)
        else:
            print("\033[93mNotice: It's the weekend, but you haven't completed any new topics yet!\033[0m\n")

    if not selected_tasks:
        print("No matches available in the database for today's rules.")
        return

    # --- HOMEPAGE PREVIEW ---
    for idx, (score, sub, top) in enumerate(selected_tasks, 1):
        type_label = "OLD REVISION REVIEW" if topics_data[sub][top]["last_revised"] else "NEW TOPIC STUDY"
        print(f"\033[1;4mTARGET TASK {idx} ({type_label})\033[0m")
        print(f"\033[1mDate:\033[0m {current_date.strftime('%Y-%m-%d')} | \033[1mSubject:\033[0m {sub} | \033[1mTopic:\033[0m {top}\n")
        print("\033[1mFull Session Plan:\033[0m")
        print(get_plan(sub, top))
        print("-" * 40 + "\n")

    input("Press [Enter] to start studying...")
    print("")

    # --- RUN POMODORO ENGINE ---
    run_pomodoro_engine(selected_tasks=selected_tasks, week_label=week_label, current_day=current_day)
    
    # --- SESSION COMPLETION INTERFACE ---
    print("\n" + "="*40)
    print("\033[1;4mSESSION COMPLETION INTERFACE\033[0m")
    
    for idx, (_, s, t) in enumerate(selected_tasks, 1):
        type_label = "Old Revision" if topics_data[s][t]["last_revised"] else "New Topic"
        print(f"\nTask {idx} [{type_label}]: {s} - {t}")
        
        while True:
            response = input("Did you complete this topic? (y/n): ").strip().lower()
            if response in ['y', 'yes']:
                save_completion(s, t)
                break
            elif response in ['n', 'no']:
                print(f"Skipped logging for '{t}'.")
                break
            print("\033[91mInvalid input! Please type 'y' for yes or 'n' for no.\033[0m")
            
    print("\nAll session tasks processed. Keep up the great work!")
    sys.exit()

if __name__ == "__main__":
    generate_schedule()
    input()