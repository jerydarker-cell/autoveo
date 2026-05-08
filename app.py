# app.py
# AUTO VEO Studio v1.2 — Personal AI Video Studio
# Chạy: streamlit run app.py
#
# Chức năng chính:
# - Project Library: mỗi dự án có thư mục riêng, lưu prompt/assets/metadata.
# - Prompt Library: save/favorite/copy prompt/template ngành.
# - Character Library: hồ sơ nhân vật + ảnh mặt/toàn thân/outfit.
# - Queue + Batch render + Retry.
# - Estimate cost trước khi render.
# - Timeline Video Studio: nhiều cảnh -> render từng clip -> nối thành video dài.
# - Auto Script -> Shot List -> Keyframes -> Video -> Final MP4.
# - Audio Studio: nhạc nền, voice-over, subtitle SRT, ghép audio/video.
# - Video Tools: upscale, crop/convert 16:9/9:16, blur background, compress.
#
# Ghi chú:
# - Đây là app cá nhân local-first, dùng SQLite và thư mục local.
# - Render thật dùng Gemini API/Veo. Mock mode dùng để test UI không tốn API.

from __future__ import annotations

import base64
import csv
import hashlib
import io
import json
import math
import os
import platform
import re
import shutil
import sqlite3
import subprocess
import tempfile
import time
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import numpy as np
import streamlit as st
from PIL import Image, ImageDraw, ImageOps

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

try:
    import cv2
except Exception:
    cv2 = None

try:
    import imageio.v2 as imageio
except Exception:
    imageio = None

try:
    from google import genai
    from google.genai import types
except Exception:
    genai = None
    types = None


APP_TITLE = "AUTO VEO Studio"
APP_VERSION = "1.5.0 Personal Deploy-Ready"
ROOT = Path(__file__).parent.resolve()
DATA_DIR = ROOT / "data"
PROJECTS_DIR = ROOT / "projects"
LIB_DIR = ROOT / "library"
CHAR_DIR = LIB_DIR / "characters"
BACKUPS_DIR = ROOT / "backups"
LOGS_DIR = ROOT / "logs"
DB_PATH = DATA_DIR / "studio.sqlite3"
DEFAULT_PROJECT_SLUG = "default_project"

for d in [DATA_DIR, PROJECTS_DIR, LIB_DIR, CHAR_DIR, BACKUPS_DIR, LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

VIDEO_MODELS = [
    "veo-3.1-generate-preview",
    "veo-3.1-fast-generate-preview",
    "veo-3.1-lite-generate-preview",
    "veo-3.0-generate-001",
    "veo-3.0-fast-generate-001",
]

IMAGE_MODELS_NATIVE = [
    "gemini-3.1-flash-image-preview",
    "gemini-3-pro-image-preview",
    "gemini-2.5-flash-image",
]

IMAGE_MODELS_IMAGEN = [
    "imagen-4.0-generate-001",
    "imagen-4.0-fast-generate-001",
    "imagen-4.0-ultra-generate-001",
]

DEFAULT_NEGATIVE = (
    "low quality, blurry, distorted hands, deformed face, bad anatomy, jitter, flicker, "
    "identity drift, outfit change, unreadable text, watermark, logo"
)

PROMPT_TEMPLATES = {
    "Quảng cáo sản phẩm": {
        "image": "A premium studio product photo of [PRODUCT], glossy reflections, clean luxury background, hero composition, commercial lighting, ultra detailed.",
        "video": "A cinematic luxury advertisement for [PRODUCT]. The camera slowly orbits around the product, highlighting texture, packaging, and premium details. Add elegant lighting, smooth motion, and aspirational mood.",
    },
    "Nhân vật TikTok": {
        "image": "A charismatic Vietnamese TikTok creator, expressive face, trendy outfit, colorful studio background, vertical composition, social media style.",
        "video": "A vertical TikTok-style video of a charismatic Vietnamese creator speaking confidently to camera. Energetic gestures, clean background, punchy camera movement, viral short-form pacing.",
    },
    "Phim ngắn": {
        "image": "A cinematic still from a dramatic short film, strong character emotion, realistic lighting, 35mm film look, shallow depth of field.",
        "video": "A cinematic short film scene. A character faces an emotional turning point. Slow camera push-in, realistic acting, atmospheric lighting, natural ambience, filmic composition.",
    },
    "Trailer": {
        "image": "An epic trailer key art frame, dramatic lighting, high contrast, hero subject, cinematic poster quality.",
        "video": "An intense cinematic trailer shot with rising tension. Dynamic camera movement, dramatic reveal, powerful atmosphere, high-end film production look.",
    },
    "Thời trang": {
        "image": "A high-fashion editorial portrait, elegant outfit, runway lighting, luxury magazine aesthetic, detailed fabric texture.",
        "video": "A fashion campaign video. The model walks slowly under elegant studio lights, fabric moves naturally, camera tracks with smooth luxury editorial style.",
    },
    "Bất động sản": {
        "image": "A luxury real estate interior, warm daylight, modern furniture, wide angle architectural photography, premium lifestyle.",
        "video": "A cinematic real estate walkthrough of a luxury property. Smooth gimbal movement, wide-angle view, warm daylight, elegant transitions between rooms.",
    },
    "Đồ ăn": {
        "image": "A mouth-watering food photography shot of [DISH], steam, rich texture, appetizing lighting, restaurant commercial style.",
        "video": "A delicious food commercial. Close-up macro shots of [DISH], steam rising, sauce pouring, slow motion details, warm appetizing lighting.",
    },
    "Mỹ phẩm": {
        "image": "A premium cosmetic product shot, soft pastel background, glossy packaging, clean beauty campaign aesthetic.",
        "video": "A beauty product commercial for [PRODUCT]. Slow macro camera movement, liquid/gloss texture, elegant reflections, soft premium lighting.",
    },
    "Âm nhạc / MV": {
        "image": "A music video still, stylish artist, dramatic colored lights, atmospheric stage, cinematic mood.",
        "video": "A cinematic music video shot. The artist performs under dramatic colored lights, smoke haze, smooth camera motion, expressive mood, synchronized visual rhythm.",
    },
    "Giáo dục": {
        "image": "A clean educational visual explaining [TOPIC], modern composition, friendly colors, professional infographic style.",
        "video": "An educational explainer video about [TOPIC]. Clear visual metaphors, smooth animated scenes, friendly professional tone, simple composition.",
    },
}

WORKFLOW_PRESETS = {
    "TikTok 30s": {
        "platform": "TikTok / Instagram Reels",
        "aspect_ratio": "9:16",
        "duration": 6,
        "resolution": "720p",
        "scenes": [
            ("Hook 0-3s", "Open with a bold visual hook. The subject appears immediately, strong movement, attention-grabbing composition, no slow intro."),
            ("Problem / Desire", "Show the main problem, desire, or transformation promise in a clear cinematic way."),
            ("Main reveal", "Reveal the character/product/result with stronger lighting, dynamic camera push-in, satisfying motion."),
            ("Proof / Detail", "Show close-up details, benefit, texture, emotion, or before-after evidence."),
            ("Call to action", "End with a memorable final shot, clean composition, strong emotional finish, designed for loop replay."),
        ],
        "subtitle_style": "short punchy captions, 1 idea per line",
    },
    "YouTube Shorts 60s": {
        "platform": "YouTube Shorts",
        "aspect_ratio": "9:16",
        "duration": 8,
        "resolution": "720p",
        "scenes": [
            ("Cold open", "Start with the most interesting moment first, cinematic vertical shot, immediate curiosity."),
            ("Context", "Quickly show where we are and who/what the story is about, clear subject and setting."),
            ("Development 1", "Build the story with a new visual beat, smooth camera movement, consistent character."),
            ("Development 2", "Add escalation, reveal more detail, keep pacing energetic."),
            ("Turning point", "Show a surprising or emotionally strong moment, dramatic lighting."),
            ("Payoff", "Deliver the answer/result/transformation in a satisfying visual scene."),
            ("CTA / Loop ending", "End with a clean final image that can loop back to the beginning."),
        ],
        "subtitle_style": "clear narration captions, 2-5 seconds per caption",
    },
    "Product Ads 4 cảnh": {
        "platform": "Product Ads",
        "aspect_ratio": "9:16",
        "duration": 8,
        "resolution": "1080p",
        "scenes": [
            ("Hero product reveal", "Premium hero shot of the product, elegant lighting, slow camera orbit, luxury commercial style."),
            ("Problem-solution", "Show the product solving a clear user problem or creating a desirable transformation."),
            ("Feature close-ups", "Macro close-ups of texture, materials, packaging, button, label, or signature details."),
            ("Lifestyle CTA", "Final lifestyle shot with product in use, aspirational mood, clean call-to-action style ending."),
        ],
        "subtitle_style": "benefit-driven ad captions",
    },
    "Trailer 45s": {
        "platform": "Trailer",
        "aspect_ratio": "16:9",
        "duration": 8,
        "resolution": "1080p",
        "scenes": [
            ("Atmospheric opening", "Wide cinematic establishing shot, mysterious tone, strong world-building."),
            ("Character introduction", "Introduce the main character with a memorable close-up and distinctive silhouette."),
            ("Conflict appears", "Reveal the central threat/conflict with dramatic lighting and tension."),
            ("Action escalation", "Fast cinematic movement, chase/action/reveal moment, high stakes."),
            ("Emotional beat", "Slow powerful emotional shot, character decision, intimate camera."),
            ("Final money shot", "Epic final reveal, poster-like composition, trailer ending energy."),
        ],
        "subtitle_style": "cinematic trailer captions",
    },
    "Real Estate Tour 48s": {
        "platform": "Real Estate",
        "aspect_ratio": "16:9",
        "duration": 8,
        "resolution": "1080p",
        "scenes": [
            ("Exterior hero", "Luxury exterior establishing shot, golden hour, smooth drone/gimbal feel."),
            ("Living room", "Smooth walkthrough into the living room, wide angle, warm daylight, premium interior."),
            ("Kitchen detail", "Elegant kitchen details, marble/wood texture, slow pan, lifestyle mood."),
            ("Bedroom suite", "Master bedroom reveal, soft lighting, calm premium atmosphere."),
            ("Amenities", "Show pool/balcony/view/amenity, aspirational lifestyle composition."),
            ("Closing hero", "Final wide shot with strongest selling point, polished commercial finish."),
        ],
        "subtitle_style": "minimal luxury captions",
    },
    "Food Reel 30s": {
        "platform": "Food / Restaurant",
        "aspect_ratio": "9:16",
        "duration": 6,
        "resolution": "720p",
        "scenes": [
            ("Ingredient hook", "Extreme close-up of fresh ingredients, texture, steam, appetizing motion."),
            ("Cooking action", "Sizzling/pouring/mixing action, dynamic macro camera, warm lighting."),
            ("Hero dish reveal", "Final dish reveal with steam and glossy texture, mouth-watering composition."),
            ("Detail bite", "Close-up bite/cut/pull/apart moment, slow motion, satisfying movement."),
            ("Restaurant CTA", "Final branded lifestyle shot, dish on table, inviting warm mood."),
        ],
        "subtitle_style": "short appetizing captions",
    },
}


VI_SPECIALIZED_PROMPTS = {
    "Mỹ phẩm cao cấp": {
        "image": "Ảnh quảng cáo mỹ phẩm cao cấp cho [SẢN PHẨM], nền pastel sạch, ánh sáng mềm, chất liệu thủy tinh/bóng cao cấp, bố cục luxury skincare, không chữ, không watermark.",
        "video": "Video quảng cáo mỹ phẩm cao cấp cho [SẢN PHẨM]. Cảnh mở đầu là hero shot sản phẩm, ánh sáng mềm, giọt serum chuyển động chậm, macro texture, cảm giác sạch và sang. Camera orbit chậm, giữ bao bì sắc nét, không logo giả, không chữ lỗi."
    },
    "Bất động sản cao cấp": {
        "image": "Ảnh kiến trúc bất động sản cao cấp, không gian hiện đại, ánh sáng vàng tự nhiên, nội thất sang trọng, góc rộng, cảm giác premium lifestyle.",
        "video": "Video walkthrough bất động sản cao cấp. Máy quay gimbal di chuyển mượt từ exterior vào living room, kitchen, bedroom, balcony/view. Ánh sáng tự nhiên, wide angle, chuyển cảnh sang trọng, không rung, không méo tường."
    },
    "Đồ ăn nhà hàng": {
        "image": "Ảnh món ăn nhà hàng [MÓN ĂN], hơi nóng, texture rõ, ánh sáng ấm, bố cục hấp dẫn, màu sắc ngon miệng, commercial food photography.",
        "video": "Video food reel cho [MÓN ĂN]. Macro shot nguyên liệu tươi, cảnh nấu sizzling, sauce pouring slow motion, hero dish reveal với hơi nóng, close-up kéo/cắt/cắn món ăn, ánh sáng ấm, nhịp nhanh dọc 9:16."
    },
    "Thời trang lookbook": {
        "image": "Ảnh lookbook thời trang, người mẫu Việt Nam trưởng thành, outfit [OUTFIT], ánh sáng editorial, phông nền tối giản, chất liệu vải rõ, dáng pose tự nhiên.",
        "video": "Video fashion lookbook. Người mẫu đi chậm trong studio/editorial location, camera tracking mượt, vải chuyển động tự nhiên, close-up chi tiết outfit, giữ khuôn mặt/tóc/trang phục nhất quán."
    },
    "Nhân vật TikTok/Reels": {
        "image": "Ảnh creator Việt Nam trưởng thành, biểu cảm tự tin, outfit trendy, background sạch, ánh sáng social media, bố cục dọc 9:16.",
        "video": "Video TikTok/Reels nhân vật nói chuyện với camera. Hook mạnh trong 3 giây đầu, biểu cảm tự nhiên, gesture rõ, camera nhẹ nhàng push-in, background sạch, caption style ngắn, năng lượng tích cực."
    },
    "Trailer phim ngắn": {
        "image": "Key visual phim ngắn cinematic, nhân vật chính trong khoảnh khắc căng thẳng, ánh sáng dramatic, bố cục poster, màu điện ảnh.",
        "video": "Trailer phim ngắn. Mở đầu atmospheric establishing shot, giới thiệu nhân vật, conflict reveal, action escalation, emotional beat, final money shot. Camera điện ảnh, âm thanh căng thẳng, giữ continuity."
    },
    "Giáo dục/khóa học": {
        "image": "Visual khóa học [CHỦ ĐỀ], thiết kế sạch, chuyên nghiệp, màu thân thiện, biểu tượng học tập, bố cục rõ ràng.",
        "video": "Video giới thiệu khóa học [CHỦ ĐỀ]. Mở đầu nêu vấn đề, sau đó giải thích lợi ích, minh họa bằng hình ảnh đơn giản, tone chuyên nghiệp thân thiện, rõ ràng, dễ hiểu."
    },
    "Du lịch/khách sạn": {
        "image": "Ảnh du lịch cao cấp tại [ĐỊA ĐIỂM], ánh sáng đẹp, phong cảnh ấn tượng, cảm giác nghỉ dưỡng sang trọng, màu cinematic.",
        "video": "Video du lịch/khách sạn tại [ĐỊA ĐIỂM]. Cảnh mở đầu phong cảnh đẹp, room reveal, trải nghiệm ăn uống/spa/hồ bơi, sunset closing shot. Camera mượt, ánh sáng tự nhiên, cảm giác aspirational."
    },
}


def preset_to_timeline_rows(preset_name: str, base_topic: str = "", duration_override: int | None = None) -> list[dict[str, Any]]:
    preset = WORKFLOW_PRESETS[preset_name]
    dur = int(duration_override or preset["duration"])
    topic = base_topic.strip()
    rows = []
    for i, (title, prompt) in enumerate(preset["scenes"], 1):
        topic_line = f" Topic/product/story: {topic}." if topic else ""
        rows.append({
            "scene": i,
            "duration": dur,
            "description": title,
            "prompt": f"{prompt}{topic_line} Platform target: {preset['platform']}. Format: {preset['aspect_ratio']}.",
        })
    return rows


def install_ffmpeg_hint() -> str:
    if ffmpeg_path():
        return "FFmpeg đã có trong PATH."
    if platform.system() == "Windows":
        return "Chưa thấy FFmpeg. Cách nhanh: mở PowerShell/CMD Admin và chạy: winget install Gyan.FFmpeg"
    if platform.system() == "Darwin":
        return "Chưa thấy FFmpeg. Cách nhanh: cài Homebrew rồi chạy: brew install ffmpeg"
    return "Chưa thấy FFmpeg. Ubuntu/Debian: sudo apt update && sudo apt install ffmpeg"



# -----------------------------
# Page CSS
# -----------------------------
st.set_page_config(page_title=APP_TITLE, page_icon="🎬", layout="wide", initial_sidebar_state="expanded")

CSS = """
<style>
.block-container { padding-top: 1rem; }
.hero {
  padding: 24px 28px;
  border-radius: 28px;
  background:
    radial-gradient(circle at 12% 15%, rgba(255, 89, 185, .32), transparent 35%),
    radial-gradient(circle at 86% 8%, rgba(75, 165, 255, .30), transparent 34%),
    linear-gradient(135deg, rgba(115,80,255,.22), rgba(255,255,255,.04));
  border: 1px solid rgba(255,255,255,.14);
  box-shadow: 0 18px 55px rgba(0,0,0,.18);
  margin-bottom: 18px;
}
.hero h1 { margin: 0; font-size: 2.15rem; letter-spacing: -.035em; }
.hero p { margin: .55rem 0 0; opacity: .86; font-size: 1.02rem; }
.badge {
  display: inline-flex; align-items: center; gap: 7px;
  border: 1px solid rgba(255,255,255,.17); border-radius: 999px;
  padding: 6px 11px; margin: 5px 7px 0 0;
  background: rgba(255,255,255,.065); font-size: .88rem;
}
.card {
  padding: 17px; border-radius: 21px; background: rgba(255,255,255,.055);
  border: 1px solid rgba(255,255,255,.12);
  box-shadow: 0 10px 34px rgba(0,0,0,.10);
}
.small { opacity: .72; font-size: .88rem; }
.ok {
  padding: 7px 11px; border-radius: 999px; display: inline-block;
  background: rgba(0, 180, 110, .13); border: 1px solid rgba(0, 180, 110, .30);
}
.warn {
  padding: 7px 11px; border-radius: 999px; display: inline-block;
  background: rgba(255, 190, 60, .13); border: 1px solid rgba(255, 190, 60, .32);
}
.danger {
  padding: 7px 11px; border-radius: 999px; display: inline-block;
  background: rgba(255, 70, 70, .13); border: 1px solid rgba(255, 70, 70, .32);
}
.asset-name { font-size: .84rem; opacity: .78; word-break: break-all; }
hr { opacity: .20; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# -----------------------------
# DB helpers
# -----------------------------
def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def slugify(text: str, fallback: str = "project") -> str:
    s = re.sub(r"[^a-zA-Z0-9_-]+", "_", text.strip().lower()).strip("_")
    return s[:60] or fallback


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row else None


def safe_json_loads(x: str | None, default: Any) -> Any:
    if not x:
        return default
    try:
        return json.loads(x)
    except Exception:
        return default


def init_db() -> None:
    with db() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            slug TEXT NOT NULL UNIQUE,
            description TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            asset_type TEXT NOT NULL,
            path TEXT NOT NULL,
            prompt TEXT DEFAULT '',
            settings_json TEXT DEFAULT '{}',
            status TEXT DEFAULT 'done',
            created_at TEXT NOT NULL,
            FOREIGN KEY(project_id) REFERENCES projects(id)
        )
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT DEFAULT '',
            prompt TEXT NOT NULL,
            is_favorite INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS characters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            bible TEXT DEFAULT '',
            locked_traits TEXT DEFAULT '',
            face_path TEXT DEFAULT '',
            body_path TEXT DEFAULT '',
            outfit_path TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            job_type TEXT NOT NULL,
            prompt TEXT NOT NULL,
            settings_json TEXT DEFAULT '{}',
            status TEXT DEFAULT 'pending',
            result_paths_json TEXT DEFAULT '[]',
            error TEXT DEFAULT '',
            cost_estimate REAL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(project_id) REFERENCES projects(id)
        )
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS usage_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            model TEXT DEFAULT '',
            units REAL DEFAULT 0,
            estimated_cost REAL DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY(project_id) REFERENCES projects(id)
        )
        """)
        # Ensure default project exists.
        exists = conn.execute("SELECT id FROM projects WHERE slug=?", (DEFAULT_PROJECT_SLUG,)).fetchone()
        if not exists:
            conn.execute(
                "INSERT INTO projects(name, slug, description, created_at, updated_at) VALUES (?,?,?,?,?)",
                ("Default Project", DEFAULT_PROJECT_SLUG, "Dự án mặc định", now(), now()),
            )
    (PROJECTS_DIR / DEFAULT_PROJECT_SLUG).mkdir(parents=True, exist_ok=True)


