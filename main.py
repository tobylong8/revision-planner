import json
import os
import random
import sys
import shutil
import time
import subprocess
from datetime import date, datetime

# Import terminal rendering components
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.text import Text
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn

def clear():
    subprocess.run("cls" if os.name == "nt" else "clear", shell=True)

# Initialize console matching terminal profiles
console = Console(highlight=False, theme=None)
clear()

# Load topics from configuration file
try:
    with open("topics.json", "r") as f:
        topics_data = json.load(f)
except FileNotFoundError:
    # Fallback mock data structure for testing safety
    topics_data = {
        "Maths": {"Calculus": {"rating": 2, "last_revised": None, "plan": {"pomodoro_1": [{"text": "Review flashcards", "url": "https://app.gizmo.ai/decks/63307975"}], "pomodoro_2": [{"text": "Solve 5 past paper equations"}]}}}
    }

def make_link(url, text):
    """Generates clean Rich-compatible terminal hyperlinks."""
    return f"[link={url}][#FF6B6B][u]{text}[/u][/#FF6B6B][/link]"

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
            
    plan_str = "\n".join(formatted_steps) if formatted_steps else "• No tasks listed."
    return Text.from_markup(plan_str)

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
    """Replaces raw stdout updates with a tracking progress bar."""
    total_seconds = duration_minutes * 60
    
    with Progress(
        SpinnerColumn(spinner_name="dots", style=color_code),
        TextColumn(f"[white]{label}[/white]"),
        BarColumn(bar_width=30, style="#2D2D2D", complete_style=color_code, finished_style="#2D2D2D"),
        TextColumn("[#888888]•[/#888888]"),
        TimeRemainingColumn(),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task("countdown", total=total_seconds)
        try:
            while not progress.finished:
                time.sleep(1)
                progress.update(task, advance=1)
            console.print(f"[bold #22C55E]🔔 {label} complete![/bold #22C55E]\n")
        except KeyboardInterrupt:
            console.print(f"\n[bold #EF4444]⏩ Skipped {label.lower()} interval.[/bold #EF4444]\n")

def run_pomodoro_engine(selected_tasks, week_label, current_day):
    total_cycles = 4 if len(selected_tasks) > 1 else 2
    
    for current_cycle in range(1, total_cycles + 1):
        task_index = 0 if current_cycle <= 2 or len(selected_tasks) == 1 else 1
        if task_index >= len(selected_tasks):
            task_index = 0
            
        score, sub, top = selected_tasks[task_index]
        type_label = "REVIEW SESSION" if topics_data[sub][top]["last_revised"] else "NEW TOPIC"
        
        phase = "pomodoro_1" if (current_cycle % 2 != 0) else "pomodoro_2"
        phase_title = "POMODORO 1: Video & Flashcards" if phase == "pomodoro_1" else "POMODORO 2: Practice Questions"
        
        clear()
        
        header_text = Text.from_markup(f"[bold white]STUDY SCHEDULE[/bold white] [#666666]❯[/#666666] [#888888]{week_label} • {current_day.upper()}[/#888888]")
        console.print(Panel(header_text, border_style="#2D2D2D", padding=(0, 2)))
        console.print()

        content_text = Text()
        content_text.append(f"Current Topic: ", style="bold white")
        content_text.append(f"{sub} ─ {top}\n", style="bold #FF6B6B")
        content_text.append(f"Session Type: ", style="white")
        content_text.append(f"{type_label}\n\n", style="#888888")
        content_text.append(f"⚡ {phase_title}\n", style="bold white")
        content_text.append(get_plan(sub, top, phase))
        content_text.append("\n", style="white")
        
        console.print(Panel(
            content_text, 
            border_style="#2D2D2D", 
            padding=(1, 2),
            title=f"[bold #FF6B6B]🍅 CYCLE {current_cycle} OF {total_cycles} ACTIVE [/bold #FF6B6B]",
            subtitle="[#666666]Press Ctrl+C to skip timer[/#666666]"
        ))
        console.print()
        
        run_countdown_clock(duration_minutes=25, label="Focus Window", color_code="#FF6B6B")
        sys.stdout.write("\a")
        sys.stdout.flush()
        
        if current_cycle < total_cycles:
            console.print(Panel(
                "[bold #EAB308]☕ Break Interval! Step away and take a breather.[/bold #EAB308]", 
                border_style="#2D2D2D", 
                padding=(1, 2)
            ))
            console.print()
            run_countdown_clock(duration_minutes=5, label="Rest Interval", color_code="#EAB308")
            sys.stdout.write("\a")
            sys.stdout.flush()
            
            console.print("[bold #666666]❯[/bold #666666] Press [bold white][Enter][/bold white] to continue...")
            input()
            clear()
        else:
            console.print()
            console.print("[bold #666666]❯[/bold #666666] Press [bold white][Enter][/bold white] to finish session...")
            input()
            clear()

    console.print(Panel("[bold #22C55E]🎉 Study session completed! Progress saved successfully.[/bold #22C55E]", border_style="#2D2D2D", padding=(1, 2)))

def save_completion(subject, topic):
    console.print()
    console.print(f"[bold white]Saving progress for:[/bold white] [bold #FF6B6B]{topic}[/bold #FF6B6B]")
    
    try:
        shutil.copy("topics.json", "topics_backup.json")
    except Exception as e:
        console.print(f"[bold #EAB308]⚠️ Warning: Could not create backup file ({e})[/bold #EAB308]")
        
    topics_data[subject][topic]["last_revised"] = date.today().strftime("%Y-%m-%d")
    current_rating = topics_data[subject][topic].get("rating", 1)
    
    console.print(f"[bold white]Confidence Level:[/bold white] [bold #EAB308]{'★' * current_rating}[/bold #EAB308]")
    
    while True:
        console.print("[bold #FF6B6B]>[/bold #FF6B6B] [white]Rate your confidence (1-5, or [Enter] to keep current)[/white] [#666666]❯[/#666666] ", end="")
        new_rating_input = input().strip()
        if new_rating_input == "":
            break 
        if new_rating_input.isdigit() and 1 <= int(new_rating_input) <= 5:
            topics_data[subject][topic]["rating"] = int(new_rating_input)
            break
        console.print("[bold #EF4444]❌ Invalid input. Please enter a number between 1 and 5.[/bold #EF4444]")

    with open("topics.json", "w") as f:
        json.dump(topics_data, f, indent=2)
    console.print(f"[bold #22C55E]✓ Progress updated successfully for '{topic}'![/bold #22C55E]\n")

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
    
    header_text = Text.from_markup(f"[bold white]STUDY SESSION MANAGER[/bold white] [#666666]❯[/#666666] [#888888]{week_label} • {current_day.upper()}[/#888888]")
    console.print(Panel(header_text, border_style="#2D2D2D", padding=(0, 2)))
    console.print()

    selected_tasks = []

    if today_subject in topics_data:
        new_pool = []
        for topic_name, meta in topics_data[today_subject].items():
            if meta["last_revised"] is None:
                new_pool.append((today_subject, topic_name, meta))
        best_new = get_best_topic(new_pool)
        if best_new:
            selected_tasks.append(best_new)
    
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
            all_new_pool = []
            for subject, sub_dict in topics_data.items():
                for topic_name, meta in sub_dict.items():
                    if meta["last_revised"] is None:
                        all_new_pool.append((subject, topic_name, meta))
            best_fallback = get_best_topic(all_new_pool)
            if best_fallback:
                selected_tasks.append(best_fallback)

    if not selected_tasks:
        console.print(Panel("[bold #EF4444]❌ No topics found for today's schedule.[/bold #EF4444]", border_style="#2D2D2D"))
        return

    console.print(f"[bold white]Today's Subject:[/bold white] [bold #FF6B6B]{today_subject}[/bold #FF6B6B]")
    console.print()

    table = Table(box=None, show_header=True, header_style="bold #888888")
    table.add_column("Idx", width=4, justify="left")
    table.add_column("Subject & Topic", width=45)
    table.add_column("Session Type", justify="right", style="#888888")
    
    for idx, (score, sub, top) in enumerate(selected_tasks, 1):
        type_label = "REVIEW SESSION" if topics_data[sub][top]["last_revised"] else "NEW TOPIC"
        table.add_row(f"[#FF6B6B]0{idx}[/#FF6B6B]", f"[bold white]{sub}[/bold white] ─ {top}", type_label)
        
    console.print(Panel(table, border_style="#2D2D2D", padding=(1, 2)))
    console.print()

    run_pomodoro_engine(selected_tasks, week_label, current_day)
    
    for score, sub, top in selected_tasks:
        save_completion(sub, top)

if __name__ == "__main__":
    generate_schedule()
    input()
    sys.exit()