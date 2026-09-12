#!/usr/bin/env python3
"""Render assets/hero.svg: a terminal window with an ASCII portrait and a profile card."""

import json
import os

from PIL import Image, ImageOps

INK, PANEL, LINE = "#0B0E14", "#0F1520", "#1A2230"
TEXT, MUTED, DIM, ACC = "#E9EEF6", "#8B97AA", "#5C6779", "#5B8DEF"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA = os.path.join(ROOT, ".github", "data", "profile.json")
OUT = os.path.join(ROOT, "assets", "hero.svg")
PORTRAIT = next(
    (p for p in (
        os.path.join(ROOT, ".github", "data", "portrait.png"),
        os.path.join(ROOT, ".github", "data", "portrait.jpg"),
        os.path.join(ROOT, ".github", "data", "portrait.jpeg"),
    ) if os.path.exists(p)),
    None,
)

W, H = 1200, 610
BAR = 42
PAD = 32
LEFT_W = 440
GAP = 24
FS = 7.0
CHAR_W = FS * 0.6
RAMP = " .,:;i1tfLCG08@"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def ascii_rows(path, cols, rows):
    img = ImageOps.exif_transpose(Image.open(path)).convert("L")
    img = ImageOps.autocontrast(img, cutoff=2)
    target = (cols * CHAR_W) / (rows * FS)
    w, h = img.size
    if w / h > target:
        new_w = int(h * target)
        img = img.crop(((w - new_w) // 2, 0, (w + new_w) // 2, h))
    else:
        new_h = int(w / target)
        img = img.crop((0, (h - new_h) // 2, w, (h + new_h) // 2))
    img = img.resize((cols, rows), Image.LANCZOS)
    px = img.load()
    out = []
    for y in range(rows):
        out.append("".join(RAMP[min(len(RAMP) - 1, px[x, y] * len(RAMP) // 256)] for x in range(cols)))
    return out


def placeholder(cols, rows):
    out = []
    for y in range(rows):
        line = []
        for x in range(cols):
            edge = min(x, cols - 1 - x, y, rows - 1 - y)
            line.append("." if edge % 7 == 0 else " ")
        out.append("".join(line))
    return out


def leader(label, value, width=30):
    dots = "." * max(3, width - len(label) - 2)
    return label, dots, value


def render(cfg):
    left_x, left_y = PAD, BAR + 22
    left_h = H - left_y - 62
    inner_w, inner_h = LEFT_W - 36, left_h - 40
    cols, rows = int(inner_w / CHAR_W), int(inner_h / FS)
    art = ascii_rows(PORTRAIT, cols, rows) if PORTRAIT else placeholder(cols, rows)

    right_x = PAD + LEFT_W + GAP
    right_w = W - PAD - right_x

    s = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-label="{esc(cfg["rows"][0][1])} terminal profile card">',
        "  <defs>",
        f'    <linearGradient id="ascii" x1="0" y1="0" x2="0.4" y2="1">'
        f'<stop offset="0" stop-color="#9DB9F0"/><stop offset="0.55" stop-color="{ACC}"/>'
        f'<stop offset="1" stop-color="#2C4A7A"/></linearGradient>',
        f'    <clipPath id="win"><rect width="{W}" height="{H}" rx="16"/></clipPath>',
        "  </defs>",
        f'  <g clip-path="url(#win)">',
        f'    <rect width="{W}" height="{H}" fill="{INK}"/>',
        f'    <rect width="{W}" height="{BAR}" fill="#0E131B"/>',
        f'    <path d="M0 {BAR}.5H{W}" stroke="{LINE}"/>',
        "  </g>",
        f'  <rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="16" fill="none" stroke="{LINE}"/>',
    ]

    for i, cx in enumerate((26, 46, 66)):
        s.append(f'  <circle cx="{cx}" cy="{BAR/2:.0f}" r="5" fill="{DIM}" opacity="{0.45 + i*0.12:.2f}"/>')
    s.append(
        f'  <text x="{W/2:.0f}" y="{BAR/2 + 4:.0f}" text-anchor="middle" font-family="{MONO}" font-size="11.5" '
        f'fill="{DIM}">{esc(cfg["prompt"])}</text>'
    )
    s.append(f'  <circle cx="{W-118}" cy="{BAR/2:.0f}" r="3.5" fill="{ACC}"/>')
    s.append(
        f'  <text x="{W-104}" y="{BAR/2 + 4:.0f}" font-family="{MONO}" font-size="10" letter-spacing="1.4" '
        f'fill="{ACC}">{esc(cfg["status"])}</text>'
    )

    s.append(
        f'  <rect x="{left_x}" y="{left_y}" width="{LEFT_W}" height="{left_h}" rx="10" '
        f'fill="#080B10" stroke="{LINE}"/>'
    )
    s.append(
        f'  <text x="{left_x + 18}" y="{left_y + 22}" font-family="{MONO}" font-size="9.5" letter-spacing="1.6" '
        f'fill="{DIM}">{esc(cfg["portrait_label"])}</text>'
    )

    ay = left_y + 36 + FS
    s.append(f'  <g font-family="{MONO}" font-size="{FS}" fill="url(#ascii)" xml:space="preserve">')
    for i, line in enumerate(art):
        s.append(f'    <text x="{left_x + 18}" y="{ay + i * FS:.1f}">{esc(line)}</text>')
    s.append("  </g>")

    y = left_y + 20
    s.append(
        f'  <text x="{right_x}" y="{y}" font-family="{MONO}" font-size="9.5" letter-spacing="1.6" '
        f'fill="{DIM}">{esc(cfg["card_label"])}</text>'
    )
    y += 26
    s.append(
        f'  <text x="{right_x}" y="{y}" font-family="{MONO}" font-size="12.5" fill="{MUTED}">'
        f'{esc(cfg["user"])} {"-" * 44}</text>'
    )

    def block(title, items, y):
        y += 30
        if title:
            s.append(
                f'  <text x="{right_x}" y="{y}" font-family="{MONO}" font-size="10.5" letter-spacing="1.5" '
                f'fill="{DIM}">{esc(title)} {"-" * 34}</text>'
            )
            y += 22
        for label, value in items:
            lab, dots, val = leader(label, value)
            s.append(
                f'  <text x="{right_x}" y="{y}" font-family="{MONO}" font-size="12.5" xml:space="preserve">'
                f'<tspan fill="{ACC}">{esc(lab)}:</tspan>'
                f'<tspan fill="#28303D"> {esc(dots)} </tspan>'
                f'<tspan fill="{TEXT}">{esc(val)}</tspan></text>'
            )
            y += 21
        return y

    y = block("", cfg["rows"], y - 8)
    y = block("BUILD.FOCUS", cfg["focus"], y)
    y = block("SELECTED.WORK", cfg["work"], y)

    s.append(
        f'  <text x="{right_x}" y="{y + 28}" font-family="{MONO}" font-size="11.5" letter-spacing="1.2" '
        f'fill="{MUTED}">{esc(cfg["tagline"])}</text>'
    )
    s.append(
        f'  <text x="{W/2:.0f}" y="{H-22}" text-anchor="middle" font-family="{MONO}" font-size="9.5" '
        f'letter-spacing="2" fill="#39424F">{esc(cfg["footer"])}</text>'
    )
    s.append("</svg>")
    return "\n".join(s) + "\n"


if __name__ == "__main__":
    with open(DATA, encoding="utf-8") as f:
        cfg = json.load(f)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(render(cfg))
    print("wrote", OUT, "portrait:", PORTRAIT or "placeholder")
