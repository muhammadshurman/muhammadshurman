#!/usr/bin/env python3
"""Inject the featured-work table and recent activity feed into README.md."""

import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
README = os.path.join(ROOT, "README.md")
DATA = os.path.join(ROOT, ".github", "data", "projects.json")

LOGIN = os.environ.get("GH_LOGIN", "muhammadshurman")
TOKEN = os.environ.get("GH_TOKEN", "")
EVENT_COUNT = 6


def api(url, attempts=3):
    last = None
    for i in range(attempts):
        req = urllib.request.Request(
            url,
            headers={
                "Authorization": f"bearer {TOKEN}",
                "Accept": "application/vnd.github+json",
                "User-Agent": "profile-readme",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.load(r)
        except urllib.error.URLError as e:
            last = e
            time.sleep(2 ** i)
    raise RuntimeError(f"GET {url} failed: {last}")


def work_block(projects):
    lines = ['<img src="assets/work.svg" alt="Selected work: projects, focus and stack" width="100%" />']
    links = [f"[{p['name']}]({p.get('live') or p['url']})" for p in projects if p.get("live") or p.get("url")]
    if links:
        lines += ["", "Live: " + " · ".join(links)]
    return "\n".join(lines)


def describe(event):
    repo = event["repo"]["name"]
    link = f"[{repo}](https://github.com/{repo})"
    kind = event["type"]
    payload = event.get("payload", {})

    if kind == "PushEvent":
        n = payload.get("size", 1)
        return f"pushed {n} commit{'s' if n != 1 else ''} to {link}"
    if kind == "PullRequestEvent":
        num = payload.get("number", "")
        action = payload.get("action", "opened")
        if action == "closed" and payload.get("pull_request", {}).get("merged"):
            action = "merged"
        return f"{action} pull request #{num} in {link}"
    if kind == "IssuesEvent":
        return f"{payload.get('action', 'opened')} issue #{payload.get('issue', {}).get('number', '')} in {link}"
    if kind == "CreateEvent":
        return f"created a {payload.get('ref_type', 'branch')} in {link}"
    if kind == "ReleaseEvent":
        return f"published a release in {link}"
    if kind == "WatchEvent":
        return f"starred {link}"
    if kind == "ForkEvent":
        return f"forked {link}"
    return None


def activity_list():
    if not TOKEN:
        return "_Activity feed renders once the workflow runs._"

    events = api(f"https://api.github.com/users/{LOGIN}/events/public?per_page=60")
    lines = []
    for event in events:
        text = describe(event)
        if not text:
            continue
        when = datetime.strptime(event["created_at"], "%Y-%m-%dT%H:%M:%SZ")
        lines.append(f"- {when:%b %d, %Y}: {text}")
        if len(lines) == EVENT_COUNT:
            break
    return "\n".join(lines) if lines else "_No public activity in the last 90 days._"


def inject(text, marker, body):
    start, end = f"<!-- {marker}:start -->", f"<!-- {marker}:end -->"
    if start not in text or end not in text:
        return text
    head = text.index(start) + len(start)
    tail = text.index(end)
    return text[:head] + "\n" + body + "\n" + text[tail:]


if __name__ == "__main__":
    with open(DATA, encoding="utf-8") as f:
        projects = json.load(f)
    with open(README, encoding="utf-8") as f:
        text = f.read()

    text = inject(text, "work", work_block(projects))
    text = inject(text, "activity", activity_list())

    with open(README, "w", encoding="utf-8") as f:
        f.write(text)
    print("updated", README)
