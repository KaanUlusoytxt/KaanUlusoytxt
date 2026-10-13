"""Generate light/dark contribution heatmap SVGs for the profile README.

Usage:
    GH_TOKEN=... GH_USER=KaanUlusoytxt python scripts/heatmap.py
    python scripts/heatmap.py --demo   # random data, no token needed
"""
import json
import os
import random
import sys
import urllib.request
from datetime import date, timedelta
from pathlib import Path

USER = os.environ.get("GH_USER", "KaanUlusoytxt")
OUT = Path(__file__).resolve().parent.parent / "assets"

THEMES = {
    "light": {
        "bg": "none", "text": "#57606a", "muted": "#8c959f",
        "levels": ["#ebeef1", "#c6e9d6", "#7fd1a6", "#2fa36b", "#146c43"],
    },
    "dark": {
        "bg": "none", "text": "#9198a1", "muted": "#6e7681",
        "levels": ["#1b2129", "#0f3d2c", "#17694a", "#22a06b", "#4ae09a"],
    },
}

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}"""


def fetch():
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("GH_TOKEN yok. Demo için: python scripts/heatmap.py --demo")
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        payload = json.load(r)
    if "errors" in payload:
        sys.exit(payload["errors"])
    cal = payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    weeks = [[(d["date"], d["contributionCount"]) for d in w["contributionDays"]] for w in cal["weeks"]]
    return weeks, cal["totalContributions"]


def demo():
    end = date.today()
    start = end - timedelta(days=364 + (end.weekday() + 1) % 7)
    weeks, cur, total = [], [], 0
    d = start
    while d <= end:
        c = 0 if random.random() < 0.35 else int(random.expovariate(0.25))
        total += c
        cur.append((d.isoformat(), c))
        if len(cur) == 7:
            weeks.append(cur)
            cur = []
        d += timedelta(days=1)
    if cur:
        weeks.append(cur)
    return weeks, total


def level(c, peaks):
    if c == 0:
        return 0
    for i, p in enumerate(peaks, start=1):
        if c <= p:
            return i
    return 4


def render(weeks, total, theme):
    t = THEMES[theme]
    cell, gap, left, top = 11, 3, 30, 22
    width = left + len(weeks) * (cell + gap) + 4
    height = top + 7 * (cell + gap) + 26
    counts = sorted(c for w in weeks for _, c in w if c)
    q = lambda f: counts[min(len(counts) - 1, int(len(counts) * f))] if counts else 1
    peaks = [q(0.25), q(0.5), q(0.75)]

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
        f'font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif">',
    ]
    last_month = None
    for x, w in enumerate(weeks):
        m = w[0][0][5:7]
        if m != last_month and w[0][0][8:10] <= "07":
            name = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][int(m) - 1]
            out.append(f'<text x="{left + x * (cell + gap)}" y="12" font-size="10" fill="{t["text"]}">{name}</text>')
            last_month = m
    for i, lbl in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        out.append(f'<text x="0" y="{top + i * (cell + gap) + 9}" font-size="9" fill="{t["muted"]}">{lbl}</text>')

    for x, w in enumerate(weeks):
        for d, c in w:
            y = date.fromisoformat(d).isoweekday() % 7
            col = t["levels"][level(c, peaks)]
            out.append(
                f'<rect x="{left + x * (cell + gap)}" y="{top + y * (cell + gap)}" width="{cell}" height="{cell}" '
                f'rx="2.5" fill="{col}"><title>{d}: {c}</title></rect>'
            )

    by = height - 6
    out.append(f'<text x="{left}" y="{by}" font-size="10" fill="{t["text"]}">{total:,} contributions in the last year</text>')
    lx = width - 5 * (cell + gap) - 34
    out.append(f'<text x="{lx - 26}" y="{by}" font-size="9" fill="{t["muted"]}">Less</text>')
    for i, col in enumerate(t["levels"]):
        out.append(f'<rect x="{lx + i * (cell + gap)}" y="{by - 9}" width="{cell - 1}" height="{cell - 1}" rx="2" fill="{col}"/>')
    out.append(f'<text x="{lx + 5 * (cell + gap) + 3}" y="{by}" font-size="9" fill="{t["muted"]}">More</text>')
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    weeks, total = demo() if "--demo" in sys.argv else fetch()
    OUT.mkdir(exist_ok=True)
    for theme in THEMES:
        (OUT / f"heatmap-{theme}.svg").write_text(render(weeks, total, theme), encoding="utf-8")
    print(f"ok: {total} contributions, {len(weeks)} weeks")