init_db()


def create_project(name: str, description: str = "") -> dict[str, Any]:
    base = slugify(name, "project")
    slug = base
    i = 2
    with db() as conn:
        while conn.execute("SELECT id FROM projects WHERE slug=?", (slug,)).fetchone():
            slug = f"{base}_{i}"
            i += 1
        conn.execute(
            "INSERT INTO projects(name, slug, description, created_at, updated_at) VALUES (?,?,?,?,?)",
            (name.strip() or "Untitled Project", slug, description, now(), now()),
        )
        pid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    pdir = PROJECTS_DIR / slug
    for sub in ["images", "videos", "audio", "frames", "timeline", "exports", "uploads"]:
        (pdir / sub).mkdir(parents=True, exist_ok=True)
    save_project_manifest(pid)
    return get_project(pid)


def list_projects() -> list[dict[str, Any]]:
    with db() as conn:
        rows = conn.execute("SELECT * FROM projects ORDER BY updated_at DESC, id DESC").fetchall()
    return [dict(r) for r in rows]


def get_project(project_id: int) -> dict[str, Any]:
    with db() as conn:
        row = conn.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
    if not row:
        return create_project("Default Project")
    return dict(row)


def touch_project(project_id: int) -> None:
    with db() as conn:
        conn.execute("UPDATE projects SET updated_at=? WHERE id=?", (now(), project_id))


def project_dir(project: dict[str, Any]) -> Path:
    p = PROJECTS_DIR / project["slug"]
    p.mkdir(parents=True, exist_ok=True)
    for sub in ["images", "videos", "audio", "frames", "timeline", "exports", "uploads"]:
        (p / sub).mkdir(parents=True, exist_ok=True)
    return p


def save_project_manifest(project_id: int) -> Path:
    project = get_project(project_id)
    pdir = project_dir(project)
    with db() as conn:
        assets = [dict(r) for r in conn.execute("SELECT * FROM assets WHERE project_id=? ORDER BY id", (project_id,)).fetchall()]
        jobs = [dict(r) for r in conn.execute("SELECT * FROM jobs WHERE project_id=? ORDER BY id", (project_id,)).fetchall()]
    manifest = {"project": project, "assets": assets, "jobs": jobs, "exported_at": now(), "app_version": APP_VERSION}
    path = pdir / "project_manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def add_asset(project_id: int, asset_type: str, path: str | Path, prompt: str = "", settings: dict[str, Any] | None = None) -> int:
    touch_project(project_id)
    with db() as conn:
        conn.execute(
            "INSERT INTO assets(project_id, asset_type, path, prompt, settings_json, status, created_at) VALUES (?,?,?,?,?,?,?)",
            (project_id, asset_type, str(path), prompt, json.dumps(settings or {}, ensure_ascii=False), "done", now()),
        )
        aid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    save_project_manifest(project_id)
    return int(aid)


def list_assets(project_id: int, asset_type: str | None = None, limit: int = 80) -> list[dict[str, Any]]:
    sql = "SELECT * FROM assets WHERE project_id=?"
    params: list[Any] = [project_id]
    if asset_type:
        sql += " AND asset_type=?"
        params.append(asset_type)
    sql += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    with db() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def rename_asset(asset_id: int, new_name: str) -> tuple[bool, str]:
    with db() as conn:
        row = conn.execute("SELECT * FROM assets WHERE id=?", (asset_id,)).fetchone()
    if not row:
        return False, "Không thấy asset."
    old = Path(row["path"])
    if not old.exists():
        return False, "File không tồn tại."
    name = slugify(new_name, "asset")
    new_path = old.with_name(name + old.suffix)
    if new_path.exists():
        new_path = old.with_name(f"{name}_{int(time.time())}{old.suffix}")
    old.rename(new_path)
    with db() as conn:
        conn.execute("UPDATE assets SET path=? WHERE id=?", (str(new_path), asset_id))
    save_project_manifest(row["project_id"])
    return True, str(new_path)


def export_project_zip(project_id: int) -> Path:
    project = get_project(project_id)
    pdir = project_dir(project)
    save_project_manifest(project_id)
    out = pdir / "exports" / f"{project['slug']}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for path in pdir.rglob("*"):
            if path.is_file() and path != out:
                z.write(path, arcname=path.relative_to(pdir))
    return out


def add_usage(project_id: int, event_type: str, model: str = "", units: float = 0, estimated_cost: float = 0) -> None:
    with db() as conn:
        conn.execute(
            "INSERT INTO usage_log(project_id, event_type, model, units, estimated_cost, created_at) VALUES (?,?,?,?,?,?)",
            (project_id, event_type, model, units, estimated_cost, now()),
        )


# -----------------------------
# Prompt library
# -----------------------------
def save_prompt(title: str, category: str, prompt: str, favorite: bool = False) -> int:
    with db() as conn:
        conn.execute(
            "INSERT INTO prompts(title, category, prompt, is_favorite, created_at, updated_at) VALUES (?,?,?,?,?,?)",
            (title.strip() or "Untitled prompt", category, prompt, 1 if favorite else 0, now(), now()),
        )
        return int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])


def list_prompts(favorites_only: bool = False, category: str | None = None) -> list[dict[str, Any]]:
    sql = "SELECT * FROM prompts WHERE 1=1"
    params: list[Any] = []
    if favorites_only:
        sql += " AND is_favorite=1"
    if category:
        sql += " AND category=?"
        params.append(category)
    sql += " ORDER BY is_favorite DESC, updated_at DESC, id DESC"
    with db() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def update_prompt_favorite(prompt_id: int, favorite: bool) -> None:
    with db() as conn:
        conn.execute("UPDATE prompts SET is_favorite=?, updated_at=? WHERE id=?", (1 if favorite else 0, now(), prompt_id))


def copy_button(text: str, label: str = "Copy Prompt") -> None:
    import html
    esc = html.escape(text).replace("\n", "\\n").replace("'", "\\'")
    button_html = f"""
    <button onclick="navigator.clipboard.writeText('{esc}'); this.innerText='Copied ✓';"
      style="border-radius:10px;padding:8px 12px;border:1px solid rgba(255,255,255,.22);background:rgba(255,255,255,.08);color:inherit;cursor:pointer;">
      {html.escape(label)}
    </button>
    """
    st.components.v1.html(button_html, height=46)


# -----------------------------
# Character library
# -----------------------------
def save_uploaded_to(uploaded_file, folder: Path, prefix: str = "upload") -> str:
    folder.mkdir(parents=True, exist_ok=True)
    suffix = Path(uploaded_file.name).suffix or ".bin"
    name = f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}{suffix}"
    path = folder / name
    uploaded_file.seek(0)
    path.write_bytes(uploaded_file.read())
    uploaded_file.seek(0)
    return str(path)


def create_character(name: str, bible: str, locked_traits: str, face, body, outfit) -> int:
    char_slug = slugify(name, "character")
    folder = CHAR_DIR / char_slug
    folder.mkdir(parents=True, exist_ok=True)
    face_path = save_uploaded_to(face, folder, "face") if face else ""
    body_path = save_uploaded_to(body, folder, "body") if body else ""
    outfit_path = save_uploaded_to(outfit, folder, "outfit") if outfit else ""
    with db() as conn:
        conn.execute(
            "INSERT INTO characters(name, bible, locked_traits, face_path, body_path, outfit_path, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
            (name.strip() or "Unnamed Character", bible, locked_traits, face_path, body_path, outfit_path, now(), now()),
        )
        return int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])


def list_characters() -> list[dict[str, Any]]:
    with db() as conn:
        rows = conn.execute("SELECT * FROM characters ORDER BY updated_at DESC, id DESC").fetchall()
    return [dict(r) for r in rows]


def character_ref_images(character: dict[str, Any]) -> list[Image.Image]:
    imgs = []
    for key in ["face_path", "body_path", "outfit_path"]:
        p = character.get(key, "")
        if p and Path(p).exists():
            try:
                imgs.append(Image.open(p).convert("RGB"))
            except Exception:
                pass
    return imgs[:3]


# -----------------------------
# Environment / file helpers
# -----------------------------
def ffmpeg_path() -> str | None:
    return shutil.which("ffmpeg")


def ffprobe_path() -> str | None:
    return shutil.which("ffprobe")


