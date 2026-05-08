from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw

TEMPLATES = {
    "dark tech": {"bg": (10, 16, 28), "band": (0, 0, 0), "accent": (0, 220, 255), "text": (255, 255, 255)},
    "finance yellow-black": {"bg": (18, 18, 18), "band": (0, 0, 0), "accent": (255, 204, 0), "text": (255, 255, 255)},
    "history cinematic": {"bg": (45, 30, 20), "band": (18, 10, 6), "accent": (220, 145, 70), "text": (255, 242, 220)},
    "news clean": {"bg": (240, 245, 250), "band": (10, 40, 80), "accent": (220, 30, 45), "text": (255, 255, 255)},
    "product ad clean": {"bg": (235, 235, 232), "band": (255, 255, 255), "accent": (20, 20, 20), "text": (10, 10, 10)},
    "red warning": {"bg": (35, 0, 0), "band": (0, 0, 0), "accent": (255, 40, 40), "text": (255, 255, 255)},
    "before-after": {"bg": (25, 25, 35), "band": (0, 0, 0), "accent": (0, 210, 120), "text": (255, 255, 255)},
}

def wrap(text: str, limit: int) -> list[str]:
    words = text.strip().split()
    lines, line = [], ""
    for word in words:
        test = (line + " " + word).strip()
        if len(test) > limit and line:
            lines.append(line); line = word
        else:
            line = test
    if line: lines.append(line)
    return lines[:4]

def make_thumbnail(project_dir: Path, base_image: str | None, title: str, template: str, vertical: bool = True) -> str:
    cfg = TEMPLATES.get(template, TEMPLATES["dark tech"])
    size = (1080, 1920) if vertical else (1920, 1080)
    if base_image and Path(base_image).exists():
        img = Image.open(base_image).convert("RGB").resize(size)
    else:
        img = Image.new("RGB", size, cfg["bg"])
    draw = ImageDraw.Draw(img)
    w, h = img.size
    draw.rectangle([0, 0, w, int(h*.12)], fill=cfg["band"])
    draw.rectangle([0, int(h*.68), w, h], fill=cfg["band"])
    draw.rectangle([0, int(h*.68), int(w*.035), h], fill=cfg["accent"])
    draw.rectangle([0, 0, w, int(h*.018)], fill=cfg["accent"])
    y = int(h*.72)
    for line in wrap(title.upper(), 22 if vertical else 34):
        draw.text((int(w*.07), y), line, fill=cfg["text"])
        y += int(h*.045)
    pill = "SAVE THIS"
    x1, y1 = int(w*.07), int(h*.055)
    x2, y2 = x1 + int(w*.32), y1 + int(h*.045)
    draw.rounded_rectangle([x1, y1, x2, y2], radius=18, fill=cfg["accent"])
    draw.text((x1+18, y1+10), pill, fill=cfg["band"])
    out = project_dir / "thumbs" / f"thumbnail_{template.replace(' ','_')}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    return str(out)
