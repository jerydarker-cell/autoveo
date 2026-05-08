from __future__ import annotations

import json
import os
from pathlib import Path

import streamlit as st

from src.project import (
    ensure_project, list_projects, export_zip, backup_project, storage_report,
    read_errors, log_error, save_json, now
)
from src.viral import (
    NICHES, FORMATS, make_blueprint, export_blueprint_zip
)
from src.flow import (
    inbox_dir, scan_inbox, save_uploads, merge_clips, missing_scenes,
    normalize_names, write_prompt_txt
)
from src.media import (
    concat_videos, make_srt, thumbnail_from_video, mix_audio_subtitles,
    publish_package, ffmpeg_path
)
from src.tts import VOICE_PRESETS, tts_edge
from src.thumbnails import TEMPLATES, make_thumbnail


APP_VERSION = "2.0.0 Clean UX"
FLOW_URL = "https://labs.google/fx/tools/flow"

st.set_page_config(page_title="AUTO VEO Studio v2.0", page_icon="🎬", layout="wide")

CSS = """
<style>
.block-container { padding-top: .85rem; max-width: 1320px; }
.hero {
  padding: 22px 26px; border-radius: 26px;
  background: radial-gradient(circle at 12% 18%, rgba(0,220,255,.20), transparent 32%),
              radial-gradient(circle at 88% 8%, rgba(255,190,0,.16), transparent 34%),
              linear-gradient(135deg, rgba(90,80,255,.18), rgba(255,255,255,.035));
  border: 1px solid rgba(255,255,255,.14);
  margin-bottom: 18px;
}
.hero h1 { margin: 0; font-size: 2rem; letter-spacing: -.03em; }
.hero p { margin: .4rem 0 0; opacity: .85; }
.badge {
  display:inline-block; padding:6px 11px; border-radius:999px;
  background:rgba(255,255,255,.07); border:1px solid rgba(255,255,255,.14);
  margin:5px 6px 0 0; font-size:.86rem;
}
.card {
  padding: 16px; border-radius: 18px; background: rgba(255,255,255,.055);
  border: 1px solid rgba(255,255,255,.12);
}
.small { opacity: .72; font-size: .88rem; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# -----------------------------
# Session defaults
# -----------------------------
DEFAULTS = {
    "viral_blueprint": None,
    "flow_rows": [],
    "flow_clips": [],
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v.copy() if isinstance(v, list) else v


# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:
    st.markdown("## 🎬 AUTO VEO Studio")
    st.caption(APP_VERSION)

    compact = st.checkbox("Giao diện gọn", value=True)
    ui_mode = st.radio("Chế độ", ["Simple", "Advanced"], horizontal=True, index=0)

    st.divider()
    st.markdown("### 📁 Project")
    projects = list_projects()
    selected = st.selectbox("Chọn project", projects, index=0)
    new_project = st.text_input("Tạo/chọn tên project mới", value="")
    if st.button("➕ Tạo/mở project", use_container_width=True):
        if new_project.strip():
            selected = new_project.strip()
            ensure_project(selected)
            st.success("Đã tạo/mở project.")
            st.rerun()

    project_name = selected
    pdir = ensure_project(project_name)
    st.caption(f"Folder: `{pdir.name}`")

    st.divider()
    st.markdown("### ⚙️ Runtime")
    mock_mode = st.checkbox("Mock/TTS fallback mode", value=False)
    st.caption(f"FFmpeg: {'OK' if ffmpeg_path() else 'Chưa thấy'}")
    if not ffmpeg_path():
        st.warning("Cần FFmpeg để nối video/ghép subtitle/audio.")
        st.code("Windows: winget install Gyan.FFmpeg\nMac: brew install ffmpeg")

    st.divider()
    st.markdown("### 🎨 Thumbnail default")
    default_thumb_template = st.selectbox("Template thumbnail", list(TEMPLATES.keys()), index=0)


# -----------------------------
# Header
# -----------------------------
st.markdown(
    f"""
<div class="hero">
  <h1>🎬 AUTO VEO Studio v2.0 — Clean UX</h1>
  <p>Viral Director · Flow Assisted · Flow Inbox · Smart Scoring · Thumbnail Templates · Publish Package</p>
  <span class="badge">📁 {project_name}</span>
  <span class="badge">🎯 viral score</span>
  <span class="badge">⚡ flow inbox</span>
  <span class="badge">🖼️ thumbnail templates</span>
  <span class="badge">🧩 code split into src/</span>