def run_cmd(cmd: list[str], timeout: int = 600) -> tuple[bool, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        out = (p.stdout or "") + (p.stderr or "")
        return p.returncode == 0, out[-4000:]
    except Exception as e:
        return False, str(e)


def pil_from_upload(uploaded_file) -> Image.Image:
    uploaded_file.seek(0)
    img = Image.open(uploaded_file)
    uploaded_file.seek(0)
    return ImageOps.exif_transpose(img).convert("RGB")


def copy_to_project(project: dict[str, Any], src: str | Path, subfolder: str, wanted_name: str | None = None) -> str:
    src = Path(src)
    dest_dir = project_dir(project) / subfolder
    dest_dir.mkdir(parents=True, exist_ok=True)
    name = wanted_name or src.name
    name = re.sub(r"[^a-zA-Z0-9_.-]+", "_", name)
    dest = dest_dir / name
    if dest.exists():
        dest = dest_dir / f"{dest.stem}_{datetime.now().strftime('%H%M%S_%f')}{dest.suffix}"
    shutil.copy2(src, dest)
    return str(dest)


def save_pil_to_project(project: dict[str, Any], img: Image.Image, subfolder: str, prefix: str) -> str:
    dest_dir = project_dir(project) / subfolder
    dest_dir.mkdir(parents=True, exist_ok=True)
    path = dest_dir / f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.png"
    img.save(path)
    return str(path)


def is_video(path: str | Path) -> bool:
    return Path(path).suffix.lower() in [".mp4", ".mov", ".m4v", ".webm"]


def is_image(path: str | Path) -> bool:
    return Path(path).suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"]


def show_asset_preview(path: str, caption: str = "") -> None:
    p = Path(path)
    if not p.exists():
        st.error(f"Không thấy file: {path}")
        return
    if is_image(p):
        st.image(str(p), caption=caption or p.name, use_container_width=True)
    elif is_video(p):
        st.video(str(p))
        if caption:
            st.caption(caption)
    elif p.suffix.lower() in [".mp3", ".wav", ".m4a"]:
        st.audio(str(p))
    else:
        st.code(p.read_text(encoding="utf-8", errors="ignore")[:2000])


def download_file(path: str, label: str = "⬇️ Tải file") -> None:
    p = Path(path)
    if not p.exists():
        return
    mime = {
        ".mp4": "video/mp4",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".zip": "application/zip",
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".srt": "text/plain",
        ".json": "application/json",
    }.get(p.suffix.lower(), "application/octet-stream")
    st.download_button(label, p.read_bytes(), file_name=p.name, mime=mime, use_container_width=True)



# -----------------------------
# Quality / Backup / Publish helpers
# -----------------------------
def auto_backup_project(project_id: int, reason: str = "manual") -> Path:
    project = get_project(project_id)
    pdir = project_dir(project)
    save_project_manifest(project_id)
    out_dir = BACKUPS_DIR / project["slug"]
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{project['slug']}_backup_{reason}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for path in pdir.rglob("*"):
            if path.is_file():
                z.write(path, arcname=path.relative_to(pdir))
    return out


def daily_backup_if_needed(project_id: int) -> Path | None:
    project = get_project(project_id)
    out_dir = BACKUPS_DIR / project["slug"]
    out_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y%m%d")
    existing = list(out_dir.glob(f"{project['slug']}_backup_daily_{today}_*.zip"))
    if existing:
        return None
    return auto_backup_project(project_id, "daily")


def list_backups(project: dict[str, Any]) -> list[Path]:
    folder = BACKUPS_DIR / project["slug"]
    if not folder.exists():
        return []
    return sorted(folder.glob("*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)


def check_prompt_quality(prompt: str, mode: str = "video", negative_prompt: str = "") -> dict[str, Any]:
    text = (prompt or "").lower()
    checks = [
        ("Nhân vật/chủ thể", ["person", "character", "woman", "man", "girl", "boy", "product", "subject", "nhân vật", "người", "sản phẩm", "chủ thể"]),
        ("Bối cảnh", ["in ", "at ", "on ", "background", "location", "scene", "bối cảnh", "địa điểm", "căn phòng", "đường phố", "studio"]),
        ("Hành động", ["walk", "run", "hold", "look", "turn", "move", "pour", "reveal", "show", "bước", "cầm", "nhìn", "di chuyển", "xoay", "đổ", "mở"]),
        ("Camera", ["camera", "lens", "shot", "close-up", "wide", "dolly", "pan", "tracking", "zoom", "góc máy", "ống kính", "cận cảnh", "toàn cảnh"]),
        ("Ánh sáng/mood", ["light", "lighting", "neon", "golden", "dramatic", "soft", "shadow", "ánh sáng", "đèn", "màu", "tâm trạng"]),
    ]
    if mode == "video":
        checks.append(("Chuyển động", ["motion", "movement", "animate", "camera moves", "smooth", "natural", "chuyển động", "di chuyển", "mượt"]))
        checks.append(("Tính nhất quán", ["consistent", "preserve", "same", "continuity", "identity", "giữ nguyên", "nhất quán", "không đổi"]))
    passed, missing = [], []
    for name, words in checks:
        if any(w in text for w in words):
            passed.append(name)
        else:
            missing.append(name)
    if negative_prompt.strip() or "avoid:" in text or "negative" in text:
        passed.append("Negative prompt")
    else:
        missing.append("Negative prompt")

    length = len(prompt.strip())
    if length < 80:
        score = 45
        missing.append("Prompt quá ngắn")
    elif length < 180:
        score = 65
    else:
        score = 80
    score += len(passed) * 3
    score -= len(missing) * 4
    score = max(0, min(100, score))

    suggestions = []
    if "Nhân vật/chủ thể" in missing:
        suggestions.append("Thêm chủ thể rõ: ai/cái gì, tuổi/phong cách/sản phẩm.")
    if "Bối cảnh" in missing:
        suggestions.append("Thêm bối cảnh: ở đâu, thời gian, môi trường, background.")
    if "Camera" in missing:
        suggestions.append("Thêm camera: close-up/wide/dolly/tracking/35mm.")
    if "Ánh sáng/mood" in missing:
        suggestions.append("Thêm ánh sáng: neon, golden hour, studio, dramatic...")
    if "Chuyển động" in missing:
        suggestions.append("Thêm chuyển động: nhân vật làm gì, camera di chuyển thế nào.")
    if "Tính nhất quán" in missing and mode == "video":
        suggestions.append("Thêm câu giữ nhất quán nhân vật/outfit/mặt/tóc qua toàn clip.")
    if "Negative prompt" in missing:
        suggestions.append("Thêm negative prompt để giảm lỗi mặt/tay/flicker/watermark.")
    if "Prompt quá ngắn" in missing:
        suggestions.append("Prompt nên dài hơn 2-5 câu, có chủ thể + bối cảnh + hành động + camera + ánh sáng.")
    return {"score": score, "passed": passed, "missing": missing, "suggestions": suggestions}


def show_prompt_quality(prompt: str, mode: str = "video", negative_prompt: str = "") -> dict[str, Any]:
    result = check_prompt_quality(prompt, mode, negative_prompt)
    score = result["score"]
    if score >= 80:
        st.success(f"Prompt quality: {score}/100 — tốt để render.")
    elif score >= 60:
        st.warning(f"Prompt quality: {score}/100 — dùng được nhưng nên bổ sung.")
    else:
        st.error(f"Prompt quality: {score}/100 — nên chỉnh trước khi tốn API.")
    c1, c2 = st.columns(2)
    with c1:
        st.caption("Đã có")
        st.write(", ".join(result["passed"]) if result["passed"] else "Chưa có mục nào rõ.")
    with c2:
        st.caption("Còn thiếu")
        st.write(", ".join(dict.fromkeys(result["missing"])) if result["missing"] else "Không thiếu mục quan trọng.")
    if result["suggestions"]:
        with st.expander("Gợi ý cải thiện prompt", expanded=False):
            for s in result["suggestions"]:
                st.write("• " + s)
    return result


def build_social_caption(prompt: str, platform: str, tone: str = "cinematic") -> str:
    base = re.sub(r"\s+", " ", prompt.strip())
    base = base[:260] + ("..." if len(base) > 260 else "")
    if platform.lower().startswith("tiktok") or "short" in platform.lower() or "reels" in platform.lower():
        return f"Khoảnh khắc này nhìn như bước ra từ một bộ phim. 🎬\n\n{base}\n\nBạn thích cảnh nào nhất?"
    if "product" in platform.lower() or "ads" in platform.lower():
        return f"Giới thiệu sản phẩm theo phong cách {tone}: rõ lợi ích, hình ảnh premium, cảm xúc mạnh.\n\n{base}"
    return f"Một cảnh cinematic được dựng bằng AI video workflow.\n\n{base}"


def suggest_hashtags(prompt: str, platform: str) -> str:
    text = prompt.lower()
    tags = ["#AIVideo", "#Veo", "#AIStudio", "#CinematicAI"]
    if "product" in text or "sản phẩm" in text:
        tags += ["#ProductAd", "#BrandVideo"]
    if "food" in text or "đồ ăn" in text or "dish" in text:
        tags += ["#FoodReel", "#FoodVideo"]
    if "real estate" in text or "bất động sản" in text:
        tags += ["#RealEstateVideo", "#PropertyTour"]
    if "tiktok" in platform.lower():
        tags += ["#TikTokCreative", "#ViralVideo"]
    if "short" in platform.lower():
        tags += ["#YouTubeShorts"]
    return " ".join(dict.fromkeys(tags))


def extract_thumbnail_from_video(project: dict[str, Any], video_path: str) -> str | None:
    if cv2 is None or not Path(video_path).exists():
        return None
    try:
        cap = cv2.VideoCapture(video_path)
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        if total <= 0:
            return None
        idxs = np.linspace(0, total - 1, min(36, total)).astype(int)
        best = None
        for idx in idxs:
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
            ok, frame = cap.read()
            if not ok:
                continue
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
            sharp = cv2.Laplacian(gray, cv2.CV_64F).var()
            bright = 100 - abs(float(np.mean(gray)) - 128)
            score = sharp + bright * 2
            if best is None or score > best[0]:
                best = (score, rgb)
        cap.release()
        if best is None:
            return None
        return save_pil_to_project(project, Image.fromarray(best[1]), "frames", "publish_thumbnail")
    except Exception:
        return None


def create_publish_package(project: dict[str, Any], video_path: str, prompt: str, settings: dict[str, Any] | None = None, platform: str = "TikTok / Reels") -> Path:
    pdir = project_dir(project)
    package_dir = pdir / "exports" / f"publish_package_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    package_dir.mkdir(parents=True, exist_ok=True)
    video_src = Path(video_path)
    copied_video = package_dir / ("final_video" + video_src.suffix)
    if video_src.exists():
        shutil.copy2(video_src, copied_video)

    thumb = extract_thumbnail_from_video(project, video_path)
    if thumb and Path(thumb).exists():
        shutil.copy2(thumb, package_dir / "thumbnail.png")

    caption = build_social_caption(prompt, platform)
    hashtags = suggest_hashtags(prompt, platform)
    metadata = {
        "project": project,
        "video": str(video_path),
        "prompt": prompt,
        "settings": settings or {},
        "platform": platform,
        "caption": caption,
        "hashtags": hashtags,
        "created_at": now(),
        "app_version": APP_VERSION,
    }
    (package_dir / "caption.txt").write_text(caption + "\n\n" + hashtags + "\n", encoding="utf-8")
    (package_dir / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    zip_path = pdir / "exports" / f"publish_package_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for path in package_dir.rglob("*"):
            if path.is_file():
                z.write(path, arcname=path.relative_to(package_dir))
    return zip_path


def log_api_error(context: str, error: Exception | str, settings: dict[str, Any] | None = None, prompt: str = "") -> str:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    record = {
        "time": now(),
        "context": context,
        "error": str(error),
        "settings": settings or {},
        "prompt_preview": (prompt or "")[:1000],
        "app_version": APP_VERSION,
    }
    path = LOGS_DIR / "api_errors.jsonl"
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return str(path)


def read_api_error_logs(limit: int = 80) -> list[dict[str, Any]]:
    path = LOGS_DIR / "api_errors.jsonl"
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()[-limit:]
    rows = []
    for line in lines:
        try:
            rows.append(json.loads(line))
        except Exception:
            rows.append({"raw": line})
    return list(reversed(rows))


def clear_api_error_logs() -> None:
    path = LOGS_DIR / "api_errors.jsonl"
    if path.exists():
        path.unlink()


def copy_backup_to_sync_folder(project_id: int, sync_folder: str, reason: str = "cloud_sync") -> Path:
    src_zip = auto_backup_project(project_id, reason)
    folder = Path(sync_folder).expanduser()
    folder.mkdir(parents=True, exist_ok=True)
    dest = folder / src_zip.name
    shutil.copy2(src_zip, dest)
    return dest


def guess_sync_folders() -> list[str]:
    home = Path.home()
    candidates = [
        home / "Google Drive",
        home / "My Drive",
        home / "iCloud Drive",
        home / "Library" / "Mobile Documents" / "com~apple~CloudDocs",
        home / "Dropbox",
        home / "OneDrive",
    ]
    return [str(p) for p in candidates if p.exists()]


def is_probably_streamlit_cloud() -> bool:
    home = os.getenv("HOME", "")
    host = os.getenv("HOSTNAME", "")
    return "/mount/src" in home or "streamlit" in host.lower() or os.getenv("GITHUB_REPOSITORY") is not None


def project_storage_report(project: dict[str, Any]) -> dict[str, Any]:
    pdir = project_dir(project)
    total = 0
    files = 0
    largest = []
    for p in pdir.rglob("*"):
        if p.is_file():
            size = p.stat().st_size
            total += size
            files += 1
            largest.append((size, str(p)))
    largest = sorted(largest, reverse=True)[:10]
    return {
        "total_mb": round(total / 1024 / 1024, 2),
        "files": files,
        "largest": [{"mb": round(s / 1024 / 1024, 2), "path": path} for s, path in largest],
    }


def cleanup_project_exports(project: dict[str, Any], keep_latest: int = 5) -> int:
    exports = sorted((project_dir(project) / "exports").glob("*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)
    removed = 0
    for p in exports[keep_latest:]:
        try:
            p.unlink()
            removed += 1
        except Exception:
            pass
    return removed


def deploy_readiness_check() -> list[tuple[str, bool, str]]:
    checks = [
        ("app.py", (ROOT / "app.py").exists(), "Entry point chính."),
        ("requirements.txt", (ROOT / "requirements.txt").exists(), "Python dependencies."),
        ("packages.txt", (ROOT / "packages.txt").exists(), "System packages, ví dụ ffmpeg cho Streamlit Cloud."),
        (".streamlit/config.toml", (ROOT / ".streamlit" / "config.toml").exists(), "Cấu hình Streamlit."),
        (".env.example", (ROOT / ".env.example").exists(), "Mẫu API key local."),
        (".gitignore", (ROOT / ".gitignore").exists(), "Không đẩy API key/output lên GitHub."),
    ]
    return checks


def fallback_video_settings(settings: dict[str, Any]) -> list[dict[str, Any]]:
    primary = normalize_video_settings(settings, "text_video")
    candidates = [primary]
    fallback_models = [
        "veo-3.1-fast-generate-preview",
        "veo-3.1-lite-generate-preview",
        "veo-3.0-fast-generate-001",
        "veo-3.0-generate-001",
    ]
    for model in fallback_models:
        if model == primary.get("model"):
            continue
        s = dict(primary)
        s["model"] = model
        if "lite" in model:
            s["resolution"] = "720p"
        candidates.append(normalize_video_settings(s, "text_video"))
    # Last safe draft
    safe = dict(primary)
    safe.update({"model": "veo-3.1-fast-generate-preview", "resolution": "720p", "duration": min(int(primary.get("duration", 8)), 4)})
    candidates.append(normalize_video_settings(safe, "text_video"))
    unique = []
    seen = set()
    for c in candidates:
        key = (c.get("model"), c.get("resolution"), c.get("duration"), c.get("aspect_ratio"))
        if key not in seen:
            seen.add(key)
            unique.append(c)
    return unique


def generate_video_with_fallback(
    project: dict[str, Any],
    api_key: str,
    prompt: str,
    settings: dict[str, Any],
    mock: bool,
    mode: str = "text_video",
    input_image: Image.Image | None = None,
    last_frame: Image.Image | None = None,
    ref_images: list[Image.Image] | None = None,
    extend_video_object: Any | None = None,
    enable_fallback: bool = True,
) -> tuple[str, Any | None, dict[str, Any]]:
    attempts = [normalize_video_settings(settings, mode)]
    if enable_fallback and mode in ["text_video", "timeline_scene", "script_scene"]:
        attempts = fallback_video_settings(settings)
    errors = []
    for i, s in enumerate(attempts, 1):
        try:
            if len(attempts) > 1:
                st.info(f"Render attempt {i}/{len(attempts)} · {s.get('model')} · {s.get('resolution')} · {s.get('duration')}s")
            path, obj = generate_video(project, api_key, prompt, s, mock, mode, input_image, last_frame, ref_images, extend_video_object)
            return path, obj, s
        except Exception as e:
            log_api_error(f"generate_video_with_fallback::{mode}::attempt_{i}", e, s, prompt)
            errors.append(f"{s.get('model')} / {s.get('resolution')} / {s.get('duration')}s: {e}")
            st.warning(f"Attempt {i} lỗi, thử fallback tiếp..." if i < len(attempts) else "Tất cả fallback đều lỗi.")
    raise RuntimeError("Render lỗi sau tất cả fallback:\n" + "\n\n".join(errors))


def create_timeline_scene_jobs(project_id: int, rows: list[dict[str, Any]], settings: dict[str, Any], base_prompt: str = "") -> list[int]:
    ids = []
    for row in rows:
        s = dict(settings)
        s["duration"] = int(row.get("duration") or settings.get("duration", 8))
        s["timeline_scene"] = int(row.get("scene") or len(ids) + 1)
        prompt = str(row.get("prompt") or row.get("description") or base_prompt)
        cost = estimate_cost("text_video", s, price_image if "price_image" in globals() else 0.03, price_video_sec if "price_video_sec" in globals() else 0.25)
        ids.append(create_job(project_id, "text_video", prompt, s, cost))
    return ids


# -----------------------------
# Generation helpers
# -----------------------------
def require_client(api_key: str):
    if genai is None or types is None:
        raise RuntimeError("Thiếu google-genai. Chạy: pip install google-genai")
    if not api_key:
        raise RuntimeError("Chưa nhập GEMINI_API_KEY.")
    return genai.Client(api_key=api_key)


def response_parts(resp: Any) -> list[Any]:
    parts = []
    direct = getattr(resp, "parts", None)
    if direct:
        parts.extend(direct)
    candidates = getattr(resp, "candidates", None) or []
    for cand in candidates:
        content = getattr(cand, "content", None)
        cparts = getattr(content, "parts", None) if content else None
        if cparts:
            parts.extend(cparts)
    return parts


def part_to_pil(part: Any) -> Optional[Image.Image]:
    try:
        img = part.as_image()
        if img:
            return img.convert("RGB")
    except Exception:
        pass
    inline = getattr(part, "inline_data", None) or getattr(part, "inlineData", None)
    if inline is not None:
        data = getattr(inline, "data", None)
        if data:
            try:
                if isinstance(data, str):
                    data = base64.b64decode(data)
                return Image.open(io.BytesIO(data)).convert("RGB")
            except Exception:
                return None
    return None


def genai_image_to_pil(image_obj: Any) -> Optional[Image.Image]:
    if image_obj is None:
        return None
    if isinstance(image_obj, Image.Image):
        return image_obj.convert("RGB")
    for attr in ("image_bytes", "data"):
        data = getattr(image_obj, attr, None)
        if data:
            try:
                if isinstance(data, str):
                    data = base64.b64decode(data)
                return Image.open(io.BytesIO(data)).convert("RGB")
            except Exception:
                pass
    try:
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        tmp.close()
        image_obj.save(tmp.name)
        return Image.open(tmp.name).convert("RGB")
    except Exception:
        return None


def enhance_prompt(
    prompt: str,
    mode: str,
    style: str,
    camera: str,
    mood: str,
    negative: str,
    character_bible: str = "",
    locked_traits: str = "",
) -> str:
    blocks = [prompt.strip() or "A cinematic scene."]
    if character_bible:
        blocks.append(f"Character bible: {character_bible}.")
    if locked_traits:
        blocks.append(f"Locked traits that must not change: {locked_traits}.")
    blocks += [
        f"Style: {style}.",
        f"Camera: {camera}.",
        f"Mood and lighting: {mood}.",
    ]
    if mode == "video":
        blocks += [
            "Motion: smooth cinematic motion, realistic physics, stable temporal consistency, no random scene cuts.",
            "Continuity: preserve identity, outfit, proportions, color palette and environment logic across the whole clip.",
        ]
    if negative:
        blocks.append(f"Avoid: {negative}.")
    return "\n".join(blocks)


def ratio_size(aspect_ratio: str, short: int = 720) -> tuple[int, int]:
    if aspect_ratio == "9:16":
        return short, int(short * 16 / 9)
    if aspect_ratio == "1:1":
        return short, short
    return int(short * 16 / 9), short


def mock_image(project: dict[str, Any], prompt: str, aspect_ratio: str, prefix: str = "mock_image") -> str:
    w, h = ratio_size(aspect_ratio, 900 if aspect_ratio != "9:16" else 720)
    img = Image.new("RGB", (w, h), (24, 26, 38))
    draw = ImageDraw.Draw(img)
    for i in range(0, h, max(8, h // 70)):
        col = (24 + i % 55, 26 + (i * 2) % 45, 56 + (i * 3) % 90)
        draw.rectangle([0, i, w, i + max(6, h // 70)], fill=col)
    draw.rounded_rectangle([45, 45, w - 45, h - 45], radius=34, outline=(255, 255, 255), width=3)
    draw.text((75, 72), "MOCK IMAGE — API chưa gọi", fill=(255, 235, 140))
    body = prompt[:500] + ("..." if len(prompt) > 500 else "")
    draw.multiline_text((75, 125), body, fill=(245, 245, 245), spacing=8)
    return save_pil_to_project(project, img, "images", prefix)


def mock_video(project: dict[str, Any], prompt: str, aspect_ratio: str, seconds: int = 4, prefix: str = "mock_video") -> str:
    if imageio is None:
        path = project_dir(project) / "videos" / f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        path.write_text("Thiếu imageio[ffmpeg] để tạo mock video.\n\n" + prompt, encoding="utf-8")
        return str(path)
    w, h = ratio_size(aspect_ratio, 540)
    path = project_dir(project) / "videos" / f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.mp4"
    frames = []
    n = max(24, int(seconds) * 24)
    for t in range(n):
        img = Image.new("RGB", (w, h), (14, 16, 28))
        draw = ImageDraw.Draw(img)
        cx = int(w * (0.1 + 0.8 * t / max(1, n - 1)))
        cy = int(h * (0.52 + 0.08 * math.sin(t / 7)))
        for r in range(max(w, h) // 3, 30, -18):
            col = (70 + r % 90, 90 + r % 80, 180 + r % 60)
            draw.ellipse([cx-r, cy-r, cx+r, cy+r], outline=col, width=2)
        draw.rounded_rectangle([28, 28, w - 28, h - 28], radius=26, outline=(255, 255, 255), width=2)
        draw.text((48, 46), f"MOCK VIDEO {seconds}s — thay API key để render thật", fill=(255, 235, 140))
        draw.multiline_text((48, 88), prompt[:300], fill=(245, 245, 245), spacing=6)
        frames.append(np.asarray(img))
    imageio.mimsave(path, frames, fps=24, quality=8)
    return str(path)


def build_video_config(settings: dict[str, Any]):
    if types is None:
        return None
    cfg = types.GenerateVideosConfig(
        aspect_ratio=settings.get("aspect_ratio", "16:9"),
        duration_seconds=int(settings.get("duration", 8)),
        resolution=settings.get("resolution", "720p"),
        number_of_videos=1,
        person_generation=settings.get("person_generation", "allow_adult"),
    )
    return cfg


def normalize_video_settings(settings: dict[str, Any], mode: str) -> dict[str, Any]:
    s = dict(settings)
    model = s.get("model", "")
    if "lite" in model.lower():
        if s.get("resolution") == "4k":
            s["resolution"] = "720p"
        if mode in ["reference_video", "extend_video"]:
            s["model"] = "veo-3.1-generate-preview"
    if s.get("resolution") in ["1080p", "4k"]:
        s["duration"] = 8
    if mode in ["start_end_video", "reference_video"]:
        s["duration"] = 8
    if mode == "extend_video":
        s["duration"] = 8
        s["resolution"] = "720p"
    return s


def generate_text_image(project: dict[str, Any], api_key: str, prompt: str, settings: dict[str, Any], mock: bool) -> list[str]:
    n = int(settings.get("number_of_images", 1))
    aspect_ratio = settings.get("aspect_ratio", "16:9")
    if mock:
        return [mock_image(project, prompt, aspect_ratio, "text_image") for _ in range(n)]

    client = require_client(api_key)
    paths = []
    family = settings.get("family", "Native")
    model = settings.get("model", IMAGE_MODELS_NATIVE[0])
    image_size = settings.get("image_size", "1K")
    person_generation = settings.get("person_generation", "allow_adult")

    if family == "Imagen":
        resp = client.models.generate_images(
            model=model,
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=n,
                aspect_ratio=aspect_ratio,
                image_size=image_size,
                person_generation=person_generation,
            ),
        )
        for generated in getattr(resp, "generated_images", []) or []:
            pil = genai_image_to_pil(getattr(generated, "image", None))
            if pil:
                paths.append(save_pil_to_project(project, pil, "images", "imagen"))
    else:
        resp = client.models.generate_content(
            model=model,
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"],
                image_config=types.ImageConfig(aspect_ratio=aspect_ratio, image_size=image_size),
            ),
        )
        for part in response_parts(resp):
            pil = part_to_pil(part)
            if pil:
                paths.append(save_pil_to_project(project, pil, "images", "native_image"))

    if not paths:
        raise RuntimeError("Không nhận được ảnh từ API.")
    return paths


def generate_image_to_image(project: dict[str, Any], api_key: str, prompt: str, image: Image.Image, settings: dict[str, Any], mock: bool) -> list[str]:
    if mock:
        img = image.copy().resize(ratio_size(settings.get("aspect_ratio", "16:9"), 720))
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle([30, 30, img.width - 30, 135], radius=22, fill=(0, 0, 0))
        draw.text((55, 52), "MOCK IMAGE EDIT", fill=(255, 235, 140))
        draw.text((55, 88), prompt[:90], fill=(255, 255, 255))
        return [save_pil_to_project(project, img, "images", "image_edit")]

    client = require_client(api_key)
    model = settings.get("model", IMAGE_MODELS_NATIVE[0])
    resp = client.models.generate_content(
        model=model,
        contents=[prompt, image],
        config=types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"],
            image_config=types.ImageConfig(
                aspect_ratio=settings.get("aspect_ratio", "16:9"),
                image_size=settings.get("image_size", "1K"),
            ),
        ),
    )
    paths = []
    for part in response_parts(resp):
        pil = part_to_pil(part)
        if pil:
            paths.append(save_pil_to_project(project, pil, "images", "image_edit"))
    if not paths:
        raise RuntimeError("Không nhận được ảnh edit từ API.")
    return paths


def poll_video(client, operation, poll_seconds: int = 10) -> tuple[str, Any]:
    status = st.empty()
    progress = st.progress(0)
    t0 = time.time()
    pct = 3
    while not getattr(operation, "done", False):
        pct = min(92, pct + 3)
        progress.progress(pct)
        status.info(f"Đang render video... {int(time.time() - t0)}s")
        time.sleep(poll_seconds)
        operation = client.operations.get(operation)
    progress.progress(100)
    status.success("Render xong. Đang tải video...")
    generated = operation.response.generated_videos[0]
    client.files.download(file=generated.video)
    return generated.video, generated.video


def generate_video(
    project: dict[str, Any],
    api_key: str,
    prompt: str,
    settings: dict[str, Any],
    mock: bool,
    mode: str = "text_video",
    input_image: Image.Image | None = None,
    last_frame: Image.Image | None = None,
    ref_images: list[Image.Image] | None = None,
    extend_video_object: Any | None = None,
) -> tuple[str, Any | None]:
    settings = normalize_video_settings(settings, mode)
    if mock:
        path = mock_video(project, prompt, settings.get("aspect_ratio", "16:9"), int(settings.get("duration", 8)), mode)
        return path, None

    client = require_client(api_key)
    cfg = build_video_config(settings)
    if last_frame is not None:
        cfg.last_frame = last_frame
    if ref_images:
        cfg.reference_images = [
            types.VideoGenerationReferenceImage(image=img, reference_type="asset")
            for img in ref_images[:3]
        ]

    kwargs = {"model": settings.get("model", VIDEO_MODELS[0]), "prompt": prompt, "config": cfg}
    if input_image is not None:
        kwargs["image"] = input_image
    if extend_video_object is not None:
        kwargs["video"] = extend_video_object

    operation = client.models.generate_videos(**kwargs)
    video_obj, saved_obj = poll_video(client, operation, int(settings.get("poll_seconds", 10)))
    path = project_dir(project) / "videos" / f"veo_{mode}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.mp4"
    video_obj.save(str(path))
    return str(path), saved_obj


# -----------------------------
# Queue / cost
# -----------------------------
def estimate_cost(job_type: str, settings: dict[str, Any], price_image: float, price_video_second: float) -> float:
    if job_type in ["text_image", "image_image", "script_image"]:
        return float(settings.get("number_of_images", 1)) * price_image
    if "video" in job_type or job_type in ["timeline", "script_to_video"]:
        scenes = int(settings.get("scenes", 1))
        duration = int(settings.get("duration", 8))
        return scenes * duration * price_video_second
    return 0.0


def create_job(project_id: int, job_type: str, prompt: str, settings: dict[str, Any], cost_estimate: float = 0) -> int:
    with db() as conn:
        conn.execute(
            "INSERT INTO jobs(project_id, job_type, prompt, settings_json, status, cost_estimate, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
            (project_id, job_type, prompt, json.dumps(settings, ensure_ascii=False), "pending", cost_estimate, now(), now()),
        )
        jid = int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])
    touch_project(project_id)
    return jid


def update_job(job_id: int, status: str, result_paths: list[str] | None = None, error: str = "") -> None:
    with db() as conn:
        conn.execute(
            "UPDATE jobs SET status=?, result_paths_json=?, error=?, updated_at=? WHERE id=?",
            (status, json.dumps(result_paths or [], ensure_ascii=False), error, now(), job_id),
        )


def list_jobs(project_id: int, status: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    sql = "SELECT * FROM jobs WHERE project_id=?"
    params: list[Any] = [project_id]
    if status:
        sql += " AND status=?"
        params.append(status)
    sql += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    with db() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def duplicate_job(job: dict[str, Any]) -> int:
    settings = safe_json_loads(job.get("settings_json"), {})
    return create_job(int(job["project_id"]), job["job_type"], job["prompt"], settings, float(job.get("cost_estimate") or 0))


def execute_job(project: dict[str, Any], job: dict[str, Any], api_key: str, mock: bool) -> list[str]:
    update_job(job["id"], "running")
    settings = safe_json_loads(job.get("settings_json"), {})
    prompt = job.get("prompt", "")
    paths: list[str] = []
    try:
        if job["job_type"] == "text_image":
            paths = generate_text_image(project, api_key, prompt, settings, mock)
            for p in paths:
                add_asset(project["id"], "image", p, prompt, settings)
            add_usage(project["id"], "image", settings.get("model", ""), len(paths), float(job.get("cost_estimate") or 0))

        elif job["job_type"] == "text_video":
            path, _ = generate_video(project, api_key, prompt, settings, mock, mode="text_video")
            paths = [path]
            add_asset(project["id"], "video", path, prompt, settings)
            add_usage(project["id"], "video", settings.get("model", ""), int(settings.get("duration", 8)), float(job.get("cost_estimate") or 0))

        else:
            raise RuntimeError(f"Job type chưa hỗ trợ chạy từ queue: {job['job_type']}")

        update_job(job["id"], "done", paths)
        return paths
    except Exception as e:
        log_api_error(f"execute_job::{job.get('job_type')}::job_{job.get('id')}", e, settings, prompt)
        update_job(job["id"], "failed", [], str(e))
        raise


# -----------------------------
# Video tools
# -----------------------------
def ffmpeg_concat_videos(project: dict[str, Any], clips: list[str], output_name: str, add_fade: bool = False) -> str:
    if len(clips) < 1:
        raise RuntimeError("Chưa có clip để nối.")
    if len(clips) == 1:
        return copy_to_project(project, clips[0], "timeline", output_name)

    ffmpeg = ffmpeg_path()
    if not ffmpeg:
        # Fallback: copy first clip only.
        return copy_to_project(project, clips[0], "timeline", output_name)

    work = Path(tempfile.mkdtemp())
    processed = []
    for i, clip in enumerate(clips):
        src = Path(clip)
        if add_fade:
            out = work / f"fade_{i}.mp4"
            # Fade-in/out nhẹ, không yêu cầu biết duration chính xác.
            vf = "fade=t=in:st=0:d=0.25,fade=t=out:st=7.65:d=0.25"
            ok, msg = run_cmd([ffmpeg, "-y", "-i", str(src), "-vf", vf, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(out)], timeout=900)
            processed.append(str(out if ok else src))
        else:
            processed.append(str(src))

    list_file = work / "concat.txt"
    list_file.write_text("\n".join([f"file '{Path(p).resolve().as_posix()}'" for p in processed]), encoding="utf-8")
    out = project_dir(project) / "timeline" / output_name
    if not out.suffix:
        out = out.with_suffix(".mp4")

    ok, msg = run_cmd([ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(list_file), "-c", "copy", str(out)], timeout=900)
    if not ok:
        # Re-encode fallback for files with different stream format.
        ok, msg = run_cmd([ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(list_file), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(out)], timeout=1200)
    if not ok:
        raise RuntimeError("FFmpeg nối video lỗi:\n" + msg)
    return str(out)


def get_video_duration(path: str) -> float:
    ffprobe = ffprobe_path()
    if not ffprobe:
        return 0.0
    ok, out = run_cmd([ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", path], timeout=60)
    if ok:
        try:
            return float(out.strip().splitlines()[0])
        except Exception:
            return 0.0
    return 0.0


def video_convert(project: dict[str, Any], input_video: str, mode: str, target_ratio: str, upscale_to: str, compress_crf: int) -> str:
    ffmpeg = ffmpeg_path()
    if not ffmpeg:
        raise RuntimeError("Chưa cài ffmpeg. Cần ffmpeg cho Video Tools.")
    pdir = project_dir(project) / "videos"
    out = pdir / f"converted_{mode}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"

    if mode == "Upscale":
        scale = "1920:1080" if upscale_to == "1080p" else "3840:2160"
        vf = f"scale={scale}:flags=lanczos"
    elif mode == "Crop center":
        if target_ratio == "9:16":
            vf = "crop=ih*9/16:ih:(iw-ih*9/16)/2:0,scale=1080:1920"
        else:
            vf = "crop=iw:iw*9/16:0:(ih-iw*9/16)/2,scale=1920:1080"
    elif mode == "Blur background":
        if target_ratio == "9:16":
            vf = "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:1[bg];[0:v]scale=1080:1920:force_original_aspect_ratio=decrease[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2"
        else:
            vf = "[0:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,boxblur=25:1[bg];[0:v]scale=1920:1080:force_original_aspect_ratio=decrease[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2"
    else:  # Compress
        vf = "scale=trunc(iw/2)*2:trunc(ih/2)*2"

    ok, msg = run_cmd([ffmpeg, "-y", "-i", input_video, "-vf", vf, "-c:v", "libx264", "-crf", str(compress_crf), "-preset", "medium", "-c:a", "aac", "-b:a", "160k", str(out)], timeout=1200)
    if not ok:
        raise RuntimeError("FFmpeg convert lỗi:\n" + msg)
    return str(out)


def make_srt_from_text(project: dict[str, Any], text: str, seconds_per_caption: int = 3) -> str:
    lines = [x.strip() for x in re.split(r"[\n。.!?]+", text) if x.strip()]
    if not lines:
        lines = [text.strip() or "Caption"]
    def ts(sec: int) -> str:
        h = sec // 3600
        m = (sec % 3600) // 60
        s = sec % 60
        return f"{h:02d}:{m:02d}:{s:02d},000"
    blocks = []
    t = 0
    for i, line in enumerate(lines, 1):
        blocks.append(f"{i}\n{ts(t)} --> {ts(t + seconds_per_caption)}\n{line}\n")
        t += seconds_per_caption
    path = project_dir(project) / "audio" / f"captions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.srt"
    path.write_text("\n".join(blocks), encoding="utf-8")
    return str(path)


def audio_studio_mix(project: dict[str, Any], video_path: str, music_path: str | None, voice_path: str | None, srt_path: str | None, music_volume: float, voice_volume: float) -> str:
    ffmpeg = ffmpeg_path()
    if not ffmpeg:
        raise RuntimeError("Chưa cài ffmpeg. Cần ffmpeg cho Audio Studio.")
    out = project_dir(project) / "videos" / f"audio_mix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"

    cmd = [ffmpeg, "-y", "-i", video_path]
    inputs = 1
    filters = []
    audio_labels = []

    if music_path:
        cmd += ["-i", music_path]
        filters.append(f"[{inputs}:a]volume={music_volume}[m]")
        audio_labels.append("[m]")
        inputs += 1
    if voice_path:
        cmd += ["-i", voice_path]
        filters.append(f"[{inputs}:a]volume={voice_volume}[v]")
        audio_labels.append("[v]")
        inputs += 1

    vf = None
    if srt_path:
        # Windows path safety: use forward slashes and escape colon.
        srt_escaped = Path(srt_path).resolve().as_posix().replace(":", "\\:")
        vf = f"subtitles='{srt_escaped}'"

    if audio_labels:
        filters.append("".join(audio_labels) + f"amix=inputs={len(audio_labels)}:duration=longest[aout]")
        if vf:
            cmd += ["-vf", vf]
        cmd += ["-filter_complex", ";".join(filters), "-map", "0:v", "-map", "[aout]", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(out)]
    else:
        if vf:
            cmd += ["-vf", vf, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "copy", str(out)]
        else:
            raise RuntimeError("Chưa chọn nhạc/voice/subtitle để xử lý.")

    ok, msg = run_cmd(cmd, timeout=1200)
    if not ok:
        raise RuntimeError("FFmpeg audio/subtitle lỗi:\n" + msg)
    return str(out)



# -----------------------------
# Auto Content Machine helpers
# -----------------------------
AUTO_CONTENT_NICHES = {
    "Tài chính": {"visual": "clean financial graphics, city skyline, charts, professional lighting", "hook_vi": "Sự thật tài chính này nhiều người bỏ qua.", "hook_en": "Most people miss this simple money rule."},
    "Lịch sử": {"visual": "cinematic historical reenactment, ancient city, dramatic light, textured costumes", "hook_vi": "Có một khoảnh khắc đã thay đổi cả lịch sử.", "hook_en": "One moment changed the course of history."},
    "News": {"visual": "modern newsroom, abstract news graphics, city b-roll, documentary style", "hook_vi": "Đây là điều bạn cần biết hôm nay.", "hook_en": "Here is what you need to know today."},
    "AI/Tech": {"visual": "futuristic interface, glowing data, clean tech lab, cinematic AI visuals", "hook_vi": "Workflow AI này có thể thay đổi cách bạn làm content.", "hook_en": "This AI workflow can change how you create content."},
    "AFF sản phẩm số": {"visual": "screen mockups, digital dashboard, laptop, clean creator workspace", "hook_vi": "Nếu bạn làm online, công cụ này rất đáng thử.", "hook_en": "If you work online, this tool is worth testing."},
    "AFF sản phẩm vật lý": {"visual": "product close-ups, lifestyle usage, clean commercial lighting", "hook_vi": "Món đồ nhỏ này giải quyết một vấn đề rất khó chịu.", "hook_en": "This small product solves a very annoying problem."},
    "Giáo dục": {"visual": "clean educational graphics, whiteboard, friendly motion, simple icons", "hook_vi": "Hiểu khái niệm này trong chưa đầy một phút.", "hook_en": "Understand this concept in under a minute."},
    "Mỹ phẩm": {"visual": "premium skincare commercial, macro texture, soft pastel lighting, clean beauty", "hook_vi": "Một routine nhỏ nhưng cảm giác rất khác.", "hook_en": "A small routine step that feels different."},
}

AUTO_PLATFORMS = {
    "TikTok 30s": {"aspect_ratio": "9:16", "scene_count": 5, "duration": 6, "resolution": "720p"},
    "YouTube Shorts 60s": {"aspect_ratio": "9:16", "scene_count": 7, "duration": 8, "resolution": "720p"},
    "Reels 30s": {"aspect_ratio": "9:16", "scene_count": 5, "duration": 6, "resolution": "720p"},
    "YouTube ngang 48s": {"aspect_ratio": "16:9", "scene_count": 6, "duration": 8, "resolution": "1080p"},
    "Product Ads 4 cảnh": {"aspect_ratio": "9:16", "scene_count": 4, "duration": 8, "resolution": "1080p"},
}

VOICE_PRESETS = {
    "Tiếng Việt - Nam": "vi-VN-NamMinhNeural",
    "Tiếng Việt - Nữ": "vi-VN-HoaiMyNeural",
    "English - Male": "en-US-GuyNeural",
    "English - Female": "en-US-JennyNeural",
}


def generate_auto_script(topic: str, niche: str, language: str, platform: str, scene_count: int) -> dict[str, Any]:
    info = AUTO_CONTENT_NICHES.get(niche, AUTO_CONTENT_NICHES["AI/Tech"])
    topic_clean = topic.strip() or "AI content system"
    is_en = language == "English"
    is_bi = language == "Song ngữ Việt-Anh"
    hook = info["hook_en"] if is_en else info["hook_vi"]
    if is_en:
        title = f"{topic_clean}: quick breakdown"
        lines = [
            f"{hook} Today we break down {topic_clean} in a simple visual way.",
            f"The core idea is that {topic_clean} becomes useful when you understand the context.",
            "The important part is not only what happens, but why it matters.",
            "Here is a practical example that makes the point easy to remember.",
            "The takeaway is simple: focus on the signal, not the noise.",
            "Save this video if you want a quick reference later.",
        ]
    elif is_bi:
        title = f"{topic_clean} / Quick breakdown"
        lines = [
            f"{hook} / Today we break down {topic_clean}.",
            f"Ý chính là bối cảnh của {topic_clean}. / The key is the context.",
            "Điều quan trọng không chỉ là kết quả, mà là lý do phía sau. / The why matters.",
            "Một ví dụ đơn giản giúp bạn nhớ lâu hơn. / A simple example makes it stick.",
            "Kết luận: tập trung vào tín hiệu chính. / Focus on the signal.",
            "Lưu lại nếu bạn muốn xem lại. / Save this for later.",
        ]
    else:
        title = f"{topic_clean}: tóm tắt nhanh"
        lines = [
            f"{hook} Hôm nay mình tóm tắt nhanh về: {topic_clean}.",
            f"Ý chính đầu tiên là: {topic_clean} không chỉ là một chủ đề đơn lẻ, mà là một câu chuyện có bối cảnh.",
            "Điểm quan trọng nằm ở nguyên nhân phía sau, không chỉ là kết quả bên ngoài.",
            "Một ví dụ đơn giản sẽ giúp bạn thấy rõ vấn đề hơn.",
            "Kết luận rất ngắn: hãy tập trung vào tín hiệu chính, đừng bị nhiễu bởi chi tiết phụ.",
            "Lưu video này nếu bạn muốn xem lại sau.",
        ]
    while len(lines) < scene_count:
        lines.append(lines[(len(lines)-1) % max(1, len(lines)-1)])
    lines = lines[:scene_count]
    scenes = []
    for i, line in enumerate(lines, 1):
        scenes.append({
            "scene": i,
            "narration": line,
            "visual_prompt": (
                f"{line}\nTopic: {topic_clean}. Niche: {niche}. Visual style: {info['visual']}. "
                f"Platform: {platform}. Cinematic scene, clear subject, smooth camera motion, no readable text, no watermark."
            ),
        })
    return {"title": title, "voiceover": " ".join(lines), "scenes": scenes, "niche": niche, "language": language, "platform": platform}


def make_srt_from_auto_scenes(project: dict[str, Any], scenes: list[dict[str, Any]], total_seconds: int) -> str:
    per = max(2, int(total_seconds / max(1, len(scenes))))
    def ts(sec: int) -> str:
        return f"{sec//3600:02d}:{(sec%3600)//60:02d}:{sec%60:02d},000"
    blocks = []
    t = 0
    for i, sc in enumerate(scenes, 1):
        end = min(total_seconds, t + per)
        blocks.append(f"{i}\n{ts(t)} --> {ts(end)}\n{sc['narration']}\n")
        t = end
    path = project_dir(project) / "audio" / f"auto_content_{datetime.now().strftime('%Y%m%d_%H%M%S')}.srt"
    path.write_text("\n".join(blocks), encoding="utf-8")
    return str(path)


def create_silent_wav(project: dict[str, Any], seconds: int = 8) -> str:
    import wave, struct
    path = project_dir(project) / "audio" / f"silent_voice_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
    rate = 24000
    frames = rate * max(1, seconds)
    with wave.open(str(path), "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(struct.pack("<h", 0) * frames)
    return str(path)


def generate_tts_edge(project: dict[str, Any], text: str, voice: str, mock: bool = False) -> str:
    if mock:
        return create_silent_wav(project, max(4, min(120, len(text) // 14)))
    try:
        import asyncio
        import edge_tts
        out = project_dir(project) / "audio" / f"voice_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
        async def _run():
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(str(out))
        asyncio.run(_run())
        return str(out)
    except Exception as e:
        try:
            log_api_error("edge_tts", e, {"voice": voice}, text)
        except Exception:
            pass
        st.warning("TTS lỗi, app tạo silent voice fallback để pipeline vẫn chạy.")
        return create_silent_wav(project, max(4, min(120, len(text) // 14)))


def make_thumbnail_with_title(project: dict[str, Any], video_path: str, title: str, platform: str) -> str:
    base_thumb = extract_thumbnail_from_video(project, video_path)
    if base_thumb and Path(base_thumb).exists():
        img = Image.open(base_thumb).convert("RGB")
    else:
        img = Image.new("RGB", ratio_size("9:16" if "ngang" not in platform else "16:9", 900), (18, 22, 35))
    draw = ImageDraw.Draw(img)
    w, h = img.size
    band_h = int(h * 0.24)
    draw.rectangle([0, h - band_h, w, h], fill=(0, 0, 0))
    words = title.strip()[:80].split()
    lines, line = [], ""
    for word in words:
        test = (line + " " + word).strip()
        if len(test) > 28:
            lines.append(line)
            line = word
        else:
            line = test
    if line:
        lines.append(line)
    y = h - band_h + 24
    for ln in lines[:3]:
        draw.text((32, y), ln, fill=(255, 255, 255))
        y += 36
    out = project_dir(project) / "frames" / f"auto_thumbnail_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    img.save(out)
    return str(out)


def create_auto_content_package(project: dict[str, Any], final_video: str, thumbnail: str, script_data: dict[str, Any], srt_path: str, voice_path: str, platform: str, settings: dict[str, Any]) -> Path:
    pdir = project_dir(project)
    package_dir = pdir / "exports" / f"auto_content_package_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    package_dir.mkdir(parents=True, exist_ok=True)
    file_map = {"final_video.mp4": final_video, "thumbnail.png": thumbnail, "subtitle.srt": srt_path}
    if voice_path:
        file_map["voiceover" + Path(voice_path).suffix] = voice_path
    for name, src in file_map.items():
        if src and Path(src).exists():
            shutil.copy2(src, package_dir / name)
    caption = build_social_caption(script_data.get("voiceover", ""), platform)
    hashtags = suggest_hashtags(script_data.get("voiceover", ""), platform)
    (package_dir / "title.txt").write_text(script_data.get("title", "Auto video"), encoding="utf-8")
    (package_dir / "caption.txt").write_text(caption + "\n\n" + hashtags, encoding="utf-8")
    (package_dir / "script.json").write_text(json.dumps(script_data, ensure_ascii=False, indent=2), encoding="utf-8")
    (package_dir / "metadata.json").write_text(json.dumps({"created_at": now(), "platform": platform, "settings": settings, "app_version": APP_VERSION}, ensure_ascii=False, indent=2), encoding="utf-8")
    zip_path = pdir / "exports" / f"auto_content_package_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for p in package_dir.rglob("*"):
            if p.is_file():
                z.write(p, arcname=p.relative_to(package_dir))
    return zip_path


# -----------------------------
# UI component functions
# -----------------------------
def video_settings_panel(key: str, defaults: dict[str, Any] | None = None, compact: bool = False) -> dict[str, Any]:
    defaults = defaults or {}
    st.markdown("#### ⚙️ Cấu hình video")
    preset = st.selectbox(
        "Preset nhanh",
        ["Custom", "TikTok/Reels 9:16", "YouTube/TV 16:9", "Draft tiết kiệm", "Hero 4K"],
        key=f"{key}_preset",
    )

    model_default = defaults.get("model", VIDEO_MODELS[0])
    aspect_default = defaults.get("aspect_ratio", "9:16")
    duration_default = str(defaults.get("duration", 8))
    resolution_default = defaults.get("resolution", "720p")

    if preset == "TikTok/Reels 9:16":
        aspect_default, duration_default, resolution_default = "9:16", "8", "720p"
    elif preset == "YouTube/TV 16:9":
        aspect_default, duration_default, resolution_default = "16:9", "8", "1080p"
    elif preset == "Draft tiết kiệm":
        model_default, aspect_default, duration_default, resolution_default = "veo-3.1-fast-generate-preview", "9:16", "4", "720p"
    elif preset == "Hero 4K":
        model_default, aspect_default, duration_default, resolution_default = "veo-3.1-generate-preview", "16:9", "8", "4k"

    cols = st.columns(4)
    with cols[0]:
        model = st.selectbox("Model", VIDEO_MODELS, index=VIDEO_MODELS.index(model_default) if model_default in VIDEO_MODELS else 0, key=f"{key}_model")
    with cols[1]:
        aspect_ratio = st.selectbox("Tỉ lệ khung", ["9:16", "16:9"], index=["9:16", "16:9"].index(aspect_default), key=f"{key}_ratio")
    with cols[2]:
        duration = st.selectbox("Độ dài", ["4", "6", "8"], index=["4", "6", "8"].index(str(duration_default)), key=f"{key}_duration")
    with cols[3]:
        resolution = st.selectbox("Độ phân giải", ["720p", "1080p", "4k"], index=["720p", "1080p", "4k"].index(resolution_default), key=f"{key}_res")

    person_generation = st.selectbox("Person generation", ["allow_adult", "allow_all", "dont_allow"], index=0, key=f"{key}_person")
    poll_seconds = st.slider("Polling giây/lần", 5, 20, 10, key=f"{key}_poll")
    settings = {
        "model": model,
        "aspect_ratio": aspect_ratio,
        "duration": int(duration),
        "resolution": resolution,
        "person_generation": person_generation,
        "poll_seconds": poll_seconds,
    }
    norm = normalize_video_settings(settings, key)
    if norm != settings:
        st.warning("Một số cấu hình đã được tự chỉnh để phù hợp ràng buộc model/API.")
    return norm


def image_settings_panel(key: str) -> dict[str, Any]:
    st.markdown("#### ⚙️ Cấu hình ảnh")
    family = st.selectbox("Engine", ["Native", "Imagen"], key=f"{key}_family")
    model_list = IMAGE_MODELS_NATIVE if family == "Native" else IMAGE_MODELS_IMAGEN
    model = st.selectbox("Model", model_list, key=f"{key}_model")
    c1, c2, c3 = st.columns(3)
    with c1:
        aspect_ratio = st.selectbox("Tỉ lệ ảnh", ["1:1", "3:4", "4:3", "9:16", "16:9"], index=4, key=f"{key}_ar")
    with c2:
        image_size = st.selectbox("Image size", ["1K", "2K", "4K"], key=f"{key}_size")
    with c3:
        n = st.slider("Số ảnh", 1, 4, 1, key=f"{key}_n")
    person_generation = st.selectbox("Person generation ảnh", ["allow_adult", "allow_all", "dont_allow"], key=f"{key}_person_img")
    return {
        "family": family,
        "model": model,
        "aspect_ratio": aspect_ratio,
        "image_size": image_size,
        "number_of_images": int(n),
        "person_generation": person_generation,
    }


def split_script_to_scenes(script: str, max_scenes: int = 8, seconds_each: int = 8, character_bible: str = "") -> list[dict[str, Any]]:
    lines = [x.strip(" -\t") for x in script.splitlines() if x.strip()]
    if len(lines) <= 1:
        # Split by sentence if user pasted paragraph.
        lines = [x.strip() for x in re.split(r"(?<=[.!?。])\s+", script) if x.strip()]
    lines = lines[:max_scenes] or ["Opening scene"]
    scenes = []
    for i, line in enumerate(lines, 1):
        scenes.append({
            "scene": i,
            "duration": seconds_each,
            "description": line,
            "prompt": (
                f"Scene {i}. {line}\n"
                f"{('Character bible: ' + character_bible) if character_bible else ''}\n"
                "Cinematic continuity, clear subject, smooth camera movement, production-quality lighting."
            ).strip(),
        })
    return scenes


def display_cost_box(job_type: str, settings: dict[str, Any], price_img: float, price_sec: float) -> float:
    cost = estimate_cost(job_type, settings, price_img, price_sec)
    st.markdown(
        f"""
<div class="card">
<b>💰 Ước tính chi phí local</b><br>
<span class="small">Đây là số tự tính theo đơn giá bạn nhập ở sidebar, không phải báo giá chính thức của Google.</span><br><br>
<b>{cost:,.4f} USD</b>
</div>
""",
        unsafe_allow_html=True,
    )
    return cost


def render_asset_gallery(project_id: int, kind: str | None = None, limit: int = 24) -> None:
    assets = list_assets(project_id, kind, limit)
    if not assets:
        st.info("Chưa có asset.")
        return
    cols = st.columns(3)
    for i, asset in enumerate(assets):
        with cols[i % 3]:
            p = asset["path"]
            show_asset_preview(p, f"#{asset['id']} · {Path(p).name}")
            with st.expander("Quản lý asset"):
                st.code(asset.get("prompt", "")[:1200])
                copy_button(asset.get("prompt", ""), "Copy prompt")
                new_name = st.text_input("Tên mới", value=Path(p).stem, key=f"rename_{asset['id']}")
                if st.button("Rename", key=f"rename_btn_{asset['id']}", use_container_width=True):
                    ok, msg = rename_asset(asset["id"], new_name)
                    st.success("Đã đổi tên.") if ok else st.error(msg)
                    st.rerun()
                download_file(p, "⬇️ Tải")
                if st.button("Retry prompt này", key=f"retry_asset_{asset['id']}", use_container_width=True):
                    settings = safe_json_loads(asset.get("settings_json"), {})
                    job_type = "text_video" if asset["asset_type"] == "video" else "text_image"
                    create_job(project_id, job_type, asset.get("prompt", ""), settings, 0)
                    st.success("Đã thêm vào Queue để retry.")


# -----------------------------
# Sidebar
# -----------------------------
projects = list_projects()
if not projects:
    current_project = create_project("Default Project")
    projects = list_projects()

with st.sidebar:
    st.markdown("## 🎬 AUTO VEO Studio")
    st.caption(APP_VERSION)
    compact_ui = st.checkbox("Giao diện gọn", value=True)
    if compact_ui:
        st.markdown("""
        <style>
        .block-container {max-width: 1280px; padding-top: .75rem;}
        [data-testid="stMetric"] {padding: .35rem;}
        div[data-testid="stExpander"] details {border-radius: 14px;}
        textarea {font-size: .92rem !important;}
        </style>
        """, unsafe_allow_html=True)

    st.markdown("### 📁 Project Library")
    project_names = [f"{p['name']} · {p['slug']}" for p in projects]
    selected_idx = st.selectbox("Chọn project", list(range(len(projects))), format_func=lambda i: project_names[i])
    current_project = projects[selected_idx]
    pdir = project_dir(current_project)
    st.caption(f"Thư mục: `{pdir.name}`")

    with st.expander("➕ Tạo project mới", expanded=False):
        new_project_name = st.text_input("Tên project")
        new_project_desc = st.text_area("Mô tả", height=70)
        if st.button("Tạo project", use_container_width=True):
            if new_project_name.strip():
                current_project = create_project(new_project_name, new_project_desc)
                st.success("Đã tạo project.")
                st.rerun()
            else:
                st.error("Hãy nhập tên project.")

    st.divider()
    st.markdown("### 🔌 Provider")
    provider_mode = st.radio("Chế độ", ["Gemini API thật", "Mock demo không tốn API"], index=1)
    mock = provider_mode.startswith("Mock")
    api_key = st.text_input("GEMINI_API_KEY", type="password", value=os.getenv("GEMINI_API_KEY", ""), disabled=mock)
    if not mock and not api_key:
        st.warning("Chưa nhập API key.")

    st.divider()
    st.markdown("### ✨ Prompt Enhancer")
    auto_enhance = st.checkbox("Tự nâng prompt", value=True)
    style = st.selectbox("Style", ["cinematic realism", "luxury commercial", "anime film", "documentary", "3D product render", "dark fantasy", "minimal editorial"])
    camera = st.selectbox("Camera", ["35mm lens, shallow depth of field", "wide establishing shot", "slow dolly-in", "handheld realistic", "macro close-up", "top-down product shot"])
    mood = st.selectbox("Mood/lighting", ["golden hour, soft contrast", "neon night, rain reflections", "high-key studio lighting", "dramatic chiaroscuro", "natural daylight", "moody fog and volumetric light"])
    negative = st.text_area("Negative prompt", value=DEFAULT_NEGATIVE, height=80)

    st.divider()
    st.markdown("### 💰 Cost Estimate")
    price_image = st.number_input("USD / ảnh", min_value=0.0, value=0.03, step=0.01, format="%.4f")
    price_video_sec = st.number_input("USD / giây video", min_value=0.0, value=0.25, step=0.01, format="%.4f")
    st.caption("Bạn tự chỉnh theo giá thật/quota của tài khoản.")

    st.divider()
    st.markdown("### 🧪 Môi trường")
    st.caption(f"OS: {platform.system()} · Python: {platform.python_version()}")
    st.caption(f"google-genai: {'OK' if genai else 'Thiếu'}")
    st.caption(f"OpenCV: {'OK' if cv2 else 'Thiếu'}")
    st.caption(f"imageio: {'OK' if imageio else 'Thiếu'}")
    st.caption(f"ffmpeg: {'OK' if ffmpeg_path() else 'Chưa thấy'}")
    st.caption(f"Cloud mode: {'Có thể' if is_probably_streamlit_cloud() else 'Local/không rõ'}")
    if not ffmpeg_path():
        st.warning(install_ffmpeg_hint())
        if platform.system() == "Windows":
            st.code("winget install Gyan.FFmpeg")
        elif platform.system() == "Darwin":
            st.code("brew install ffmpeg")
        else:
            st.code("sudo apt update && sudo apt install ffmpeg")


# -----------------------------
# Header
# -----------------------------
st.markdown(
    f"""
<div class="hero">
  <h1>🎬 {APP_TITLE} v1.2 — Personal Studio</h1>
  <p>Project Library · Backup · Prompt Checker · Fallback · Publish Package · Timeline · Audio · Video Tools</p>
  <div style="margin-top:12px">
    <span class="badge">📁 {current_project['name']}</span>
    <span class="badge">🧠 prompt templates</span>
    <span class="badge">🧬 character library</span>
    <span class="badge">🎞️ timeline nối cảnh</span>
    <span class="badge">⚡ workflow preset</span>
    <span class="badge">🛡️ auto backup</span>
    <span class="badge">📦 publish package</span>
    <span class="badge">💰 cost estimate</span>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

if mock:
    st.warning("Đang ở Mock demo: không gọi API, không tốn tiền. Khi test xong hãy đổi sang Gemini API thật.")
else:
    st.markdown('<span class="ok">Gemini API mode</span>' if api_key else '<span class="warn">Cần API key để render thật</span>', unsafe_allow_html=True)

if not st.session_state.auto_backup_daily_done:
    try:
        daily_backup_if_needed(current_project["id"])
        st.session_state.auto_backup_daily_done = True
    except Exception:
        pass


# Store veo objects in session for extend.
if "veo_objects" not in st.session_state:
    st.session_state.veo_objects = []
if "timeline_scenes" not in st.session_state:
    st.session_state.timeline_scenes = []
if "last_timeline_failed_rows" not in st.session_state:
    st.session_state.last_timeline_failed_rows = []
if "last_timeline_success_clips" not in st.session_state:
    st.session_state.last_timeline_success_clips = []
if "auto_backup_daily_done" not in st.session_state:
    st.session_state.auto_backup_daily_done = False


tabs = st.tabs([
    "🤖 Auto Content Machine",
    "🏠 Project",
    "🧠 Prompt Library",
    "🧬 Character Bible",
    "🎨 Image Studio",
    "🎬 Video Studio",
    "📦 Batch + Queue",
    "⚡ Workflow Presets",
    "🎞️ Timeline Studio",
    "🤖 Script → Video",
    "🎵 Audio Studio",
    "🛠️ Video Tools",
    "🚀 Deploy",
    "📊 Dashboard",
])


# -----------------------------
# Auto Content Machine
# -----------------------------
with tabs[0]:
    st.markdown("## 🤖 Auto Content Machine")
    st.caption("Nhập 1 đoạn text → tự tạo script, voice, subtitle, video, thumbnail và publish package.")

    c1, c2 = st.columns([1.15, .85])
    with c1:
        topic = st.text_area(
            "Nhập 1 đoạn text / ý tưởng / brief",
            height=190,
            placeholder="Ví dụ: Tóm tắt 3 sai lầm tài chính cá nhân phổ biến cho người mới đi làm, giọng dễ hiểu, video TikTok 30 giây..."
        )
        language = st.selectbox("Ngôn ngữ", ["Tiếng Việt", "English", "Song ngữ Việt-Anh"], index=0)
        niche = st.selectbox("Style/ngành", list(AUTO_CONTENT_NICHES.keys()), index=3)
        platform_auto = st.selectbox("Nền tảng / format", list(AUTO_PLATFORMS.keys()), index=0)
    with c2:
        st.markdown("### Cấu hình nhanh")
        pf = AUTO_PLATFORMS[platform_auto]
        model_auto = st.selectbox("Veo model", VIDEO_MODELS, index=0, key="auto_model")
        voice_label = st.selectbox("Voice", list(VOICE_PRESETS.keys()), index=0 if language != "English" else 2)
        burn_subtitles = st.checkbox("Burn subtitle vào video", value=True)
        make_keyframes = st.checkbox("Tạo keyframe ảnh trước", value=False, help="Bật nếu muốn có ảnh từng cảnh, nhưng sẽ chậm/tốn hơn.")
        auto_fallback = st.checkbox("Tự fallback model khi lỗi", value=True)
        st.markdown(
            f"""
<div class="card">
<b>Output:</b> {platform_auto}<br>
<b>Tỉ lệ:</b> {pf['aspect_ratio']}<br>
<b>Số cảnh:</b> {pf['scene_count']}<br>
<b>Mỗi cảnh:</b> {pf['duration']} giây<br>
<b>Độ phân giải:</b> {pf['resolution']}
</div>
""",
            unsafe_allow_html=True,
        )

    script_data = generate_auto_script(topic, niche, language, platform_auto, AUTO_PLATFORMS[platform_auto]["scene_count"]) if topic.strip() else None
    if script_data:
        st.markdown("### Script / Shot list tự tạo")
        st.text_input("Title", value=script_data["title"], key="auto_title_preview")
        st.text_area("Voice-over", value=script_data["voiceover"], height=120, key="auto_voice_preview")
        st.dataframe(script_data["scenes"], use_container_width=True)

    total_seconds = AUTO_PLATFORMS[platform_auto]["scene_count"] * AUTO_PLATFORMS[platform_auto]["duration"]
    auto_settings = {
        "model": model_auto,
        "aspect_ratio": AUTO_PLATFORMS[platform_auto]["aspect_ratio"],
        "duration": AUTO_PLATFORMS[platform_auto]["duration"],
        "resolution": AUTO_PLATFORMS[platform_auto]["resolution"],
        "person_generation": "allow_adult",
        "poll_seconds": 10,
        "scenes": AUTO_PLATFORMS[platform_auto]["scene_count"],
    }
    est_cost = display_cost_box("script_to_video", auto_settings, price_image, price_video_sec)

    st.divider()
    run_auto = st.button("🚀 Generate Full Video — Text → Final Video", type="primary", use_container_width=True)

    if run_auto:
        if not topic.strip():
            st.error("Hãy nhập text/ý tưởng trước.")
        else:
            try:
                project = current_project
                script_data = generate_auto_script(topic, niche, language, platform_auto, AUTO_PLATFORMS[platform_auto]["scene_count"])
                st.success("Đã tạo script/shot list.")
                show_prompt_quality(script_data["voiceover"], "video", negative)

                st.info("Bước 1/7: Tạo voice-over")
                voice_path = generate_tts_edge(project, script_data["voiceover"], VOICE_PRESETS[voice_label], mock=mock)
                add_asset(project["id"], "audio", voice_path, script_data["voiceover"], {"voice": voice_label})
                st.audio(voice_path)

                st.info("Bước 2/7: Tạo subtitle SRT")
                srt_path = make_srt_from_auto_scenes(project, script_data["scenes"], total_seconds)
                add_asset(project["id"], "subtitle", srt_path, script_data["voiceover"], {"platform": platform_auto})
                download_file(srt_path, "⬇️ Tải subtitle SRT")

                if make_keyframes:
                    st.info("Bước 3/7: Tạo keyframe ảnh từng cảnh")
                    img_settings = {
                        "family": "Native", "model": IMAGE_MODELS_NATIVE[0],
                        "aspect_ratio": auto_settings["aspect_ratio"], "image_size": "1K",
                        "number_of_images": 1, "person_generation": "allow_adult",
                    }
                    for scene in script_data["scenes"]:
                        imgs = generate_text_image(project, api_key, scene["visual_prompt"], img_settings, mock)
                        for img in imgs:
                            add_asset(project["id"], "image", img, scene["visual_prompt"], img_settings)

                st.info("Bước 4/7: Render video từng cảnh")
                clips, failed = [], []
                prog = st.progress(0)
                for i, scene in enumerate(script_data["scenes"], 1):
                    scene_prompt = enhance_prompt(scene["visual_prompt"], "video", style, camera, mood, negative) if auto_enhance else scene["visual_prompt"]
                    try:
                        clip, _, used_settings = generate_video_with_fallback(
                            project, api_key, scene_prompt, auto_settings, mock, "script_scene", enable_fallback=auto_fallback
                        )
                        clips.append(clip)
                        add_asset(project["id"], "video", clip, scene_prompt, used_settings)
                    except Exception as e:
                        failed.append({"scene": i, "error": str(e), "prompt": scene_prompt})
                        log_api_error("auto_content_scene", e, auto_settings, scene_prompt)
                    prog.progress(int(i / len(script_data["scenes"]) * 70))

                if not clips:
                    raise RuntimeError("Không render được scene nào. Hãy bật Mock demo hoặc kiểm tra API key/quota/model.")

                st.info("Bước 5/7: Nối video final")
                raw_final = ffmpeg_concat_videos(project, clips, f"auto_raw_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4", add_fade=True)
                add_asset(project["id"], "video", raw_final, json.dumps(script_data, ensure_ascii=False), {"clips": clips, "failed": failed, **auto_settings})

                st.info("Bước 6/7: Ghép voice + subtitle")
                try:
                    final_video = audio_studio_mix(
                        project, raw_final,
                        music_path=None,
                        voice_path=voice_path,
                        srt_path=srt_path if burn_subtitles else None,
                        music_volume=0.0,
                        voice_volume=1.0,
                    )
                except Exception as e:
                    log_api_error("auto_content_audio_mix", e, auto_settings, script_data["voiceover"])
                    st.warning("Ghép audio/subtitle lỗi, dùng video raw final thay thế.")
                    final_video = raw_final
                add_asset(project["id"], "video", final_video, script_data["voiceover"], {"auto_content": True, **auto_settings})

                st.info("Bước 7/7: Tạo thumbnail + publish package")
                thumb = make_thumbnail_with_title(project, final_video, script_data["title"], platform_auto)
                add_asset(project["id"], "image", thumb, script_data["title"], {"thumbnail": True})
                package_zip = create_auto_content_package(project, final_video, thumb, script_data, srt_path, voice_path, platform_auto, auto_settings)
                add_usage(project["id"], "auto_content", model_auto, total_seconds, est_cost)

                st.success("Hoàn tất: Text → Final Video")
                show_asset_preview(final_video, "Final video")
                download_file(final_video, "⬇️ Tải final video")
                st.image(thumb, caption="Thumbnail", use_container_width=True)
                download_file(thumb, "⬇️ Tải thumbnail")
                download_file(str(package_zip), "📦 Tải publish package ZIP")

                if failed:
                    st.warning(f"Có {len(failed)} scene lỗi nhưng pipeline vẫn xuất video từ các scene thành công.")
                    st.json(failed)
            except Exception as e:
                try:
                    log_api_error("auto_content_machine", e, auto_settings, topic)
                except Exception:
                    pass
                st.exception(e)


# -----------------------------
# Project tab
# -----------------------------
with tabs[1]:
    st.markdown("## 📁 Project Library")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Project", current_project["name"])
    with c2:
        st.metric("Assets", len(list_assets(current_project["id"], None, 10000)))
    with c3:
        st.metric("Jobs", len(list_jobs(current_project["id"], None, 10000)))

    st.markdown("### Export / Backup")
    cexp1, cexp2 = st.columns(2)
    with cexp1:
        if st.button("📦 Export ZIP project", type="primary", use_container_width=True):
            try:
                zip_path = export_project_zip(current_project["id"])
                backup_path = auto_backup_project(current_project["id"], "export")
                st.success("Đã tạo ZIP project và backup.")
                download_file(str(zip_path), "⬇️ Tải ZIP project")
                download_file(str(backup_path), "⬇️ Tải backup ZIP")
            except Exception as e:
                st.exception(e)
    with cexp2:
        if st.button("🛡️ Tạo backup ngay", use_container_width=True):
            try:
                backup_path = auto_backup_project(current_project["id"], "manual")
                st.success("Đã backup project.")
                download_file(str(backup_path), "⬇️ Tải backup")
            except Exception as e:
                st.exception(e)

    backups = list_backups(current_project)
    with st.expander(f"🛡️ Backups hiện có ({len(backups)})", expanded=False):
        if not backups:
            st.info("Chưa có backup.")
        for b in backups[:10]:
            st.write(f"{b.name} · {datetime.fromtimestamp(b.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
            download_file(str(b), f"⬇️ {b.name}")

    st.markdown("### Backup lên Google Drive / iCloud / ổ đồng bộ")
    guessed = guess_sync_folders()
    default_sync = guessed[0] if guessed else ""
    sync_folder = st.text_input("Thư mục đồng bộ local", value=default_sync, placeholder="Ví dụ: /Users/you/Library/Mobile Documents/com~apple~CloudDocs/AutoVeoBackups")
    st.caption("Cách này dùng thư mục Google Drive/iCloud/Dropbox đã cài trên máy. App sẽ copy ZIP backup vào đó để app đồng bộ tự upload.")
    if st.button("☁️ Backup sang thư mục đồng bộ", use_container_width=True):
        if not sync_folder.strip():
            st.error("Hãy nhập đường dẫn thư mục Google Drive/iCloud/Dropbox local.")
        else:
            try:
                dest = copy_backup_to_sync_folder(current_project["id"], sync_folder, "sync")
                st.success(f"Đã copy backup tới: {dest}")
            except Exception as e:
                st.exception(e)

    st.markdown("### Final Publish Package")
    videos = list_assets(current_project["id"], "video", 50)
    if not videos:
        st.info("Chưa có video để đóng gói publish.")
    else:
        vid_idx = st.selectbox("Chọn video final", list(range(len(videos))), format_func=lambda i: Path(videos[i]["path"]).name, key="publish_asset_select")
        platform_pub = st.selectbox("Nền tảng publish", ["TikTok / Reels", "YouTube Shorts", "Product Ads", "Facebook", "YouTube Longform"], key="publish_platform")
        if st.button("📦 Tạo Final Publish Package", use_container_width=True):
            try:
                asset = videos[vid_idx]
                zip_pub = create_publish_package(
                    current_project,
                    asset["path"],
                    asset.get("prompt", ""),
                    safe_json_loads(asset.get("settings_json"), {}),
                    platform_pub,
                )
                st.success("Đã tạo publish package gồm video, thumbnail, caption, hashtag, metadata.")
                download_file(str(zip_pub), "⬇️ Tải publish package ZIP")
            except Exception as e:
                st.exception(e)

    st.markdown("### Asset gần đây")
    render_asset_gallery(current_project["id"], None, 18)


# -----------------------------
# Prompt Library
# -----------------------------
with tabs[2]:
    st.markdown("## 🧠 Prompt Library / Template theo ngành")
    c1, c2 = st.columns([1, 1])
    with c1:
        category = st.selectbox("Chọn ngành", list(PROMPT_TEMPLATES.keys()))
        template_type = st.radio("Loại template", ["image", "video"], horizontal=True)
        template = PROMPT_TEMPLATES[category][template_type]
        st.text_area("Template", value=template, height=145, key="template_view")
        copy_button(template, "Copy template")
    with c2:
        st.markdown("### Lưu prompt")
        prompt_title = st.text_input("Tiêu đề prompt")
        prompt_cat = st.text_input("Category", value=category)
        prompt_body = st.text_area("Prompt cần lưu", height=145, value=template)
        fav = st.checkbox("Đánh dấu Favorite", value=True)
        if st.button("💾 Save Prompt", type="primary", use_container_width=True):
            save_prompt(prompt_title or category, prompt_cat, prompt_body, fav)
            st.success("Đã lưu prompt.")

    st.divider()
    st.markdown("### 🇻🇳 Preset prompt tiếng Việt chuyên ngành")
    vi_cat = st.selectbox("Ngành tiếng Việt", list(VI_SPECIALIZED_PROMPTS.keys()), key="vi_prompt_cat")
    vi_kind = st.radio("Loại prompt tiếng Việt", ["image", "video"], horizontal=True, key="vi_prompt_kind")
    vi_prompt = VI_SPECIALIZED_PROMPTS[vi_cat][vi_kind]
    st.text_area("Prompt tiếng Việt", value=vi_prompt, height=135, key="vi_prompt_text")
    copy_button(vi_prompt, "Copy prompt tiếng Việt")
    cvi1, cvi2 = st.columns(2)
    with cvi1:
        if st.button("💾 Lưu preset tiếng Việt", use_container_width=True):
            save_prompt(f"VI · {vi_cat} · {vi_kind}", vi_cat, vi_prompt, True)
            st.success("Đã lưu preset tiếng Việt.")
    with cvi2:
        if st.button("➕ Thêm preset video vào Queue", use_container_width=True):
            s = {"model": VIDEO_MODELS[0], "aspect_ratio": "9:16", "duration": 8, "resolution": "720p", "person_generation": "allow_adult", "poll_seconds": 10}
            create_job(current_project["id"], "text_video", vi_prompt, s, estimate_cost("text_video", s, price_image, price_video_sec))
            st.success("Đã thêm vào Queue.")

    st.divider()
    st.markdown("### Prompt đã lưu")
    fav_only = st.checkbox("Chỉ hiện Favorite", value=False)
    prompts = list_prompts(fav_only)
    if not prompts:
        st.info("Chưa có prompt đã lưu.")
    for p in prompts:
        with st.expander(("⭐ " if p["is_favorite"] else "") + f"{p['title']} · {p['category']}"):
            st.code(p["prompt"])
            copy_button(p["prompt"], "Copy prompt")
            cols = st.columns(2)
            with cols[0]:
                if st.button("⭐ Toggle Favorite", key=f"fav_{p['id']}", use_container_width=True):
                    update_prompt_favorite(p["id"], not bool(p["is_favorite"]))
                    st.rerun()
            with cols[1]:
                if st.button("➕ Thêm vào Queue video", key=f"qprompt_{p['id']}", use_container_width=True):
                    s = {"model": VIDEO_MODELS[0], "aspect_ratio": "9:16", "duration": 8, "resolution": "720p", "person_generation": "allow_adult", "poll_seconds": 10}
                    cost = estimate_cost("text_video", s, price_image, price_video_sec)
                    create_job(current_project["id"], "text_video", p["prompt"], s, cost)
                    st.success("Đã thêm vào Queue.")


# -----------------------------
# Character Bible
# -----------------------------
with tabs[3]:
    st.markdown("## 🧬 Character Bible nâng cao")
    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown("### Tạo hồ sơ nhân vật")
        char_name = st.text_input("Tên nhân vật")
        bible = st.text_area("Character bible", height=140, placeholder="Tuổi, quốc tịch, khuôn mặt, tóc, vóc dáng, tính cách, phong cách...")
        locked = st.text_area("Khóa đặc điểm không được thay đổi", height=95, placeholder="Mặt trái xoan, tóc bob đen, áo trench coat be, mắt nghiêm...")
        face = st.file_uploader("Ảnh mặt", type=["png", "jpg", "jpeg", "webp"], key="char_face")
        body = st.file_uploader("Ảnh toàn thân", type=["png", "jpg", "jpeg", "webp"], key="char_body")
        outfit = st.file_uploader("Ảnh outfit/phụ kiện", type=["png", "jpg", "jpeg", "webp"], key="char_outfit")
        if st.button("💾 Lưu nhân vật", type="primary", use_container_width=True):
            if not char_name.strip():
                st.error("Hãy nhập tên nhân vật.")
            else:
                create_character(char_name, bible, locked, face, body, outfit)
                st.success("Đã lưu nhân vật.")
                st.rerun()
    with c2:
        st.markdown("### Nhân vật đã lưu")
        chars = list_characters()
        if not chars:
            st.info("Chưa có nhân vật.")
        for ch in chars:
            with st.expander(f"🧬 {ch['name']}"):
                st.write(ch["bible"])
                st.caption("Locked traits: " + ch.get("locked_traits", ""))
                cols = st.columns(3)
                for i, key in enumerate(["face_path", "body_path", "outfit_path"]):
                    p = ch.get(key, "")
                    if p and Path(p).exists():
                        with cols[i]:
                            st.image(p, caption=key.replace("_path", ""), use_container_width=True)


# -----------------------------
# Image Studio
# -----------------------------
with tabs[4]:
    st.markdown("## 🎨 Image Studio")
    subtabs = st.tabs(["Text → Image", "Image → Image", "Script → Images"])

    with subtabs[0]:
        settings = image_settings_panel("img_text")
        chosen_template = st.selectbox("Template nhanh", ["Không dùng"] + list(PROMPT_TEMPLATES.keys()), key="img_tpl")
        default_prompt = PROMPT_TEMPLATES[chosen_template]["image"] if chosen_template != "Không dùng" else "A cinematic Vietnamese cyberpunk heroine on a rainy Saigon rooftop, neon lights, detailed portrait."
        prompt = st.text_area("Prompt", value=default_prompt, height=155, key="img_prompt")
        final_prompt = enhance_prompt(prompt, "image", style, camera, mood, negative) if auto_enhance else prompt
        st.text_area("Prompt cuối", value=final_prompt, height=135, key="img_final")
        show_prompt_quality(final_prompt, "image", negative)
        cost = display_cost_box("text_image", settings, price_image, price_video_sec)
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("🚀 Tạo ảnh ngay", type="primary", use_container_width=True):
                try:
                    paths = generate_text_image(current_project, api_key, final_prompt, settings, mock)
                    for p in paths:
                        add_asset(current_project["id"], "image", p, final_prompt, settings)
                    add_usage(current_project["id"], "image", settings.get("model", ""), len(paths), cost)
                    st.success(f"Đã tạo {len(paths)} ảnh.")
                    for p in paths:
                        show_asset_preview(p)
                        download_file(p)
                except Exception as e:
                    st.exception(e)
        with c2:
            if st.button("➕ Thêm vào Queue", use_container_width=True):
                create_job(current_project["id"], "text_image", final_prompt, settings, cost)
                st.success("Đã thêm vào Queue.")
        with c3:
            if st.button("💾 Save Prompt", use_container_width=True):
                save_prompt("Image prompt", chosen_template if chosen_template != "Không dùng" else "Image", final_prompt, True)
                st.success("Đã lưu prompt.")

    with subtabs[1]:
        settings = image_settings_panel("img_edit")
        upload = st.file_uploader("Upload ảnh gốc", type=["png", "jpg", "jpeg", "webp"], key="i2i_upload")
        edit_prompt = st.text_area("Yêu cầu chỉnh ảnh", value="Turn this into a cinematic poster while preserving the main subject identity.", height=140)
        if upload:
            st.image(pil_from_upload(upload), caption="Ảnh gốc", use_container_width=True)
        if st.button("🪄 Chỉnh ảnh", type="primary", use_container_width=True):
            if not upload:
                st.error("Hãy upload ảnh.")
            else:
                try:
                    final = enhance_prompt(edit_prompt, "image", style, camera, mood, negative) if auto_enhance else edit_prompt
                    paths = generate_image_to_image(current_project, api_key, final, pil_from_upload(upload), settings, mock)
                    for p in paths:
                        add_asset(current_project["id"], "image", p, final, settings)
                        show_asset_preview(p)
                        download_file(p)
                except Exception as e:
                    st.exception(e)

    with subtabs[2]:
        settings = image_settings_panel("script_img")
        script = st.text_area("Kịch bản, mỗi dòng là một cảnh", height=220)
        max_scenes = st.slider("Tối đa cảnh", 1, 20, 6, key="script_img_max")
        chars = list_characters()
        char_choice = st.selectbox("Nhân vật cố định", ["Không dùng"] + [c["name"] for c in chars], key="script_img_char")
        char_bible = ""
        locked_traits = ""
        if char_choice != "Không dùng":
            ch = next(c for c in chars if c["name"] == char_choice)
            char_bible, locked_traits = ch["bible"], ch["locked_traits"]
        if st.button("📖 Tạo ảnh từng cảnh", type="primary", use_container_width=True):
            scenes = split_script_to_scenes(script, max_scenes, 8, char_bible)
            all_paths = []
            prog = st.progress(0)
            for i, sc in enumerate(scenes, 1):
                p = enhance_prompt(sc["prompt"], "image", style, camera, mood, negative, char_bible, locked_traits) if auto_enhance else sc["prompt"]
                paths = generate_text_image(current_project, api_key, p, {**settings, "number_of_images": 1}, mock)
                for path in paths:
                    add_asset(current_project["id"], "image", path, p, settings)
                    all_paths.append(path)
                prog.progress(int(i / len(scenes) * 100))
            st.success(f"Đã tạo {len(all_paths)} ảnh.")
            for p in all_paths:
                show_asset_preview(p)


# -----------------------------
# Video Studio
# -----------------------------
with tabs[5]:
    st.markdown("## 🎬 Video Studio")
    subtabs = st.tabs(["Text → Video", "Image → Video", "Start-End → Video", "Reference Character → Video", "Extend"])

    with subtabs[0]:
        settings = video_settings_panel("text_video")
        chosen_template = st.selectbox("Template video", ["Không dùng"] + list(PROMPT_TEMPLATES.keys()), key="vid_tpl")
        default_prompt = PROMPT_TEMPLATES[chosen_template]["video"] if chosen_template != "Không dùng" else "A cinematic tracking shot of a Vietnamese female detective walking through a rainy neon alley at night."
        prompt = st.text_area("Prompt video", value=default_prompt, height=170, key="vid_prompt")
        chars = list_characters()
        char_choice = st.selectbox("Dùng character bible", ["Không dùng"] + [c["name"] for c in chars], key="vid_char")
        char_bible = locked_traits = ""
        if char_choice != "Không dùng":
            ch = next(c for c in chars if c["name"] == char_choice)
            char_bible, locked_traits = ch["bible"], ch["locked_traits"]
        final = enhance_prompt(prompt, "video", style, camera, mood, negative, char_bible, locked_traits) if auto_enhance else prompt
        st.text_area("Prompt cuối", value=final, height=150, key="vid_final")
        show_prompt_quality(final, "video", negative)
        enable_fallback_text_video = st.checkbox("Tự fallback model nếu render lỗi", value=True, key="fallback_text_video")
        cost = display_cost_box("text_video", settings, price_image, price_video_sec)
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("🎥 Render ngay", type="primary", use_container_width=True):
                try:
                    path, video_obj, used_settings = generate_video_with_fallback(current_project, api_key, final, settings, mock, "text_video", enable_fallback=enable_fallback_text_video)
                    add_asset(current_project["id"], "video", path, final, used_settings)
                    add_usage(current_project["id"], "video", used_settings.get("model", ""), used_settings.get("duration", 8), cost)
                    if video_obj is not None:
                        st.session_state.veo_objects.append({"path": path, "prompt": final, "settings": used_settings, "video": video_obj})
                    show_asset_preview(path)
                    download_file(path)
                except Exception as e:
                    st.exception(e)
        with c2:
            if st.button("➕ Thêm vào Queue", use_container_width=True):
                create_job(current_project["id"], "text_video", final, settings, cost)
                st.success("Đã thêm vào Queue.")
        with c3:
            if st.button("💾 Save/Favorite Prompt", use_container_width=True):
                save_prompt("Video prompt", chosen_template if chosen_template != "Không dùng" else "Video", final, True)
                st.success("Đã lưu prompt.")

    with subtabs[1]:
        settings = video_settings_panel("image_video")
        up = st.file_uploader("Ảnh đầu vào", type=["png", "jpg", "jpeg", "webp"], key="img2vid")
        prompt = st.text_area("Mô tả chuyển động", value="Animate this image into a cinematic scene. Smooth camera push-in, natural motion, realistic lighting.", height=140)
        if up:
            st.image(pil_from_upload(up), caption="Ảnh đầu vào", use_container_width=True)
        show_prompt_quality(prompt, "video", negative)
        cost = display_cost_box("image_video", settings, price_image, price_video_sec)
        if st.button("🖼️ Render Image → Video", type="primary", use_container_width=True):
            if not up:
                st.error("Hãy upload ảnh.")
            else:
                try:
                    final = enhance_prompt(prompt, "video", style, camera, mood, negative) if auto_enhance else prompt
                    path, video_obj = generate_video(current_project, api_key, final, settings, mock, "image_video", input_image=pil_from_upload(up))
                    add_asset(current_project["id"], "video", path, final, settings)
                    add_usage(current_project["id"], "video", settings.get("model", ""), settings.get("duration", 8), cost)
                    if video_obj is not None:
                        st.session_state.veo_objects.append({"path": path, "prompt": final, "settings": settings, "video": video_obj})
                    show_asset_preview(path)
                    download_file(path)
                except Exception as e:
                    st.exception(e)

    with subtabs[2]:
        settings = video_settings_panel("start_end_video")
        c1, c2 = st.columns(2)
        with c1:
            first = st.file_uploader("Start frame", type=["png", "jpg", "jpeg", "webp"], key="start_frame")
            if first:
                st.image(pil_from_upload(first), use_container_width=True)
        with c2:
            last = st.file_uploader("End frame", type=["png", "jpg", "jpeg", "webp"], key="end_frame")
            if last:
                st.image(pil_from_upload(last), use_container_width=True)
        prompt = st.text_area("Mô tả diễn biến ở giữa", value="Create a smooth cinematic transition between the start and end frame. Preserve identity, lighting, and realistic motion.", height=130)
        show_prompt_quality(prompt, "video", negative)
        cost = display_cost_box("start_end_video", settings, price_image, price_video_sec)
        if st.button("🔁 Render Start-End", type="primary", use_container_width=True):
            if not first or not last:
                st.error("Cần đủ start và end frame.")
            else:
                try:
                    final = enhance_prompt(prompt, "video", style, camera, mood, negative) if auto_enhance else prompt
                    path, video_obj = generate_video(current_project, api_key, final, settings, mock, "start_end_video", input_image=pil_from_upload(first), last_frame=pil_from_upload(last))
                    add_asset(current_project["id"], "video", path, final, settings)
                    add_usage(current_project["id"], "video", settings.get("model", ""), settings.get("duration", 8), cost)
                    if video_obj is not None:
                        st.session_state.veo_objects.append({"path": path, "prompt": final, "settings": settings, "video": video_obj})
                    show_asset_preview(path)
                    download_file(path)
                except Exception as e:
                    st.exception(e)

    with subtabs[3]:
        settings = video_settings_panel("reference_video")
        chars = list_characters()
        char_choice = st.selectbox("Chọn nhân vật đã lưu", ["Upload thủ công"] + [c["name"] for c in chars], key="ref_char")
        refs = []
        char_bible = locked_traits = ""
        if char_choice == "Upload thủ công":
            ups = st.file_uploader("Upload tối đa 3 ảnh reference", type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=True, key="manual_refs")
            if ups:
                refs = [pil_from_upload(u) for u in ups[:3]]
        else:
            ch = next(c for c in chars if c["name"] == char_choice)
            refs = character_ref_images(ch)
            char_bible, locked_traits = ch["bible"], ch["locked_traits"]
            st.info(f"Đang dùng character: {ch['name']}")
        if refs:
            cols = st.columns(min(3, len(refs)))
            for i, img in enumerate(refs):
                with cols[i]:
                    st.image(img, caption=f"Ref {i+1}", use_container_width=True)
        prompt = st.text_area("Prompt dùng nhân vật/sản phẩm tham chiếu", value="The referenced character walks through a futuristic police lab, picks up a glowing evidence chip, and looks determined.", height=140)
        show_prompt_quality(prompt, "video", negative)
        cost = display_cost_box("reference_video", settings, price_image, price_video_sec)
        if st.button("🧬 Render Reference Video", type="primary", use_container_width=True):
            if not refs:
                st.error("Cần ít nhất 1 ảnh reference.")
            else:
                try:
                    final = enhance_prompt(prompt, "video", style, camera, mood, negative, char_bible, locked_traits) if auto_enhance else prompt
                    path, video_obj = generate_video(current_project, api_key, final, settings, mock, "reference_video", ref_images=refs)
                    add_asset(current_project["id"], "video", path, final, settings)
                    add_usage(current_project["id"], "video", settings.get("model", ""), settings.get("duration", 8), cost)
                    if video_obj is not None:
                        st.session_state.veo_objects.append({"path": path, "prompt": final, "settings": settings, "video": video_obj})
                    show_asset_preview(path)
                    download_file(path)
                except Exception as e:
                    st.exception(e)

    with subtabs[4]:
        st.markdown("### ⏩ Extend Video")
        settings = video_settings_panel("extend_video")
        if not st.session_state.veo_objects:
            st.info("Extend tốt nhất với video object sinh từ Veo trong cùng phiên chạy. Hãy render video trước.")
        else:
            idx = st.selectbox("Chọn video để extend", list(range(len(st.session_state.veo_objects))), format_func=lambda i: Path(st.session_state.veo_objects[i]["path"]).name)
            prompt = st.text_area("Prompt phần kéo dài", value="Continue the scene naturally with the same character, mood, camera movement and continuity.", height=120)
            loops = st.slider("Số lần extend", 1, 5, 1)
            if st.button("⏩ Extend", type="primary", use_container_width=True):
                try:
                    current_obj = st.session_state.veo_objects[idx]["video"]
                    final = enhance_prompt(prompt, "video", style, camera, mood, negative) if auto_enhance else prompt
                    paths = []
                    for i in range(loops):
                        path, current_obj = generate_video(current_project, api_key, final, settings, mock, "extend_video", extend_video_object=current_obj)
                        paths.append(path)
                        add_asset(current_project["id"], "video", path, final, settings)
                        if current_obj is not None:
                            st.session_state.veo_objects.append({"path": path, "prompt": final, "settings": settings, "video": current_obj})
                    for p in paths:
                        show_asset_preview(p)
                        download_file(p)
                except Exception as e:
                    st.exception(e)


# -----------------------------
# Batch + Queue
# -----------------------------
with tabs[6]:
    st.markdown("## 📦 Batch Render + Queue chuyên nghiệp local")
    st.caption("Queue được lưu SQLite, reload app không mất. App cá nhân nên chạy từng job hoặc tất cả tuần tự để tránh quá tải API.")
    batch_type = st.selectbox("Loại batch", ["text_video", "text_image"])
    if batch_type == "text_video":
        batch_settings = video_settings_panel("batch_video")
    else:
        batch_settings = image_settings_panel("batch_image")

    prompts_text = st.text_area("Dán nhiều prompt, mỗi dòng là một job", height=220)
    lines = [x.strip() for x in prompts_text.splitlines() if x.strip()]
    batch_settings_with_scenes = dict(batch_settings)
    batch_settings_with_scenes["scenes"] = max(1, len(lines))
    cost = estimate_cost(batch_type, batch_settings_with_scenes, price_image, price_video_sec)
    st.info(f"Ước tính tổng batch: {cost:,.4f} USD cho {len(lines)} job.")
    if st.button("➕ Thêm batch vào Queue", type="primary", use_container_width=True):
        if not lines:
            st.error("Chưa có prompt.")
        else:
            per_job_cost = cost / len(lines) if lines else 0
            for line in lines:
                final = enhance_prompt(line, "video" if batch_type == "text_video" else "image", style, camera, mood, negative) if auto_enhance else line
                create_job(current_project["id"], batch_type, final, batch_settings, per_job_cost)
            st.success(f"Đã thêm {len(lines)} job vào Queue.")

    st.divider()
    st.markdown("### Queue")
    jobs = list_jobs(current_project["id"], None, 100)
    pending = [j for j in jobs if j["status"] == "pending"]
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("▶️ Chạy job pending mới nhất", use_container_width=True):
            if not pending:
                st.info("Không có job pending.")
            else:
                job = sorted(pending, key=lambda x: x["id"])[0]
                try:
                    paths = execute_job(current_project, job, api_key, mock)
                    st.success(f"Xong job #{job['id']}")
                    for p in paths:
                        show_asset_preview(p)
                except Exception as e:
                    st.exception(e)
    with c2:
        if st.button("▶️ Chạy tất cả pending tuần tự", type="primary", use_container_width=True):
            if not pending:
                st.info("Không có job pending.")
            else:
                prog = st.progress(0)
                for i, job in enumerate(sorted(pending, key=lambda x: x["id"]), 1):
                    st.info(f"Đang chạy job #{job['id']} ({i}/{len(pending)})")
                    try:
                        execute_job(current_project, job, api_key, mock)
                    except Exception as e:
                        st.error(f"Job #{job['id']} lỗi: {e}")
                    prog.progress(int(i / len(pending) * 100))
                st.success("Đã xử lý xong queue.")
    with c3:
        if st.button("🧹 Xóa job pending", use_container_width=True):
            with db() as conn:
                conn.execute("DELETE FROM jobs WHERE project_id=? AND status='pending'", (current_project["id"],))
            st.success("Đã xóa pending.")
            st.rerun()

    for job in jobs:
        with st.expander(f"#{job['id']} · {job['job_type']} · {job['status']} · est ${float(job['cost_estimate'] or 0):.4f}", expanded=False):
            st.code(job["prompt"][:1600])
            st.json(safe_json_loads(job["settings_json"], {}))
            if job.get("error"):
                st.error(job["error"])
            paths = safe_json_loads(job.get("result_paths_json"), [])
            for p in paths:
                show_asset_preview(p)
            cc1, cc2 = st.columns(2)
            with cc1:
                if st.button("🔁 Retry job này", key=f"retry_job_{job['id']}", use_container_width=True):
                    duplicate_job(job)
                    st.success("Đã tạo job retry.")
            with cc2:
                if job["status"] == "pending" and st.button("▶️ Chạy job này", key=f"run_job_{job['id']}", use_container_width=True):
                    try:
                        execute_job(current_project, job, api_key, mock)
                        st.success("Xong.")
                    except Exception as e:
                        st.exception(e)



# -----------------------------
# Workflow Presets
# -----------------------------
with tabs[7]:
    st.markdown("## ⚡ Workflow Presets theo nền tảng")
    st.caption("Chọn mục tiêu đăng nền tảng, nhập chủ đề/sản phẩm, app tự tạo timeline mẫu. Sau đó có thể gửi sang Timeline Studio để render.")
    c1, c2 = st.columns([1, 1])
    with c1:
        preset_name = st.selectbox("Workflow preset", list(WORKFLOW_PRESETS.keys()))
        topic = st.text_area("Chủ đề / sản phẩm / câu chuyện", height=120, placeholder="Ví dụ: serum vitamin C cho nữ 25-35 tuổi, phong cách luxury clean beauty...")
        override_duration = st.selectbox("Độ dài mỗi cảnh", ["Theo preset", 4, 6, 8], index=0)
        dur = None if override_duration == "Theo preset" else int(override_duration)
        rows = preset_to_timeline_rows(preset_name, topic, dur)
        preset = WORKFLOW_PRESETS[preset_name]
        st.markdown(
            f"""
<div class="card">
<b>Preset:</b> {preset_name}<br>
<b>Nền tảng:</b> {preset['platform']}<br>
<b>Tỉ lệ:</b> {preset['aspect_ratio']}<br>
<b>Độ phân giải gợi ý:</b> {preset['resolution']}<br>
<b>Số cảnh:</b> {len(rows)}<br>
<b>Tổng thời lượng xấp xỉ:</b> {sum(int(r['duration']) for r in rows)} giây<br>
<span class="small">Subtitle style: {preset['subtitle_style']}</span>
</div>
""",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown("### Shot list mẫu")
        st.dataframe(rows, use_container_width=True, hide_index=True)

    edited_rows = st.data_editor(
        rows,
        num_rows="dynamic",
        use_container_width=True,
        key="workflow_preset_editor",
        column_config={
            "scene": st.column_config.NumberColumn("Cảnh", min_value=1),
            "duration": st.column_config.NumberColumn("Giây", min_value=4, max_value=8),
            "description": st.column_config.TextColumn("Mô tả"),
            "prompt": st.column_config.TextColumn("Prompt"),
        },
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("➡️ Gửi sang Timeline Studio", type="primary", use_container_width=True):
            st.session_state.timeline_scenes = edited_rows
            st.session_state.workflow_video_defaults = {
                "aspect_ratio": WORKFLOW_PRESETS[preset_name]["aspect_ratio"],
                "duration": int(edited_rows[0]["duration"]) if edited_rows else WORKFLOW_PRESETS[preset_name]["duration"],
                "resolution": WORKFLOW_PRESETS[preset_name]["resolution"],
                "model": VIDEO_MODELS[0],
                "person_generation": "allow_adult",
                "poll_seconds": 10,
            }
            st.success("Đã gửi timeline mẫu sang tab Timeline Studio.")
    with c2:
        if st.button("➕ Thêm từng cảnh vào Queue", use_container_width=True):
            settings = {
                "model": VIDEO_MODELS[0],
                "aspect_ratio": WORKFLOW_PRESETS[preset_name]["aspect_ratio"],
                "duration": WORKFLOW_PRESETS[preset_name]["duration"],
                "resolution": WORKFLOW_PRESETS[preset_name]["resolution"],
                "person_generation": "allow_adult",
                "poll_seconds": 10,
            }
            for row in edited_rows:
                s = dict(settings)
                s["duration"] = int(row.get("duration") or settings["duration"])
                cost = estimate_cost("text_video", s, price_image, price_video_sec)
                create_job(current_project["id"], "text_video", str(row.get("prompt", "")), s, cost)
            st.success(f"Đã thêm {len(edited_rows)} cảnh vào Queue.")
    with c3:
        if st.button("💾 Lưu preset prompt vào Prompt Library", use_container_width=True):
            for row in edited_rows:
                save_prompt(f"{preset_name} · Scene {row.get('scene')}", preset_name, str(row.get("prompt", "")), True)
            st.success("Đã lưu các prompt cảnh vào Prompt Library.")

    st.divider()
    workflow_json = {
        "preset": preset_name,
        "topic": topic,
        "rows": edited_rows,
        "settings": {
            "aspect_ratio": WORKFLOW_PRESETS[preset_name]["aspect_ratio"],
            "resolution": WORKFLOW_PRESETS[preset_name]["resolution"],
            "platform": WORKFLOW_PRESETS[preset_name]["platform"],
        },
        "created_at": now(),
    }
    st.download_button(
        "⬇️ Tải workflow JSON",
        json.dumps(workflow_json, ensure_ascii=False, indent=2).encode("utf-8"),
        file_name=f"{slugify(preset_name)}_workflow.json",
        mime="application/json",
        use_container_width=True,
    )


# -----------------------------
# Timeline Studio
# -----------------------------
with tabs[8]:
    st.markdown("## 🎞️ Timeline Video Studio")
    st.caption("Tạo nhiều cảnh 4/6/8 giây, render từng cảnh, sau đó nối thành video dài.")
    settings = video_settings_panel("timeline", st.session_state.get("workflow_video_defaults", {}))
    char_bible = locked_traits = ""
    chars = list_characters()
    char_choice = st.selectbox("Character continuity", ["Không dùng"] + [c["name"] for c in chars], key="timeline_char")
    if char_choice != "Không dùng":
        ch = next(c for c in chars if c["name"] == char_choice)
        char_bible, locked_traits = ch["bible"], ch["locked_traits"]

    st.markdown("### Nhập scene")
    default_rows = st.session_state.timeline_scenes or [
        {"scene": 1, "duration": settings["duration"], "description": "Opening shot", "prompt": "Opening cinematic shot with clear establishing composition."},
        {"scene": 2, "duration": settings["duration"], "description": "Character action", "prompt": "The main character performs the key action with smooth camera movement."},
    ]
    edited = st.data_editor(
        default_rows,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "scene": st.column_config.NumberColumn("Cảnh", min_value=1),
            "duration": st.column_config.NumberColumn("Giây", min_value=4, max_value=8),
            "description": st.column_config.TextColumn("Mô tả"),
            "prompt": st.column_config.TextColumn("Prompt"),
        },
        key="timeline_editor",
    )
    st.session_state.timeline_scenes = edited
    add_fade = st.checkbox("Thêm fade-in/fade-out nhẹ trước khi nối", value=True)
    output_name = st.text_input("Tên video final", value="timeline_final.mp4")
    enable_fallback_timeline = st.checkbox("Tự fallback model cho từng cảnh lỗi", value=True, key="fallback_timeline")
    est_settings = dict(settings)
    est_settings["scenes"] = len(edited)
    cost = display_cost_box("timeline", est_settings, price_image, price_video_sec)

    if st.button("🎞️ Render timeline + nối final", type="primary", use_container_width=True):
        if not edited:
            st.error("Chưa có scene.")
        else:
            try:
                clips = []
                failed_rows = []
                prog = st.progress(0)
                for i, sc in enumerate(edited, 1):
                    scene_settings = dict(settings)
                    scene_settings["duration"] = int(sc.get("duration") or settings["duration"])
                    prompt = str(sc.get("prompt") or sc.get("description") or f"Scene {i}")
                    final = enhance_prompt(prompt, "video", style, camera, mood, negative, char_bible, locked_traits) if auto_enhance else prompt
                    st.info(f"Render scene {i}/{len(edited)}")
                    show_prompt_quality(final, "video", negative)
                    try:
                        path, _, used_settings = generate_video_with_fallback(
                            current_project, api_key, final, scene_settings, mock, "timeline_scene", enable_fallback=enable_fallback_timeline
                        )
                        clips.append(path)
                        add_asset(current_project["id"], "video", path, final, used_settings)
                    except Exception as scene_error:
                        failed = dict(sc)
                        failed["error"] = str(scene_error)
                        failed_rows.append(failed)
                        st.error(f"Scene {i} lỗi: {scene_error}")
                    prog.progress(int(i / len(edited) * 85))
                st.session_state.last_timeline_failed_rows = failed_rows
                st.session_state.last_timeline_success_clips = clips
                if failed_rows:
                    st.warning(f"Có {len(failed_rows)} scene lỗi. Có thể dùng nút retry timeline lỗi bên dưới.")
                if clips:
                    final_path = ffmpeg_concat_videos(current_project, clips, output_name, add_fade)
                    add_asset(current_project["id"], "video", final_path, "TIMELINE FINAL\n" + json.dumps(edited, ensure_ascii=False, indent=2), {"clips": clips, "failed": failed_rows, **settings})
                    add_usage(current_project["id"], "timeline", settings.get("model", ""), len(clips) * settings.get("duration", 8), cost)
                    prog.progress(100)
                    st.success("Đã xuất timeline final.")
                    show_asset_preview(final_path)
                    download_file(final_path)
                    try:
                        pub_zip = create_publish_package(current_project, final_path, "TIMELINE FINAL\n" + json.dumps(edited, ensure_ascii=False), {"clips": clips, **settings}, "TikTok / Reels")
                        download_file(str(pub_zip), "📦 Tải publish package tự động")
                    except Exception:
                        pass
            except Exception as e:
                st.exception(e)


    st.divider()
    st.markdown("### 🔁 Render lại toàn bộ timeline lỗi")
    failed_rows = st.session_state.get("last_timeline_failed_rows", [])
    if not failed_rows:
        st.info("Chưa có scene timeline lỗi trong phiên này.")
    else:
        st.warning(f"Đang có {len(failed_rows)} scene lỗi cần retry.")
        st.dataframe(failed_rows, use_container_width=True)
        retry_output_name = st.text_input("Tên final sau retry", value="timeline_retry_final.mp4")
        if st.button("🔁 Retry scene lỗi + nối lại final", type="primary", use_container_width=True):
            try:
                retry_clips = list(st.session_state.get("last_timeline_success_clips", []))
                still_failed = []
                for i, sc in enumerate(failed_rows, 1):
                    scene_settings = dict(settings)
                    scene_settings["duration"] = int(sc.get("duration") or settings["duration"])
                    prompt = str(sc.get("prompt") or sc.get("description") or f"Retry scene {i}")
                    final = enhance_prompt(prompt, "video", style, camera, mood, negative, char_bible, locked_traits) if auto_enhance else prompt
                    try:
                        path, _, used_settings = generate_video_with_fallback(
                            current_project, api_key, final, scene_settings, mock, "timeline_scene", enable_fallback=True
                        )
                        retry_clips.append(path)
                        add_asset(current_project["id"], "video", path, final, used_settings)
                    except Exception as e:
                        sc2 = dict(sc)
                        sc2["error"] = str(e)
                        still_failed.append(sc2)
                st.session_state.last_timeline_failed_rows = still_failed
                st.session_state.last_timeline_success_clips = retry_clips
                if retry_clips:
                    final_path = ffmpeg_concat_videos(current_project, retry_clips, retry_output_name, add_fade)
                    add_asset(current_project["id"], "video", final_path, "TIMELINE RETRY FINAL", {"clips": retry_clips, "failed": still_failed, **settings})
                    st.success("Đã retry và nối lại final.")
                    show_asset_preview(final_path)
                    download_file(final_path)
                if still_failed:
                    st.error(f"Vẫn còn {len(still_failed)} scene lỗi.")
            except Exception as e:
                st.exception(e)


# -----------------------------
# Script -> Video
# -----------------------------
with tabs[9]:
    st.markdown("## 🤖 Auto Script → Shot List → Video")
    st.caption("Script dài → chia cảnh → tạo prompt từng cảnh → tạo keyframe ảnh → render video từng cảnh → nối final.")
    script = st.text_area("Script dài", height=260, placeholder="Dán kịch bản ở đây. Mỗi dòng hoặc mỗi câu sẽ thành một cảnh.")
    max_scenes = st.slider("Tối đa cảnh", 1, 20, 5)
    seconds_each = st.selectbox("Giây mỗi cảnh", [4, 6, 8], index=2)
    settings_v = video_settings_panel("script_video")
    settings_i = image_settings_panel("script_keyframe")
    chars = list_characters()
    char_choice = st.selectbox("Nhân vật chính", ["Không dùng"] + [c["name"] for c in chars], key="script_vid_char")
    char_bible = locked_traits = ""
    if char_choice != "Không dùng":
        ch = next(c for c in chars if c["name"] == char_choice)
        char_bible, locked_traits = ch["bible"], ch["locked_traits"]
    scenes = split_script_to_scenes(script, max_scenes, seconds_each, char_bible) if script.strip() else []
    if scenes:
        st.markdown("### Shot list tự tạo")
        st.dataframe(scenes, use_container_width=True)
    do_keyframes = st.checkbox("Tạo keyframe ảnh trước", value=True)
    do_video = st.checkbox("Render video từng cảnh", value=True)
    add_fade = st.checkbox("Nối final có fade nhẹ", value=True, key="script_fade")
    enable_fallback_script = st.checkbox("Tự fallback model cho scene lỗi", value=True, key="fallback_script")
    output_name = st.text_input("Tên final", value="script_to_video_final.mp4")
    est_settings = dict(settings_v)
    est_settings["scenes"] = max(1, len(scenes))
    est_cost = display_cost_box("script_to_video", est_settings, price_image, price_video_sec)

    if st.button("🚀 Chạy Script → Video", type="primary", use_container_width=True):
        if not scenes:
            st.error("Hãy nhập script.")
        else:
            try:
                clips, keyframes = [], []
                prog = st.progress(0)
                for i, sc in enumerate(scenes, 1):
                    prompt_scene = enhance_prompt(sc["prompt"], "video", style, camera, mood, negative, char_bible, locked_traits) if auto_enhance else sc["prompt"]
                    if do_keyframes:
                        img_prompt = enhance_prompt(sc["prompt"], "image", style, camera, mood, negative, char_bible, locked_traits) if auto_enhance else sc["prompt"]
                        imgs = generate_text_image(current_project, api_key, img_prompt, {**settings_i, "number_of_images": 1}, mock)
                        for img in imgs:
                            keyframes.append(img)
                            add_asset(current_project["id"], "image", img, img_prompt, settings_i)
                    if do_video:
                        scene_settings = dict(settings_v)
                        scene_settings["duration"] = int(sc.get("duration") or seconds_each)
                        path, _, used_settings = generate_video_with_fallback(current_project, api_key, prompt_scene, scene_settings, mock, "script_scene", enable_fallback=enable_fallback_script)
                        clips.append(path)
                        add_asset(current_project["id"], "video", path, prompt_scene, used_settings)
                    prog.progress(int(i / len(scenes) * 85))
                if clips:
                    final_path = ffmpeg_concat_videos(current_project, clips, output_name, add_fade)
                    add_asset(current_project["id"], "video", final_path, script, {"script_scenes": scenes, **settings_v})
                    add_usage(current_project["id"], "script_to_video", settings_v.get("model", ""), len(clips) * settings_v.get("duration", 8), est_cost)
                    show_asset_preview(final_path)
                    download_file(final_path)
                    try:
                        pub_zip = create_publish_package(current_project, final_path, script, {"script_scenes": scenes, **settings_v}, "YouTube Shorts")
                        download_file(str(pub_zip), "📦 Tải publish package tự động")
                    except Exception:
                        pass
                st.success("Hoàn tất Script → Video.")
                if keyframes:
                    st.markdown("### Keyframes")
                    cols = st.columns(3)
                    for i, p in enumerate(keyframes):
                        with cols[i % 3]:
                            show_asset_preview(p)
            except Exception as e:
                st.exception(e)


# -----------------------------
# Audio Studio
# -----------------------------
with tabs[10]:
    st.markdown("## 🎵 Audio Studio")
    st.caption("Ghép nhạc nền, voice-over, sound effect đơn giản, phụ đề SRT vào video bằng ffmpeg.")
    video_upload = st.file_uploader("Video chính", type=["mp4", "mov", "m4v"], key="audio_video")
    music_upload = st.file_uploader("Nhạc nền / SFX", type=["mp3", "wav", "m4a"], key="audio_music")
    voice_upload = st.file_uploader("Voice-over", type=["mp3", "wav", "m4a"], key="audio_voice")
    caption_text = st.text_area("Text để tạo SRT tự động", height=120)
    seconds_per_caption = st.slider("Giây mỗi caption", 1, 8, 3)
    c1, c2 = st.columns(2)
    with c1:
        music_volume = st.slider("Âm lượng nhạc", 0.0, 2.0, 0.45, 0.05)
    with c2:
        voice_volume = st.slider("Âm lượng voice", 0.0, 2.0, 1.0, 0.05)

    if st.button("🎵 Ghép audio/subtitle", type="primary", use_container_width=True):
        if not video_upload:
            st.error("Hãy upload video chính.")
        else:
            try:
                vpath = save_uploaded_to(video_upload, project_dir(current_project) / "uploads", "video")
                mpath = save_uploaded_to(music_upload, project_dir(current_project) / "uploads", "music") if music_upload else None
                voicepath = save_uploaded_to(voice_upload, project_dir(current_project) / "uploads", "voice") if voice_upload else None
                srt_path = make_srt_from_text(current_project, caption_text, seconds_per_caption) if caption_text.strip() else None
                if srt_path:
                    add_asset(current_project["id"], "subtitle", srt_path, caption_text, {})
                out = audio_studio_mix(current_project, vpath, mpath, voicepath, srt_path, music_volume, voice_volume)
                add_asset(current_project["id"], "video", out, "Audio mix", {"music": bool(mpath), "voice": bool(voicepath), "srt": bool(srt_path)})
                show_asset_preview(out)
                download_file(out)
                if srt_path:
                    download_file(srt_path, "⬇️ Tải SRT")
            except Exception as e:
                st.exception(e)


# -----------------------------
# Video Tools
# -----------------------------
with tabs[11]:
    st.markdown("## 🛠️ Video Upscale / Convert / Compress")
    vup = st.file_uploader("Upload video", type=["mp4", "mov", "m4v"], key="tools_video")
    mode = st.selectbox("Chức năng", ["Upscale", "Crop center", "Blur background", "Compress"])
    target_ratio = st.selectbox("Tỉ lệ đích", ["9:16", "16:9"])
    upscale_to = st.selectbox("Upscale tới", ["1080p", "4k"])
    crf = st.slider("CRF nén: thấp = đẹp hơn/nặng hơn", 18, 35, 25)
    if st.button("🛠️ Xử lý video", type="primary", use_container_width=True):
        if not vup:
            st.error("Hãy upload video.")
        else:
            try:
                src = save_uploaded_to(vup, project_dir(current_project) / "uploads", "tool_video")
                out = video_convert(current_project, src, mode, target_ratio, upscale_to, crf)
                add_asset(current_project["id"], "video", out, f"Video tool: {mode}", {"mode": mode, "target_ratio": target_ratio, "upscale_to": upscale_to, "crf": crf})
                show_asset_preview(out)
                download_file(out)
            except Exception as e:
                st.exception(e)

    st.divider()
    st.markdown("### ✂️ Cắt frame thumbnail")
    frame_video = st.file_uploader("Video để cắt frame", type=["mp4", "mov", "m4v"], key="frame_extract_video")
    count = st.slider("Số frame", 1, 12, 6)
    if st.button("✂️ Lấy frame đẹp", use_container_width=True):
        if not frame_video:
            st.error("Hãy upload video.")
        elif cv2 is None:
            st.error("Thiếu OpenCV. Chạy pip install opencv-python-headless")
        else:
            try:
                src = save_uploaded_to(frame_video, project_dir(current_project) / "uploads", "frame_source")
                cap = cv2.VideoCapture(src)
                total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
                idxs = np.linspace(0, max(total - 1, 0), min(max(count * 10, 20), max(total, 1))).astype(int)
                candidates = []
                for idx in idxs:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
                    ok, frame = cap.read()
                    if not ok:
                        continue
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
                    sharp = cv2.Laplacian(gray, cv2.CV_64F).var()
                    bright = 100 - abs(float(np.mean(gray)) - 128)
                    candidates.append((sharp + bright * 2, idx, rgb))
                cap.release()
                candidates.sort(key=lambda x: x[0], reverse=True)
                paths = []
                for score, idx, rgb in candidates[:count]:
                    img = Image.fromarray(rgb)
                    p = save_pil_to_project(current_project, img, "frames", f"frame_{idx}")
                    paths.append(p)
                    add_asset(current_project["id"], "image", p, f"Frame from {Path(src).name}", {"frame": int(idx), "score": float(score)})
                cols = st.columns(3)
                for i, p in enumerate(paths):
                    with cols[i % 3]:
                        show_asset_preview(p)
                        download_file(p)
            except Exception as e:
                st.exception(e)


# -----------------------------
# Deploy / Maintenance
# -----------------------------
with tabs[12]:
    st.markdown("## 🚀 Deploy + bảo trì")
    st.caption("Kiểm tra repo trước khi đưa lên GitHub/Streamlit Cloud, dọn export cũ và xem log lỗi API.")
    st.markdown("### Checklist deploy")
    for name, ok, desc in deploy_readiness_check():
        st.write(("✅" if ok else "❌") + f" **{name}** — {desc}")

    st.markdown("### Secrets cho Streamlit Cloud")
    st.code('GEMINI_API_KEY = "your_gemini_api_key_here"', language="toml")
    st.warning("Không commit `.env` hoặc API key lên GitHub. Hãy nhập key trong Streamlit Cloud → Settings → Secrets.")

    st.markdown("### Storage report")
    report = project_storage_report(current_project)
    c1, c2 = st.columns(2)
    c1.metric("Project size", f"{report['total_mb']} MB")
    c2.metric("Files", report["files"])
    with st.expander("File lớn nhất", expanded=False):
        st.json(report["largest"])

    c1, c2 = st.columns(2)
    with c1:
        if st.button("🧹 Dọn ZIP export cũ, giữ 5 file mới nhất", use_container_width=True):
            removed = cleanup_project_exports(current_project, 5)
            st.success(f"Đã dọn {removed} file.")
    with c2:
        if st.button("🛡️ Backup trước deploy", use_container_width=True):
            b = auto_backup_project(current_project["id"], "before_deploy")
            download_file(str(b), "⬇️ Tải backup trước deploy")

    st.markdown("### Log lỗi API/render")
    logs = read_api_error_logs(100)
    if not logs:
        st.info("Chưa có log lỗi API/render.")
    else:
        st.dataframe(logs, use_container_width=True)
        log_path = LOGS_DIR / "api_errors.jsonl"
        if log_path.exists():
            download_file(str(log_path), "⬇️ Tải api_errors.jsonl")
        if st.button("🧹 Xóa log lỗi", use_container_width=True):
            clear_api_error_logs()
            st.success("Đã xóa log lỗi.")
            st.rerun()

    st.markdown("### Lệnh Git nhanh")
    st.code(
        """git init
git add .
git commit -m "Initial AUTO VEO Studio"
git branch -M main
git remote add origin https://github.com/jerydarker-cell/auto-veo-studio.git
git push -u origin main""",
        language="bash",
    )


# -----------------------------
# Dashboard
# -----------------------------
with tabs[13]:
    st.markdown("## 📊 Dashboard cá nhân")
    with db() as conn:
        usage = [dict(r) for r in conn.execute("SELECT * FROM usage_log WHERE project_id=? ORDER BY id DESC", (current_project["id"],)).fetchall()]
        jobs_all = list_jobs(current_project["id"], None, 10000)
        assets_all = list_assets(current_project["id"], None, 10000)

    total_cost = sum(float(u.get("estimated_cost") or 0) for u in usage)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Assets", len(assets_all))
    c2.metric("Jobs", len(jobs_all))
    c3.metric("Done jobs", len([j for j in jobs_all if j["status"] == "done"]))
    c4.metric("Est. cost", f"${total_cost:,.4f}")

    st.markdown("### Usage log")
    if usage:
        st.dataframe(usage, use_container_width=True)
    else:
        st.info("Chưa có usage log.")

    st.markdown("### Thống kê job")
    if jobs_all:
        status_counts = {}
        for j in jobs_all:
            status_counts[j["status"]] = status_counts.get(j["status"], 0) + 1
        st.json(status_counts)

    st.markdown("### Log lỗi API gần đây")
    logs = read_api_error_logs(20)
    if logs:
        st.dataframe(logs, use_container_width=True)
    else:
        st.info("Chưa có log lỗi.")

    st.markdown("### Backup gần đây")
    backups = list_backups(current_project)
    if backups:
        for b in backups[:5]:
            st.write(f"{b.name} · {datetime.fromtimestamp(b.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
            download_file(str(b), f"⬇️ {b.name}")
    else:
        st.info("Chưa có backup.")

    st.markdown("### Xuất manifest")
    manifest = save_project_manifest(current_project["id"])
    download_file(str(manifest), "⬇️ Tải project_manifest.json")


st.divider()
st.caption("Local-first personal app. Hãy kiểm tra bản quyền, quyền riêng tư và điều khoản dịch vụ API trước khi dùng nội dung đầu vào/đầu ra.")
