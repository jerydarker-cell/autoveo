from __future__ import annotations
from pathlib import Path
from datetime import datetime
import re, shutil, json

VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".webm"}

def parse_scene_number(name: str) -> int | None:
    stem = Path(name).stem.lower()
    for pat in [r"scene[_\-\s]*(\d+)", r"sc[_\-\s]*(\d+)", r"canh[_\-\s]*(\d+)", r"cảnh[_\-\s]*(\d+)", r"^(\d+)[_\-\s]", r"[_\-\s](\d+)$"]:
        m = re.search(pat, stem)
        if m:
            try: return int(m.group(1))
            except Exception: pass
    return None

def inbox_dir(project_dir: Path) -> Path:
    folder = project_dir / "flow_inbox"
    folder.mkdir(parents=True, exist_ok=True)
    return folder

def clips_dir(project_dir: Path) -> Path:
    folder = project_dir / "clips"
    folder.mkdir(parents=True, exist_ok=True)
    return folder

def scan_inbox(project_dir: Path) -> list[dict]:
    folder = inbox_dir(project_dir)
    out = []
    for p in folder.iterdir():
        if p.is_file() and p.suffix.lower() in VIDEO_EXTS:
            scene = parse_scene_number(p.name)
            if scene:
                out.append({"scene": scene, "path": str(p), "name": p.name, "source": "inbox"})
    return sorted(out, key=lambda x: x["scene"])

def save_uploads(project_dir: Path, uploaded_files: list) -> list[dict]:
    folder = clips_dir(project_dir)
    saved = []
    for idx, up in enumerate(uploaded_files, 1):
        scene = parse_scene_number(up.name) or idx
        suffix = Path(up.name).suffix or ".mp4"
        safe = re.sub(r"[^a-zA-Z0-9_.-]+", "_", Path(up.name).stem)
        path = folder / f"scene_{scene:02d}_{safe}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}{suffix}"
        up.seek(0); path.write_bytes(up.read()); up.seek(0)
        saved.append({"scene": int(scene), "path": str(path), "name": path.name, "source": "upload"})
    return sorted(saved, key=lambda x: x["scene"])

def merge_clips(*lists: list[dict]) -> list[dict]:
    by_scene = {}
    for lst in lists:
        for item in lst or []:
            scene = int(item.get("scene") or 0)
            if scene > 0:
                by_scene[scene] = item
    return [by_scene[k] for k in sorted(by_scene)]

def missing_scenes(clips: list[dict], expected: int) -> list[int]:
    have = {int(c.get("scene") or 0) for c in clips}
    return [i for i in range(1, int(expected)+1) if i not in have]

def normalize_names(clips: list[dict], project_dir: Path) -> list[dict]:
    folder = inbox_dir(project_dir)
    out = []
    for c in sorted(clips, key=lambda x: int(x.get("scene") or 0)):
        scene = int(c["scene"])
        src = Path(c["path"])
        if not src.exists(): continue
        dest = folder / f"scene_{scene:02d}{src.suffix.lower()}"
        if src.resolve() != dest.resolve():
            if dest.exists():
                dest = folder / f"scene_{scene:02d}_{datetime.now().strftime('%H%M%S')}{src.suffix.lower()}"
            shutil.copy2(src, dest)
        out.append({"scene": scene, "path": str(dest), "name": dest.name, "source": "normalized"})
    return out

def write_prompt_txt(project_dir: Path, rows: list[dict]) -> str:
    path = project_dir / "plans" / f"flow_prompts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    parts = []
    for r in rows:
        parts.append(f"SCENE {r.get('scene')}\nNARRATION:\n{r.get('narration','')}\n\nPROMPT:\n{r.get('prompt','')}\n\n---\n")
    path.write_text("\n".join(parts), encoding="utf-8")
    return str(path)
