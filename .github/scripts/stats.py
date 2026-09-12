#!/usr/bin/env python3
"""Render assets/stats.svg from the GitHub GraphQL API. No third-party services."""

import json
import os
import urllib.request
from datetime import datetime, timezone

INK, PANEL, LINE = "#0B0E14", "#0F1520", "#1A2230"
TEXT, MUTED, DIM, ACC = "#E9EEF6", "#8B97AA", "#5C6779", "#5B8DEF"
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"

LOGIN = os.environ.get("GH_LOGIN", "muhammadshurman")
TOKEN = os.environ.get("GH_TOKEN", "")
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "stats.svg")

QUERY = """
query($login: String!, $cursor: String) {
  user(login: $login) {
    followers { totalCount }
    pullRequests(states: MERGED) { totalCount }
    contributionsCollection { totalCommitContributions restrictedContributionsCount }
    repositories(first: 100, after: $cursor, ownerAffiliations: OWNER, isFork: false) {
      totalCount
      pageInfo { hasNextPage endCursor }
      nodes {
        stargazerCount
        languages(first: 12, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
  }
}
"""


def gql(cursor=None):
    body = json.dumps({"query": QUERY, "variables": {"login": LOGIN, "cursor": cursor}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={
            "Authorization": f"bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "profile-stats",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.load(r)
    if "errors" in payload:
        raise RuntimeError(payload["errors"])
    return payload["data"]["user"]


def collect():
    if not TOKEN:
        return {
            "commits": 0, "stars": 0, "prs": 0, "repos": 0,
            "langs": [("PHP", "#4F5D95", 38.0), ("TypeScript", "#3178c6", 24.0),
                      ("Blade", "#f7523f", 16.0), ("JavaScript", "#f1e05a", 12.0),
                      ("CSS", "#663399", 6.0), ("Other", "#3A4454", 4.0)],
        }

    stars, sizes, colors = 0, {}, {}
    cursor, first = None, None
    while True:
        user = gql(cursor)
        first = first or user
        repos = user["repositories"]
        for node in repos["nodes"]:
            stars += node["stargazerCount"]
            for edge in node["languages"]["edges"]:
                name = edge["node"]["name"]
                sizes[name] = sizes.get(name, 0) + edge["size"]
                colors[name] = edge["node"]["color"] or "#3A4454"
        if not repos["pageInfo"]["hasNextPage"]:
            break
        cursor = repos["pageInfo"]["endCursor"]

    contrib = first["contributionsCollection"]
    total = sum(sizes.values()) or 1
    ranked = sorted(sizes.items(), key=lambda kv: -kv[1])
    langs = [(n, colors[n], round(s / total * 100, 1)) for n, s in ranked[:6]]
    rest = round(100 - sum(p for _, _, p in langs), 1)
    if rest >= 0.5:
        langs.append(("Other", "#3A4454", rest))

    return {
        "commits": contrib["totalCommitContributions"] + contrib["restrictedContributionsCount"],
        "stars": stars,
        "prs": first["pullRequests"]["totalCount"],
        "repos": first["repositories"]["totalCount"],
        "langs": langs,
    }


def compact(n):
    return f"{n/1000:.1f}k".replace(".0k", "k") if n >= 1000 else str(n)


def render(d):
    W, PAD = 1200, 64
    inner = W - PAD * 2
    metrics = [
        (compact(d["commits"]), "COMMITS / 12 MONTHS"),
        (compact(d["repos"]), "PUBLIC REPOSITORIES"),
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
            f'  <text x="{x + 28:.0f}" y="112" font-family="{MONO}" font-size="10.5" '
            f'letter-spacing="1.4" fill="{DIM}">{label}</text>'
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
            f'  <text x="{lx + 16:.0f}" y="{legend_y}" font-family="{SANS}" font-size="12.5" '
            f'fill="{MUTED}">{label}</text>'
        )
        lx += len(label) * 6.9 + 46

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
