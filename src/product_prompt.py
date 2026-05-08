from __future__ import annotations
from pathlib import Path
from datetime import datetime
import json, zipfile, re

PRODUCT_MOODS = {
    "Năng động": {
        "music": "fast energetic modern beat, strong rhythm, exciting transitions, clean product reveal SFX",
        "emotion": "hứng khởi, nhanh, mạnh, tạo cảm giác muốn thử ngay",
        "camera": "fast push-in, smooth orbit, macro close-up, quick handheld realism",
        "voice_style": "nói nhanh, rõ, năng lượng cao, cuốn hút",
    },
    "Hài hước": {
        "music": "playful upbeat music, light comedic sound effects, pop accents, cheerful rhythm",
        "emotion": "vui nhộn, bất ngờ, tạo nụ cười nhưng vẫn giữ chất thương mại",
        "camera": "quick close-up, playful reaction shot, smooth product orbit, fun timing",
        "voice_style": "nói nhanh, dí dỏm, tự nhiên, có nhịp gây cười nhẹ",
    },
    "Truyền cảm hứng": {
        "music": "uplifting cinematic music, deep warm melody, elegant riser, premium tactile SFX",
        "emotion": "sâu lắng, tích cực, sang, truyền cảm hứng",
        "camera": "slow dolly, premium macro, elegant orbit arc, emotional hero framing",
        "voice_style": "nói nhanh vừa phải, truyền cảm, ấm, rõ và sang",
    },
}

PRODUCT_TYPES = [
    "mỹ phẩm / skincare",
    "đồ công nghệ",
    "đồ gia dụng",
    "thời trang / phụ kiện",
    "đồ ăn / đồ uống",
    "sản phẩm số / app / khóa học",
    "khác",
]

def product_lock_block(clean_text: bool = True) -> str:
    clean = "Remove or visually clean all readable text from the product surface to prevent text artifacts." if clean_text else "Keep the product surface clean and avoid generating readable text."
    return f"""PRODUCT LOCK:
Use the uploaded product image as the ONLY product reference.
Preserve the product exactly as the original reference image.
Keep the exact product shape, proportions, silhouette, color, material, finish, cap, outline, packaging form, and visual identity.
Do not redraw, redesign, stylize, simplify, replace, or invent new product details.
Do not change the product into another product.
{clean}
The final video must stay visually consistent with the uploaded product reference."""

def anti_text_block() -> str:
    return """ABSOLUTE ANTI-TEXT RULES:
No text overlay.
No subtitles.
No captions.
No UI text.
No labels in the environment.
No floating text.
No readable text on the product.
No typography in the background.
No text attached to speech, lips, hands, objects, walls, screens, packaging, or environment.
No signage.
No watermark.
No logos invented by the model."""

def concept_for_product(product_name: str, product_type: str, mood: str, target: str, objective: str) -> dict:
    mood_data = PRODUCT_MOODS[mood]
    product = product_name.strip() or "sản phẩm trong ảnh gốc"
    return {
        "concept_title": f"{product} — {mood} 8s Product Hero",
        "core_task": f"Tạo video quảng cáo 8 giây hiệu suất cao cho {product}, giữ giống tuyệt đối ảnh gốc, có người mẫu tương tác và thể hiện cách dùng.",
        "strategic_goal": objective or "Giữ chân người xem, tăng thời gian xem, tăng tương tác và khiến người xem muốn thử sản phẩm.",
        "target_audience": target or "người xem mạng xã hội thích nội dung nhanh, đẹp, thực tế và dễ tin.",
        "product_type": product_type,
        "emotion": mood_data["emotion"],
        "music_strategy": mood_data["music"],
        "camera_strategy": mood_data["camera"],
        "visual_strategy": "photorealistic, realistic commercial, cinematic angles, premium lighting, smooth product orbit, macro close-up, real human model using the product, 4K quality.",
        "no_text_policy": "Không có chữ overlay, không subtitle, không chữ trong môi trường, không chữ chạy, không chữ dính vào sản phẩm hoặc người mẫu.",
    }

def voiceovers(product_name: str, mood: str) -> list[str]:
    product = product_name.strip() or "sản phẩm này"
    if mood == "Năng động":
        return [
            f"Đây rồi, {product} đang rất đáng chú ý! Nhìn đẹp, dùng tiện, cảm giác rất cuốn. Chỉ vài giây thôi là muốn thử ngay!",
            f"Nếu bạn thích sự tiện lợi và đẹp mắt, {product} là thứ rất đáng xem. Cầm lên là thích, dùng vào là thấy khác ngay!",
            f"Một sản phẩm nhỏ nhưng tạo cảm giác rất đã. {product} nhìn sang, dùng nhanh, lên hình cuốn và cực kỳ dễ nhớ!"
        ]
    if mood == "Hài hước":
        return [
            f"Ban đầu chỉ định nhìn thử {product} thôi… ai ngờ cuốn thật! Cầm lên là thích, dùng vào thấy tiện ngay!",
            f"Tưởng bình thường mà không hề bình thường! {product} nhìn vui mắt, dùng lại tiện, đúng kiểu thử một lần là nhớ.",
            f"Đây là khoảnh khắc bạn nhận ra: à, {product} đúng là thứ mình nên có sớm hơn một chút!"
        ]
    return [
        f"Một sản phẩm đẹp không chỉ để nhìn, mà còn để cảm nhận mỗi ngày. {product} tinh tế, tiện dụng và đầy cuốn hút.",
        f"Có những thứ khiến trải nghiệm hằng ngày trở nên tốt hơn. {product} mang lại cảm giác chỉn chu, chân thực và rất đáng nhớ.",
        f"Khi thiết kế, cảm giác và sự tiện dụng gặp nhau, {product} trở thành điểm nhấn nhỏ nhưng rất khác biệt."
    ]