</div>
""",
    unsafe_allow_html=True,
)


# -----------------------------
# Tabs
# -----------------------------
SIMPLE_TABS = ["🎯 Viral Director", "🌊 Flow Assisted", "🏠 Project", "📊 Dashboard"]
ADVANCED_TABS = SIMPLE_TABS + ["🖼️ Thumbnail Lab", "🧾 Logs", "🚀 Deploy"]
tabs_names = SIMPLE_TABS if ui_mode == "Simple" else ADVANCED_TABS
tabs = st.tabs(tabs_names)

def has_tab(name: str) -> bool:
    return name in tabs_names

def tab(name: str):
    return tabs[tabs_names.index(name)]


# -----------------------------
# Viral Director
# -----------------------------
with tab("🎯 Viral Director"):
    st.markdown("## 🎯 Viral Content Director")
    st.caption("Tạo blueprint viral theo 6 bước: idea → script → cảnh quay → voice direction → timeline → gói tối ưu.")

    c1, c2 = st.columns([1.05, .95])
    with c1:
        topic = st.text_area("Chủ đề/kênh/ngách muốn làm video", height=120, value="AI/marketing/kinh doanh cho Shorts/Reels")
        platform = st.selectbox("Nền tảng", ["TikTok/Reels 9:16", "YouTube Shorts 9:16", "YouTube ngang 16:9", "Facebook Reels"])
        niche = st.selectbox("Ngách viral", list(NICHES.keys()))
        faceless = st.checkbox("Ưu tiên faceless", value=True)
    with c2:
        host = st.text_area(
            "AI host cố định nếu cần",
            value="Nam 28 tuổi, smart casual, background studio hiện đại, tone xanh đen, nói nhanh – rõ – chuyên gia.",
            height=90,
        )
        structure = st.text_input("Cấu trúc video", value="hook 3 giây → vấn đề → ví dụ thực tế → giải pháp → CTA → loop ending")
        minutes = st.selectbox("Độ dài blueprint", [3, 4, 5], index=0)
        st.info("v2.0 đã thêm chấm điểm: Hook, Retention, Faceless Ease, Production Difficulty, Thumbnail, Insight, Viral Potential.")

    if st.button("🚀 Tạo Viral Blueprint", type="primary", use_container_width=True):
        blueprint = make_blueprint(topic, platform, niche, faceless, host, minutes)
        blueprint["fixed_structure"] = structure
        st.session_state.viral_blueprint = blueprint
        zip_path = export_blueprint_zip(pdir, blueprint)
        st.success("Đã tạo Viral Blueprint.")
        st.download_button("📦 Tải Viral Blueprint ZIP", Path(zip_path).read_bytes(), Path(zip_path).name, use_container_width=True)

    bp = st.session_state.get("viral_blueprint")
    if bp:
        st.divider()
        st.markdown("### Bước 1 — 10 ý tưởng viral đã chấm điểm")
        ideas = bp["ideas"]
        st.dataframe(
            ideas,
            use_container_width=True,
            column_order=[
                "id", "viral_potential", "hook_score", "retention_score", "faceless_ease_score",
                "production_difficulty", "thumbnail_score", "insight_score",
                "title", "first_3s_hook", "content_format"
            ],
        )

        top = ideas[0]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Viral Potential", top["viral_potential"])
        c2.metric("Hook", top["hook_score"])
        c3.metric("Retention", top["retention_score"])
        c4.metric("Difficulty", top["production_difficulty"])

        st.markdown("### Bước 2 — Kịch bản giữ chân")
        st.text_input("Tiêu đề", value=bp["script"]["title"])
        st.text_area("Voiceover", value=bp["script"]["voiceover"], height=220)
        st.caption("Loop ending: " + bp["script"]["loop_ending"])

        st.markdown("### Bước 3 — Cảnh quay chi tiết + Prompt Flow/Veo")
        st.dataframe(bp["shots"], use_container_width=True)
        with st.expander("Copy prompt từng cảnh", expanded=False):
            for shot in bp["shots"]:
                st.markdown(f"#### Scene {shot['scene']} · {shot['beat_type']}")
                st.text_area("Prompt", value=shot["flow_prompt"], height=120, key=f"flow_prompt_{shot['scene']}")
                st.code(shot["flow_prompt"])
            if st.button("➡️ Gửi prompt sang Flow Assisted", use_container_width=True):
                st.session_state.flow_rows = [
                    {
                        "scene": s["scene"],
                        "status": "Chưa làm",
                        "narration": s["voiceover"],
                        "prompt": s["flow_prompt"],
                        "note": "",
                    }
                    for s in bp["shots"]
                ]
                st.success("Đã gửi prompt sang Flow Assisted.")

        st.markdown("### Bước 4 — Voice Direction")
        voice_direction = "\n".join([f"[{s['beat_type']}] {s['voiceover']}" for s in bp["shots"]])
        st.text_area("Voice direction", value=voice_direction, height=180)

        st.markdown("### Bước 5 — Timeline dựng")
        timeline = [
            {
                "time": s["time"],
                "scene": s["scene"],
                "visual": s["broll_or_host"],
                "transition": s["transition"],
                "subtitle": "burned captions, 1 short phrase per line",
                "export": "9:16 1080x1920" if "9:16" in bp["platform"] else "16:9 1920x1080",
            }
            for s in bp["shots"]
        ]
        st.dataframe(timeline, use_container_width=True)

        st.markdown("### Bước 6 — Gói tối ưu viral")
        st.json(bp["optimization"])

        c1, c2 = st.columns(2)
        with c1:
            if st.button("📅 Tạo lịch 30 ngày", use_container_width=True):
                patterns = ["gây tò mò", "đào sâu", "case study", "CTA", "myth busting", "hướng dẫn", "review", "so sánh"]
                plan = [{"day": i, "series_role": patterns[(i-1)%len(patterns)], "topic": f"{bp['topic']} — góc nhìn {i}", "format": FORMATS[(i-1)%len(FORMATS)]} for i in range(1,31)]
                st.dataframe(plan, use_container_width=True)
        with c2:
            if st.button("🧬 Tạo 10 biến thể", use_container_width=True):
                variants = [{"version": i, "hook": bp["selected_idea"]["first_3s_hook"], "new_angle": ["pain point", "ví dụ", "đối tượng", "case study", "danh sách"][i%5], "cta": "Follow/comment nếu muốn template."} for i in range(1,11)]
                st.dataframe(variants, use_container_width=True)


# -----------------------------
# Flow Assisted
# -----------------------------
with tab("🌊 Flow Assisted"):
    st.markdown("## 🌊 Flow Assisted Mode + Flow Inbox")
    st.caption("Dùng credit Google Flow nhanh nhất: copy prompt → render Flow → tải clip → upload/quét inbox → build final.")

    rows = st.session_state.get("flow_rows", [])
    c1, c2 = st.columns([1.05, .95])
    with c1:
        if not rows:
            st.info("Chưa có prompt. Hãy tạo blueprint ở Viral Director rồi bấm “Gửi prompt sang Flow Assisted”, hoặc nhập nhanh bên dưới.")
        quick_topic = st.text_area("Tạo prompt nhanh nếu chưa có", height=90, placeholder="Nhập brief ngắn...")
    with c2:
        expected = st.number_input("Số scene dự kiến", min_value=1, max_value=50, value=max(1, len(rows) or 5))
        voice_label = st.selectbox("Voice hậu kỳ", list(VOICE_PRESETS.keys()))
        burn_sub = st.checkbox("Burn subtitle vào final", value=True)
        add_fade = st.checkbox("Nối có fade nhẹ", value=True)
        thumb_template = st.selectbox("Thumbnail template", list(TEMPLATES.keys()), index=list(TEMPLATES.keys()).index(default_thumb_template))
        st.link_button("🌊 Mở Google Flow", FLOW_URL, use_container_width=True)

    if st.button("🧠 Tạo prompt nhanh 5 cảnh", use_container_width=True):
        if quick_topic.strip():
            st.session_state.flow_rows = [
                {"scene": i, "status": "Chưa làm", "narration": f"Cảnh {i}: {quick_topic}", "prompt": f"{quick_topic}. Scene {i}. Cinematic short-form video, clear subject, smooth motion, no watermark.", "note": ""}
                for i in range(1, 6)
            ]
            st.rerun()

    rows = st.session_state.get("flow_rows", [])
    if rows:
        st.markdown("### 1) Checklist + prompt")
        edited = st.data_editor(
            rows,
            num_rows="dynamic",
            use_container_width=True,
            key="flow_rows_editor_clean",
            column_config={
                "scene": st.column_config.NumberColumn("Scene", min_value=1),
                "status": st.column_config.SelectboxColumn("Trạng thái", options=["Chưa làm", "Đã copy prompt", "Đang render Flow", "Đã tải video", "Lỗi cần làm lại", "Hoàn tất"]),
                "narration": st.column_config.TextColumn("Narration"),
                "prompt": st.column_config.TextColumn("Prompt dán vào Flow"),
                "note": st.column_config.TextColumn("Ghi chú"),
            }
        )
        st.session_state.flow_rows = edited

        with st.expander("Copy prompt từng scene", expanded=False):
            for r in edited:
                st.markdown(f"#### Scene {r.get('scene')}")
                st.text_area("Prompt", value=r.get("prompt", ""), height=110, key=f"copy_scene_{r.get('scene')}")
                st.code(r.get("prompt", ""))

        prompt_txt = write_prompt_txt(pdir, edited)
        st.download_button("⬇️ Tải toàn bộ prompt TXT", Path(prompt_txt).read_bytes(), Path(prompt_txt).name, use_container_width=True)

    st.markdown("### 2) Upload hàng loạt hoặc quét Flow Inbox")
    inbox = inbox_dir(pdir)
    st.code(str(inbox), language="text")

    c1, c2, c3 = st.columns(3)
    with c1:
        uploaded = st.file_uploader("Upload nhiều clip Flow", type=["mp4", "mov", "m4v", "webm"], accept_multiple_files=True)
        if uploaded and st.button("💾 Lưu + auto map upload", use_container_width=True):
            saved = save_uploads(pdir, uploaded)
            st.session_state.flow_clips = merge_clips(st.session_state.get("flow_clips", []), saved)
            st.success(f"Đã lưu {len(saved)} clip.")
    with c2:
        if st.button("🔍 Quét flow_inbox", use_container_width=True):
            scanned = scan_inbox(pdir)
            st.session_state.flow_clips = merge_clips(st.session_state.get("flow_clips", []), scanned)
            st.success(f"Đã quét {len(scanned)} clip.")
    with c3:
        if st.button("🏷️ Chuẩn hóa tên scene_XX", use_container_width=True):
            normalized = normalize_names(st.session_state.get("flow_clips", []), pdir)
            st.session_state.flow_clips = normalized
            st.success("Đã chuẩn hóa tên clip vào flow_inbox.")

    clips = merge_clips(scan_inbox(pdir), st.session_state.get("flow_clips", []))
    miss = missing_scenes(clips, int(expected))
    if clips:
        st.dataframe(clips, use_container_width=True)
    if miss:
        st.warning("Còn thiếu scene: " + ", ".join(map(str, miss)))
    else:
        st.success("Đủ scene theo số lượng dự kiến.")

    st.markdown("### 3) Build Final")
    output_name = st.text_input("Tên final", value="flow_final.mp4")
    vertical = st.checkbox("Thumbnail dọc 9:16", value=True)
    title_text = st.text_input("Text thumbnail/title", value=(rows[0]["narration"][:60] if rows else "Flow Assisted Video"))

    if st.button("⚡ Build Final từ clip đã map", type="primary", use_container_width=True):
        try:
            clips = merge_clips(scan_inbox(pdir), st.session_state.get("flow_clips", []))
            clip_paths = [c["path"] for c in clips if Path(c["path"]).exists()]
            if not clip_paths:
                st.error("Chưa có clip hợp lệ.")
            else:
                raw = concat_videos(pdir, clip_paths, output_name, add_fade)
                narrations = [r.get("narration", "") for r in rows] if rows else [title_text]
                voice_text = " ".join(narrations)
                voice = tts_edge(pdir, voice_text, voice_label, mock=False)
                srt = make_srt(pdir, narrations, 4)
                final = mix_audio_subtitles(pdir, raw, voice, srt, burn_sub)
                base_thumb = thumbnail_from_video(pdir, final)
                thumb = make_thumbnail(pdir, base_thumb, title_text, thumb_template, vertical)
                metadata = {
                    "title": title_text,
                    "caption": voice_text[:400],
                    "hashtags": "#AIVideo #Veo #Shorts #Reels #ViralContent",
                    "clips": clips,
                    "created_at": now(),
                    "template": thumb_template,
                }
                package = publish_package(pdir, final, thumb, srt, voice, metadata)
                st.success("Đã build xong final video.")
                st.video(final)
                st.download_button("⬇️ Tải final video", Path(final).read_bytes(), Path(final).name, use_container_width=True)
                st.image(thumb, caption="Thumbnail", use_container_width=True)
                st.download_button("⬇️ Tải thumbnail", Path(thumb).read_bytes(), Path(thumb).name, use_container_width=True)
                st.download_button("📦 Tải publish package", Path(package).read_bytes(), Path(package).name, use_container_width=True)
        except Exception as e:
            log_error("build_flow_final", e, {"project": project_name})
            st.exception(e)


# -----------------------------
# Project
# -----------------------------
with tab("🏠 Project"):
    st.markdown("## 🏠 Project")
    report = storage_report(project_name)
    c1, c2 = st.columns(2)
    c1.metric("Project size", f"{report['total_mb']} MB")
    c2.metric("Files", report["files"])

    c1, c2 = st.columns(2)
    with c1:
        if st.button("📦 Export ZIP project", type="primary", use_container_width=True):
            z = export_zip(project_name)
            st.download_button("⬇️ Tải ZIP", Path(z).read_bytes(), Path(z).name, use_container_width=True)
    with c2:
        if st.button("🛡️ Backup project", use_container_width=True):
            z = backup_project(project_name)
            st.download_button("⬇️ Tải backup", Path(z).read_bytes(), Path(z).name, use_container_width=True)

    with st.expander("File lớn nhất", expanded=False):
        st.json(report["largest"])


# -----------------------------
# Dashboard
# -----------------------------
with tab("📊 Dashboard"):
    st.markdown("## 📊 Dashboard")
    st.json(storage_report(project_name))
    errors = read_errors(50)
    st.markdown("### Logs")
    if errors:
        st.dataframe(errors, use_container_width=True)
    else:
        st.info("Chưa có log lỗi.")


# -----------------------------
# Advanced tabs
# -----------------------------
if has_tab("🖼️ Thumbnail Lab"):
    with tab("🖼️ Thumbnail Lab"):
        st.markdown("## 🖼️ Thumbnail Lab")
        upload = st.file_uploader("Ảnh nền hoặc thumbnail base", type=["png", "jpg", "jpeg", "webp"])
        text = st.text_input("Text thumbnail", value="ĐỪNG LÀM SAI")
        template = st.selectbox("Template", list(TEMPLATES.keys()))
        vertical = st.checkbox("Dọc 9:16", value=True, key="thumb_lab_vertical")
        if st.button("Tạo thumbnail", type="primary"):
            base_path = None
            if upload:
                base_path = str(pdir / "frames" / upload.name)
                Path(base_path).parent.mkdir(parents=True, exist_ok=True)
                upload.seek(0); Path(base_path).write_bytes(upload.read()); upload.seek(0)
            thumb = make_thumbnail(pdir, base_path, text, template, vertical)
            st.image(thumb, use_container_width=True)
            st.download_button("⬇️ Tải thumbnail", Path(thumb).read_bytes(), Path(thumb).name)

if has_tab("🧾 Logs"):
    with tab("🧾 Logs"):
        st.markdown("## 🧾 Logs")
        st.dataframe(read_errors(200), use_container_width=True)

if has_tab("🚀 Deploy"):
    with tab("🚀 Deploy"):
        st.markdown("## 🚀 Deploy checklist")
        checks = {
            "app.py": Path("app.py").exists(),
            "requirements.txt": Path("requirements.txt").exists(),
            "packages.txt": Path("packages.txt").exists(),
            ".streamlit/config.toml": Path(".streamlit/config.toml").exists(),
            ".gitignore": Path(".gitignore").exists(),
        }
        st.json(checks)
        st.code("""git init
git add .
git commit -m "AUTO VEO Studio v2.0"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/auto-veo-studio.git
git push -u origin main""", language="bash")

st.caption("v2.0 Clean UX: tập trung vào viral blueprint + Flow Assisted + inbox + thumbnail + publish package. Các tab API nặng đã được lược bỏ khỏi bản clean để chạy mượt hơn.")
