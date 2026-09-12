#!/usr/bin/env python3
"""Render assets/stats.svg from the GitHub GraphQL API. No third-party services."""

import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

INK, PANEL, LINE = "#0B0E14", "#0F1520", "#1A2230"
TEXT, MUTED, DIM, ACC = "#E9EEF6", "#8B97AA", "#5C6779", "#5B8DEF"
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"

LOGIN = os.environ.get("GH_LOGIN", "muhammadshurman")
TOKEN = os.environ.get("GH_TOKEN", "")
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "stats.svg")

TOTALS = """
query {
  viewer {
    pullRequests(states: MERGED) { totalCount }
    contributionsCollection { totalCommitContributions restrictedContributionsCount }
  }
}
"""

COLORS = {
    "PHP": "#4F5D95", "Blade": "#f7523f", "JavaScript": "#f1e05a", "TypeScript": "#3178c6",
    "HTML": "#e34c26", "CSS": "#663399", "SCSS": "#c6538c", "Less": "#1d365d",
    "Python": "#3572A5", "Java": "#b07219", "Kotlin": "#A97BFF", "Dart": "#00B4AB",
    "C#": "#178600", "C++": "#f34b7d", "C": "#555555", "Go": "#00ADD8", "Rust": "#dea584",
    "Ruby": "#701516", "Swift": "#F05138", "Shell": "#89e051", "PowerShell": "#012456",
    "Dockerfile": "#384d54", "Makefile": "#427819", "Vue": "#41b883", "Svelte": "#ff3e00",
    "Astro": "#ff5a03", "SQL": "#e38c00", "PLpgSQL": "#336790", "TSQL": "#e38c00",
    "Twig": "#c1d026", "Smarty": "#f0c040", "MDX": "#fcb32c", "Hack": "#878787",
    "Handlebars": "#f7931e", "EJS": "#a91e50", "Batchfile": "#C1F12E", "Procfile": "#3A4454",
}
FALLBACK = "#3A4454"
IGNORED = {"HTML", "CSS", "SCSS", "Less", "Hack", "Batchfile", "Procfile", "Dockerfile", "Makefile",
           "C#", "Kotlin", "ShaderLab", "HLSL", "Java", "Swift"}


