from __future__ import annotations
import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def safe_filename(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", name or "uploaded_file")


THUMB_FLOW_MODEL_CREDITS = {
    "🍌 Nano Banana Pro": 5,
    "🍌 Nano Banana 2": 3,
    "Imagen 4": 4,
    "Imagen 4 Ultra": 6,
}

STYLE_PRESETS={
    "Cyberpunk":"neon cyberpunk, futuristic city glow, purple-blue-pink lighting, holographic accents, high contrast, moody sci-fi atmosphere",
    "Realistic Commercial":"photorealistic, premium commercial ad, polished lighting, clean subject focus, realistic textures",
    "Luxury Premium":"luxury editorial, gold accents, premium lighting, elegant composition, high-end product aesthetic",
    "Minimal Clean":"minimalist, clean composition, lots of negative space, simple shapes, modern design language",
    "Cute Pastel":"cute pastel, soft tones, adorable visual mood, playful design, friendly rounded forms",
    "Futuristic Tech":"futuristic tech, blue glow, sleek interfaces, sci-fi surfaces, premium innovation mood",
    "Cinematic Dark":"cinematic dark mood, dramatic lighting, bold contrast, movie-poster feeling",
    "Street Hype":"streetwear hype style, bold framing, urban energy, trendy social-media look"
}


STYLE_COLORS={
    "Cyberpunk":{"accent":"#ff00c8","secondary":"#00e5ff","bg1":"#0a0f2e","bg2":"#23113a","text":"#ecfeff","palette":"purple, cyan, hot pink, electric blue"},
    "Realistic Commercial":{"accent":"#2f80ed","secondary":"#9ad0ff","bg1":"#10161f","bg2":"#1b2430","text":"#f5f7fa","palette":"clean blue, white, steel gray"},
    "Luxury Premium":{"accent":"#d4af37","secondary":"#f7e7a1","bg1":"#1d160c","bg2":"#33250f","text":"#fff7dc","palette":"gold, champagne, deep brown"},
    "Minimal Clean":{"accent":"#222222","secondary":"#cfcfcf","bg1":"#f4f4f1","bg2":"#deded8","text":"#111111","palette":"off-white, charcoal, soft gray"},
    "Cute Pastel":{"accent":"#ff7eb6","secondary":"#ffd6e8","bg1":"#fff0f7","bg2":"#f7d8e8","text":"#5c3f55","palette":"pink pastel, lilac, cream"},
    "Futuristic Tech":{"accent":"#00d1ff","secondary":"#7cf3ff","bg1":"#071a2e","bg2":"#0c2b4a","text":"#effdff","palette":"cyan, blue glow, dark navy"},
    "Cinematic Dark":{"accent":"#ff5a36","secondary":"#f4c095","bg1":"#111111","bg2":"#2b1d1a","text":"#fff1ea","palette":"burnt orange, black, warm shadows"},
    "Street Hype":{"accent":"#ff4747","secondary":"#ffd166","bg1":"#161616","bg2":"#2d2d2d","text":"#f8f8f8","palette":"red, yellow, black, urban gray"},
}

def style_palette_text(style_name: str) -> str:
    cfg = STYLE_COLORS.get(style_name, {})
    return cfg.get('palette', 'balanced commercial palette')

def project_style_path(pdir: Path) -> Path:
    return pdir / 'project_style.json'

def load_project_style(pdir: Path) -> dict:
    fp = project_style_path(pdir)
    if fp.exists():
        try:
            data = json.loads(fp.read_text(encoding='utf-8'))
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    return {'locked': False, 'selected_style': 'Realistic Commercial'}

def save_project_style(pdir: Path, data: dict) -> Path:
    fp = project_style_path(pdir)
    fp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    return fp

def style_preview_card(name: str, selected: bool=False) -> str:
    cfg = STYLE_COLORS.get(name, {})
    accent = cfg.get('accent', '#4f46e5')
    secondary = cfg.get('secondary', '#93c5fd')
    bg1 = cfg.get('bg1', '#111827')
    bg2 = cfg.get('bg2', '#1f2937')
    text_color = cfg.get('text', '#ffffff')
    palette = cfg.get('palette', '')
    ring = f'2px solid {accent}' if selected else '1px solid rgba(255,255,255,.12)'
    badge = 'SELECTED' if selected else 'PREVIEW'
    return f"""<div style='border:{ring};border-radius:18px;padding:14px;margin:8px 0;background:linear-gradient(135deg,{bg1},{bg2});box-shadow:0 10px 22px rgba(0,0,0,.18);'>
<div style='display:flex;justify-content:space-between;align-items:center;gap:10px;'>
<div style='font-weight:700;color:{text_color};font-size:1rem'>{name}</div>
<div style='font-size:.72rem;padding:4px 8px;border-radius:999px;background:{accent};color:#fff'>{badge}</div>
</div>
<div style='display:flex;gap:8px;margin-top:10px;margin-bottom:10px;'>
<div style='height:44px;flex:1;border-radius:10px;background:linear-gradient(135deg,{accent},{secondary});'></div>
<div style='height:44px;flex:1;border-radius:10px;background:linear-gradient(135deg,{bg2},{accent});'></div>
<div style='height:44px;flex:1;border-radius:10px;background:linear-gradient(135deg,{secondary},{bg1});'></div>
</div>
<div style='font-size:.82rem;color:{text_color};opacity:.95;'>Palette: {palette}</div>
<div style='font-size:.76rem;color:{text_color};opacity:.74;margin-top:6px;'>{STYLE_PRESETS.get(name, name)}</div>
</div>"""




def hex_to_rgb(hex_color: str):
    h = hex_color.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb):
    return '#%02x%02x%02x' % rgb

def blend(c1, c2, t: float):
    a = hex_to_rgb(c1); b = hex_to_rgb(c2)
    return rgb_to_hex(tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3)))

def style_theme_css(style_name: str, secondary_style: str | None = None) -> str:
    cfg = STYLE_COLORS.get(style_name, {})
    secondary_style = normalize_secondary_style(secondary_style)
    cfg2 = STYLE_COLORS.get(secondary_style, {}) if secondary_style else {}
    accent = cfg.get('accent', '#6d5efc')
    secondary = cfg2.get('accent', cfg.get('secondary', '#4fd1ff'))
    bg1 = cfg.get('bg1', '#121826')
    bg2 = cfg2.get('bg2', cfg.get('bg2', '#1f2937'))
    text_color = cfg.get('text', '#f8fafc')
    return f"""<style>
    .stApp {{background: radial-gradient(circle at top left, {blend(bg2, secondary, .08)}, #0b0f16 58%) !important;}}
    [data-testid="stSidebar"] {{background: linear-gradient(180deg, {bg1}, {bg2}) !important; border-right: 1px solid rgba(255,255,255,.08);}}
    .hero {{background: linear-gradient(135deg, {blend(bg1, accent, .15)}, {blend(bg2, secondary, .18)}) !important; border:1px solid {blend(accent, '#ffffff', .18)} !important; box-shadow:0 18px 34px rgba(0,0,0,.18);}}
    .badge {{background:{blend(accent, '#111111', .72)} !important; border:1px solid {blend(accent, '#ffffff', .25)} !important; color:{text_color} !important;}}
    .stButton>button {{background: linear-gradient(135deg, {accent}, {secondary}) !important; color:white !important; border:none !important; border-radius:14px !important; box-shadow:0 10px 20px rgba(0,0,0,.18);}}
    .stButton>button:hover {{filter:brightness(1.06); transform: translateY(-1px);}}
    [data-baseweb="tab-list"] button[aria-selected="true"] {{border-bottom: 2px solid {accent} !important; color: {accent} !important;}}
    div[data-testid="stMetricValue"] {{color: {accent} !important;}}
    .style-note {{padding:10px 12px;border-radius:14px;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);}}
    </style>"""

