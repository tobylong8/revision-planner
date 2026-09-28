import json, os, webbrowser
from datetime import date, datetime

def export_html_dashboard():
    """Generates a polished HTML dashboard matching the terminal UI aesthetic and opens it in Edge."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, "topics.json")
    html_path = os.path.join(base_dir, "dashboard.html")
    accent_colour = "#FF6B6B"

    try:
        with open(json_path, "r") as f:
            topics_data = json.load(f)
    except FileNotFoundError:
        print("topics.json not found.")
        return

    # Filter out non-subject keys like history if present
    subjects = {k: v for k, v in topics_data.items() if k not in ["history", "Placeholder"]}

    # Calculate overall stats
    total_topics = 0
    revised_topics = 0
    total_rating_sum = 0
    rating_counts = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

    for sub, tops in subjects.items():
        for top, meta in tops.items():
            total_topics += 1
            r = meta.get("rating", 0)
            total_rating_sum += r
            rating_counts[r] = rating_counts.get(r, 0) + 1
            if meta.get("last_revised") is not None:
                revised_topics += 1

    completion_pct = (revised_topics / total_topics * 100) if total_topics > 0 else 0
    mastery_pct = (total_rating_sum / (total_topics * 5) * 100) if total_topics > 0 else 0

    # Polished HTML layout matching the terminal theme
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GCSE Revision Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{ background-color: #0b0f19; color: #f8fafc; font-family: system-ui, -apple-system, sans-serif; }}
        .terminal-panel {{ background-color: #0f172a; border: 1px solid #2d2d2d; border-radius: 0.75rem; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2); }}
        .accent-text {{ color: {accent_colour}; }}
    </style>
</head>
<body class="p-6 md:p-10 max-w-6xl mx-auto space-y-6">
    
    <!-- Top Banner -->
    <div class="terminal-panel p-6 text-center">
        <h1 class="text-2xl font-bold tracking-tight text-white">GCSE Analytics Dashboard</h1>
        <p class="text-xs font-mono uppercase tracking-wider text-slate-400 mt-1">Performance & Revision Tracker</p>
    </div>

    <!-- Quick Stats Grid -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div class="terminal-panel p-5">
            <span class="text-xs font-mono text-slate-400 uppercase">Days until Mocks</span>
            <p class="text-3xl font-bold mt-2 text-red-400">{((date(date.today().year if date.today() <= date(date.today().year, 11, 2) else date.today().year + 1, 11, 2)) - date.today()).days}</p>
        </div>
        <div class="terminal-panel p-5">
            <span class="text-xs font-mono text-slate-400 uppercase">GCSE Mastery</span>
            <p class="text-3xl font-bold mt-2 text-emerald-400">{mastery_pct:.1f}%</p>
        </div>
        <div class="terminal-panel p-5">
            <span class="text-xs font-mono text-slate-400 uppercase">Topics Revised</span>
            <p class="text-3xl font-bold mt-2 text-emerald-400">{revised_topics}/{total_topics}</p>
        </div>
        <div class="terminal-panel p-5">
            <span class="text-xs font-mono text-slate-400 uppercase">Mastered Topics</span>
            <p class="text-3xl font-bold mt-2 text-blue-400">{rating_counts.get(5, 0)}/{total_topics}</p>
        </div>
    </div>

    <!-- Subject Breakdowns Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
"""

    # Badge mappings: Grade 9 = blue, Grade 7-8 = green
    rating_badges = {
        5: {"bg": "bg-blue-500/15", "text": "text-blue-400", "border": "border-blue-500/40", "label": "★★★★★ Grade 9"},
        4: {"bg": "bg-emerald-500/10", "text": "text-emerald-400", "border": "border-emerald-500/30", "label": "★★★★☆ Grade 7-8"},
        3: {"bg": "bg-yellow-500/10", "text": "text-yellow-400", "border": "border-yellow-500/30", "label": "★★★☆☆ Grade 6"},
        2: {"bg": "bg-orange-500/10", "text": "text-orange-400", "border": "border-orange-500/30", "label": "★★☆☆☆ Grade 5"},
        1: {"bg": "bg-rose-500/10", "text": "text-rose-400", "border": "border-rose-500/30", "label": "★☆☆☆☆ Review Needed"},
        0: {"bg": "bg-rose-500/10", "text": "text-rose-400", "border": "border-rose-500/30", "label": "☆☆☆☆☆ Review Needed"},
    }

    for sub, tops in subjects.items():
        sub_total_topics = len(tops)
        sub_rating_sum = sum(meta.get("rating", 0) for meta in tops.values())
        sub_mastery_pct = (sub_rating_sum / (sub_total_topics * 5) * 100) if sub_total_topics > 0 else 0

        # Make Maths span both columns to balance out its 20 topics
        span_class = "md:col-span-2" if sub == "Maths" else ""

        html_content += f"""
        <div class="terminal-panel p-6 flex flex-col justify-between {span_class}">
            <div>
                <div class="mb-4 pb-3 border-b border-slate-800">
                    <h3 class="text-lg font-bold accent-text">{sub} - {sub_mastery_pct:.1f}% mastered</h3>
                </div>
                <div class="space-y-3">
"""
        for top, meta in tops.items():
            rating = meta.get("rating", 0)
            raw_revised = meta.get("last_revised")
            
            if not raw_revised:
                revised_text = "Never Revised"
            else:
                try:
                    revised_date = datetime.strptime(raw_revised, "%Y-%m-%d").date()
                    days_ago = (date.today() - revised_date).days
                    if days_ago == 0:
                        time_str = "Today"
                    elif days_ago == 1:
                        time_str = "1 day ago"
                    else:
                        time_str = f"{days_ago} days ago"
                    revised_text = f"Last revised: {time_str}"
                except Exception:
                    revised_text = f"Last revised: {raw_revised}"

            badge = rating_badges.get(rating, rating_badges[0])
            
            html_content += f"""
                    <div class="bg-slate-900/50 p-3.5 rounded-lg border border-slate-800/80 flex justify-between items-center text-sm">
                        <div class="space-y-0.5 pr-2">
                            <span class="font-medium text-slate-200 block">{top}</span>
                            <span class="text-xs text-slate-500 font-mono">{revised_text}</span>
                        </div>
                        <div>
                            <span class="px-2.5 py-1 rounded text-xs font-mono font-semibold border {badge['bg']} {badge['text']} {badge['border']} whitespace-nowrap">
                                {badge['label']}
                            </span>
                        </div>
                    </div>
"""
        html_content += """
                </div>
            </div>
        </div>
"""

    html_content += """
    </div>
</body>
</html>
"""

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    # Open automatically in Edge work profile
    try:
        edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
        os.popen(f'"{edge_path}" --profile-directory="Profile 1" "{html_path}"')
    except Exception:
        webbrowser.open(html_path)

if __name__ == "__main__":
    export_html_dashboard()