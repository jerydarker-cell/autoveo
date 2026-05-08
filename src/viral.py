from __future__ import annotations
from datetime import datetime
import json, zipfile
from pathlib import Path

NICHES = {
    "AI/marketing/kinh doanh": {
        "audience": "creator, marketer, chủ shop, freelancer",
        "pain": "thiếu ý tưởng, làm nhiều nhưng không có kết quả, sợ tụt lại vì AI",
        "promise": "workflow đơn giản để tạo content nhanh và có chiến lược",
        "visual_style": "studio hiện đại, tone xanh đen, hologram, laptop, dashboard, faceless B-roll",
    },
    "Tài chính cá nhân": {
        "audience": "người mới đi làm, người muốn quản lý tiền",
        "pain": "mất tiền vì tiêu sai, đầu tư theo cảm xúc, thiếu kế hoạch",
        "promise": "hiểu tiền bạc dễ hơn và tránh lỗi phổ biến",
        "visual_style": "chart tài chính, ví tiền, thành phố, navy/yellow, clean infographic",
    },
    "Lịch sử": {
        "audience": "người thích chuyện thật, bí mật lịch sử, bài học quyền lực",
        "pain": "muốn hiểu sự kiện lớn nhưng không thích nội dung dài khô",
        "promise": "biến lịch sử thành câu chuyện điện ảnh dễ nhớ",
        "visual_style": "historical reenactment, bản đồ cổ, dramatic lighting, cinematic texture",
    },
    "News": {
        "audience": "người bận rộn muốn hiểu nhanh sự kiện",
        "pain": "quá nhiều thông tin, không biết điểm chính",
        "promise": "tóm tắt ngắn, trung lập, dễ hiểu, có bối cảnh",
        "visual_style": "newsroom hiện đại, city B-roll, abstract graphics, documentary style",
    },
    "AFF sản phẩm số": {
        "audience": "người làm online, creator, freelancer",
        "pain": "mất thời gian, tool rời rạc, không biết chọn gì",
        "promise": "review/workflow giúp tiết kiệm thời gian và tăng hiệu suất",
        "visual_style": "dashboard mockup, laptop, workspace creator, clean UI",
    },
    "AFF sản phẩm vật lý": {
        "audience": "người mua hàng thông minh, thích review nhanh",
        "pain": "không biết sản phẩm có đáng tiền không",
        "promise": "review tự nhiên theo vấn đề-lợi ích-kết quả",
        "visual_style": "product close-up, lifestyle usage, macro detail, commercial lighting",
    },
}

FORMATS = ["kể chuyện", "danh sách", "hướng dẫn", "case study", "so sánh trước-sau", "myth busting", "review", "giải thích đơn giản"]

def make_ideas(topic: str, platform: str, niche: str, faceless: bool = True) -> list[dict]:
    pack = NICHES[niche]
    topic = topic.strip() or "AI content"
    hooks = [
        "Đừng làm điều này nếu bạn mới bắt đầu.",
        "99% người mới bỏ qua điểm này.",
        "Một lỗi nhỏ có thể khiến bạn mất rất nhiều thời gian.",
        "Nếu chỉ có 30 giây, hãy nhớ điều này.",
        "Đây là phần người ta thường không nói với bạn.",
        "Trước khi bạn thử, hãy xem ví dụ này.",
        "Điều này nghe đơn giản nhưng cực kỳ dễ sai.",
        "Tôi sẽ giải thích bằng một ví dụ rất dễ hiểu.",
        "Nếu muốn kết quả nhanh hơn, bắt đầu từ đây.",
        "Một thay đổi nhỏ tạo khác biệt rất lớn.",
    ]
    titles = [
        f"Đừng mắc lỗi này khi làm {topic}",
        f"3 sự thật về {topic} mà người mới thường bỏ qua",
        f"Cách hiểu {topic} trong 60 giây",
        f"{topic}: ví dụ đơn giản khiến bạn nhớ ngay",
        f"Trước khi bắt đầu {topic}, hãy xem điều này",
        f"Vì sao nhiều người làm {topic} nhưng không có kết quả",
        f"Một framework ngắn để làm {topic} tốt hơn",
        f"So sánh cách cũ và cách mới khi làm {topic}",
        f"Bài học đắt giá từ {topic}",
        f"Nếu bắt đầu lại với {topic}, tôi sẽ làm 3 việc này",
    ]
    ideas = []
    for i in range(10):
        ideas.append({
            "id": i + 1,
            "title": titles[i],
            "psychological_insight": f"Người xem quan tâm vì họ đang {pack['pain']} và muốn {pack['promise']}.",
            "first_3s_hook": hooks[i],
            "content_format": FORMATS[i % len(FORMATS)] + (" / faceless B-roll" if faceless else " / AI host"),
            "retention_reason": "Hook gây tò mò, đoạn ngắn, thay đổi hình ảnh liên tục, có ví dụ thực tế và loop ending.",
            "thumbnail_idea": f"Chữ nổi: “ĐỪNG LÀM SAI”, “3 ĐIỀU CẦN BIẾT”; visual: {pack['visual_style']}.",
            "faceless": faceless,
            "platform": platform,
            "niche": niche,
        })
    return score_ideas(ideas)

