import json, os, subprocess
from datetime import date

with open("topics.json", "r") as f:
    topics = json.load(f)

def make_link(url, text):
    return f"\x1b]8;;{url}\x1b\\{text}\x1b]8;;\x1b\\"

def clear():
    subprocess.run("cls" if os.name == "nt" else "clear", shell=True)

day_of_week = date.today().strftime("%A")

schedule = {
    "Monday": "Maths",
    "Tuesday": "Science",
    "Wednesday": "Computer Science",
    "Thursday": "English",
    "Friday": "Spanish",
    "Saturday": "Geography",
    "Sunday": "Science"
}

subject = schedule[day_of_week]

def get_plan(subject, topic):
    steps = topics[subject][topic]["plan"]
    formatted_steps = []
    
    for item in steps:
        if item["url"]:
            link_text = make_link(item["url"], item["text"])
            formatted_steps.append(f"• {link_text}")
        else:
            formatted_steps.append(f"• {item['text']}")
            
    return "\n".join(formatted_steps)

clear()
print("\033[4mREVISION PLAN:\033[0m")
print(get_plan("Science", "B1 - Cell Biology"))
