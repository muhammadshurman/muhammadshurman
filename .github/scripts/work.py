#!/usr/bin/env python3
"""Render assets/work.svg from .github/data/projects.json."""

import json
import os

INK, PANEL, LINE = "#0B0E14", "#0F1520", "#1A2230"
TEXT, MUTED, DIM, ACC = "#E9EEF6", "#8B97AA", "#5C6779", "#5B8DEF"
CHIP = "#C3CCDA"
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA = os.path.join(ROOT, ".github", "data", "projects.json")
OUT = os.path.join(ROOT, "assets", "work.svg")

W, PAD, GAP = 1200, 40, 20
CARD_W = (W - PAD * 2 - GAP) // 2
CARD_H, ROW_GAP = 196, 20
HEAD = 62


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def wrap(text, width):
    words, lines, line = text.split(), [], ""
    for word in words:
        probe = f"{line} {word}".strip()
        if len(probe) > width and line:
            lines.append(line)
            line = word
        else:
            line = probe
    if line:
        lines.append(line)
    return lines[:2]


def card(p, x, y):
    s = [
        f'  <rect x="{x}" y="{y}" width="{CARD_W}" height="{CARD_H}" rx="12" fill="{PANEL}" stroke="{LINE}"/>',
        f'  <rect x="{x + 20}" y="{y + 27}" width="2.5" height="22" rx="1" fill="{ACC}"/>',
        f'  <text x="{x + 34}" y="{y + 44}" font-family="{SANS}" font-size="20" font-weight="600" '
        f'letter-spacing="-0.2" fill="{TEXT}">{esc(p["name"])}</text>',
        f'  <text x="{x + 34}" y="{y + 66}" font-family="{MONO}" font-size="11" '
        f'letter-spacing="1.3" fill="{ACC}" opacity="0.85">{esc(p["focus"].upper())}</text>',
        f'  <path d="M{x + 20} {y + 84}H{x + CARD_W - 20}" stroke="{LINE}"/>',
    ]

    for i, line in enumerate(wrap(p["why"], 52)):
        s.append(
            f'  <text x="{x + 20}" y="{y + 110 + i * 22}" font-family="{SANS}" font-size="15" '
            f'fill="{MUTED}">{esc(line)}</text>'
        )

    cx = x + 20
    for label in p["stack"]:
        cw = round(len(label) * 7.6 + 26)
        s.append(
            f'  <rect x="{cx}" y="{y + CARD_H - 50}" width="{cw}" height="27" rx="7" '
            f'fill="#0B0F16" stroke="{LINE}"/>'
        )
        s.append(
            f'  <text x="{cx + cw / 2:.0f}" y="{y + CARD_H - 32}" text-anchor="middle" font-family="{MONO}" '
            f'font-size="12.5" fill="{CHIP}">{esc(label)}</text>'
        )
        cx += cw + 7

    if p.get("live") or p.get("url"):
        s.append(
            f'  <text x="{x + CARD_W - 20}" y="{y + CARD_H - 32}" text-anchor="end" font-family="{MONO}" '
            f'font-size="11" letter-spacing="1.2" fill="{DIM}">LIVE</text>'
        )
    return s


def render(projects):
    rows = (len(projects) + 1) // 2
    H = HEAD + rows * (CARD_H + ROW_GAP) + 10

    s = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-label="Selected work">',
        f'  <rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="18" fill="{INK}" stroke="{LINE}"/>',
        f'  <text x="{PAD}" y="40" font-family="{MONO}" font-size="12" letter-spacing="1.6" '
        f'fill="{DIM}">SELECTED.WORK {"-" * 52}</text>',
        f'  <text x="{W - PAD}" y="40" text-anchor="end" font-family="{MONO}" font-size="12" '
        f'letter-spacing="1.4" fill="{DIM}">{len(projects)} PROJECTS</text>',
    ]

    for i, p in enumerate(projects):
        x = PAD + (i % 2) * (CARD_W + GAP)
        y = HEAD + (i // 2) * (CARD_H + ROW_GAP)
        s += card(p, x, y)

    s.append("</svg>")
    return "\n".join(s) + "\n"


if __name__ == "__main__":
    with open(DATA, encoding="utf-8") as f:
        projects = json.load(f)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(render(projects))
    print("wrote", OUT)
