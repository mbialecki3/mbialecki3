import json
import os
import urllib.request
from datetime import datetime

USERNAME = os.environ.get("GITHUB_USERNAME", "mbialecki3")
TOKEN = os.environ["GITHUB_TOKEN"]

query = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        weeks {
          contributionDays {
            contributionCount
            contributionLevel
            date
            weekday
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
        "User-Agent": "github-profile-heatmap"
    }
)

with urllib.request.urlopen(request) as response:
    data = json.load(response)

weeks = (
    data["data"]["user"]
    ["contributionsCollection"]
    ["contributionCalendar"]
    ["weeks"]
)

CELL = 11
GAP = 3
STEP = CELL + GAP

LEFT = 34
TOP = 28

width = LEFT + len(weeks) * STEP + 15
height = TOP + 7 * STEP + 20

colors = {
    "NONE": "#1a1b26",
    "FIRST_QUARTILE": "#283457",
    "SECOND_QUARTILE": "#3d59a1",
    "THIRD_QUARTILE": "#7aa2f7",
    "FOURTH_QUARTILE": "#7dcfff",
}

svg = [
    f'<svg xmlns="http://www.w3.org/2000/svg" '
    f'width="{width}" height="{height}" '
    f'viewBox="0 0 {width} {height}">',
    """
<style>
text {
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco,
                 Consolas, "Liberation Mono", monospace;
    font-size: 10px;
    fill: #787c99;
}
</style>
"""
]

last_month = None

for week_index, week in enumerate(weeks):
    x = LEFT + week_index * STEP

    for day in week["contributionDays"]:
        date = datetime.strptime(day["date"], "%Y-%m-%d")

        if date.day <= 7 and date.month != last_month:
            svg.append(
                f'<text x="{x}" y="11">'
                f'{date.strftime("%b")}'
                f'</text>'
            )
            last_month = date.month

        y = TOP + day["weekday"] * STEP
        color = colors[day["contributionLevel"]]

        svg.append(
            f'<rect '
            f'x="{x}" '
            f'y="{y}" '
            f'width="{CELL}" '
            f'height="{CELL}" '
            f'rx="2" '
            f'fill="{color}">'
            f'<title>{day["date"]}: '
            f'{day["contributionCount"]} contributions</title>'
            f'</rect>'
        )

svg.append("</svg>")

os.makedirs("assets", exist_ok=True)

with open("assets/contributions.svg", "w", encoding="utf-8") as f:
    f.write("\n".join(svg))

print("Generated assets/contributions.svg")
