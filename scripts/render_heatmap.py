import json
import os
import urllib.request
from collections import defaultdict
from datetime import datetime

USERNAME = os.environ.get("GITHUB_USERNAME", "mbialecki3")
TOKEN = os.environ["GITHUB_TOKEN"]

query = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            contributionCount
            date
          }
        }
      }
    }
  }
}
"""

payload = json.dumps({
    "query": query,
    "variables": {"login": USERNAME}
}).encode()

request = urllib.request.Request(
    "https://api.github.com/graphql",
    data=payload,
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "github-profile-activity"
    }
)

with urllib.request.urlopen(request) as response:
    data = json.load(response)

calendar = (
    data["data"]["user"]
    ["contributionsCollection"]
    ["contributionCalendar"]
)

weeks = calendar["weeks"]
total_contributions = calendar["totalContributions"]

# Flatten days
days = []

for week in weeks:
    for day in week["contributionDays"]:
        date = datetime.strptime(day["date"], "%Y-%m-%d")

        days.append({
            "date": date,
            "count": day["contributionCount"]
        })

days.sort(key=lambda d: d["date"])

# -------------------------
# Monthly contribution data
# -------------------------

monthly = defaultdict(int)
monthly_active_days = defaultdict(int)

for day in days:
    key = day["date"].strftime("%Y-%m")

    monthly[key] += day["count"]

    if day["count"] > 0:
        monthly_active_days[key] += 1

# Keep the most recent 12 months
month_keys = sorted(monthly.keys())[-12:]

# -------------------------
# Other metrics
# -------------------------

active_days = sum(1 for d in days if d["count"] > 0)

# Busiest day
busiest_day = max(days, key=lambda d: d["count"])

# Current streak
current_streak = 0

for day in reversed(days):
    if day["count"] > 0:
        current_streak += 1
    else:
        break

# Longest streak
longest_streak = 0
running_streak = 0

for day in days:
    if day["count"] > 0:
        running_streak += 1
        longest_streak = max(longest_streak, running_streak)
    else:
        running_streak = 0

# -------------------------
# SVG dimensions
# -------------------------

WIDTH = 900
HEIGHT = 325

LEFT = 45
BAR_START = 285
BAR_WIDTH = 535
BAR_HEIGHT = 10
ROW_GAP = 20

max_contributions = max(
    (monthly[m] for m in month_keys),
    default=1
)

# -------------------------
# Colors
# -------------------------

BACKGROUND = "#0f1117"
PANEL = "#0f1117"
BORDER = "#2a2f3a"
TAB = "#1a1d26"

TEXT = "#c0caf5"
MUTED = "#787c99"
PROMPT = "#7aa2f7"

BAR_BG = "#1a1b26"
BAR = "#7aa2f7"
BAR_END = "#7dcfff"

# -------------------------
# SVG
# -------------------------

svg = [
    f'''
<svg
    xmlns="http://www.w3.org/2000/svg"
    width="{WIDTH}"
    height="{HEIGHT}"
    viewBox="0 0 {WIDTH} {HEIGHT}"
>
<defs>

<style>
    .mono {{
        font-family:
            ui-monospace,
            SFMono-Regular,
            Menlo,
            Monaco,
            Consolas,
            "Liberation Mono",
            monospace;
    }}

    .label {{
        font-size: 13px;
        fill: {TEXT};
    }}

    .muted {{
        font-size: 12px;
        fill: {MUTED};
    }}

    .stat {{
        font-size: 14px;
        fill: {TEXT};
    }}

    .value {{
        font-size: 14px;
        fill: {PROMPT};
    }}

    .title {{
        font-size: 13px;
        fill: {TEXT};
    }}
</style>

<linearGradient id="activityGradient" x1="0%" y1="0%" x2="100%" y2="0%">
    <stop offset="0%" stop-color="{BAR}"/>
    <stop offset="100%" stop-color="{BAR_END}"/>
</linearGradient>

</defs>
'''
]

# Main panel
svg.append(
    f'''
<rect
    x="1"
    y="1"
    width="{WIDTH - 2}"
    height="{HEIGHT - 2}"
    rx="10"
    fill="{PANEL}"
    stroke="{BORDER}"
    stroke-width="2"
/>
'''
)

# Kitty-style tab
svg.append(
    f'''
<rect
    x="18"
    y="10"
    width="210"
    height="28"
    rx="6"
    fill="{TAB}"
/>

<text
    x="31"
    y="29"
    class="mono title"
>
    activity / last 12 months
</text>

<line
    x1="1"
    y1="47"
    x2="{WIDTH - 1}"
    y2="47"
    stroke="#24283b"
/>
'''
)

# -------------------------
# Month bars
# -------------------------

start_y = 70

for index, month_key in enumerate(month_keys):
    date = datetime.strptime(month_key, "%Y-%m")
    label = date.strftime("%b")

    contributions = monthly[month_key]

    ratio = (
        contributions / max_contributions
        if max_contributions > 0
        else 0
    )

    width = max(3, BAR_WIDTH * ratio)

    y = start_y + index * ROW_GAP

    svg.append(
        f'''
<text
    x="{LEFT}"
    y="{y + 10}"
    class="mono label"
>
    {label}
</text>

<rect
    x="{BAR_START}"
    y="{y}"
    width="{BAR_WIDTH}"
    height="{BAR_HEIGHT}"
    rx="5"
    fill="{BAR_BG}"
/>

<rect
    x="{BAR_START}"
    y="{y}"
    width="{width:.1f}"
    height="{BAR_HEIGHT}"
    rx="5"
    fill="url(#activityGradient)"
/>

<text
    x="{BAR_START - 18}"
    y="{y + 10}"
    text-anchor="end"
    class="mono muted"
>
    {contributions}
</text>
'''
    )

# -------------------------
# Stats
# -------------------------

stats_y = 285

svg.append(
    f'''
<line
    x1="40"
    y1="267"
    x2="860"
    y2="267"
    stroke="#24283b"
/>

<text
    x="45"
    y="{stats_y}"
    class="mono muted"
>
    contributions
</text>

<text
    x="45"
    y="{stats_y + 20}"
    class="mono value"
>
    {total_contributions}
</text>


<text
    x="245"
    y="{stats_y}"
    class="mono muted"
>
    active days
</text>

<text
    x="245"
    y="{stats_y + 20}"
    class="mono value"
>
    {active_days}
</text>


<text
    x="430"
    y="{stats_y}"
    class="mono muted"
>
    current streak
</text>

<text
    x="430"
    y="{stats_y + 20}"
    class="mono value"
>
    {current_streak} days
</text>


<text
    x="630"
    y="{stats_y}"
    class="mono muted"
>
    longest streak
</text>

<text
    x="630"
    y="{stats_y + 20}"
    class="mono value"
>
    {longest_streak} days
</text>
'''
)

svg.append("</svg>")

os.makedirs("assets", exist_ok=True)

with open("assets/activity.svg", "w", encoding="utf-8") as f:
    f.write("\n".join(svg))

print("Generated assets/activity.svg")
