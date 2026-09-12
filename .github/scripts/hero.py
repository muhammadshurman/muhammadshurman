#!/usr/bin/env python3
"""Render assets/hero.svg: a terminal window with an ASCII portrait and a profile card."""

import base64
import io
import json
import os

import math

from PIL import Image, ImageFilter, ImageOps

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


def ascii_rows(path, cols, rows, opt):
    img = ImageOps.exif_transpose(Image.open(path)).convert("L")

    box = opt.get("crop")
    if box:
        w, h = img.size
        img = img.crop((int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h)))

    img = ImageOps.autocontrast(img, cutoff=tuple(opt.get("cutoff", [1, 1])))
    if opt.get("invert"):
        img = ImageOps.invert(img)

    if opt.get("autocrop", False):
        thresh = int(opt.get("subject_threshold", 45))
        bb = img.point(lambda v: 255 if v > thresh else 0).getbbox()
        if bb:
            iw, ih = img.size
            mx, my = int(iw * 0.03), int(ih * 0.03)
            bb = (max(0, bb[0] - mx), max(0, bb[1] - my), min(iw, bb[2] + mx), min(ih, bb[3] + my))
            if (bb[2] - bb[0]) * (bb[3] - bb[1]) < iw * ih * 0.92:
                img = ImageOps.autocontrast(img.crop(bb), cutoff=2)

    gw, gh = cols + 2, rows + 2
    target = (gw * CHAR_W) / (gh * FS)
    w, h = img.size
    if opt.get("fit", "cover") == "cover":
        if w / h > target:
            nw = int(h * target)
            img = img.crop(((w - nw) // 2, 0, (w + nw) // 2, h))
        else:
            nh = int(w / target)
            img = img.crop((0, (h - nh) // 2, w, (h + nh) // 2))
        grid = img.resize((gw, gh), Image.LANCZOS)
    else:
        scale = min(gw * CHAR_W / w, gh * FS / h)
        nw = max(1, min(gw, int(w * scale / CHAR_W)))
        nh = max(1, min(gh, int(h * scale / FS)))
        grid = Image.new("L", (gw, gh), 0)
        grid.paste(img.resize((nw, nh), Image.LANCZOS), ((gw - nw) // 2, (gh - nh) // 2))

    if opt.get("mode", "edges") == "edges":
        grid = grid.filter(ImageFilter.GaussianBlur(float(opt.get("blur", 0.6))))
        px = grid.load()
        mag = [[math.hypot(px[x + 1, y] - px[x - 1, y], px[x, y + 1] - px[x, y - 1])
                for x in range(1, cols + 1)] for y in range(1, rows + 1)]
        peak = max(max(r) for r in mag) or 1
        floor = float(opt.get("edge_floor", 0.16))
        gain = float(opt.get("edge_gain", 1.5))
        out = []
        for row in mag:
            line = ""
            for v in row:
                n = (v / peak - floor) / (1 - floor)
                line += " " if n <= 0 else RAMP[min(len(RAMP) - 1, int(n ** 0.8 * gain * (len(RAMP) - 1)))]
            out.append(line)
        return out

    gamma = float(opt.get("gamma", 1.0))
    lift = float(opt.get("lift", 1.0))
    floor = int(opt.get("floor", 0))
    lut = []
    for v in range(256):
        v = 255 * (v / 255) ** gamma * lift
        lut.append(0 if v < floor else int(min(255, max(0, v))))
    grid = grid.point(lut)
    px = grid.load()
    return ["".join(RAMP[min(len(RAMP) - 1, px[x, y] * len(RAMP) // 256)] for x in range(1, cols + 1))
            for y in range(1, rows + 1)]


def photo_block(path, opt, x, y, w, h):
    img = ImageOps.exif_transpose(Image.open(path)).convert("L")

    box = opt.get("crop")
    if box:
        iw, ih = img.size
        img = img.crop((int(box[0] * iw), int(box[1] * ih), int(box[2] * iw), int(box[3] * ih)))

    img = ImageOps.autocontrast(img, cutoff=tuple(opt.get("cutoff", [1, 1])))
    target = w / h
    iw, ih = img.size
    if iw / ih > target:
        nw = int(ih * target)
        img = img.crop(((iw - nw) // 2, 0, (iw + nw) // 2, ih))
    else:
        nh = int(iw / target)
        img = img.crop((0, int((ih - nh) * float(opt.get("anchor", 0.5))), iw,
                        int((ih - nh) * float(opt.get("anchor", 0.5))) + nh))
    img = img.resize((int(w * 2), int(h * 2)), Image.LANCZOS)
    img = ImageOps.colorize(img, black=opt.get("shadow", "#070A10"),
                            mid=opt.get("mid", "#2F4C7C"), white=opt.get("highlight", "#DCE7FA"))

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=int(opt.get("quality", 82)), optimize=True)
    b64 = base64.b64encode(buf.getvalue()).decode()

    return [
        f'  <defs><clipPath id="photo"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8"/></clipPath>',
        f'    <pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse">'
        f'<rect width="4" height="1" fill="#000000" opacity="0.13"/></pattern></defs>',
        f'  <g clip-path="url(#photo)" opacity="1">'
        f'<animate attributeName="opacity" values="0;1" dur="1.1s" fill="freeze"/>',
        f'    <image x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="xMidYMid slice" '
        f'href="data:image/jpeg;base64,{b64}"/>',
        f'    <rect x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#scan)"/>',
        f'    <rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{ACC}" opacity="0.05"/>',
        "  </g>",
        f'  <rect x="{x}.5" y="{y}.5" width="{w-1}" height="{h-1}" rx="8" fill="none" stroke="{LINE}"/>',
    ]


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
    side = cfg.get("layout", "left")
    left_x = W - PAD - LEFT_W if side == "right" else PAD
    left_y = BAR + 22
    left_h = H - left_y - 62
    inner_w, inner_h = LEFT_W - 36, left_h - 40
    cols, rows = int(inner_w / CHAR_W), int(inner_h / FS)
    opt = cfg.get("portrait", {})
    photo_mode = opt.get("mode") == "photo" and PORTRAIT
    art = [] if photo_mode else (
        ascii_rows(PORTRAIT, cols, rows, opt) if PORTRAIT else placeholder(cols, rows))

    right_x = PAD if side == "right" else PAD + LEFT_W + GAP
    right_w = W - PAD - LEFT_W - GAP - PAD

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
    s.append(
        f'  <rect x="{W/2 + len(cfg["prompt"]) * 3.45:.0f}" y="{BAR/2 - 7:.0f}" width="7" height="13" fill="{ACC}">'
        f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.45;0.5;1" dur="1.1s" '
        f'repeatCount="indefinite"/></rect>'
    )
    s.append(f'  <circle cx="{W-118}" cy="{BAR/2:.0f}" r="3.5" fill="{ACC}">'
             f'<animate attributeName="opacity" values="1;0.25;1" dur="2.4s" repeatCount="indefinite"/></circle>')
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

    if photo_mode:
        s += photo_block(PORTRAIT, opt, left_x + 14, left_y + 32, LEFT_W - 28, left_h - 46)

    ay = left_y + 36 + FS
    s.append(f'  <g font-family="{MONO}" font-size="{FS}" fill="url(#ascii)" xml:space="preserve">')
    n = max(1, len(art))
    for i, line in enumerate(art):
        t0 = 0.02 + 0.62 * i / n
        s.append(
            f'    <text x="{left_x + 18}" y="{ay + i * FS:.1f}" opacity="1">{esc(line)}'
            f'<animate attributeName="opacity" values="0;0;1" keyTimes="0;{t0:.3f};{min(0.999, t0 + 0.05):.3f}" '
            f'dur="2.6s" fill="freeze"/></text>'
        )
    s.append("  </g>")
    s.append(
        f'  <rect x="{left_x + 1}" y="{left_y}" width="{LEFT_W - 2}" height="2" fill="{ACC}" opacity="0">'
        f'<animate attributeName="y" values="{left_y};{left_y + left_h}" dur="2.6s" fill="freeze"/>'
        f'<animate attributeName="opacity" values="0;0.5;0" keyTimes="0;0.5;1" dur="2.6s" '
        f'fill="freeze"/></rect>'
    )

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

    reveal = []

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
            t0 = 0.30 + 0.045 * len(reveal)
            reveal.append(1)
            s.append(
                f'  <text x="{right_x}" y="{y}" font-family="{MONO}" font-size="12.5" opacity="1" '
                f'xml:space="preserve">'
                f'<tspan fill="{ACC}">{esc(lab)}:</tspan>'
                f'<tspan fill="#28303D"> {esc(dots)} </tspan>'
                f'<tspan fill="{TEXT}">{esc(val)}</tspan>'
                f'<animate attributeName="opacity" values="0;0;1" '
                f'keyTimes="0;{min(0.94, t0):.3f};{min(0.999, t0 + 0.05):.3f}" dur="2.9s" fill="freeze"/></text>'
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
