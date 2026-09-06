import json, os, random, sys, shutil, time, subprocess, threading, pygame, msvcrt, pyperclip, urllib.parse
from datetime import date, datetime, timedelta

# Import terminal rendering components
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

# Define global accent color and audio states
accent_colour = "#FF6B6B"
muted = False
current_volume = 0.2

# Realistic averaged percentage thresholds for subject grade boundaries
SUBJECT_BOUNDARIES = {
    "Biology": {"9": 75, "8": 65, "7": 55, "6": 45, "5": 35, "4": 25},
    "Chemistry": {"9": 75, "8": 65, "7": 55, "6": 45, "5": 35, "4": 25},
    "Physics": {"9": 75, "8": 65, "7": 55, "6": 45, "5": 35, "4": 25},
    "Computer Science": {"9": 80, "8": 70, "7": 60, "6": 50, "5": 40, "4": 30},
}

def clear():
    subprocess.run("cls" if os.name == "nt" else "clear", shell=True)

# Initialize console matching terminal profiles
console = Console(highlight=False, theme=None)
base_dir = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(base_dir, "topics.json")
backup_path = os.path.join(base_dir, "topics_backup.json")
clear()

# Load topics from configuration file
try:
    with open(json_path, "r") as f:
        topics_data = json.load(f)
except FileNotFoundError:
    topics_data = {
            "Placeholder": {"placeholder": {"rating": 1, "last_revised": None, "plan": "No tasks listed."}}
        }

def print_banner(target_date=date(2026, 11, 2)):
    """Always displays the GCSEs countdown banner at the top."""
    days_left = (target_date - date.today()).days
    banner_grid = Table.grid(expand=True)
    banner_grid.add_column(justify="center")
    banner_grid.add_row(f"[bold {accent_colour}]⏳ {days_left} days[/bold {accent_colour}] [white]until Mocks[/white]")
    console.print(Panel(banner_grid, border_style="#2D2D2D", padding=(0, 2), expand=True))
    console.print()

def play_random_folder_background(folder_path):
    """Continues playing background music if already active; otherwise, starts the random playlist loop."""
    def background_loop():
        try:
            pygame.mixer.init()
            if pygame.mixer.music.get_busy():
                return
                
            songs = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.lower().endswith('.mp3')]
            if not songs:
                return
            
            random.shuffle(songs)
            while True:
                for song in songs:
                    pygame.mixer.music.load(song)
                    pygame.mixer.music.play()
                    pygame.mixer.music.set_volume(0.0 if muted else current_volume)
                    while pygame.mixer.music.get_busy():
                        time.sleep(1)
                random.shuffle(songs)
        except Exception as e:
            if "mixer not initialized" not in str(e):
                print(f"Audio playback error: {e}")

    audio_thread = threading.Thread(target=background_loop, daemon=True)
    audio_thread.start()

def play_alarm():
    """Plays the alarm sound effect concurrently using a mixer channel without stopping background music."""
    try:
        alarm_path = r"C:\Projects\revision-planner-main\alarm.mp3"
        if os.path.exists(alarm_path):
            alarm_sound = pygame.mixer.Sound(alarm_path)
            alarm_sound.set_volume(1.0)
            channel = alarm_sound.play()
            while channel.get_busy():
                time.sleep(0.5)
    except Exception as e:
        print(f"Alarm playback error: {e}")

def make_link(url, text):
    """Generates clean Rich-compatible terminal hyperlinks."""
    return f"[link={url}][{accent_colour}][u]{text}[/u][/{accent_colour}][/link]"

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

