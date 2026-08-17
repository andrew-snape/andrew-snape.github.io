#!/usr/bin/env python3
"""Generate a per-post social preview card for any post missing `image:`.

Runs before `jekyll build`. Renders assets/images/og/<slug>.png for each
post that doesn't already set its own `image:` front matter, then injects
that path into the post's front matter so jekyll-seo-tag picks it up as
og:image/twitter:image. Safe to re-run: posts that already have `image:`
(including ones this script wrote on a previous run) are left untouched.
"""
import re
import sys
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = ROOT / "_posts"
OUT_DIR = ROOT / "assets" / "images" / "og"
FONT_PATH = ROOT / "assets" / "fonts" / "Inter-Variable.ttf"

W, H = 1200, 630
BG = "#fdfdfb"
TEXT = "#1b1b18"
MUTED = "#6e6e68"
BORDER = "#e6e5e0"
PAD = 90

FRONT_MATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def variable_font(size, weight=400, opsz=14):
    font = ImageFont.truetype(str(FONT_PATH), size)
    try:
        font.set_variation_by_axes([opsz, weight])
    except Exception:
        pass
    return font


def parse_front_matter(text):
    match = FRONT_MATTER_RE.match(text)
    if not match:
        return {}, None
    fields = {}
    for line in match.group(1).splitlines():
        if line.startswith("title:"):
            fields["title"] = line.split(":", 1)[1].strip().strip('"')
        elif line.startswith("categories:"):
            raw = line.split(":", 1)[1].strip().strip("[]")
            fields["categories"] = [c.strip() for c in raw.split(",") if c.strip()]
        elif line.startswith("image:"):
            fields["image"] = line.split(":", 1)[1].strip()
    return fields, match


def wrap_and_fit(draw, text, max_width, max_height, start_size, min_size, weight):
    size = start_size
    font, lines, line_height = None, [], 0
    while size >= min_size:
        font = variable_font(size, weight)
        words = text.split()
        lines, current = [], ""
        for word in words:
            trial = (current + " " + word).strip()
            if draw.textlength(trial, font=font) <= max_width:
                current = trial
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        line_height = size * 1.28
        if len(lines) * line_height <= max_height:
            return font, lines, line_height
        size -= 4
    return font, lines, line_height


def render_card(title, category, slug):
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    draw.rectangle([28, 28, W - 28, H - 28], outline=BORDER, width=2)

    kicker_font = variable_font(28, 600)
    draw.text((PAD, 96), (category or "blog").upper(), font=kicker_font, fill=MUTED)

    title_font, lines, line_height = wrap_and_fit(
        draw, title, max_width=W - PAD * 2, max_height=330,
        start_size=68, min_size=38, weight=700,
    )
    y = 172
    for line in lines:
        draw.text((PAD, y), line, font=title_font, fill=TEXT)
        y += line_height

    footer_font = variable_font(26, 500)
    draw.text((PAD, H - 96), "Andrew Snape · andrew-snape.github.io", font=footer_font, fill=MUTED)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"{slug}.png"
    img.save(out_path, "PNG")
    return out_path


def main():
    if not POSTS_DIR.exists():
        print("No _posts directory found, nothing to do.")
        return

    for post_path in sorted(POSTS_DIR.glob("*.md")):
        text = post_path.read_text(encoding="utf-8")
        fields, match = parse_front_matter(text)
        if match is None:
            continue

        slug = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", post_path.stem)
        title = fields.get("title", slug)
        category = (fields.get("categories") or ["blog"])[0]

        render_card(title, category, slug)
        print(f"generated assets/images/og/{slug}.png")

        if "image" not in fields:
            fm_body = match.group(1).rstrip("\n")
            new_fm = f"{fm_body}\nimage: /assets/images/og/{slug}.png\n"
            new_text = "---\n" + new_fm + "---\n" + text[match.end():]
            post_path.write_text(new_text, encoding="utf-8")
            print(f"  -> added image: front matter to {post_path.name}")


if __name__ == "__main__":
    sys.exit(main())