def api(url, attempts=4):
    for i in range(attempts):
        req = urllib.request.Request(
            url,
            headers={
                "Authorization": f"bearer {TOKEN}",
                "Accept": "application/vnd.github+json",
                "User-Agent": "profile-stats",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except urllib.error.URLError as e:
            last = e
        time.sleep(2 ** i)
    raise RuntimeError(f"GET {url} failed: {last}")


def gql(query, attempts=4):
    body = json.dumps({"query": query}).encode()
    last = None
    for i in range(attempts):
        req = urllib.request.Request(
            "https://api.github.com/graphql",
            data=body,
            headers={
                "Authorization": f"bearer {TOKEN}",
                "Content-Type": "application/json",
                "User-Agent": "profile-stats",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                payload = json.load(r)
            if "errors" not in payload:
                return payload["data"]["viewer"]
            last = payload["errors"]
        except urllib.error.URLError as e:
            last = e
        time.sleep(2 ** i)
    raise RuntimeError(last)


MOCK = {
    "commits": 0, "stars": 0, "prs": 0, "repos": 0,
    "langs": [("PHP", "#4F5D95", 38.0), ("TypeScript", "#3178c6", 24.0),
              ("Blade", "#f7523f", 16.0), ("JavaScript", "#f1e05a", 12.0),
              ("CSS", "#663399", 6.0), ("Other", FALLBACK, 4.0)],
}

AFFILIATION = os.environ.get("GH_AFFILIATION", "owner,collaborator,organization_member")


def collect():
    if not TOKEN:
        if os.environ.get("GITHUB_ACTIONS"):
            raise SystemExit("GH_TOKEN is empty in CI")
        return MOCK

    repos, page = [], 1
    while page <= 5:
        batch = api(
            "https://api.github.com/user/repos"
            f"?per_page=100&page={page}&affiliation={AFFILIATION}&sort=pushed"
        )
        repos += [r for r in batch if not r["fork"] and not r["archived"]]
        if len(batch) < 100:
            break
        page += 1

    stars = sum(r["stargazers_count"] for r in repos if r["owner"]["login"].lower() == LOGIN.lower())
    owned = sum(1 for r in repos if r["owner"]["login"].lower() == LOGIN.lower())

    sizes = {}
    for r in repos[:80]:
        for name, size in api(f"https://api.github.com/repos/{r['full_name']}/languages").items():
            if name in IGNORED:
                continue
            sizes[name] = sizes.get(name, 0) + size

    total = sum(sizes.values()) or 1
    ranked = sorted(sizes.items(), key=lambda kv: -kv[1])
    langs = [(n, COLORS.get(n, FALLBACK), round(s / total * 100, 1)) for n, s in ranked[:6]]
    langs = [l for l in langs if l[2] >= 0.5]
    rest = round(100 - sum(p for _, _, p in langs), 1)
    if rest >= 0.5:
        langs.append(("Other", FALLBACK, rest))

    totals = gql(TOTALS)
    contrib = totals["contributionsCollection"]
    return {
        "commits": contrib["totalCommitContributions"] + contrib["restrictedContributionsCount"],
        "stars": stars,
        "prs": totals["pullRequests"]["totalCount"],
        "repos": owned,
        "langs": langs,
    }


def compact(n):
    return f"{n/1000:.1f}k".replace(".0k", "k") if n >= 1000 else str(n)


def render(d):
    W, PAD = 1200, 64
    inner = W - PAD * 2
    metrics = [
        (compact(d["commits"]), "COMMITS / 12 MONTHS"),
        (compact(d["repos"]), "REPOSITORIES"),
        (compact(d["prs"]), "MERGED PULL REQUESTS"),
        (compact(d["stars"]), "STARS EARNED"),
    ]
    cell = inner / len(metrics)
    bar_y, bar_h = 176, 10
    legend_y = 218
    H = 258

    s = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-label="GitHub activity for {LOGIN}">',
        f'  <rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="18" fill="{INK}" stroke="{LINE}"/>',
    ]

    for i, (value, label) in enumerate(metrics):
        x = PAD + cell * i
        if i:
            s.append(f'  <path d="M{x:.0f} 44V116" stroke="{LINE}"/>')
        s.append(
            f'  <text x="{x + 28:.0f}" y="88" font-family="{SANS}" font-size="34" font-weight="600" '
            f'letter-spacing="-0.5" fill="{TEXT}">{value}</text>'
        )
        s.append(
            f'  <text x="{x + 28:.0f}" y="112" font-family="{MONO}" font-size="12" '
            f'letter-spacing="1.2" fill="{DIM}">{label}</text>'
        )

    s.append(f'  <path d="M{PAD} 146H{W-PAD}" stroke="{LINE}"/>')

    x = float(PAD)
    s.append(f'  <clipPath id="barclip"><rect x="{PAD}" y="{bar_y}" width="{inner}" height="{bar_h}" rx="5"/></clipPath>')
    s.append(f'  <g clip-path="url(#barclip)">')
    for name, color, pct in d["langs"]:
        w = inner * pct / 100
        s.append(f'    <rect x="{x:.1f}" y="{bar_y}" width="{w + 1:.1f}" height="{bar_h}" fill="{color}"/>')
        x += w
    s.append("  </g>")

    lx = float(PAD)
    for name, color, pct in d["langs"]:
        label = f"{name} {pct:g}%"
        s.append(f'  <circle cx="{lx + 4:.0f}" cy="{legend_y - 4}" r="4" fill="{color}"/>')
        s.append(
            f'  <text x="{lx + 16:.0f}" y="{legend_y}" font-family="{SANS}" font-size="15" '
            f'fill="{MUTED}">{label}</text>'
        )
        lx += len(label) * 8.2 + 46

    s.append(
        f'  <text x="{W-PAD}" y="{H-22}" text-anchor="end" font-family="{MONO}" font-size="10" '
        f'letter-spacing="1.3" fill="#3E4757">UPDATED {datetime.now(timezone.utc):%Y-%m-%d}</text>'
    )
    s.append("</svg>")
    return "\n".join(s) + "\n"


if __name__ == "__main__":
    os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
    with open(os.path.abspath(OUT), "w", encoding="utf-8") as f:
        f.write(render(collect()))
    print("wrote", os.path.abspath(OUT))