def score_idea(idea: dict) -> dict:
    title = idea.get("title", "")
    hook = idea.get("first_3s_hook", "")
    fmt = idea.get("content_format", "")
    faceless = bool(idea.get("faceless", False))
    insight = idea.get("psychological_insight", "")
    retention = idea.get("retention_reason", "")
    thumb = idea.get("thumbnail_idea", "")
    hook_score = 50 + min(30, len(hook) * .9) + (12 if any(x in hook.lower() for x in ["đừng","sai","lỗi","99","bỏ qua"]) else 0)
    retention_score = 45 + min(35, len(retention) * .35) + (12 if any(x in retention.lower() for x in ["ví dụ","loop","tò mò","ngắt"]) else 0)
    faceless_score = 92 if faceless or "faceless" in fmt.lower() else 58
    difficulty = 38 - (10 if any(x in fmt.lower() for x in ["faceless","danh sách","hướng dẫn"]) else 0) + (12 if "lịch sử" in title.lower() else 0)
    difficulty = max(10, min(100, difficulty))
    thumbnail_score = 45 + min(35, len(thumb) * .25) + (10 if any(x in thumb.lower() for x in ["đừng","3","sai"]) else 0)
    insight_score = 45 + min(40, len(insight) * .25) + (10 if any(x in insight.lower() for x in ["sợ","muốn","pain","quan tâm"]) else 0)
    viral = hook_score*.28 + retention_score*.24 + faceless_score*.14 + thumbnail_score*.14 + insight_score*.16 + (100-difficulty)*.04
    return {
        "hook_score": round(min(100, hook_score), 1),
        "retention_score": round(min(100, retention_score), 1),
        "faceless_ease_score": round(min(100, faceless_score), 1),
        "production_difficulty": round(difficulty, 1),
        "thumbnail_score": round(min(100, thumbnail_score), 1),
        "insight_score": round(min(100, insight_score), 1),
        "viral_potential": round(min(100, viral), 1),
    }

def score_ideas(ideas: list[dict]) -> list[dict]:
    out = []
    for idea in ideas:
        item = dict(idea)
        item.update(score_idea(item))
        out.append(item)
    return sorted(out, key=lambda x: x["viral_potential"], reverse=True)

def make_script(topic: str, idea: dict, minutes: int = 3) -> dict:
    title = idea.get("title", topic)
    hook = idea.get("first_3s_hook", "Đây là điều bạn cần biết.")
    beats = [
        {"time": "0:00-0:05", "type": "HOOK", "text": f"{hook} Nếu hiểu sai điểm này, toàn bộ chiến lược về {topic} có thể đi lệch."},
        {"time": "0:05-0:25", "type": "VẤN ĐỀ", "text": f"Hầu hết mọi người tiếp cận {topic} bằng cảm tính: thấy ai đó làm được, rồi bắt chước phần bề nổi."},
        {"time": "0:25-0:50", "type": "VÍ DỤ", "text": f"Hai người cùng làm {topic}: một người copy công thức, một người hiểu insight và pain point của người xem."},
        {"time": "0:50-1:15", "type": "NGẮT NHỊP", "text": "Điểm ngắt nhịp: thứ tạo ra kết quả thường không phải công cụ, mà là cách bạn đặt vấn đề."},
        {"time": "1:15-1:50", "type": "GIẢI PHÁP", "text": "Bước một: viết rõ người xem là ai, họ đang đau ở đâu, và họ cần câu trả lời nào nhanh nhất."},
        {"time": "1:50-2:20", "type": "GIẢI PHÁP", "text": "Bước hai: chia nội dung thành đoạn ngắn. Mỗi 20-30 giây phải có hình ảnh mới, câu hỏi mới hoặc ví dụ mới."},
        {"time": "2:20-2:45", "type": "CTA", "text": "Nếu bạn muốn, hãy lưu video này lại. Cấu trúc này có thể dùng lại cho rất nhiều nội dung."},
        {"time": "2:45-3:10", "type": "LOOP ENDING", "text": f"Và quay lại câu đầu tiên: đừng làm {topic} nếu chưa biết người xem thật sự đang quan tâm điều gì."},
    ]
    return {"title": title, "beats": beats, "voiceover": "\n".join(b["text"] for b in beats), "loop_ending": beats[-1]["text"]}