def shot_list_8s(mood: str) -> list[dict]:
    if mood == "Hài hước":
        return [
            {"time": "0-2s", "shot": "playful hook", "description": "model notices product with a surprised delighted reaction, quick close-up, comedic timing"},
            {"time": "2-4s", "shot": "beauty orbit", "description": "smooth orbit around product, premium reflections, realistic texture"},
            {"time": "4-6s", "shot": "usage demo", "description": "model naturally tries/uses product, friendly expression, realistic hand movement"},
            {"time": "6-8s", "shot": "hero finish", "description": "model happily presents product to camera, playful confident ending"},
        ]
    if mood == "Truyền cảm hứng":
        return [
            {"time": "0-2s", "shot": "elegant reveal", "description": "soft dramatic light, slow push-in, emotional premium reveal"},
            {"time": "2-4s", "shot": "macro detail", "description": "macro close-up, refined texture, realistic highlights"},
            {"time": "4-6s", "shot": "calm usage", "description": "model uses product naturally with calm confidence and warm lifestyle feeling"},
            {"time": "6-8s", "shot": "inspiring hero", "description": "product and model framed together, subtle camera arc, premium final moment"},
        ]
    return [
        {"time": "0-2s", "shot": "strong hook", "description": "dramatic hero reveal, fast push-in, glossy lighting, energetic mood"},
        {"time": "2-4s", "shot": "product orbit", "description": "smooth orbit around product, macro detail, premium reflections"},
        {"time": "4-6s", "shot": "usage demo", "description": "stylish model picks up and uses product confidently, realistic hand interaction"},
        {"time": "6-8s", "shot": "hero CTA feel", "description": "model presents product toward camera, camera circles slightly, strong finish"},
    ]

def build_product_prompts(product_name: str, product_type: str, mood: str, target: str, objective: str, use_model: bool = True, clean_text: bool = True, variants: int = 3) -> dict:
    concept = concept_for_product(product_name, product_type, mood, target, objective)
    mood_data = PRODUCT_MOODS[mood]
    shots = shot_list_8s(mood)
    vos = voiceovers(product_name, mood)
    product = product_name.strip() or "the uploaded product"
    prompts = []
    for i in range(max(1, variants)):
        vo = vos[i % len(vos)]
        interaction = "A real human model naturally interacts with and uses the product, showing a simple believable usage demonstration." if use_model else "Use realistic hands and lifestyle interaction without showing a full face."
        prompt = f"""Create an 8-second photorealistic cinematic product commercial using the uploaded product image as the ONLY product reference.

{product_lock_block(clean_text)}

CORE CONCEPT:
Product: {product}
Product category: {product_type}
Mood: {mood}
Goal: {concept['strategic_goal']}
Target audience: {concept['target_audience']}
Core task: {concept['core_task']}

VISUAL STRATEGY:
{concept['visual_strategy']}
{interaction}
Use cinematic product angles, full realistic sound design, smooth camera movement around the product, macro detail shots, premium lighting, realistic commercial style, 4K quality.
The product must remain identical to the uploaded image and must not be reinvented.
If the uploaded product contains text, clean it visually so the product has no readable text artifacts.

SHOT FLOW:
0-2s: {shots[0]['description']}.
2-4s: {shots[1]['description']}.
4-6s: {shots[2]['description']}.
6-8s: {shots[3]['description']}.

CAMERA:
{mood_data['camera']}. Smooth cinematic motion, natural depth of field, realistic lens behavior, premium commercial framing.

MUSIC AND SOUND:
Music mood: {mood_data['music']}.
Sound effects: clean product reveal SFX, subtle whoosh, tactile handling sounds, soft impact where appropriate.
The audio should support viewer retention and match the visual rhythm.

VOICEOVER — Vietnamese with diacritics, fast, attractive, complete within 8 seconds:
“{vo}”

{anti_text_block()}

FLOW SAFETY:
Keep the scene simple and focused on one product and one model interaction.
Avoid too many objects, avoid complicated backgrounds, avoid text generation, avoid busy typography, avoid logos, avoid signs.
Style must be realistic like a real commercial shot from the uploaded product reference."""
        prompts.append({
            "variant": i + 1,
            "mood": mood,
            "voiceover": vo,
            "prompt": prompt,
            "estimated_flow_setting": {
                "mode": "Video",
                "source": "Ingredients / reference image",
                "aspect_ratio": "9:16",
                "model": "Veo 3.1 - Fast or Quality",
                "duration": "8s",
            }
        })
    return {"concept": concept, "shots": shots, "prompts": prompts}

def export_product_prompt_package(project_dir: Path, data: dict, image_path: str | None = None) -> str:
    folder = project_dir / "exports" / f"product_prompt_studio_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "product_concept.json").write_text(json.dumps(data["concept"], ensure_ascii=False, indent=2), encoding="utf-8")
    (folder / "shot_list.json").write_text(json.dumps(data["shots"], ensure_ascii=False, indent=2), encoding="utf-8")
    (folder / "flow_prompts.txt").write_text("\n\n====================\n\n".join([p["prompt"] for p in data["prompts"]]), encoding="utf-8")
    (folder / "voiceovers.txt").write_text("\n\n".join([f"Prompt {p['variant']}:\n{p['voiceover']}" for p in data["prompts"]]), encoding="utf-8")
    (folder / "full_package.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    if image_path and Path(image_path).exists():
        import shutil
        shutil.copy2(image_path, folder / ("uploaded_product" + Path(image_path).suffix))
    zip_path = project_dir / "exports" / f"product_prompt_studio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for p in folder.rglob("*"):
            if p.is_file():
                z.write(p, arcname=p.relative_to(folder))
    return str(zip_path)