def get_plan(subject, topic, phase=None, prompt_text=None):
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
        
        if phase == "pomodoro_1" and subject in ["Biology", "Chemistry", "Physics"] and "ChatGPT" in text:
            if prompt_text:
                encoded_prompt = urllib.parse.quote(prompt_text)
                chatgpt_url = f"https://chatgpt.com/?model=gpt-4o&temporary-chat=true&prompt={encoded_prompt}"
                link_text = f"[link={chatgpt_url}][{accent_colour}][u]{text}[/u][/{accent_colour}][/link]"
                formatted_steps.append(f"• {link_text}")
                continue
                
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
    global muted, current_volume
    total_seconds = duration_minutes * 60
    elapsed = 0
    paused = False
    
    def format_time(secs):
        rem = max(0, total_seconds - secs)
        m, s = divmod(rem, 60)
        return f"{int(m):02d}:{int(s):02d}"

    with Progress(
        SpinnerColumn(spinner_name="dots", style=color_code),
        TextColumn(f"[white]{label}[/white]"),
        BarColumn(bar_width=30, style="#2D2D2D", complete_style=color_code, finished_style="#2D2D2D"),
        TextColumn("[#888888]•[/#888888]"),
        TextColumn("[bold cyan]{task.fields[time_left]}[/bold cyan]"),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task("countdown", total=total_seconds, time_left=format_time(0))
        try:
            while elapsed < total_seconds:
                if msvcrt.kbhit():
                    key = msvcrt.getch()
                    if key in (b'\x00', b'\xe0'):
                        arrow_key = msvcrt.getch()
                        if arrow_key == b'H': 
                            current_volume = min(1.0, current_volume + 0.1)
                            muted = False
                            pygame.mixer.music.set_volume(current_volume)
                        elif arrow_key == b'P': 
                            current_volume = max(0.0, current_volume - 0.1)
                            pygame.mixer.music.set_volume(current_volume)
                    else:
                        try:
                            char = key.decode('utf-8', errors='ignore').lower()
                            if char == 'p':
                                paused = not paused
                            elif char == 'm':
                                muted = not muted
                                pygame.mixer.music.set_volume(0.0 if muted else current_volume)
                        except:
                            pass
                
                if not paused:
                    time.sleep(1)
                    elapsed += 1
                    progress.update(task, advance=1, time_left=format_time(elapsed))
                else:
                    time.sleep(0.1)
                    
            console.print(f"[bold #22C55E]🔔 {label} complete![/bold #22C55E]\n")
        except KeyboardInterrupt:
            console.print(f"\n[bold #EF4444]⏩ Skipped {label.lower()} interval.[/bold #EF4444]\n")

def display_streak_summary(selected_tasks):
    raw_history = topics_data.get("history", [])
    if raw_history is None:
        raw_history = []
        
    history = set(str(d).strip() for d in raw_history if d)
    today = date.today()
    history.add(today.strftime("%Y-%m-%d"))
    
    current_streak = 0
    check_date = today
    while check_date.strftime("%Y-%m-%d") in history:
        current_streak += 1
        check_date -= timedelta(days=1)
        
    valid_dates = []
    for d_str in history:
        try:
            valid_dates.append(datetime.strptime(d_str, "%Y-%m-%d").date())
        except ValueError:
            pass
            
    sorted_dates = sorted(list(set(valid_dates)))
    longest_streak = 0
    temp_streak = 0
    prev_date = None
    
    for d in sorted_dates:
        if prev_date is None or (d - prev_date).days == 1:
            temp_streak += 1
        elif (d - prev_date).days > 1:
            temp_streak = 1
        longest_streak = max(longest_streak, temp_streak)
        prev_date = d

    num_weeks = 14
    total_grid_days = num_weeks * 7
    
    current_sunday = today + timedelta(days=(6 - today.weekday()))
    start_grid_date = current_sunday - timedelta(days=total_grid_days - 1)
    
    grid = [["[#333333]■[/]" for _ in range(num_weeks)] for _ in range(7)]
    curr = start_grid_date
    
    for day_count in range(total_grid_days):
        w_idx = day_count // 7
        d_idx = curr.weekday()
        date_str = curr.strftime("%Y-%m-%d")
        
        if curr <= today and date_str in history:
            grid[d_idx][w_idx] = "[bold #22C55E]■[/bold #22C55E]"
        else:
            grid[d_idx][w_idx] = "[#333333]■[/]"
            
        curr += timedelta(days=1)

    days_labels = ["Mon", "", "Wed", "", "Fri", "", "Sun"]
    heatmap_lines = []
    for r in range(7):
        label = f"{days_labels[r]:<3}"
        row_str = f"[#888888] {label} [/#888888] " + "  ".join(grid[r])
        heatmap_lines.append(row_str)
    
    heatmap_str = "\n".join(heatmap_lines)
    cards_studied = len(selected_tasks)
    
    current_label = f"{current_streak} {'day' if current_streak == 1 else 'days'}"
    longest_label = f"{longest_streak} {'day' if longest_streak == 1 else 'days'}"
    
    summary_markup = (
        f"[bold white]Studied {cards_studied} topic(s) today.[/bold white]\n\n"
        f"{heatmap_str}\n\n"
        f"[white]Current Streak:[/white] [bold #22C55E]{current_label}[/bold #22C55E]    "
        f"[white]Longest Streak:[/white] [bold {accent_colour}]{longest_label}[/bold {accent_colour}]"
    )
    
    console.print(Panel(
        Text.from_markup(summary_markup),
        border_style="#2D2D2D",
        padding=(1, 2),
        title=f"[bold {accent_colour}]📊 {today.strftime('%Y')} ACTIVITY HEATMAP[/bold {accent_colour}]"
    ))

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
        
        prompt_text = None
        if phase == "pomodoro_1" and sub in ["Biology", "Chemistry", "Physics"]:
            prompt_text = (
                f"I am studying GCSE {sub} for the AQA Combined Science specification.\n"
                f"I just watched a lesson on {top}.\n"
                "Act as an expert GCSE examiner. Generate a strict active-recall summary quiz based ONLY on the core facts and definitions required for this specific topic.\n"
                "Follow these formatting rules strictly:\n\n"
                "Provide short-answer questions covering the important subtopics (max 15).\n"
                "The questions must target the exact technical keywords required to score full marks in an exam.\n"
                "Do not use vague or open-ended questions.\n"
                "Do not include content that is not required for AQA Combined Science.\n\n"
                "After the quiz, I will answer the questions. When I provide my answers, act as an expert GCSE examiner and:\n"
                "Mark each answer strictly according to AQA-style marking points.\n"
                "Give me an overall score.\n"
                "Identify my weakest subtopics based on my mistakes.\n"
                "Give me a short list of the subtopics I most need to revise.\n"
                "Do not recommend topics I answered correctly unless my wording was insufficient for full marks.\n"
                "Focus on precise exam terminology rather than general understanding.\n"
                "Then give a very summarised study guide explaining my weak subtopics simply"
            )
            pyperclip.copy(prompt_text)

        clear()
        print_banner()
        
        header_text = Text.from_markup(f"[bold white]STUDY SCHEDULE[/bold white] [#666666]❯[/#666666] [#888888]{week_label} • {current_day.upper()}[/#888888]")
        console.print(Panel(header_text, border_style="#2D2D2D", padding=(0, 2)))
        console.print()

        content_text = Text()
        content_text.append(f"Subject: ", style="bold white")
        content_text.append(f"{sub}\n", style=f"bold {accent_colour}")
        content_text.append(f"Topic: ", style="bold white")
        content_text.append(f"{top}\n", style="white")
        content_text.append(f"Session Type: ", style="white")
        content_text.append(f"{type_label}\n\n", style="#888888")
        content_text.append(f"⚡ {phase_title}\n", style="bold white")
        
        content_text.append(get_plan(sub, top, phase, prompt_text))
        content_text.append("\n", style="white")

        console.print(Panel(
            content_text, 
            border_style="#2D2D2D", 
            padding=(1, 2),
            title=f"[bold {accent_colour}]🍅 CYCLE {current_cycle} OF {total_cycles} ACTIVE [/bold {accent_colour}]",
            subtitle="[#666666]Press 'p' pause • 'm' mute • '↑/↓' volume • Ctrl+C skip[/#666666]"
        ))
        console.print()
        print()
        
        run_countdown_clock(duration_minutes=30, label="Focus Window", color_code=accent_colour)
        sys.stdout.write("\a")
        sys.stdout.flush()
        play_alarm()
        
        if current_cycle < total_cycles:
            console.print()
            console.print("[bold #666666]❯[/bold #666666] Press [bold white][Enter][/bold white] to start break...")
            input()
            
            console.print(Panel(
                "[bold #EAB308]☕ Break Interval! Step away and take a breather.[/bold #EAB308]", 
                border_style="#2D2D2D", 
                padding=(1, 2)
            ))
            console.print()
            run_countdown_clock(duration_minutes=5, label="Rest Interval", color_code="#EAB308")
            sys.stdout.write("\a")
            sys.stdout.flush()
            play_alarm()
            print()
            
            console.print("[bold #666666]❯[/bold #666666] Press [bold white][Enter][/bold white] to continue...")
            input()
            clear()
        else:
            console.print()
            console.print("[bold #666666]❯[/bold #666666] Press [bold white][Enter][/bold white] to finish session...")
            input()
            clear()

def save_completion(subject, topic):
    clear()
    print_banner()
    console.print(Panel("[bold #22C55E]🎉 Study session completed! Progress saved successfully.[/bold #22C55E]", border_style="#2D2D2D", padding=(1, 2)))
    console.print()
    
    console.print(f"[bold white]Evaluating past paper performance for:[/bold white] [bold {accent_colour}]{subject} ─ {topic}[/bold {accent_colour}]")
    
    try:
        shutil.copy(json_path, backup_path)
    except Exception as e:
        console.print(f"[bold #EAB308]⚠️ Warning: Could not create backup file ({e})[/bold #EAB308]")
        
    today_str = date.today().strftime("%Y-%m-%d")
    topics_data[subject][topic]["last_revised"] = today_str
    
    if "history" not in topics_data or not isinstance(topics_data["history"], list):
        topics_data["history"] = []
    if today_str not in topics_data["history"]:
        topics_data["history"].append(today_str)
        
    console.print(f"\n[bold {accent_colour}]📋 PAST PAPER SCORE EVALUATION[/bold {accent_colour}]")
    console.print("[#888888]Enter your score from the practice questions to map against realistic grade averages.[/#888888]\n")

    while True:
        try:
            console.print(f"[bold white]Marks achieved[/bold white] [#666666]❯[/#666666] ", end="")
            marks_achieved = float(input().strip())
            console.print(f"[bold white]Total possible marks[/bold white] [#666666]❯[/#666666] ", end="")
            total_marks = float(input().strip())
            if total_marks > 0 and 0 <= marks_achieved <= total_marks:
                break
        except ValueError:
            pass
        console.print("[bold #EF4444]❌ Invalid input. Please enter valid numeric marks.[/bold #EF4444]")

    percentage = (marks_achieved / total_marks) * 100
    
    boundaries = SUBJECT_BOUNDARIES.get(subject, {"9": 75, "8": 65, "7": 55, "6": 45, "5": 35, "4": 25})
    
    assigned_grade = "U"
    for grade in ["9", "8", "7", "6", "5", "4"]:
        if percentage >= boundaries[grade]:
            assigned_grade = grade
            break

    grade_to_rating = {"9": 5, "8": 5, "7": 4, "6": 3, "5": 2, "4": 1, "U": 1}
    automated_rating = grade_to_rating.get(assigned_grade, 1)

    rating_colors = {1: "#EF4444", 2: "#F97316", 3: "#EAB308", 4: "#3B82F6", 5: "#22C55E"}
    current_color = rating_colors.get(automated_rating, "white")

    topics_data[subject][topic]["rating"] = automated_rating
    
    console.print()
    result_text = Text()
    result_text.append(f"Evaluated Subject: {subject} ─ {topic}\n\n", style="bold white")
    result_text.append(f"Percentage Score: ", style="white")
    result_text.append(f"{percentage:.1f}%\n", style=f"bold {accent_colour}")
    result_text.append(f"Estimated GCSE Grade: ", style="white")
    result_text.append(f"Grade {assigned_grade}\n", style=f"bold {current_color}")
    result_text.append(f"Calculated Confidence Index: ", style="white")
    result_text.append(f"{'★' * automated_rating}", style=f"bold {current_color}")

    console.print(Panel(result_text, border_style="#2D2D2D", padding=(1, 2), title=f"[bold {accent_colour}]📋 EVALUATION RESULTS[/bold {accent_colour}]"))
    console.print()

    with open(json_path, "w") as f:
        json.dump(topics_data, f, indent=2)
        
    console.print(f"[bold #22C55E]✓ Priority weights updated using grade boundary averages.[/bold #22C55E]\n")
    console.print("[bold #666666]❯[/bold #666666] Press [bold white][Enter][/bold white] to continue...")
    input()
    
    clear()
    print_banner()

def generate_schedule():
    schedule_week_1 = {
        "Monday": "Biology", "Tuesday": "Chemistry", "Wednesday": "Physics",
        "Thursday": "Biology", "Friday": "Chemistry", "Saturday": "Physics", "Sunday": "Biology"
    }
    schedule_week_2 = {
        "Monday": "Chemistry", "Tuesday": "Physics", "Wednesday": "Biology",
        "Thursday": "Chemistry", "Friday": "Physics", "Saturday": "Biology", "Sunday": "Chemistry"
    }
    
    current_date = date.today()
    current_day = current_date.strftime("%A")
    is_weekend = current_day in ["Saturday", "Sunday"]
    
    week_number = current_date.isocalendar()[1]
    is_week_1 = (week_number % 2 == 0)
    
    today_subject = schedule_week_1.get(current_day) if is_week_1 else schedule_week_2.get(current_day)
    week_label = "WEEK 1" if is_week_1 else "WEEK 2"
    
    clear()
    print_banner()

    header_text = Text.from_markup(f"[bold white]STUDY SCHEDULE[/bold white] [#666666]❯[/#666666] [#888888]{week_label} • {current_day.upper()}[/#888888]")
    console.print(Panel(header_text, border_style="#2D2D2D", padding=(0, 2), expand=True))
    console.print()

    selected_tasks = []

    if today_subject in topics_data and isinstance(topics_data[today_subject], dict):
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
            if subject == "history" or not isinstance(sub_dict, dict):
                continue
            for topic_name, meta in sub_dict.items():
                if meta["last_revised"] is not None:
                    global_old_pool.append((subject, topic_name, meta))
        best_old = get_best_topic(global_old_pool)
        if best_old: 
            selected_tasks.append(best_old)
        else:
            all_new_pool = []
            for subject, sub_dict in topics_data.items():
                if subject == "history" or not isinstance(sub_dict, dict):
                    continue
                for topic_name, meta in sub_dict.items():
                    if meta["last_revised"] is None:
                        all_new_pool.append((subject, topic_name, meta))
            best_fallback = get_best_topic(all_new_pool)
            if best_fallback:
                selected_tasks.append(best_fallback)

    if not selected_tasks:
        console.print(Panel("[bold #EF4444]❌ No topics found for today's schedule.[/bold #EF4444]", border_style="#2D2D2D", expand=True))
        return

    content_lines = []
    for idx, (score, sub, top) in enumerate(selected_tasks, 1):
        if idx > 1:
            content_lines.append("")
        type_label = "REVIEW SESSION" if topics_data[sub][top]["last_revised"] else "NEW TOPIC"
        content_lines.append(f"[bold white]Subject:[/bold white] [bold {accent_colour}]{sub}[/bold {accent_colour}]")
        content_lines.append(f"[bold white]Topic:[/bold white] {top}")
        content_lines.append(f"[bold white]Session Type:[/bold white] [#888888]{type_label}[/#888888]")
        
    panel_content = "\n".join(content_lines)

    console.print(Panel(
        panel_content, 
        border_style="#2D2D2D", 
        padding=(1, 2), 
        expand=True,
        title=f"[bold {accent_colour}]🎯 TODAY'S STUDY PLAN[/bold {accent_colour}]"
    ))
    console.print()

    print()
    console.print("[bold #666666]❯[/bold #666666] Press [bold white][Enter][/bold white] to start study session...")
    input()

    run_pomodoro_engine(selected_tasks, week_label, current_day)
    
    for score, sub, top in selected_tasks:
        save_completion(sub, top)
        
    print()
    display_streak_summary(selected_tasks)

if __name__ == "__main__":
    play_random_folder_background(r"C:\Projects\revision-planner-main\Music")
    generate_schedule()
    print("\n")
    console.print("[bold #666666]❯[/bold #666666] Press [bold white][Enter][/bold white] to exit...")
    input()
    try:
        pygame.mixer.music.stop()
        pygame.mixer.quit()
    except:
        pass
    sys.exit()