def make_shots(script: dict, visual_style: str, host: str, faceless: bool) -> list[dict]:
    shots = []
    motions = ["fast push-in", "slow dolly", "macro close-up", "side tracking", "top-down insert", "wide establishing"]
    transitions = ["whip pan", "match cut", "zoom cut", "glitch light", "soft fade", "speed ramp"]
    for idx, beat in enumerate(script["beats"], 1):
        broll = "abstract B-roll, kinetic text, icons, UI mockups, hands typing, charts" if faceless else f"AI host: {host}"
        shots.append({
            "scene": idx,
            "time": beat["time"],
            "beat_type": beat["type"],
            "voiceover": beat["text"],
            "camera_motion": motions[idx % len(motions)],
            "transition": transitions[idx % len(transitions)],
            "text_overlay": beat["type"] + " · " + beat["text"][:52],
            "broll_or_host": broll,
            "flow_prompt": f"{beat['text']}\nVisual: {visual_style}. {broll}. Camera: cinematic {motions[idx % len(motions)]}. Lighting: premium short-form style. No watermark, no unreadable text.",
        })
    return shots

def make_optimization(script: dict, topic: str) -> dict:
    return {
        "hook_score_notes": "Hook có cảnh báo/lợi ích rõ. Có thể test thêm con số, lỗi cụ thể hoặc kết quả đối lập.",
        "drop_risk_segments": ["Đoạn giải thích dài sau 0:25 cần B-roll thay đổi nhanh.", "Đoạn giải pháp nên có ví dụ minh họa.", "CTA không nên quá dài."],
        "cta_timing": "Sau khi đưa ra framework, trước loop ending.",
        "top_3_titles": [f"Đừng làm {topic} nếu chưa biết điều này", f"3 lỗi khiến {topic} không có kết quả", f"Cách làm {topic} dễ hiểu hơn trong 3 phút"],
        "seo_descriptions": [f"Giải thích {topic} theo cấu trúc dễ hiểu, có ví dụ thực tế.", f"Những insight quan trọng giúp tránh sai lầm khi làm {topic}."],
        "hashtags": ["#AIVideo", "#ContentStrategy", "#Shorts", "#Reels", "#Marketing", "#KinhDoanh", "#AI", "#ViralContent", "#CreatorTools", "#VideoMarketing"],
        "ab_hooks": [f"Đừng bắt đầu {topic} nếu chưa trả lời câu này.", f"Đây là lý do 90% người làm {topic} bị kẹt.", f"Một thay đổi nhỏ làm {topic} dễ hơn rất nhiều."],
        "thumbnail_texts": ["ĐỪNG LÀM SAI", "3 LỖI PHỔ BIẾN", "CÁCH LÀM ĐÚNG"],
    }

def make_blueprint(topic: str, platform: str, niche: str, faceless: bool, host: str, minutes: int) -> dict:
    ideas = make_ideas(topic, platform, niche, faceless)
    selected = ideas[0]
    script = make_script(topic, selected, minutes)
    shots = make_shots(script, NICHES[niche]["visual_style"], host, faceless)
    return {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "topic": topic,
        "platform": platform,
        "niche": niche,
        "ideas": ideas,
        "selected_idea": selected,
        "script": script,
        "shots": shots,
        "optimization": make_optimization(script, topic),
    }

def export_blueprint_zip(project_dir: Path, blueprint: dict) -> str:
    out_dir = project_dir / "exports" / f"viral_blueprint_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "viral_blueprint.json").write_text(json.dumps(blueprint, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "script_voiceover.txt").write_text(blueprint["script"]["voiceover"], encoding="utf-8")
    (out_dir / "flow_prompts.txt").write_text("\n\n---\n\n".join(s["flow_prompt"] for s in blueprint["shots"]), encoding="utf-8")
    (out_dir / "titles_hashtags.json").write_text(json.dumps(blueprint["optimization"], ensure_ascii=False, indent=2), encoding="utf-8")
    zip_path = project_dir / "exports" / f"viral_blueprint_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for p in out_dir.rglob("*"):
            z.write(p, arcname=p.relative_to(out_dir))
    return str(zip_path)