def ensure_style_sample(style_name: str, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    fp = out_dir / f"{safe_filename(style_name)}.png"
    if fp.exists():
        return fp
    cfg = STYLE_COLORS.get(style_name, {})
    bg1 = cfg.get('bg1', '#111827'); bg2 = cfg.get('bg2', '#1f2937'); accent = cfg.get('accent', '#6d5efc'); secondary = cfg.get('secondary', '#4fd1ff'); text_color = cfg.get('text', '#ffffff')
    w, h = 960, 540
    img = Image.new('RGB', (w, h), hex_to_rgb(bg1))
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(1, h-1)
        draw.line((0, y, w, y), fill=hex_to_rgb(blend(bg1, bg2, t)), width=1)
    draw.ellipse((40, 40, 280, 280), fill=hex_to_rgb(blend(accent, '#ffffff', .10)))
    draw.rectangle((w-280, 40, w-60, 220), fill=hex_to_rgb(blend(secondary, '#111111', .35)))
    draw.rounded_rectangle((80, 300, w-80, h-70), radius=26, outline=hex_to_rgb(blend(accent, '#ffffff', .18)), width=4, fill=hex_to_rgb(blend(bg2, '#000000', .15)))
    font_big = ImageFont.load_default(); font_small = ImageFont.load_default()
    draw.text((80, 70), style_name, fill=hex_to_rgb(text_color), font=font_big)
    draw.text((80, 102), style_palette_text(style_name), fill=hex_to_rgb(text_color), font=font_small)
    draw.text((100, 330), 'Sample cover / moodboard / thumbnail preview', fill=hex_to_rgb(text_color), font=font_small)
    draw.text((100, 360), STYLE_PRESETS.get(style_name, style_name)[:90], fill=hex_to_rgb(text_color), font=font_small)
    draw.text((100, 410), 'Use as visual reference for consistent style direction', fill=hex_to_rgb(blend(text_color, '#888888', .18)), font=font_small)
    img.save(fp)
    return fp

def compute_style_consistency(project_style_cfg: dict, global_style: str, global_secondary_style: str | None = None, global_tertiary_style: str | None = None) -> tuple[int, list[dict]]:
    global_secondary_style = normalize_secondary_style(global_secondary_style)
    global_tertiary_style = normalize_secondary_style(global_tertiary_style)
    flow_settings = st.session_state.get('flow_quick_settings', {})
    flow_style = flow_settings.get('style_preset')
    flow_secondary = normalize_secondary_style(flow_settings.get('secondary_style'))
    flow_tertiary = normalize_secondary_style(flow_settings.get('tertiary_style'))
    thumb_style = st.session_state.get('thumb_style_preset')
    thumb_secondary = normalize_secondary_style(st.session_state.get('thumb_secondary_style_preset'))
    thumb_tertiary = normalize_secondary_style(st.session_state.get('thumb_tertiary_style_preset'))
    product_data = st.session_state.get('viral_product_prompt_data') or {}
    product_style = None
    product_secondary = None
    product_tertiary = None
    if isinstance(product_data, dict):
        concept = product_data.get('concept', {})
        product_style = concept.get('image_style_preset')
        product_secondary = normalize_secondary_style(concept.get('image_secondary_style'))
        product_tertiary = normalize_secondary_style(concept.get('image_tertiary_style'))
    ref_count = len(list_style_references(project_dir(st.session_state.get('current_project_name', 'default')))) if 'current_project_name' in st.session_state else 0
    checks = [
        {'name':'Global primary style', 'actual': global_style, 'expected': global_style, 'ok': True, 'weight': 10},
        {'name':'Global secondary style', 'actual': global_secondary_style or '(none)', 'expected': global_secondary_style or '(none)', 'ok': True, 'weight': 7},
        {'name':'Global third style', 'actual': global_tertiary_style or '(none)', 'expected': global_tertiary_style or '(none)', 'ok': True, 'weight': 6},
        {'name':'Project lock style', 'actual': blended_style_label(project_style_cfg.get('selected_style', '(none)'), project_style_cfg.get('secondary_style'), project_style_cfg.get('tertiary_style')), 'expected': blended_style_label(global_style, global_secondary_style, global_tertiary_style), 'ok': (not project_style_cfg.get('locked')) or (project_style_cfg.get('selected_style') == global_style and normalize_secondary_style(project_style_cfg.get('secondary_style')) == global_secondary_style and normalize_secondary_style(project_style_cfg.get('tertiary_style')) == global_tertiary_style), 'weight': 17},
        {'name':'Flow Assisted style', 'actual': blended_style_label(flow_style or '(chưa đặt)', flow_secondary, flow_tertiary), 'expected': blended_style_label(global_style, global_secondary_style, global_tertiary_style), 'ok': flow_style == global_style and flow_secondary == global_secondary_style and flow_tertiary == global_tertiary_style, 'weight': 20},
        {'name':'Thumbnail Lab style', 'actual': blended_style_label(thumb_style or '(chưa đặt)', thumb_secondary, thumb_tertiary), 'expected': blended_style_label(global_style, global_secondary_style, global_tertiary_style), 'ok': thumb_style == global_style and thumb_secondary == global_secondary_style and thumb_tertiary == global_tertiary_style, 'weight': 15},
        {'name':'Product Prompt style', 'actual': blended_style_label(product_style or '(chưa tạo)', product_secondary, product_tertiary), 'expected': blended_style_label(global_style, global_secondary_style, global_tertiary_style), 'ok': product_style == global_style and product_secondary == global_secondary_style and product_tertiary == global_tertiary_style, 'weight': 15},
        {'name':'Project style references', 'actual': f'{ref_count} file(s)', 'expected': '>=1 file khuyến nghị', 'ok': ref_count >= 1, 'weight': 10},
    ]
    score = sum(item['weight'] for item in checks if item['ok'])
    return score, checks


def normalize_secondary_style(style_name: str | None):
    if not style_name or str(style_name).strip() in {"", "(None)", "None"}:
        return None
    return style_name

def blended_style_label(primary_style: str, secondary_style: str | None = None) -> str:
    secondary_style = normalize_secondary_style(secondary_style)
    return primary_style if not secondary_style else f"{primary_style} + {secondary_style}"

def blended_style_description(primary_style: str, secondary_style: str | None = None) -> str:
    primary_desc = STYLE_PRESETS.get(primary_style, primary_style)
    secondary_style = normalize_secondary_style(secondary_style)
    if not secondary_style:
        return primary_desc
    secondary_desc = STYLE_PRESETS.get(secondary_style, secondary_style)
    return f"Blend two styles consistently. Primary style: {primary_style} — {primary_desc}. Secondary style: {secondary_style} — {secondary_desc}. Keep the final result balanced, coherent, premium, and visually intentional."

def blended_style_palette(primary_style: str, secondary_style: str | None = None) -> str:
    primary_palette = style_palette_text(primary_style)
    secondary_style = normalize_secondary_style(secondary_style)
    if not secondary_style:
        return primary_palette
    return f"{primary_palette} + {style_palette_text(secondary_style)}"

def style_reference_dir(pdir: Path) -> Path:
    return pdir / "style_references"

def list_style_references(pdir: Path) -> list[Path]:
    ref_dir = style_reference_dir(pdir)
    ref_dir.mkdir(parents=True, exist_ok=True)
    return sorted([p for p in ref_dir.iterdir() if p.is_file()])

def save_style_reference_files(pdir: Path, uploaded_files) -> list[str]:
    ref_dir = style_reference_dir(pdir)
    ref_dir.mkdir(parents=True, exist_ok=True)
    saved = []
    for f in uploaded_files or []:
        name = safe_filename(getattr(f, "name", "style_ref.png"))
        path = ref_dir / name
        f.seek(0)
        path.write_bytes(f.read())
        f.seek(0)
        saved.append(str(path))
    return saved

def style_reference_summary(pdir: Path) -> str:
    refs = list_style_references(pdir)
    if not refs:
        return "No project style reference images were provided."
    names = ", ".join(p.name for p in refs[:5])
    more = "" if len(refs) <= 5 else f", and {len(refs)-5} more"
    return f"Project style reference images are available: {names}{more}. Use them as supporting visual inspiration for color, mood, texture and overall style language."

def style_memory_path(pdir: Path) -> Path:
    return pdir / "style_memory.json"

def load_style_memory(pdir: Path) -> dict:
    fp = style_memory_path(pdir)
    if fp.exists():
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                data.setdefault("last_series", "default")
                data.setdefault("series", {})
                return data
        except Exception:
            pass
    return {"last_series": "default", "series": {}}

def save_style_memory(pdir: Path, data: dict) -> Path:
    fp = style_memory_path(pdir)
    fp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return fp

def suggest_style_combo(product_name: str, product_type: str, product_mood: str, target: str) -> dict:
    raw = f"{product_name} {product_type} {target}".lower()
    mood = (product_mood or "").lower()
    primary = "Realistic Commercial"
    secondary = None
    reason = "Phù hợp an toàn cho quảng cáo sản phẩm chân thực, dễ bán và dễ giữ sự rõ ràng."

    if any(k in raw for k in ["serum", "skincare", "mỹ phẩm", "cosmetic", "beauty", "son", "kem", "perfume", "nước hoa"]):
        primary, secondary = "Luxury Premium", "Minimal Clean"
        reason = "Mỹ phẩm và làm đẹp thường hợp phong cách sang trọng + sạch để tạo cảm giác cao cấp, tin cậy."
    elif any(k in raw for k in ["app", "software", "ai", "tool", "ứng dụng", "công nghệ", "phone", "laptop", "smart", "gadget"]):
        primary, secondary = "Futuristic Tech", "Realistic Commercial"
        reason = "Nhóm công nghệ phù hợp ánh sáng hiện đại, sắc xanh tương lai và bố cục quảng cáo rõ ràng."
    elif any(k in raw for k in ["snack", "food", "đồ ăn", "thức ăn", "drink", "đồ uống", "cafe", "trà", "tea", "coffee"]):
        primary, secondary = "Cute Pastel", "Realistic Commercial"
        reason = "Đồ ăn/đồ uống hợp phong cách tươi vui, thân thiện, dễ tạo cảm giác ngon mắt và gần gũi."
    elif any(k in raw for k in ["fashion", "thời trang", "áo", "quần", "giày", "shoe", "bag", "túi", "phụ kiện", "accessory"]):
        primary, secondary = "Street Hype", "Luxury Premium"
        reason = "Thời trang/phụ kiện hợp nhịp trẻ, trendy, có thể pha chút cao cấp để tăng cảm giác đắt tiền."
    elif any(k in raw for k in ["home", "gia dụng", "kitchen", "nhà bếp", "decor", "nội thất"]):
        primary, secondary = "Minimal Clean", "Realistic Commercial"
        reason = "Sản phẩm gia dụng cần gọn, sáng, sạch và thực tế để tăng độ tin tưởng."
    elif any(k in raw for k in ["game", "gaming", "cyber", "rgb", "neon"]):
        primary, secondary = "Cyberpunk", "Futuristic Tech"
        reason = "Nhóm neon/game rất hợp phong cách cyberpunk pha công nghệ để nổi bật mạnh."
    elif any(k in raw for k in ["premium", "luxury", "cao cấp", "sang trọng"]):
        primary, secondary = "Luxury Premium", "Cinematic Dark"
        reason = "Từ khóa sang trọng/cao cấp phù hợp phong cách luxury pha cinematic để tăng chiều sâu cảm xúc."

    if "hài" in mood or "hài hước" in mood:
        if primary != "Cute Pastel":
            secondary = "Cute Pastel"
            reason += " Mood hài hước nên thêm chất vui, mềm và thân thiện."
    elif "truyền cảm hứng" in mood:
        secondary = "Cinematic Dark" if primary != "Cinematic Dark" else secondary
        reason += " Mood truyền cảm hứng hợp thêm cinematic để tăng cảm xúc."
    elif "năng động" in mood:
        if primary not in {"Street Hype", "Cyberpunk", "Futuristic Tech"}:
            secondary = "Street Hype"
            reason += " Mood năng động nên pha thêm nhịp visual trẻ, mạnh và nhiều năng lượng."

    return {
        "primary_style": primary,
        "secondary_style": secondary,
        "reason": reason,
        "style_wording": blended_style_description(primary, secondary),
        "palette": blended_style_palette(primary, secondary),
    }


def analyze_reference_images(paths: list[Path]) -> dict:
    """Local lightweight vision analysis for uploaded style references."""
    stats = {
        "count": 0, "avg_brightness": None, "avg_saturation": None,
        "dominant_hint": "neutral", "neon_hint": False, "luxury_hint": False,
        "minimal_hint": False, "pastel_hint": False, "dark_hint": False,
        "notes": []
    }
    vals_b, vals_s, color_votes = [], [], []
    for p in paths or []:
        try:
            img = Image.open(p).convert("RGB").resize((64, 64))
            pixels = list(img.getdata())
            if not pixels:
                continue
            br = sum((r + g + b) / 3 for r, g, b in pixels) / len(pixels)
            sat = sum((max(r, g, b) - min(r, g, b)) for r, g, b in pixels) / len(pixels)
            vals_b.append(br); vals_s.append(sat)
            # crude dominant vote
            avg_r = sum(r for r, g, b in pixels) / len(pixels)
            avg_g = sum(g for r, g, b in pixels) / len(pixels)
            avg_b = sum(b for r, g, b in pixels) / len(pixels)
            if avg_r > avg_g * 1.12 and avg_r > avg_b * 1.12:
                color_votes.append("warm/red")
            elif avg_b > avg_r * 1.12 and avg_b > avg_g * 1.05:
                color_votes.append("blue/cyan")
            elif avg_g > avg_r * 1.05 and avg_g > avg_b * 1.05:
                color_votes.append("green")
            elif br > 205:
                color_votes.append("bright/clean")
            elif br < 75:
                color_votes.append("dark")
            else:
                color_votes.append("neutral")
        except Exception:
            continue
    if vals_b:
        stats["count"] = len(vals_b)
        stats["avg_brightness"] = round(sum(vals_b) / len(vals_b), 1)
        stats["avg_saturation"] = round(sum(vals_s) / len(vals_s), 1)
        votes = {v: color_votes.count(v) for v in set(color_votes)}
        stats["dominant_hint"] = max(votes, key=votes.get) if votes else "neutral"
        stats["neon_hint"] = stats["avg_saturation"] > 75 and stats["avg_brightness"] < 140
        stats["luxury_hint"] = stats["dominant_hint"] in {"warm/red", "dark"} and stats["avg_brightness"] < 165
        stats["minimal_hint"] = stats["avg_brightness"] > 190 and stats["avg_saturation"] < 55
        stats["pastel_hint"] = stats["avg_brightness"] > 165 and 35 <= stats["avg_saturation"] <= 85
        stats["dark_hint"] = stats["avg_brightness"] < 95
        stats["notes"].append(f"Analyzed {stats['count']} style reference image(s).")
        stats["notes"].append(f"Brightness {stats['avg_brightness']}, saturation {stats['avg_saturation']}, dominant hint {stats['dominant_hint']}.")
    else:
        stats["notes"].append("No readable style reference images found.")
    return stats

def ranked_style_suggestions(product_name: str, product_type: str, product_mood: str, target: str, ref_analysis: dict | None = None) -> list[dict]:
    """Rank all style presets for product + mood + local reference image analysis."""
    raw = f"{product_name} {product_type} {target}".lower()
    mood = (product_mood or "").lower()
    ref_analysis = ref_analysis or {}
    ranked = []
    for style in STYLE_PRESETS.keys():
        score = 45
        reasons = []
        if style == "Realistic Commercial":
            score += 14; reasons.append("an toàn cho quảng cáo sản phẩm chân thực")
        if any(k in raw for k in ["serum","skincare","mỹ phẩm","cosmetic","beauty","son","kem","perfume","nước hoa"]):
            if style in {"Luxury Premium","Minimal Clean","Realistic Commercial"}:
                score += 24; reasons.append("hợp mỹ phẩm/làm đẹp")
        if any(k in raw for k in ["app","software","ai","tool","ứng dụng","công nghệ","phone","laptop","smart","gadget"]):
            if style in {"Futuristic Tech","Realistic Commercial","Cyberpunk"}:
                score += 22; reasons.append("hợp công nghệ/app/tool")
        if any(k in raw for k in ["snack","food","đồ ăn","drink","đồ uống","cafe","trà","tea","coffee"]):
            if style in {"Cute Pastel","Realistic Commercial","Minimal Clean"}:
                score += 20; reasons.append("hợp đồ ăn/đồ uống")
        if any(k in raw for k in ["fashion","thời trang","áo","quần","giày","shoe","bag","túi","phụ kiện","accessory"]):
            if style in {"Street Hype","Luxury Premium","Cinematic Dark"}:
                score += 22; reasons.append("hợp thời trang/phụ kiện")
        if any(k in raw for k in ["home","gia dụng","kitchen","nhà bếp","decor","nội thất"]):
            if style in {"Minimal Clean","Realistic Commercial","Luxury Premium"}:
                score += 18; reasons.append("hợp gia dụng/nội thất")
        if any(k in raw for k in ["game","gaming","cyber","rgb","neon"]):
            if style in {"Cyberpunk","Futuristic Tech","Street Hype"}:
                score += 26; reasons.append("hợp gaming/neon")
        if any(k in raw for k in ["premium","luxury","cao cấp","sang trọng"]):
            if style in {"Luxury Premium","Cinematic Dark","Minimal Clean"}:
                score += 18; reasons.append("hợp định vị cao cấp")
        if "hài" in mood and style in {"Cute Pastel","Street Hype"}:
            score += 12; reasons.append("hợp mood hài hước")
        if "truyền cảm hứng" in mood and style in {"Cinematic Dark","Luxury Premium","Realistic Commercial"}:
            score += 12; reasons.append("hợp mood truyền cảm hứng")
        if "năng động" in mood and style in {"Street Hype","Cyberpunk","Futuristic Tech"}:
            score += 12; reasons.append("hợp mood năng động")
        # Style reference image signals
        if ref_analysis.get("neon_hint") and style in {"Cyberpunk","Futuristic Tech"}:
            score += 18; reasons.append("ảnh reference có tín hiệu neon/đậm màu")
        if ref_analysis.get("minimal_hint") and style in {"Minimal Clean","Realistic Commercial"}:
            score += 18; reasons.append("ảnh reference sáng/sạch/tối giản")
        if ref_analysis.get("pastel_hint") and style in {"Cute Pastel","Minimal Clean"}:
            score += 16; reasons.append("ảnh reference có vibe sáng mềm/pastel")
        if ref_analysis.get("dark_hint") and style in {"Cinematic Dark","Cyberpunk","Luxury Premium"}:
            score += 14; reasons.append("ảnh reference tối/dramatic")
        if ref_analysis.get("luxury_hint") and style in {"Luxury Premium","Cinematic Dark"}:
            score += 14; reasons.append("ảnh reference gợi cảm giác sang/dramatic")
        ranked.append({
            "style": style,
            "score": min(100, int(score)),
            "palette": style_palette_text(style),
            "prompt_wording": STYLE_PRESETS.get(style, style),
            "reasons": "; ".join(reasons) if reasons else "phù hợp mức trung bình",
        })
    return sorted(ranked, key=lambda x: x["score"], reverse=True)

def suggest_style_combo_v32(product_name: str, product_type: str, product_mood: str, target: str, pdir: Path) -> dict:
    refs = list_style_references(pdir)
    ref_analysis = analyze_reference_images(refs)
    ranking = ranked_style_suggestions(product_name, product_type, product_mood, target, ref_analysis)
    primary = ranking[0]["style"] if ranking else "Realistic Commercial"
    secondary = ranking[1]["style"] if len(ranking) > 1 else None
    tertiary = ranking[2]["style"] if len(ranking) > 2 else None
    return {
        "primary_style": primary,
        "secondary_style": secondary,
        "tertiary_style": tertiary,
        "ranking": ranking,
        "reference_analysis": ref_analysis,
        "reason": "Gợi ý dựa trên sản phẩm, mood, target và phân tích màu/ánh sáng từ style reference upload.",
        "style_wording": blended_style_description(primary, secondary, tertiary),
        "palette": blended_style_palette(primary, secondary, tertiary),
    }

def blended_style_label(primary_style: str, secondary_style: str | None = None, tertiary_style: str | None = None) -> str:
    styles = [primary_style]
    for s in [secondary_style, tertiary_style]:
        s = normalize_secondary_style(s)
        if s and s not in styles:
            styles.append(s)
    return " + ".join(styles)

def blended_style_description(primary_style: str, secondary_style: str | None = None, tertiary_style: str | None = None) -> str:
    styles = []
    for s in [primary_style, secondary_style, tertiary_style]:
        s = normalize_secondary_style(s)
        if s and s not in styles:
            styles.append(s)
    if len(styles) == 1:
        return STYLE_PRESETS.get(styles[0], styles[0])
    parts = [f"{s} — {STYLE_PRESETS.get(s, s)}" for s in styles]
    return "Blend these styles consistently. " + " | ".join(parts) + ". Keep a coherent premium result; primary style remains dominant while other styles add accents."

def blended_style_palette(primary_style: str, secondary_style: str | None = None, tertiary_style: str | None = None) -> str:
    styles = []
    for s in [primary_style, secondary_style, tertiary_style]:
        s = normalize_secondary_style(s)
        if s and s not in styles:
            styles.append(s)
    return " + ".join(style_palette_text(s) for s in styles)


def prompt_bank_dir(pdir: Path) -> Path:
    folder = pdir / "prompt_bank"
    folder.mkdir(parents=True, exist_ok=True)
    return folder

def save_prompt_bank_text(pdir: Path, name: str, content: str, source: str = "manual") -> str:
    folder = prompt_bank_dir(pdir)
    safe = safe_filename(name or f"{source}_prompt.txt")
    if not safe.lower().endswith(".txt"):
        safe += ".txt"
    path = folder / safe
    path.write_text(content or "", encoding="utf-8")
    return str(path)

def list_prompt_bank_files(pdir: Path) -> list[Path]:
    folder = prompt_bank_dir(pdir)
    return sorted([p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in {".txt", ".md", ".json"}])

def read_prompt_bank_summary(pdir: Path, max_chars: int = 5000) -> str:
    files = list_prompt_bank_files(pdir)
    if not files:
        return "No prompt bank files saved yet."
    parts = []
    each = max(600, max_chars // max(1, min(len(files), 8)))
    for fp in files[:8]:
        try:
            txt = fp.read_text(encoding="utf-8", errors="ignore")[:each]
            parts.append(f"FILE: {fp.name}\n{txt}")
        except Exception:
            pass
    return "\n\n---\n\n".join(parts)[:max_chars]

def build_prompt_sync_context(pdir: Path) -> str:
    return (
        "PROMPT SYNC CONTEXT:\n"
        "Use the user's local prompt bank and style memory as guidance.\n\n"
        "Style memory:\n"
        + json.dumps(load_style_memory(pdir), ensure_ascii=False, indent=2)[:2500]
        + "\n\nPrompt bank:\n"
        + read_prompt_bank_summary(pdir, 5000)
        + "\n\nStyle references:\n"
        + style_reference_summary(pdir)
    )

def call_gemini_prompt_sync(user_task: str, context: str, api_key: str = "") -> tuple[bool, str]:
    """Optional Gemini API call using official API key. No cookies/browser automation."""
    api_key = (api_key or "").strip()
    if not api_key:
        return False, "Chưa có GEMINI_API_KEY. Hãy dán API key vào sidebar hoặc dùng Prompt Bank local."
    try:
        import urllib.request
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        payload = {
            "contents": [{
                "parts": [{
                    "text": context + "\n\nTASK:\n" + user_task + "\n\nReturn concise Vietnamese output with reusable Flow/Veo prompt blocks."
                }]
            }]
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=45) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
        parts = raw.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        txt = "\n".join(p.get("text", "") for p in parts).strip()
        return True, txt or "Gemini không trả về nội dung."
    except Exception as e:
        return False, str(e)


def series_prompt_pack(series_name: str, primary_style: str, secondary_style: str | None, tertiary_style: str | None, product_context: str = "") -> dict:
    label = blended_style_label(primary_style, secondary_style, tertiary_style)
    desc = blended_style_description(primary_style, secondary_style, tertiary_style)
    palette = blended_style_palette(primary_style, secondary_style, tertiary_style)
    base = product_context.strip() or "sản phẩm / nội dung của series"
    return {
        "series_name": series_name or "default",
        "style_label": label,
        "palette": palette,
        "prompt_templates": [
            {
                "name": "Product Hero 8s",
                "prompt": f"Create an 8-second product hero video for {base}. Visual style: {label}. {desc}. Preferred palette: {palette}. Keep the subject consistent, premium, realistic, high-retention, no text overlay, no watermark."
            },
            {
                "name": "Faceless Viral Hook",
                "prompt": f"Create a faceless viral short video hook for {base}. Use style blend: {label}. {desc}. Fast pacing, strong first 2 seconds, cinematic B-roll, clear product focus, no readable text."
            },
            {
                "name": "Thumbnail Image",
                "prompt": f"Create a scroll-stopping thumbnail for {base}. Style: {label}. Palette: {palette}. Clean high contrast composition, one clear focal subject, no clutter, no misspelled text."
            },
            {
                "name": "Lifestyle Usage Demo",
                "prompt": f"Create a realistic lifestyle usage demo for {base}. Style: {label}. {desc}. Natural human interaction, smooth camera motion, premium light, authentic usage, no captions."
            },
        ]
    }

def estimate_thumb_credits(model: str, variants: str) -> int:
    base = THUMB_FLOW_MODEL_CREDITS.get(model, 4)
    try:
        mult = int(str(variants).replace("x", ""))
    except Exception:
        mult = 1
    return max(1, base * max(1, mult))

def build_thumbnail_flow_prompt(title: str, aspect: str, model: str, media_mode: str, style: str, style_preset: str, secondary_style_preset: str | None, tertiary_style_preset: str | None, no_text: bool, product_ref: bool, ref_summary: str = "") -> str:
    title = title.strip() or "viral thumbnail"
    style_desc = blended_style_description(style_preset, secondary_style_preset, tertiary_style_preset)
    style_label = blended_style_label(style_preset, secondary_style_preset, tertiary_style_preset)
    palette_desc = blended_style_palette(style_preset, secondary_style_preset, tertiary_style_preset)
    text_rule = (
        "No readable text, no letters, no typography, no logo, no watermark. Create a clean visual thumbnail without text."
        if no_text else
        "If text is needed, keep it extremely short, bold, clean, and readable. Avoid misspelled text."
    )
    ref_rule = (
        "Use the uploaded product/reference image as the main visual reference. Preserve the product identity, shape, color, material and proportions."
        if product_ref else
        "Create a strong standalone thumbnail concept."
    )
    return f"""Create a high-performing {media_mode.lower()} thumbnail concept for Flow image generation.

Main idea:
{title}

Format:
Aspect ratio: {aspect}
Target model: {model}
Local template family: {style}
Image style preset: {style_label}

Visual direction:
Make it bold, high contrast, scroll-stopping, clean composition, premium lighting, strong focal point, social-media friendly.
Apply this image style: {style_desc}.
Preferred color palette: {palette_desc}.
{ref_rule}
{ref_summary}

Rules:
{text_rule}
No clutter, no busy background, no distorted hands or faces, no low-quality artifacts.

Output should look like a polished viral thumbnail ready for TikTok/Reels/Shorts or product promotion."""


import json
import streamlit as st
import streamlit.components.v1 as components
from src.project import project_dir, list_projects, export_zip, backup_project, storage_report, read_errors, log_error, now
from src.viral import NICHES, FORMATS, make_blueprint, export_blueprint_zip
from src.flow import inbox_dir, scan_inbox, save_uploads, merge_clips, missing_scenes, normalize_names, write_prompt_txt
from src.media import concat_videos, concat_videos_studio, make_srt, thumbnail_from_video, mix_audio_subtitles, publish_package, ffmpeg_path
from src.tts import VOICE_PRESETS, tts_edge
from src.thumbnails import TEMPLATES, make_thumbnail
from src.product_prompt import PRODUCT_MOODS, PRODUCT_TYPES, build_product_prompts, export_product_prompt_package
APP_VERSION='3.5.1 Final Checked Stable'
FLOW_URL='https://labs.google/fx/tools/flow'
FLOW_MODEL_CREDITS={'Veo 3.1 - Lite':8,'Veo 3.1 - Fast':10,'Veo 3.1 - Quality':15,'Veo 3.1 - Lite [Lower Priority]':6,'Veo 3.1 - Fast [Lower Priority]':8}
def estimate_flow_credits(settings):
    base=FLOW_MODEL_CREDITS.get(settings.get('model'),10); factor={4:.65,6:.82,8:1.0}.get(int(settings.get('duration',8)),1.0); variants=int(str(settings.get('variants','1x')).replace('x','') or 1)
    return max(1,int(round(base*factor*variants)))
def flow_settings_suffix(settings):
    action=settings.get('action_mode','Generate'); source=settings.get('source_mode','Text')
    style_name=settings.get('style_preset','Realistic Commercial')
    secondary_style=normalize_secondary_style(settings.get('secondary_style'))
    tertiary_style=normalize_secondary_style(settings.get('tertiary_style'))
    style_desc=blended_style_description(style_name, secondary_style, tertiary_style)
    style_label=blended_style_label(style_name, secondary_style, tertiary_style)
    parts=[f"Flow mode: {settings.get('media_mode','Video')}.",f"Source: {source}.",f"Action: {action}.",f"Aspect ratio: {settings.get('aspect_ratio','9:16')}.",f"Model target: {settings.get('model','Veo 3.1 - Fast')}.",f"Duration: {settings.get('duration',8)}s.",f"Generate variants: {settings.get('variants','1x')}.",f"Image style preset: {style_label}.",f"Style direction: {style_desc}.",f"Preferred color palette: {blended_style_palette(style_name, secondary_style, tertiary_style)}.", style_reference_summary(project_dir(st.session_state.get('current_project_name', 'default')))]
    if action=='Extend': parts.append('Continue the previous shot naturally, preserve identity, lighting, style and motion continuity.')
    elif action=='Insert': parts.append('Insert a new visual beat that matches the previous and next shot, seamless continuity.')
    elif action=='Remove': parts.append('Remove unwanted object/element cleanly while keeping background and motion natural.')
    elif action=='Camera': parts.append('Focus on camera movement and cinematic framing.')
    if source=='Frames': parts.append('Use start/end frame logic if images are provided in Flow.')
    elif source=='Ingredients': parts.append('Use reference ingredients/images to preserve character, product, object and style.')
    if settings.get('camera_note'): parts.append('Camera instruction: '+settings.get('camera_note'))
    parts.append('No watermark, no unreadable text, clean composition.')
    return ' '.join(parts)
st.set_page_config(page_title='AUTO VEO Studio v3.2',page_icon='🎬',layout='wide')
st.markdown('''<style>.block-container{padding-top:.85rem;max-width:1320px}.hero{padding:22px 26px;border-radius:26px;background:linear-gradient(135deg,rgba(90,80,255,.18),rgba(255,255,255,.035));border:1px solid rgba(255,255,255,.14);margin-bottom:18px}.hero h1{margin:0;font-size:2rem}.badge{display:inline-block;padding:6px 11px;border-radius:999px;background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.14);margin:5px 6px 0 0;font-size:.86rem}</style>''',unsafe_allow_html=True)

VIDEO_STATUS_META = {
    'Chưa làm': {'class': 'gray', 'label': '⚪ Chưa làm'},
    'Sẵn sàng copy': {'class': 'blue', 'label': '🔵 Sẵn sàng copy'},
    'Đang render': {'class': 'yellow', 'label': '🟡 Đang render'},
    'Đã có video': {'class': 'teal', 'label': '🟢 Đã có video'},
    'Lỗi': {'class': 'red', 'label': '🔴 Lỗi'},
    'Hoàn tất': {'class': 'green', 'label': '✅ Hoàn tất'},
}

def default_video_grid_rows(count: int = 10) -> list[dict]:
    return [{
        'scene': i,
        'title': f'Cảnh {i}',
        'status': 'Chưa làm',
        'done': False,
        'narration': '',
        'prompt': '',
        'note': '',
        'video_path': ''
    } for i in range(1, count + 1)]

def normalize_video_grid_rows(rows: list[dict] | None, count: int = 10) -> list[dict]:
    rows = rows or []
    by_scene = {}
    for r in rows:
        try:
            sc = int(r.get('scene') or 0)
        except Exception:
            sc = 0
        if sc > 0:
            by_scene[sc] = {
                'scene': sc,
                'title': r.get('title', f'Cảnh {sc}') or f'Cảnh {sc}',
                'status': r.get('status', 'Chưa làm') or 'Chưa làm',
                'done': bool(r.get('done', False)),
                'narration': r.get('narration', '') or '',
                'prompt': r.get('prompt', '') or '',
                'note': r.get('note', '') or '',
                'video_path': r.get('video_path', '') or '',
            }
    out = []
    for i in range(1, count + 1):
        out.append(by_scene.get(i, {
            'scene': i,
            'title': f'Cảnh {i}',
            'status': 'Chưa làm',
            'done': False,
            'narration': '',
            'prompt': '',
            'note': '',
            'video_path': '',
        }))
    return out

def video_grid_from_flow_rows(flow_rows: list[dict] | None, count: int = 10) -> list[dict]:
    flow_rows = flow_rows or []
    out = default_video_grid_rows(count)
    for i, r in enumerate(flow_rows[:count], start=1):
        out[i-1].update({
            'scene': i,
            'title': f'Cảnh {i}',
            'status': 'Sẵn sàng copy' if (r.get('prompt') or '').strip() else 'Chưa làm',
            'done': False,
            'narration': r.get('narration', '') or '',
            'prompt': r.get('prompt', '') or '',
            'note': r.get('note', '') or '',
        })
    return out

def flow_rows_from_video_grid(rows: list[dict]) -> list[dict]:
    rows = normalize_video_grid_rows(rows, len(rows) if rows else 10)
    out = []
    status_map = {
        'Chưa làm': 'Chưa làm',
        'Sẵn sàng copy': 'Đã copy prompt',
        'Đang render': 'Đang render Flow',
        'Đã có video': 'Đã tải video',
        'Lỗi': 'Lỗi cần làm lại',
        'Hoàn tất': 'Hoàn tất',
    }
    for r in rows:
        out.append({
            'scene': r['scene'],
            'status': status_map.get(r.get('status'), 'Chưa làm'),
            'narration': r.get('narration', ''),
            'prompt': r.get('prompt', ''),
            'note': r.get('note', ''),
        })
    return out

def video_grid_summary(rows: list[dict]) -> dict:
    rows = normalize_video_grid_rows(rows, len(rows) if rows else 10)
    done = sum(1 for r in rows if r.get('done'))
    prompts = sum(1 for r in rows if (r.get('prompt') or '').strip())
    videos = sum(1 for r in rows if (r.get('video_path') or '').strip())
    completed = sum(1 for r in rows if r.get('status') == 'Hoàn tất')
    errors = sum(1 for r in rows if r.get('status') == 'Lỗi')
    return {'done': done, 'prompts': prompts, 'videos': videos, 'completed': completed, 'errors': errors, 'total': len(rows)}

def video_status_chip(status: str, done: bool = False) -> str:
    meta = VIDEO_STATUS_META.get(status, VIDEO_STATUS_META['Chưa làm'])
    text = '✅ ' + meta['label'] if done and status != 'Hoàn tất' else meta['label']
    return f"<span class='video-chip {meta['class']}'>{text}</span>"

def video_grid_progress_ratio(rows: list[dict]) -> float:
    rows = normalize_video_grid_rows(rows, len(rows) if rows else 10)
    if not rows:
        return 0.0
    score = 0
    for r in rows:
        status = r.get('status')
        if r.get('done') or status == 'Hoàn tất':
            score += 100
        elif status == 'Đã có video':
            score += 75
        elif status == 'Đang render':
            score += 45
        elif status == 'Sẵn sàng copy':
            score += 25
        elif (r.get('prompt') or '').strip():
            score += 20
    return min(1.0, max(0.0, score / (len(rows) * 100)))

def filter_video_grid_rows(rows: list[dict], filter_name: str) -> list[dict]:
    rows = normalize_video_grid_rows(rows, len(rows) if rows else 10)
    if filter_name == 'Tất cả':
        return rows
    if filter_name == 'Chỉ ô lỗi':
        return [r for r in rows if r.get('status') == 'Lỗi']
    if filter_name == 'Chỉ ô chưa làm':
        return [r for r in rows if r.get('status') == 'Chưa làm' or not (r.get('prompt') or '').strip()]
    if filter_name == 'Chỉ ô hoàn tất':
        return [r for r in rows if r.get('status') == 'Hoàn tất' or r.get('done')]
    if filter_name == 'Chưa hoàn tất':
        return [r for r in rows if not r.get('done') and r.get('status') != 'Hoàn tất']
    if filter_name == 'Đã có video':
        return [r for r in rows if r.get('status') == 'Đã có video' or (r.get('video_path') or '').strip()]
    return rows

def reorder_video_grid_rows(rows: list[dict], order_rows: list[dict]) -> list[dict]:
    rows = normalize_video_grid_rows(rows, len(rows) if rows else 10)
    by_scene = {int(r['scene']): r for r in rows}
    ordered = []
    for item in order_rows or []:
        try:
            scene = int(item.get('scene') or 0)
            order = int(item.get('order') or 999)
        except Exception:
            continue
        if scene in by_scene:
            ordered.append((order, scene, by_scene[scene]))
    ordered = [x[2] for x in sorted(ordered, key=lambda x: (x[0], x[1]))]
    # Renumber visual scene order to 1..N while preserving title/prompt/video
    out = []
    for i, r in enumerate(ordered, start=1):
        nr = dict(r)
        nr['scene'] = i
        if not nr.get('title') or nr.get('title', '').startswith('Cảnh '):
            nr['title'] = f'Cảnh {i}'
        out.append(nr)
    return normalize_video_grid_rows(out, len(rows))

def copy_prompt_component(prompt: str, key: str, height: int = 58):
    safe_prompt = json.dumps(prompt or "", ensure_ascii=False)
    components.html(f"""
    <div style="display:flex;gap:8px;align-items:center;margin:4px 0 8px 0;">
      <button id="copy_{key}" style="padding:8px 12px;border-radius:12px;border:0;background:#2563eb;color:white;font-weight:700;cursor:pointer;">📋 Copy Prompt</button>
      <span id="msg_{key}" style="font-size:12px;opacity:.8;"></span>
    </div>
    <script>
      const promptText_{key} = {safe_prompt};
      const btn_{key} = document.getElementById("copy_{key}");
      const msg_{key} = document.getElementById("msg_{key}");
      btn_{key}.onclick = async () => {{
        try {{
          await navigator.clipboard.writeText(promptText_{key});
          msg_{key}.innerText = "Đã copy";
        }} catch(e) {{
          msg_{key}.innerText = "Không copy tự động được, hãy copy trong ô Prompt.";
        }}
      }};
    </script>
    """, height=height)

def flow_open_component(url: str, key: str, height: int = 54):
    components.html(f"""
    <a href="{url}" target="_blank" style="display:inline-block;padding:8px 12px;border-radius:12px;background:#111827;color:white;text-decoration:none;font-weight:700;margin:4px 0 8px 0;">🌊 Mở Flow</a>
    """, height=height)


for k,v in {'viral_blueprint':None,'flow_rows':[],'flow_clips':[],'flow_quick_settings':{},'viral_product_prompt_data':None,'video_grid_rows':default_video_grid_rows(10)}.items():
    if k not in st.session_state: st.session_state[k]=v.copy() if isinstance(v,(list,dict)) else v
with st.sidebar:
    st.markdown('## 🎬 AUTO VEO Studio'); st.caption(APP_VERSION); compact=st.checkbox('Giao diện gọn',value=True); ui_mode=st.radio('Chế độ',['Simple','Advanced'],horizontal=True,index=0)
    st.divider(); st.markdown('### 📁 Project'); projects=list_projects(); selected=st.selectbox('Chọn project',projects,index=0); new_project=st.text_input('Tạo/chọn tên project mới',value='')
    if st.button('➕ Tạo/mở project',use_container_width=True):
        if new_project.strip(): selected=new_project.strip(); project_dir(selected); st.success('Đã tạo/mở project.'); st.rerun()
    project_name=selected; pdir=project_dir(project_name); st.caption(f'Folder: `{pdir.name}`')
    st.divider(); st.markdown('### ⚙️ Runtime'); st.caption(f"FFmpeg: {'OK' if ffmpeg_path() else 'Chưa thấy'}")
    if not ffmpeg_path(): st.warning('Cần FFmpeg để nối video/ghép subtitle/audio.'); st.code('Windows: winget install Gyan.FFmpeg\nMac: brew install ffmpeg')
    st.divider(); default_thumb_template=st.selectbox('Template thumbnail',list(TEMPLATES.keys()),index=0)
    style_names=list(STYLE_PRESETS.keys())
    secondary_options=['(None)'] + style_names
    project_style_cfg=load_project_style(pdir)
    st.session_state['current_project_name'] = project_name
    locked_style=bool(project_style_cfg.get('locked', False))
    saved_style=project_style_cfg.get('selected_style', 'Realistic Commercial') if project_style_cfg.get('selected_style', 'Realistic Commercial') in style_names else 'Realistic Commercial'
    saved_secondary=project_style_cfg.get('secondary_style', '(None)')
    saved_secondary = saved_secondary if saved_secondary in secondary_options else '(None)'
    global_style_preset=st.selectbox('🎨 Global style preset', style_names, index=style_names.index(saved_style) if saved_style in style_names else 0, disabled=locked_style, key=f'global_style_{project_name}')
    global_secondary_style=st.selectbox('🎨 Secondary blend style', secondary_options, index=secondary_options.index(saved_secondary) if saved_secondary in secondary_options else 0, disabled=locked_style, key=f'global_secondary_style_{project_name}')
    saved_tertiary=project_style_cfg.get('tertiary_style', '(None)')
    saved_tertiary=saved_tertiary if saved_tertiary in secondary_options else '(None)'
    global_tertiary_style=st.selectbox('🎨 Third blend style', secondary_options, index=secondary_options.index(saved_tertiary) if saved_tertiary in secondary_options else 0, disabled=locked_style, key=f'global_tertiary_style_{project_name}')
    active_secondary_style=normalize_secondary_style(global_secondary_style)
    active_tertiary_style=normalize_secondary_style(global_tertiary_style)
    lock_project_style=st.checkbox('🔒 Lock style cho project này', value=locked_style, key=f'lock_style_{project_name}')
    if st.button('💾 Lưu style project', use_container_width=True):
        save_project_style(pdir, {'locked': lock_project_style, 'selected_style': global_style_preset, 'secondary_style': active_secondary_style, 'tertiary_style': active_tertiary_style, 'palette': blended_style_palette(global_style_preset, active_secondary_style, active_tertiary_style)})
        st.success('Đã lưu style cho project.')
        st.rerun()
    if locked_style:
        global_style_preset=saved_style
        active_secondary_style=normalize_secondary_style(saved_secondary)
        active_tertiary_style=normalize_secondary_style(saved_tertiary)
        st.info(f'Project này đang lock style: {blended_style_label(saved_style, active_secondary_style, active_tertiary_style)}')
    st.caption('Style này sẽ làm mặc định cho Product Prompt, Flow Assisted và Thumbnail Lab.')
    with st.expander('🎨 Style preview + màu mẫu', expanded=False):
        ensure_style_sample(global_style_preset, pdir / 'style_samples')
        st.markdown(style_preview_card(global_style_preset, selected=True), unsafe_allow_html=True)
        st.caption('Màu gợi ý: ' + blended_style_palette(global_style_preset, active_secondary_style, active_tertiary_style))
        if active_secondary_style:
            ensure_style_sample(active_secondary_style, pdir / 'style_samples')
            st.markdown(style_preview_card(active_secondary_style, selected=False), unsafe_allow_html=True)
        if active_tertiary_style:
            ensure_style_sample(active_tertiary_style, pdir / 'style_samples')
            st.markdown(style_preview_card(active_tertiary_style, selected=False), unsafe_allow_html=True)
        for _s in style_names:
            if _s not in {global_style_preset, active_secondary_style, active_tertiary_style}:
                st.markdown(style_preview_card(_s, selected=False), unsafe_allow_html=True)

    st.divider(); st.markdown('### 🖼️ Style reference upload')
    style_ref_uploads = st.file_uploader('Upload style reference riêng cho project', type=['png','jpg','jpeg','webp'], accept_multiple_files=True, key=f'style_ref_uploads_{project_name}')
    if st.button('📥 Lưu style references', use_container_width=True):
        saved_refs = save_style_reference_files(pdir, style_ref_uploads)
        st.success(f'Đã lưu {len(saved_refs)} style reference file.')
        st.rerun()
    existing_style_refs = list_style_references(pdir)
    st.caption(f'Style refs hiện có: {len(existing_style_refs)} file')
    if existing_style_refs:
        st.write(', '.join(p.name for p in existing_style_refs[:6]))

    st.divider(); st.markdown('### 🧠 Style memory cho project/video series')
    style_memory = load_style_memory(pdir)
    current_series_default = style_memory.get('last_series', 'default')
    current_series = st.text_input('Tên series / campaign', value=current_series_default, key=f'current_series_{project_name}')
    saved_series_names = ['(none)'] + sorted(style_memory.get('series', {}).keys())
    selected_series = st.selectbox('Series đã lưu', saved_series_names, key=f'selected_series_{project_name}')
    series_notes_default = style_memory.get('series', {}).get(current_series_default, {}).get('notes', '')
    series_notes = st.text_area('Ghi chú style memory', value=series_notes_default, height=70, key=f'series_notes_{project_name}')
    s1, s2 = st.columns(2)
    with s1:
        if st.button('💾 Lưu style vào series', use_container_width=True):
            style_memory['last_series'] = current_series
            style_memory.setdefault('series', {})
            style_memory['series'][current_series] = {
                'primary_style': global_style_preset,
                'secondary_style': active_secondary_style,
                'tertiary_style': active_tertiary_style,
                'locked': lock_project_style,
                'notes': series_notes,
                'updated_at': now(),
                'style_references': [p.name for p in existing_style_refs],
            }
            save_style_memory(pdir, style_memory)
            st.success('Đã lưu style memory cho series.')
            st.rerun()
    with s2:
        if st.button('📂 Load style từ series', use_container_width=True):
            if selected_series != '(none)' and selected_series in style_memory.get('series', {}):
                entry = style_memory['series'][selected_series]
                save_project_style(pdir, {
                    'locked': bool(entry.get('locked', False)),
                    'selected_style': entry.get('primary_style', 'Realistic Commercial'),
                    'secondary_style': normalize_secondary_style(entry.get('secondary_style')),
                    'tertiary_style': normalize_secondary_style(entry.get('tertiary_style')),
                    'palette': blended_style_palette(entry.get('primary_style', 'Realistic Commercial'), entry.get('secondary_style'), entry.get('tertiary_style')),
                })
                st.success(f'Đã load style từ series: {selected_series}')
                st.rerun()

    if st.button('🧾 Tự sinh prompt mẫu cho series', use_container_width=True):
        pack = series_prompt_pack(current_series, global_style_preset, active_secondary_style, active_tertiary_style, series_notes)
        out = pdir / 'series_prompt_pack.json'
        out.write_text(json.dumps(pack, ensure_ascii=False, indent=2), encoding='utf-8')
        st.download_button('⬇️ Tải series_prompt_pack.json', out.read_bytes(), out.name, mime='application/json', use_container_width=True)
    st.divider(); st.markdown('### 🔄 Prompt Sync')
    gemini_api_key_sidebar = st.text_input('Gemini API key optional', value='', type='password', help='Chỉ dùng nếu bạn muốn app gọi Gemini API chính thức. Không dùng cookie/browser automation.')
    st.caption('ChatGPT prompt sync: copy/paste prompt từ ChatGPT vào Prompt Bank. Gemini sync: dùng API key nếu có.')
    st.caption('Flow/Veo account: app không lấy cookie tài khoản Google Flow. Dùng Manual Flow hoặc API key chính thức khi có.')

st.markdown(style_theme_css(global_style_preset, active_secondary_style),unsafe_allow_html=True)

st.markdown("""
<style>
.block-container {padding-top: 0.9rem; padding-bottom: 1.2rem; max-width: 1450px;}
div[data-testid="stHorizontalBlock"] {gap: 0.8rem;}
.video-chip {display:inline-block; padding:4px 10px; border-radius:999px; font-size:12px; font-weight:700; margin-bottom:8px;}
.video-chip.gray {background:#e5e7eb; color:#111827;}
.video-chip.blue {background:#dbeafe; color:#1d4ed8;}
.video-chip.yellow {background:#fef3c7; color:#92400e;}
.video-chip.teal {background:#ccfbf1; color:#0f766e;}
.video-chip.red {background:#fee2e2; color:#b91c1c;}
.video-chip.green {background:#dcfce7; color:#166534;}
.video-card {border:1px solid rgba(255,255,255,.12); border-radius:18px; padding:12px; background:rgba(255,255,255,.03);}
.small-muted {opacity:.8; font-size:12px;}
.grid-progress-label {font-size:13px; font-weight:700; margin: 4px 0 8px 0;}
.reorder-box {padding:10px;border:1px dashed rgba(255,255,255,.18);border-radius:16px;background:rgba(255,255,255,.025);}
</style>
""", unsafe_allow_html=True)

st.markdown(f'''<div class="hero"><h1>🎬 AUTO VEO Studio v3.5.1 — Final Checked Stable</h1><p>Final Checked · Even Resolution · Stable FFmpeg · Flow Manual</p><span class="badge">📁 {project_name}</span><span class="badge">⚙️ Flow settings</span><span class="badge">💳 credit estimate</span><span class="badge">📱 giống Google Flow mobile</span></div>''',unsafe_allow_html=True)
SIMPLE_TABS=['🎯 Viral Director','🎞️ Video Grid','🌊 Flow Assisted','🏠 Project']; ADVANCED_TABS=SIMPLE_TABS+['🔄 Prompt Sync','🖼️ Thumbnail Lab','📊 Dashboard']; names=SIMPLE_TABS if ui_mode=='Simple' else ADVANCED_TABS; tabs=st.tabs(names)
def tab(name): return tabs[names.index(name)]
def has_tab(name): return name in names
with tab('🎯 Viral Director'):
    st.markdown('## 🎯 Viral Content Director')
    st.caption('Tạo idea/prompt tại đây, sau đó bấm gửi sang 10 ô Video Grid hoặc Flow Assisted.')
    st.markdown('### 🎨 Preview style đang dùng')
    st.markdown(style_preview_card(global_style_preset, selected=True), unsafe_allow_html=True)
    c1,c2=st.columns([1.05,.95])
    with c1:
        topic=st.text_area('Chủ đề/kênh/ngách muốn làm video',height=120,value='AI/marketing/kinh doanh cho Shorts/Reels'); platform=st.selectbox('Nền tảng',['TikTok/Reels 9:16','YouTube Shorts 9:16','YouTube ngang 16:9','Facebook Reels']); niche=st.selectbox('Ngách viral',list(NICHES.keys())); faceless=st.checkbox('Ưu tiên faceless',value=True)
    with c2:
        host=st.text_area('AI host cố định nếu cần',value='Nam 28 tuổi, smart casual, background studio hiện đại, tone xanh đen, nói nhanh – rõ – chuyên gia.',height=90); minutes=st.selectbox('Độ dài blueprint',[3,4,5],index=0); st.info('Có chấm điểm Viral Potential, Hook, Retention, Faceless Ease, Difficulty.')

    st.divider()
    st.markdown('### 🛍️ Upload ảnh sản phẩm ngay trong Viral Director')
    st.caption('Tạo concept + kịch bản 8s + 3 prompt Flow/Veo từ ảnh sản phẩm, rồi gửi sang Flow Assisted để copy prompt và build final.')

    pc1, pc2 = st.columns([1.05, .95])
    with pc1:
        viral_product_upload = st.file_uploader('Upload ảnh sản phẩm gốc', type=['png','jpg','jpeg','webp'], key='viral_product_upload')
        viral_product_name = st.text_input('Tên sản phẩm', value='sản phẩm trong ảnh gốc', key='viral_product_name')
        viral_product_type = st.selectbox('Loại sản phẩm', PRODUCT_TYPES, key='viral_product_type')
        viral_product_target = st.text_area('Khách hàng mục tiêu', value='người xem mạng xã hội thích sản phẩm đẹp, chân thực, dễ dùng và đáng tin', height=80, key='viral_product_target')
    with pc2:
        viral_product_mood = st.selectbox('Mood nhạc / cảm xúc', list(PRODUCT_MOODS.keys()), index=0, key='viral_product_mood')
        viral_product_style_preset = st.selectbox('Phong cách hình ảnh sản phẩm', list(STYLE_PRESETS.keys()), index=list(STYLE_PRESETS.keys()).index(global_style_preset) if global_style_preset in list(STYLE_PRESETS.keys()) else 0, key='viral_product_style_preset')
        viral_product_secondary_style = st.selectbox('Blend phong cách phụ', ['(None)'] + list(STYLE_PRESETS.keys()), index=(['(None)'] + list(STYLE_PRESETS.keys())).index(active_secondary_style) if active_secondary_style in (['(None)'] + list(STYLE_PRESETS.keys())) else 0, key='viral_product_secondary_style')
        viral_product_tertiary_style = st.selectbox('Blend phong cách thứ 3', ['(None)'] + list(STYLE_PRESETS.keys()), index=(['(None)'] + list(STYLE_PRESETS.keys())).index(active_tertiary_style) if active_tertiary_style in (['(None)'] + list(STYLE_PRESETS.keys())) else 0, key='viral_product_tertiary_style')
        viral_product_objective = st.text_area('Mục tiêu video sản phẩm', value='Hiệu suất cao, giữ chân người xem, tăng thời gian xem, tăng tương tác và khiến người xem muốn thử sản phẩm.', height=80, key='viral_product_objective')
        viral_product_model = st.checkbox('Có người mẫu sử dụng sản phẩm', value=True, key='viral_product_model')
        viral_product_clean_text = st.checkbox('Xoá sạch chữ trên sản phẩm / cấm text overlay', value=True, key='viral_product_clean_text')

    viral_product_image_path = None
    if viral_product_upload:
        product_ref_dir = pdir / 'product_refs'
        product_ref_dir.mkdir(parents=True, exist_ok=True)
        safe_product_file = safe_filename(viral_product_upload.name)
        viral_product_image_path = product_ref_dir / safe_product_file
        viral_product_upload.seek(0)
        viral_product_image_path.write_bytes(viral_product_upload.read())
        viral_product_upload.seek(0)
        st.image(str(viral_product_image_path), caption='Ảnh sản phẩm gốc dùng làm reference trong Google Flow Ingredients', use_container_width=True)

    st.info('Prompt sẽ khóa sản phẩm theo ảnh gốc, giữ nguyên hình dáng/màu/chất liệu, cấm tự vẽ lại, cấm chữ overlay, cấm chữ môi trường, và yêu cầu xoá chữ trên sản phẩm để giảm lỗi Flow.')

    sg1, sg2 = st.columns([1,1])
    with sg1:
        if st.button('🤖 AI gợi ý style theo sản phẩm', use_container_width=True):
            suggestion = suggest_style_combo_v32(viral_product_name, viral_product_type, viral_product_mood, viral_product_target, pdir)
            # Không gán trực tiếp vào key widget sau khi widget đã render.
            # Streamlit sẽ lỗi nếu set st.session_state['viral_product_style_preset'] tại đây.
            st.session_state['last_product_style_suggestion'] = suggestion
            st.success('Đã tạo gợi ý style. Bấm Apply suggestion 1 chạm để áp dụng vào project.')
            st.rerun()
    with sg2:
        suggestion = st.session_state.get('last_product_style_suggestion')
        if suggestion:
            st.markdown(f"<div class='style-note'><b>AI gợi ý:</b> {blended_style_label(suggestion['primary_style'], suggestion['secondary_style'], suggestion['tertiary_style'])}<br><b>Lý do:</b> {suggestion['reason']}<br><b>Palette:</b> {suggestion['palette']}</div>", unsafe_allow_html=True)
            with st.expander('Style ranking theo sản phẩm', expanded=False):
                st.dataframe(suggestion.get('ranking', []), use_container_width=True)
                st.json(suggestion.get('reference_analysis', {}))
            if st.button('✅ Apply suggestion 1 chạm', use_container_width=True):
                save_project_style(pdir, {'locked': lock_project_style, 'selected_style': suggestion['primary_style'], 'secondary_style': suggestion['secondary_style'], 'tertiary_style': suggestion['tertiary_style'], 'palette': suggestion['palette']})
                st.success('Đã apply style suggestion cho project.')
                st.rerun()

    cp1, cp2 = st.columns([1, 1])
    with cp1:
        make_product_prompts = st.button('🛍️ Tạo Concept + Kịch bản 8s + 3 Prompt Flow', type='primary', use_container_width=True)
    with cp2:
        st.markdown(
            f"""
<div class="card">
<b>Music mood:</b><br>{PRODUCT_MOODS[viral_product_mood]['music']}<br><br>
<b>Camera:</b><br>{PRODUCT_MOODS[viral_product_mood]['camera']}<br><br>
<b>Style:</b><br>{blended_style_label(viral_product_style_preset, normalize_secondary_style(viral_product_secondary_style), normalize_secondary_style(viral_product_tertiary_style))} — {blended_style_description(viral_product_style_preset, normalize_secondary_style(viral_product_secondary_style), normalize_secondary_style(viral_product_tertiary_style))}<br><br>
<b>Voice:</b><br>{PRODUCT_MOODS[viral_product_mood]['voice_style']}
</div>
""",
            unsafe_allow_html=True,
        )

    if make_product_prompts:
        if not viral_product_upload:
            st.error('Hãy upload ảnh sản phẩm gốc trước.')
        else:
            pdata = build_product_prompts(
                viral_product_name,
                viral_product_type,
                viral_product_mood,
                viral_product_target,
                viral_product_objective,
                viral_product_model,
                viral_product_clean_text,
                3,
            )
            pdata['viral_context'] = {'topic': topic, 'platform': platform, 'niche': niche, 'faceless': faceless, 'host': host}
            secondary_style = normalize_secondary_style(viral_product_secondary_style)
            tertiary_style = normalize_secondary_style(viral_product_tertiary_style)
            style_desc = blended_style_description(viral_product_style_preset, secondary_style, tertiary_style)
            palette_desc = blended_style_palette(viral_product_style_preset, secondary_style, tertiary_style)
            pdata['concept']['image_style_preset'] = viral_product_style_preset
            pdata['concept']['image_secondary_style'] = secondary_style
            pdata['concept']['image_tertiary_style'] = tertiary_style
            pdata['concept']['image_style_description'] = style_desc
            pdata['concept']['color_palette_preset'] = palette_desc
            pdata['concept']['style_reference_summary'] = style_reference_summary(pdir)
            for _p in pdata['prompts']:
                _p['prompt'] = _p['prompt'] + f"\n\nIMAGE STYLE PRESET:\nUse this visual style blend: {blended_style_label(viral_product_style_preset, secondary_style, tertiary_style)}. {style_desc}. Preferred color palette: {palette_desc}. {style_reference_summary(pdir)} Keep the whole video visually consistent with this style while preserving the uploaded product exactly."
                _p['estimated_flow_setting']['style_preset'] = viral_product_style_preset
                _p['estimated_flow_setting']['secondary_style'] = secondary_style
                _p['estimated_flow_setting']['tertiary_style'] = tertiary_style
                _p['estimated_flow_setting']['style_palette'] = palette_desc
            if viral_product_image_path:
                pdata['product_reference_image'] = str(viral_product_image_path)
            st.session_state.viral_product_prompt_data = pdata
            z = export_product_prompt_package(pdir, pdata, str(viral_product_image_path) if viral_product_image_path else None)
            st.success('Đã tạo Product Concept + Kịch bản 8s + 3 Prompt Flow.')
            st.download_button('📦 Tải Product Prompt Package ZIP', Path(z).read_bytes(), Path(z).name, use_container_width=True)

    vpdata = st.session_state.get('viral_product_prompt_data')
    if vpdata:
        st.markdown('#### ✅ Product Concept')
        with st.expander('Xem concept chiến lược sản phẩm', expanded=False):
            st.json(vpdata['concept'])

        st.markdown('#### 🎬 Shot list 8s')
        st.dataframe(vpdata['shots'], use_container_width=True)

        st.markdown('#### 🧾 3 Prompt Flow/Veo từ ảnh sản phẩm')
        for pr in vpdata['prompts']:
            with st.expander(f"Prompt {pr['variant']} · {pr['mood']} · Voiceover", expanded=pr['variant'] == 1):
                st.markdown('**Voiceover tiếng Việt:**')
                st.write(pr['voiceover'])
                st.markdown('**Prompt Flow/Veo:**')
                st.text_area('Prompt', value=pr['prompt'], height=320, key=f"viral_product_prompt_{pr['variant']}")
                st.code(pr['prompt'])
                st.json(pr['estimated_flow_setting'])

        send1, sendall, downloadall = st.columns(3)
        with send1:
            if st.button('➡️ Gửi prompt 1 sang Flow Assisted', use_container_width=True, key='send_vproduct_1_fixed'):
                p0 = vpdata['prompts'][0]
                st.session_state.flow_rows = [{'scene': 1, 'status': 'Chưa làm', 'narration': p0['voiceover'], 'prompt': p0['prompt'], 'note': 'Viral Director Product Upload'}]
                st.success('Đã gửi prompt 1 sang Flow Assisted.')
        with sendall:
            if st.button('➡️ Gửi cả 3 prompt sang Flow Assisted', use_container_width=True, key='send_vproduct_all_fixed'):
                st.session_state.flow_rows = [
                    {'scene': p['variant'], 'status': 'Chưa làm', 'narration': p['voiceover'], 'prompt': p['prompt'], 'note': 'Viral Director Product Upload'}
                    for p in vpdata['prompts']
                ]
                st.success('Đã gửi cả 3 prompt sang Flow Assisted.')
        with downloadall:
            all_prompts = '\n\n====================\n\n'.join([p['prompt'] for p in vpdata['prompts']])
            st.download_button('⬇️ Tải 3 prompt TXT', all_prompts.encode('utf-8'), 'viral_product_flow_prompts.txt', use_container_width=True)

    st.divider()


    if st.button('🚀 Tạo Viral Blueprint',type='primary',use_container_width=True):
        bp=make_blueprint(topic,platform,niche,faceless,host,minutes); st.session_state.viral_blueprint=bp; z=export_blueprint_zip(pdir,bp); st.success('Đã tạo Viral Blueprint.'); st.download_button('📦 Tải Viral Blueprint ZIP',Path(z).read_bytes(),Path(z).name,use_container_width=True)
    bp=st.session_state.get('viral_blueprint')
    if bp:
        st.divider(); st.markdown('### 10 ý tưởng viral đã chấm điểm'); st.dataframe(bp['ideas'],use_container_width=True,column_order=['id','viral_potential','hook_score','retention_score','faceless_ease_score','production_difficulty','thumbnail_score','insight_score','title','first_3s_hook','content_format'])
        top=bp['ideas'][0]; a,b,c,d=st.columns(4); a.metric('Viral Potential',top['viral_potential']); b.metric('Hook',top['hook_score']); c.metric('Retention',top['retention_score']); d.metric('Difficulty',top['production_difficulty'])
        st.markdown('### Kịch bản'); st.text_area('Voiceover',value=bp['script']['voiceover'],height=220)
        st.markdown('### Shot prompts'); st.dataframe(bp['shots'],use_container_width=True)
        if st.button('➡️ Gửi prompt sang Flow Assisted',use_container_width=True):
            suffix=flow_settings_suffix(st.session_state.get('flow_quick_settings',{})); st.session_state.flow_rows=[{'scene':s['scene'],'status':'Chưa làm','narration':s['voiceover'],'prompt':s['flow_prompt']+'\n\n'+suffix,'note':''} for s in bp['shots']]; st.success('Đã gửi prompt sang Flow Assisted.')
        st.markdown('### Gói tối ưu'); st.json(bp['optimization'])
with tab('🎞️ Video Grid'):
    st.markdown('## 🎞️ Video Grid Pro — 10 ô video riêng biệt')
    st.caption('Mỗi ô có prompt riêng, copy prompt, mở Flow, upload video, dấu tích, màu trạng thái, reorder và lọc nhanh.')

    if 'video_grid_rows' not in st.session_state or not st.session_state.get('video_grid_rows'):
        st.session_state.video_grid_rows = default_video_grid_rows(10)
    st.session_state.video_grid_rows = normalize_video_grid_rows(st.session_state.video_grid_rows, 10)

    gs = video_grid_summary(st.session_state.video_grid_rows)
    progress = video_grid_progress_ratio(st.session_state.video_grid_rows)
    st.markdown(f"<div class='grid-progress-label'>Tiến độ tổng: {int(progress*100)}%</div>", unsafe_allow_html=True)
    st.progress(progress)

    g1,g2,g3,g4,g5 = st.columns(5)
    g1.metric('Tổng ô', gs['total'])
    g2.metric('Có prompt', gs['prompts'])
    g3.metric('Có video', gs['videos'])
    g4.metric('Hoàn tất', gs['completed'])
    g5.metric('Lỗi', gs['errors'])

    st.markdown('### ⚡ Thao tác nhanh')
    a1,a2,a3,a4 = st.columns(4)
    with a1:
        if st.button('📥 Nạp prompt từ Viral/Flow', use_container_width=True):
            st.session_state.video_grid_rows = video_grid_from_flow_rows(st.session_state.get('flow_rows', []), 10)
            st.success('Đã nạp prompt vào 10 ô video.')
            st.rerun()
    with a2:
        if st.button('💾 Lưu 10 ô sang Flow Assisted', use_container_width=True):
            st.session_state.flow_rows = flow_rows_from_video_grid(st.session_state.video_grid_rows)
            st.success('Đã đồng bộ 10 ô sang Flow Assisted.')
    with a3:
        if st.button('🌊 Mở Google Flow', use_container_width=True):
            st.link_button('Bấm để mở Flow', FLOW_URL, use_container_width=True)
    with a4:
        if st.button('🧹 Reset 10 ô video', use_container_width=True):
            st.session_state.video_grid_rows = default_video_grid_rows(10)
            st.success('Đã reset 10 ô video.')
            st.rerun()

    st.markdown('### 🔎 Lọc & đổi thứ tự')
    f1, f2 = st.columns([1, 1.4])
    with f1:
        grid_filter = st.selectbox('Lọc ô video', ['Tất cả','Chỉ ô lỗi','Chỉ ô chưa làm','Chỉ ô hoàn tất','Chưa hoàn tất','Đã có video'], index=0)
    with f2:
        with st.expander('↕️ Kéo/sửa thứ tự scene', expanded=False):
            st.caption('Streamlit chưa hỗ trợ drag-drop native ổn định, nên bản này dùng bảng order: sửa số thứ tự rồi bấm áp dụng. Kết quả giống reorder scene.')
            order_data = [{'order': i+1, 'scene': r['scene'], 'title': r.get('title','')} for i, r in enumerate(st.session_state.video_grid_rows)]
            edited_order = st.data_editor(
                order_data,
                use_container_width=True,
                hide_index=True,
                key='video_grid_order_editor',
                column_config={
                    'order': st.column_config.NumberColumn('Thứ tự mới', min_value=1, max_value=10, step=1),
                    'scene': st.column_config.NumberColumn('Scene hiện tại', disabled=True),
                    'title': st.column_config.TextColumn('Tên cảnh', disabled=True),
                }
            )
            if st.button('✅ Áp dụng thứ tự mới', use_container_width=True):
                st.session_state.video_grid_rows = reorder_video_grid_rows(st.session_state.video_grid_rows, edited_order)
                st.success('Đã đổi thứ tự 10 ô video.')
                st.rerun()

    clips_lookup = {}
    for c in merge_clips(scan_inbox(pdir), st.session_state.get('flow_clips', [])):
        try:
            clips_lookup[int(c.get('scene') or 0)] = c
        except Exception:
            pass

    rows_all = normalize_video_grid_rows(st.session_state.video_grid_rows, 10)
    rows_show = filter_video_grid_rows(rows_all, grid_filter)
    st.caption(f'Đang hiển thị {len(rows_show)}/10 ô theo bộ lọc: {grid_filter}')

    updated_by_scene = {r['scene']: dict(r) for r in rows_all}
    if not rows_show:
        st.warning('Không có ô nào khớp bộ lọc hiện tại.')
    for start_i in range(0, len(rows_show), 2):
        cols = st.columns(2)
        pair = rows_show[start_i:start_i+2]
        for col, row in zip(cols, pair):
            sc = row['scene']
            clip = clips_lookup.get(sc)
            with col:
                with st.container(border=True):
                    st.markdown(video_status_chip(row.get('status', 'Chưa làm'), row.get('done', False)), unsafe_allow_html=True)
                    top1, top2 = st.columns([1.2, 1])
                    with top1:
                        title = st.text_input(f'Tên ô {sc}', value=row.get('title', f'Cảnh {sc}'), key=f'grid_title_{sc}')
                    with top2:
                        status = st.selectbox(
                            f'Trạng thái {sc}',
                            list(VIDEO_STATUS_META.keys()),
                            index=list(VIDEO_STATUS_META.keys()).index(row.get('status', 'Chưa làm')) if row.get('status', 'Chưa làm') in list(VIDEO_STATUS_META.keys()) else 0,
                            key=f'grid_status_{sc}'
                        )
                    done = st.checkbox(f'Đánh dấu hoàn thành ô {sc}', value=bool(row.get('done', False)), key=f'grid_done_{sc}')

                    narration = st.text_area(f'Voice/Narration {sc}', value=row.get('narration', ''), height=60, key=f'grid_narration_{sc}', placeholder='Voiceover hoặc mô tả ngắn...')
                    prompt = st.text_area(f'Prompt scene {sc}', value=row.get('prompt', ''), height=145, key=f'grid_prompt_{sc}', placeholder='Prompt riêng cho cảnh này...')

                    bcopy, bflow = st.columns(2)
                    with bcopy:
                        copy_prompt_component(prompt, f'scene_{sc}')
                    with bflow:
                        flow_open_component(FLOW_URL, f'flow_scene_{sc}')

                    note = st.text_input(f'Ghi chú {sc}', value=row.get('note', ''), key=f'grid_note_{sc}', placeholder='Ghi chú nhanh...')
                    up = st.file_uploader(f'Upload video cho ô {sc}', type=['mp4','mov','m4v','webm'], key=f'grid_upload_{sc}')

                    video_path = row.get('video_path', '')
                    if up is not None:
                        saved = save_uploads(pdir, [up])
                        if saved:
                            saved[0]['scene'] = sc
                            video_path = saved[0]['path']
                            st.session_state.flow_clips = merge_clips(st.session_state.get('flow_clips', []), [saved[0]])
                            if status in ['Chưa làm', 'Sẵn sàng copy', 'Đang render']:
                                status = 'Đã có video'
                            st.success(f'Đã lưu video cho ô {sc}')
                    elif clip and Path(clip['path']).exists():
                        video_path = clip['path']

                    if video_path and Path(video_path).exists():
                        st.video(video_path)
                        st.caption(Path(video_path).name)

                    final_status = 'Hoàn tất' if done and status == 'Đã có video' else status
                    updated_by_scene[sc] = {
                        'scene': sc,
                        'title': title,
                        'status': final_status,
                        'done': done,
                        'narration': narration,
                        'prompt': prompt,
                        'note': note,
                        'video_path': video_path,
                    }

    st.session_state.video_grid_rows = normalize_video_grid_rows([updated_by_scene[i] for i in sorted(updated_by_scene)], 10)
    st.download_button('⬇️ Tải 10 ô video JSON', json.dumps(st.session_state.video_grid_rows, ensure_ascii=False, indent=2).encode('utf-8'), 'video_grid_rows.json', use_container_width=True)

with tab('🌊 Flow Assisted'):
    st.markdown('## 🌊 Flow Assisted Mode + Flow Quick Settings')
    rows=st.session_state.get('flow_rows',[])
    if (not rows) and st.session_state.get('video_grid_rows'):
        st.session_state.flow_rows = flow_rows_from_video_grid(st.session_state.get('video_grid_rows', []))
        rows = st.session_state.get('flow_rows',[])
    c1,c2=st.columns([1.05,.95])
    with c1:
        if not rows: st.info('Chưa có prompt. Tạo ở Viral Director, Video Grid hoặc nhập nhanh bên dưới.')
        quick_topic=st.text_area('Tạo prompt nhanh nếu chưa có',height=90,placeholder='Nhập brief ngắn...')
    with c2:
        expected=st.number_input('Số scene dự kiến',min_value=1,max_value=50,value=max(1,len(rows) or 5)); voice_label=st.selectbox('Voice hậu kỳ',list(VOICE_PRESETS.keys())); burn_sub=st.checkbox('Burn subtitle vào final',value=True); add_fade=st.checkbox('Nối có fade nhẹ',value=True); thumb_template=st.selectbox('Thumbnail template',list(TEMPLATES.keys()),index=list(TEMPLATES.keys()).index(default_thumb_template)); st.link_button('🌊 Mở Google Flow',FLOW_URL,use_container_width=True)
    st.markdown('### 🎨 Flow style preview')
    st.markdown(style_preview_card(global_style_preset, selected=True), unsafe_allow_html=True)
    st.markdown('### ⚙️ Flow Quick Settings giống Google Flow')
    q1,q2,q3,q4=st.columns(4)
    with q1: media_mode=st.radio('Loại',['Image','Video'],index=1,horizontal=True); source_mode=st.radio('Nguồn',['Text','Frames','Ingredients'],index=0,horizontal=True)
    with q2: aspect_ratio=st.radio('Tỉ lệ',['9:16','16:9'],index=0,horizontal=True); variants=st.radio('Số bản',['1x','2x','3x','4x'],index=0,horizontal=True)
    with q3: model_flow=st.selectbox('Model Flow',['Veo 3.1 - Lite','Veo 3.1 - Fast','Veo 3.1 - Quality','Veo 3.1 - Lite [Lower Priority]','Veo 3.1 - Fast [Lower Priority]'],index=1); duration_flow=st.radio('Thời lượng',[4,6,8],index=2,horizontal=True)
    with q4:
        style_preset=st.selectbox('Phong cách hình ảnh', list(STYLE_PRESETS.keys()), index=list(STYLE_PRESETS.keys()).index(global_style_preset) if global_style_preset in list(STYLE_PRESETS.keys()) else 0)
        secondary_style_preset=st.selectbox('Blend phong cách phụ', ['(None)'] + list(STYLE_PRESETS.keys()), index=(['(None)'] + list(STYLE_PRESETS.keys())).index(active_secondary_style) if active_secondary_style in (['(None)'] + list(STYLE_PRESETS.keys())) else 0)
        tertiary_style_preset=st.selectbox('Blend phong cách thứ 3', ['(None)'] + list(STYLE_PRESETS.keys()), index=(['(None)'] + list(STYLE_PRESETS.keys())).index(active_tertiary_style) if active_tertiary_style in (['(None)'] + list(STYLE_PRESETS.keys())) else 0)
        action_mode=st.selectbox('Action',['Generate','Extend','Insert','Remove','Camera'],index=0)
        camera_note=st.text_input('Camera note',value='',placeholder='slow dolly in, orbit...')
    flow_settings={'media_mode':media_mode,'source_mode':source_mode,'aspect_ratio':aspect_ratio,'variants':variants,'model':model_flow,'duration':int(duration_flow),'style_preset':style_preset,'secondary_style':normalize_secondary_style(secondary_style_preset),'tertiary_style':normalize_secondary_style(tertiary_style_preset),'series_name': st.session_state.get(f'current_series_{project_name}', 'default'),'action_mode':action_mode,'camera_note':camera_note}; st.session_state.flow_quick_settings=flow_settings; credit=estimate_flow_credits(flow_settings); st.info(f'Ước tính: **{credit} credit/scene**, tổng **{credit*int(expected)} credit** cho {int(expected)} scene.')
    with st.expander('Prompt suffix tự thêm vào mỗi scene',expanded=False):
        st.text_area('Flow settings suffix',value=flow_settings_suffix(flow_settings),height=120); st.download_button('⬇️ Tải flow_settings.json',json.dumps({**flow_settings,'estimated_credits_per_scene':credit},ensure_ascii=False,indent=2).encode('utf-8'),'flow_settings.json',mime='application/json',use_container_width=True)
    if st.button('🧠 Tạo prompt nhanh 5 cảnh',use_container_width=True):
        if quick_topic.strip(): st.session_state.flow_rows=[{'scene':i,'status':'Chưa làm','narration':f'Cảnh {i}: {quick_topic}','prompt':f'{quick_topic}. Scene {i}. Cinematic short-form video, clear subject, smooth motion. '+flow_settings_suffix(flow_settings),'note':''} for i in range(1,6)]; st.rerun()
    rows=st.session_state.get('flow_rows',[])
    if rows:
        st.markdown('### 1) Checklist + prompt (compact)'); edited=st.data_editor(rows,num_rows='dynamic',use_container_width=True,key='flow_rows_editor_clean',column_config={'scene':st.column_config.NumberColumn('Scene',min_value=1),'status':st.column_config.SelectboxColumn('Trạng thái',options=['Chưa làm','Đã copy prompt','Đang render Flow','Đã tải video','Lỗi cần làm lại','Hoàn tất']),'narration':st.column_config.TextColumn('Narration'),'prompt':st.column_config.TextColumn('Prompt dán vào Flow'),'note':st.column_config.TextColumn('Ghi chú')}); st.session_state.flow_rows=edited; txt=write_prompt_txt(pdir,edited); st.download_button('⬇️ Tải toàn bộ prompt TXT',Path(txt).read_bytes(),Path(txt).name,use_container_width=True)
    st.markdown('### 2) Upload hàng loạt hoặc quét Flow Inbox'); inbox=inbox_dir(pdir); st.code(str(inbox),language='text')
    u1,u2,u3=st.columns(3)
    with u1:
        uploaded=st.file_uploader('Upload nhiều clip Flow',type=['mp4','mov','m4v','webm'],accept_multiple_files=True)
        if uploaded and st.button('💾 Lưu + auto map upload',use_container_width=True): saved=save_uploads(pdir,uploaded); st.session_state.flow_clips=merge_clips(st.session_state.get('flow_clips',[]),saved); st.success(f'Đã lưu {len(saved)} clip.')
    with u2:
        if st.button('🔍 Quét flow_inbox',use_container_width=True): scanned=scan_inbox(pdir); st.session_state.flow_clips=merge_clips(st.session_state.get('flow_clips',[]),scanned); st.success(f'Đã quét {len(scanned)} clip.')
    with u3:
        if st.button('🏷️ Chuẩn hóa tên scene_XX',use_container_width=True): st.session_state.flow_clips=normalize_names(st.session_state.get('flow_clips',[]),pdir); st.success('Đã chuẩn hóa tên clip vào flow_inbox.')
    clips=merge_clips(scan_inbox(pdir),st.session_state.get('flow_clips',[])); miss=missing_scenes(clips,int(expected))
    if clips: st.dataframe(clips,use_container_width=True)
    st.warning('Còn thiếu scene: '+', '.join(map(str,miss))) if miss else st.success('Đủ scene theo số lượng dự kiến.')
    with st.expander('📋 Bảng cấu hình Flow để thao tác trên điện thoại giống ảnh',expanded=False): st.json(flow_settings)
    st.markdown('### 3) Build Final — thời lượng, tỉ lệ, khung, độ phân giải')
    output_name=st.text_input('Tên final',value='flow_final.mp4')
    r1,r2,r3,r4=st.columns(4)
    with r1:
        final_seconds_per_clip=st.number_input('Mỗi clip bao nhiêu giây',min_value=0.0,max_value=60.0,value=float(duration_flow),step=1.0,help='0 = giữ thời lượng gốc. Nếu nhập số, app sẽ cắt/kéo frame cuối để mỗi clip đúng số giây.')
        final_aspect=st.selectbox('Tỉ lệ khung', ['9:16','16:9','1:1','4:5','3:4'], index=['9:16','16:9','1:1','4:5','3:4'].index(aspect_ratio) if aspect_ratio in ['9:16','16:9','1:1','4:5','3:4'] else 0)
    with r2:
        final_resolution=st.selectbox('Độ phân giải', ['720','1080','2000'], index=1, help='720/1080/2000 là cạnh dài theo tỉ lệ đã chọn. Ví dụ 9:16 1080 = 608x1080.')
        final_fps=st.selectbox('Khung hình / FPS', [24,30,60], index=1)
    with r3:
        final_fit_mode=st.selectbox('Chế độ khung', ['pad','crop'], index=0, format_func=lambda x: 'Giữ đủ hình + viền nền' if x=='pad' else 'Crop kín khung')
        vertical=st.checkbox('Thumbnail dọc 9:16',value=(final_aspect in ['9:16','3:4','4:5']))
    with r4:
        final_use_studio=st.checkbox('Chuẩn hóa clip trước khi nối', value=True, help='Nên bật nếu clip tải từ Flow có kích thước/FPS khác nhau.')
        st.info(f'Final: {final_aspect} · {final_resolution} · {final_fps}fps')
    title_text=st.text_input('Text thumbnail/title',value=(rows[0]['narration'][:60] if rows else 'Flow Assisted Video'))

    if st.button('⚡ Build Final từ clip đã map',type='primary',use_container_width=True):
        try:
            clip_paths=[c['path'] for c in clips if Path(c['path']).exists()]
            if not clip_paths: st.error('Chưa có clip hợp lệ.')
            else:
                if final_use_studio:
                    raw=concat_videos_studio(
                        pdir,
                        clip_paths,
                        output_name,
                        add_fade,
                        seconds_per_clip=final_seconds_per_clip,
                        aspect_ratio=final_aspect,
                        resolution=final_resolution,
                        fps=final_fps,
                        fit_mode=final_fit_mode,
                    )
                else:
                    raw=concat_videos(pdir,clip_paths,output_name,add_fade)
                narr=[r.get('narration','') for r in rows] if rows else [title_text]
                voice_text=' '.join(narr)
                voice=tts_edge(pdir,voice_text,voice_label)
                caption_seconds=max(1, int(final_seconds_per_clip or 4))
                srt=make_srt(pdir,narr,caption_seconds)
                final=mix_audio_subtitles(pdir,raw,voice,srt,burn_sub)
                base_thumb=thumbnail_from_video(pdir,final)
                thumb=make_thumbnail(pdir,base_thumb,title_text,thumb_template,vertical)
                meta={
                    'title':title_text,
                    'caption':voice_text[:400],
                    'hashtags':'#AIVideo #Veo #Shorts #Reels #ViralContent',
                    'clips':clips,
                    'created_at':now(),
                    'template':thumb_template,
                    'flow_settings':flow_settings,
                    'final_render_settings':{
                        'seconds_per_clip': final_seconds_per_clip,
                        'aspect_ratio': final_aspect,
                        'resolution': final_resolution,
                        'fps': final_fps,
                        'fit_mode': final_fit_mode,
                        'standardize_before_concat': final_use_studio,
                    }
                }
                package=publish_package(pdir,final,thumb,srt,voice,meta)
                st.success('Đã build xong final video.')
                st.video(final)
                st.download_button('⬇️ Tải final video',Path(final).read_bytes(),Path(final).name,use_container_width=True)
                st.image(thumb,caption='Thumbnail',use_container_width=True)
                st.download_button('📦 Tải publish package',Path(package).read_bytes(),Path(package).name,use_container_width=True)
        except Exception as e: log_error('build_flow_final',e,{'project':project_name}); st.exception(e)
with tab('🏠 Project'):
    st.markdown('## 🏠 Project'); rep=storage_report(project_name); style_score, style_checks = compute_style_consistency(project_style_cfg, global_style_preset, active_secondary_style, active_tertiary_style); a,b,e=st.columns(3); a.metric('Project size',f"{rep['total_mb']} MB"); b.metric('Files',rep['files']); e.metric('Style consistency', f'{style_score}/100'); c,d=st.columns(2)
    with c:
        if st.button('📦 Export ZIP project',type='primary',use_container_width=True): z=export_zip(project_name); st.download_button('⬇️ Tải ZIP',Path(z).read_bytes(),Path(z).name,use_container_width=True)
    with d:
        if st.button('🛡️ Backup project',use_container_width=True): z=backup_project(project_name); st.download_button('⬇️ Tải backup',Path(z).read_bytes(),Path(z).name,use_container_width=True)
    with st.expander('File lớn nhất',expanded=False): st.json(rep['largest'])
    with st.expander('🎨 Project style assets', expanded=False):
        st.json(project_style_cfg)
        sample_path = ensure_style_sample(global_style_preset, pdir / 'style_samples')
        st.image(str(sample_path), caption=f'Style sample: {global_style_preset}', use_container_width=True)
        if active_secondary_style:
            sample2 = ensure_style_sample(active_secondary_style, pdir / 'style_samples')
            st.image(str(sample2), caption=f'Style sample blend: {active_secondary_style}', use_container_width=True)
        if active_tertiary_style:
            sample3 = ensure_style_sample(active_tertiary_style, pdir / 'style_samples')
            st.image(str(sample3), caption=f'Style sample blend 3: {active_tertiary_style}', use_container_width=True)
        st.markdown('**Style references:** ' + (', '.join(p.name for p in list_style_references(pdir)) if list_style_references(pdir) else 'Chưa có'))
        st.json(load_style_memory(pdir))
        st.dataframe(style_checks, use_container_width=True)
with tab('📊 Dashboard'):
    st.markdown('## 📊 Dashboard'); score, checks = compute_style_consistency(project_style_cfg, global_style_preset, active_secondary_style, active_tertiary_style); m1,m2=st.columns(2); m1.metric('Style consistency score', f'{score}/100'); m2.metric('Current theme', global_style_preset); st.json(storage_report(project_name)); st.markdown('### Style checks'); st.dataframe(checks,use_container_width=True); errors=read_errors(50); st.markdown('### Logs'); st.dataframe(errors,use_container_width=True) if errors else st.info('Chưa có log lỗi.')
if has_tab('🎨 Style Gallery'):
    with tab('🎨 Style Gallery'):
        st.markdown('## 🎨 Style Gallery v3.1')
        st.caption('Có style reference upload, AI gợi ý style, auto map wording, blend 2 phong cách và style memory cho series.')
        style_score, style_checks = compute_style_consistency(project_style_cfg, global_style_preset, active_secondary_style, active_tertiary_style)
        g1,g2 = st.columns([.9,1.1])
        with g1:
            st.metric('Style consistency score', f"{style_score}/100")
            st.dataframe(style_checks, use_container_width=True)
        with g2:
            st.markdown(style_preview_card(global_style_preset, selected=True), unsafe_allow_html=True)
            st.markdown(f"<div class='style-note'><b>Theme hiện tại:</b> {blended_style_label(global_style_preset, active_secondary_style, active_tertiary_style)}<br><b>Palette:</b> {blended_style_palette(global_style_preset, active_secondary_style, active_tertiary_style)}<br><b>Mô tả:</b> {blended_style_description(global_style_preset, active_secondary_style, active_tertiary_style)}</div>", unsafe_allow_html=True)
        st.divider()
        styles = list(STYLE_PRESETS.keys())
        for i in range(0, len(styles), 2):
            cols = st.columns(2)
            for col, style_name in zip(cols, styles[i:i+2]):
                with col:
                    sample_path = ensure_style_sample(style_name, pdir / 'style_samples')
                    st.image(str(sample_path), caption=f'Mẫu preset: {style_name}', use_container_width=True)
                    st.markdown(style_preview_card(style_name, selected=(style_name==global_style_preset)), unsafe_allow_html=True)
                    b1, b2 = st.columns(2)
                    with b1:
                        if st.button(f'✨ Apply {style_name}', key=f'apply_style_{style_name}', use_container_width=True):
                            save_project_style(pdir, {'locked': False, 'selected_style': style_name, 'secondary_style': None, 'tertiary_style': None, 'palette': blended_style_palette(style_name, None, None)})
                            st.session_state[f'global_style_{project_name}'] = style_name
                            st.success(f'Đã apply style: {style_name}')
                            st.rerun()
                    with b2:
                        if st.button(f'🔒 Apply + Lock', key=f'lock_style_{style_name}', use_container_width=True):
                            save_project_style(pdir, {'locked': True, 'selected_style': style_name, 'secondary_style': None, 'tertiary_style': None, 'palette': blended_style_palette(style_name, None, None)})
                            st.session_state[f'global_style_{project_name}'] = style_name
                            st.success(f'Đã apply và lock style: {style_name}')
                            st.rerun()
                    st.caption('Prompt direction: ' + STYLE_PRESETS.get(style_name, style_name) + ' | Palette: ' + style_palette_text(style_name))
        st.info('Tip: Nếu muốn blend 2 phong cách, hãy Apply style chính rồi chọn thêm Secondary blend style ở sidebar. Style memory có thể lưu cho từng series/campaign.')

if has_tab('🔄 Prompt Sync'):
    with tab('🔄 Prompt Sync'):
        st.markdown('## 🔄 Prompt Sync — ChatGPT + Gemini')
        st.caption('Đồng bộ prompt theo cách an toàn: ChatGPT dùng copy/paste prompt bank; Gemini dùng API key chính thức nếu bạn có. Không lấy cookie tài khoản.')

        st.markdown('### 1) Prompt Bank từ ChatGPT/Gemini')
        uploaded_prompt_files = st.file_uploader('Upload file prompt .txt/.md/.json', type=['txt','md','json'], accept_multiple_files=True, key='prompt_bank_uploads')
        pasted_prompt = st.text_area('Hoặc dán prompt từ ChatGPT/Gemini vào đây', height=180, placeholder='Dán prompt, template, kịch bản, prompt Flow/Veo...')
        prompt_bank_name = st.text_input('Tên file lưu prompt', value='chatgpt_gemini_prompt.txt')
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button('💾 Lưu vào Prompt Bank', use_container_width=True):
                saved = []
                if pasted_prompt.strip():
                    saved.append(save_prompt_bank_text(pdir, prompt_bank_name, pasted_prompt, 'manual'))
                for f in uploaded_prompt_files or []:
                    f.seek(0)
                    content = f.read().decode('utf-8', errors='ignore')
                    f.seek(0)
                    saved.append(save_prompt_bank_text(pdir, f.name, content, 'upload'))
                st.success(f'Đã lưu {len(saved)} prompt file.')
        with col_b:
            if st.button('📖 Refresh Prompt Bank', use_container_width=True):
                st.rerun()

        files = list_prompt_bank_files(pdir)
        st.write(f'Prompt Bank hiện có: {len(files)} file')
        if files:
            st.dataframe([{'file': p.name, 'size_kb': round(p.stat().st_size/1024, 1)} for p in files], use_container_width=True)
            with st.expander('Xem tóm tắt Prompt Bank', expanded=False):
                st.text_area('Prompt bank summary', read_prompt_bank_summary(pdir), height=240)

        st.markdown('### 2) Sinh prompt đồng bộ theo style/project')
        sync_task = st.text_area('Yêu cầu sinh prompt đồng bộ', value='Tạo 3 prompt Flow/Veo 8s cho sản phẩm, giữ style project, có voiceover tiếng Việt, không text overlay.', height=120)
        context = build_prompt_sync_context(pdir)
        with st.expander('Context sẽ gửi cho AI', expanded=False):
            st.text_area('Prompt sync context', context, height=260)

        c1, c2 = st.columns(2)
        with c1:
            if st.button('🧠 Tạo prompt local từ Prompt Bank', use_container_width=True):
                local_output = (
                    context
                    + "\n\nLOCAL SYNTHESIS TASK:\n"
                    + sync_task
                    + "\n\nPROMPT OUTPUT:\n"
                    + f"Use current project style blend: {blended_style_label(global_style_preset, active_secondary_style, active_tertiary_style)}.\n"
                    + f"Palette: {blended_style_palette(global_style_preset, active_secondary_style, active_tertiary_style)}.\n"
                    + "Generate Flow/Veo prompts that preserve product identity, avoid text overlay, use Vietnamese voiceover, and follow saved prompt bank style."
                )
                st.session_state['prompt_sync_output'] = local_output
        with c2:
            if st.button('🔮 Gọi Gemini API để gợi ý prompt', use_container_width=True):
                ok, out = call_gemini_prompt_sync(sync_task, context, gemini_api_key_sidebar)
                if ok:
                    st.session_state['prompt_sync_output'] = out
                    st.success('Gemini đã trả về prompt.')
                else:
                    st.error(out)

        output = st.session_state.get('prompt_sync_output', '')
        if output:
            st.markdown('### 3) Output prompt đồng bộ')
            st.text_area('Prompt Sync Output', output, height=360)
            st.download_button('⬇️ Tải prompt_sync_output.txt', output.encode('utf-8'), 'prompt_sync_output.txt', use_container_width=True)
            if st.button('➡️ Gửi output sang Flow Assisted', use_container_width=True):
                st.session_state.flow_rows = [{
                    'scene': 1,
                    'status': 'Chưa làm',
                    'narration': 'Prompt Sync Output',
                    'prompt': output,
                    'note': 'Prompt Sync',
                }]
                st.success('Đã gửi sang Flow Assisted.')


if has_tab('🖼️ Thumbnail Lab'):
    with tab('🖼️ Thumbnail Lab'):
        st.markdown('## 🖼️ Thumbnail Lab')
        st.caption('Tạo thumbnail local + chuẩn bị setting giống Google Flow Image panel.')

        upload=st.file_uploader('Ảnh nền / ảnh sản phẩm / thumbnail base',type=['png','jpg','jpeg','webp'], key='thumb_lab_upload')
        text=st.text_input('Text / ý tưởng thumbnail',value='ĐỪNG LÀM SAI', key='thumb_lab_text')
        template=st.selectbox('Template local',list(TEMPLATES.keys()), key='thumb_lab_template')

        st.markdown('### 🎨 Thumbnail style preview')
        st.markdown(style_preview_card(global_style_preset, selected=True), unsafe_allow_html=True)
        if active_secondary_style:
            st.markdown(style_preview_card(active_secondary_style, selected=False), unsafe_allow_html=True)
        st.markdown('### ⚙️ Flow Image Quick Panel')
        t1,t2,t3,t4=st.columns(4)
        with t1:
            thumb_media_mode=st.radio('Loại', ['Image','Video'], index=0, horizontal=True, key='thumb_media_mode')
            thumb_ref_mode=st.radio('Nguồn', ['Text','Reference image'], index=1 if upload else 0, horizontal=True, key='thumb_ref_mode')
        with t2:
            thumb_aspect=st.radio('Tỉ lệ', ['16:9','4:3','1:1','3:4','9:16'], index=4, horizontal=True, key='thumb_aspect')
            thumb_variants=st.radio('Số bản', ['1x','2x','3x','4x'], index=0, horizontal=True, key='thumb_variants')
        with t3:
            thumb_model=st.selectbox('Model ảnh', ['🍌 Nano Banana Pro','🍌 Nano Banana 2','Imagen 4','Imagen 4 Ultra'], index=1, key='thumb_model')
            thumb_style=st.selectbox('Template local', list(TEMPLATES.keys()), index=0, key='thumb_style')
        with t4:
            thumb_style_preset=st.selectbox('Phong cách tạo ảnh', list(STYLE_PRESETS.keys()), index=list(STYLE_PRESETS.keys()).index(global_style_preset) if global_style_preset in list(STYLE_PRESETS.keys()) else 0, key='thumb_style_preset')
            thumb_secondary_style_preset=st.selectbox('Blend phong cách phụ', ['(None)'] + list(STYLE_PRESETS.keys()), index=(['(None)'] + list(STYLE_PRESETS.keys())).index(active_secondary_style) if active_secondary_style in (['(None)'] + list(STYLE_PRESETS.keys())) else 0, key='thumb_secondary_style_preset')
            thumb_tertiary_style_preset=st.selectbox('Blend phong cách thứ 3', ['(None)'] + list(STYLE_PRESETS.keys()), index=(['(None)'] + list(STYLE_PRESETS.keys())).index(active_tertiary_style) if active_tertiary_style in (['(None)'] + list(STYLE_PRESETS.keys())) else 0, key='thumb_tertiary_style_preset')
            no_text=st.checkbox('Cấm chữ trong ảnh Flow', value=True, key='thumb_no_text')
            use_product_ref=st.checkbox('Khóa theo ảnh upload/reference', value=True if upload else False, key='thumb_product_ref')
            thumb_credits=estimate_thumb_credits(thumb_model, thumb_variants)
            st.metric('Credit ước tính', thumb_credits)

        st.caption('Ví dụ style: Cyberpunk, Realistic Commercial, Luxury Premium, Minimal Clean, Cute Pastel...')
        flow_thumb_prompt=build_thumbnail_flow_prompt(
            text, thumb_aspect, thumb_model, thumb_media_mode, thumb_style, thumb_style_preset, normalize_secondary_style(thumb_secondary_style_preset), normalize_secondary_style(thumb_tertiary_style_preset), no_text, use_product_ref, style_reference_summary(pdir)
        )

        with st.expander('🧾 Prompt tạo thumbnail cho Google Flow Image', expanded=False):
            st.text_area('Flow Image Prompt', value=flow_thumb_prompt, height=220, key='thumb_flow_prompt')
            st.code(flow_thumb_prompt)

        settings_json={
            'media_mode': thumb_media_mode,
            'source': thumb_ref_mode,
            'aspect_ratio': thumb_aspect,
            'variants': thumb_variants,
            'model': thumb_model,
            'local_template': thumb_style,
            'image_style_preset': thumb_style_preset,
            'secondary_style_preset': normalize_secondary_style(thumb_secondary_style_preset),
            'tertiary_style_preset': normalize_secondary_style(thumb_tertiary_style_preset),
            'style_palette': blended_style_palette(thumb_style_preset, normalize_secondary_style(thumb_secondary_style_preset), normalize_secondary_style(thumb_tertiary_style_preset)),
            'style_reference_summary': style_reference_summary(pdir),
            'no_text': no_text,
            'use_product_reference': use_product_ref,
            'estimated_credits': thumb_credits,
        }
        st.download_button(
            '⬇️ Tải thumbnail_flow_settings.json',
            json.dumps(settings_json, ensure_ascii=False, indent=2).encode('utf-8'),
            'thumbnail_flow_settings.json',
            mime='application/json',
            use_container_width=True
        )

        st.markdown('### 🖼️ Tạo thumbnail local trong app')
        vertical = thumb_aspect in ['9:16','3:4']
        if st.button('Tạo thumbnail local',type='primary', use_container_width=True):
            base_path=None
            if upload:
                safe_upload_name=safe_filename(upload.name)
                base_path=str(pdir/'frames'/safe_upload_name)
                Path(base_path).parent.mkdir(parents=True,exist_ok=True)
                upload.seek(0)
                Path(base_path).write_bytes(upload.read())
                upload.seek(0)
            thumb=make_thumbnail(pdir,base_path,text,template,vertical)
            st.image(thumb,use_container_width=True)
            st.download_button('⬇️ Tải thumbnail',Path(thumb).read_bytes(),Path(thumb).name, use_container_width=True)

        st.info('Cách dùng với Google Flow: upload ảnh reference nếu có, chọn Image, chọn đúng tỉ lệ/model/số bản như panel này, chọn phong cách tạo ảnh như Cyberpunk hoặc Realistic Commercial, dán prompt ở trên rồi tạo ảnh thumbnail.')
if has_tab('🧾 Logs'):
    with tab('🧾 Logs'): st.markdown('## 🧾 Logs'); st.dataframe(read_errors(200),use_container_width=True)
if has_tab('🚀 Deploy'):
    with tab('🚀 Deploy'):
        st.markdown('## 🚀 Deploy checklist'); st.json({'app.py':Path('app.py').exists(),'requirements.txt':Path('requirements.txt').exists(),'packages.txt':Path('packages.txt').exists(),'.streamlit/config.toml':Path('.streamlit/config.toml').exists(),'.gitignore':Path('.gitignore').exists()}); st.code('git init\ngit add .\ngit commit -m "AUTO VEO Studio v2.1"\ngit branch -M main\ngit remote add origin https://github.com/YOUR_USERNAME/auto-veo-studio.git\ngit push -u origin main',language='bash')
st.caption('v3.5.1 Final Checked Stable: thêm setting giống Google Flow mobile để copy prompt và chọn model/tỉ lệ/thời lượng/credit nhanh hơn.')
