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

W, PAD, ROW = 1200, 56, 74
CHIP_H, CHIP_PAD, CHIP_GAP, CHIP_FS = 24, 11, 7, 11.5


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def chip_w(label):
    return round(len(label) * CHIP_FS * 0.58 + CHIP_PAD * 2)


def render(projects):
    H = PAD + len(projects) * ROW + 12
    s = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-label="Selected work">',
        f'  <rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="18" fill="{INK}" stroke="{LINE}"/>',
    ]

    y = PAD - 10
    for i, p in enumerate(projects):
        if i:
            s.append(f'  <path d="M{PAD} {y}H{W-PAD}" stroke="{LINE}"/>')

        s.append(f'  <rect x="{PAD}" y="{y + 22}" width="2" height="26" rx="1" fill="{ACC}" opacity="0.7"/>')
        s.append(
            f'  <text x="{PAD + 18}" y="{y + 38}" font-family="{SANS}" font-size="17" font-weight="600" '
            f'letter-spacing="-0.2" fill="{TEXT}">{esc(p["name"])}</text>'
        )
        s.append(
            f'  <text x="{PAD + 18}" y="{y + 59}" font-family="{SANS}" font-size="13" '
            f'fill="{MUTED}">{esc(p["blurb"])}</text>'
        )

        widths = [chip_w(c) for c in p["stack"]]
        x = W - PAD - (sum(widths) + CHIP_GAP * (len(widths) - 1))
        cy = y + 34
        for label, cw in zip(p["stack"], widths):
            s.append(
                f'  <rect x="{x:.0f}" y="{cy - CHIP_H/2:.0f}" width="{cw}" height="{CHIP_H}" rx="7" '
                f'fill="{PANEL}" stroke="{LINE}"/>'
            )
            s.append(
                f'  <text x="{x + cw/2:.0f}" y="{cy + 4:.0f}" text-anchor="middle" font-family="{MONO}" '
                f'font-size="{CHIP_FS}" fill="{CHIP}">{esc(label)}</text>'
            )
            x += cw + CHIP_GAP

        y += ROW

    s.append("</svg>")
    return "\n".join(s) + "\n"


if __name__ == "__main__":
    with open(DATA, encoding="utf-8") as f:
        projects = json.load(f)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(render(projects))
    print("wrote", OUT)
