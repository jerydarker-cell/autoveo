from __future__ import annotations
from pathlib import Path
from datetime import datetime
import subprocess, shutil, zipfile, json, wave, struct
from PIL import Image, ImageDraw
import numpy as np

try:
    import cv2
except Exception:
    cv2 = None

def ffmpeg_path() -> str | None:
    return shutil.which("ffmpeg")

def run_cmd(cmd: list[str], timeout: int = 1200) -> tuple[bool, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode == 0, (p.stdout or "") + (p.stderr or "")
    except Exception as e:
        return False, str(e)

def concat_videos(project_dir: Path, clips: list[str], output_name: str = "final.mp4", add_fade: bool = False) -> str:
    if not clips:
        raise RuntimeError("Chưa có clip để nối.")
    out = project_dir / "exports" / output_name
    out.parent.mkdir(parents=True, exist_ok=True)
    if len(clips) == 1:
        shutil.copy2(clips[0], out)
        return str(out)
    ffmpeg = ffmpeg_path()
    if not ffmpeg:
        shutil.copy2(clips[0], out)
        return str(out)
    work = project_dir / "exports" / f"concat_{datetime.now().strftime('%H%M%S')}"
    work.mkdir(parents=True, exist_ok=True)
    list_file = work / "concat.txt"
    list_file.write_text("\n".join([f"file '{Path(c).resolve().as_posix()}'" for c in clips]), encoding="utf-8")
    ok, msg = run_cmd([ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(list_file), "-c", "copy", str(out)])
    if not ok:
        ok, msg = run_cmd([ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(list_file), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(out)])
    if not ok:
        raise RuntimeError(msg)
    return str(out)

def make_srt(project_dir: Path, lines: list[str], seconds_per_caption: int = 4) -> str:
    path = project_dir / "audio" / f"subtitle_{datetime.now().strftime('%Y%m%d_%H%M%S')}.srt"
    path.parent.mkdir(parents=True, exist_ok=True)
    def ts(sec: int) -> str:
        return f"{sec//3600:02d}:{(sec%3600)//60:02d}:{sec%60:02d},000"
    t, blocks = 0, []
    for i, line in enumerate([x for x in lines if x.strip()] or ["Caption"], 1):
        blocks.append(f"{i}\n{ts(t)} --> {ts(t+seconds_per_caption)}\n{line.strip()}\n")
        t += seconds_per_caption
    path.write_text("\n".join(blocks), encoding="utf-8")
    return str(path)

def silent_voice(project_dir: Path, seconds: int = 12) -> str:
    path = project_dir / "audio" / f"silent_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
    path.parent.mkdir(parents=True, exist_ok=True)
    rate = 24000
    with wave.open(str(path), "w") as wav:
        wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(rate)
        wav.writeframes(struct.pack("<h", 0) * rate * max(1, seconds))
    return str(path)

def thumbnail_from_video(project_dir: Path, video: str) -> str | None:
    if cv2 is None or not Path(video).exists():
        return None
    cap = cv2.VideoCapture(video)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    if total <= 0:
        return None
    best = None
    for idx in np.linspace(0, total-1, min(36, total)).astype(int):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
        ok, frame = cap.read()
        if not ok: continue
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        score = cv2.Laplacian(gray, cv2.CV_64F).var() + (100 - abs(float(np.mean(gray)) - 128)) * 2
        if best is None or score > best[0]:
            best = (score, rgb)
    cap.release()
    if best is None: return None
    out = project_dir / "frames" / f"thumb_base_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(best[1]).save(out)
    return str(out)

def mix_audio_subtitles(project_dir: Path, video: str, voice: str | None, srt: str | None, burn_subtitles: bool = True) -> str:
    ffmpeg = ffmpeg_path()
    if not ffmpeg:
        return video
    out = project_dir / "exports" / f"final_mix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
    cmd = [ffmpeg, "-y", "-i", video]
    if voice:
        cmd += ["-i", voice]
    if voice and burn_subtitles and srt:
        srt_escaped = Path(srt).resolve().as_posix().replace(":", "\\:")
        cmd += ["-vf", f"subtitles='{srt_escaped}'", "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(out)]
    elif voice:
        cmd += ["-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-shortest", str(out)]
    elif burn_subtitles and srt:
        srt_escaped = Path(srt).resolve().as_posix().replace(":", "\\:")
        cmd += ["-vf", f"subtitles='{srt_escaped}'", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "copy", str(out)]
    else:
        return video
    ok, msg = run_cmd(cmd)
    return str(out) if ok else video

def publish_package(project_dir: Path, final_video: str, thumbnail: str | None, srt: str | None, voice: str | None, metadata: dict) -> str:
    folder = project_dir / "exports" / f"publish_package_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    folder.mkdir(parents=True, exist_ok=True)
    files = {"final_video.mp4": final_video, "thumbnail.png": thumbnail, "subtitle.srt": srt, "voiceover" + (Path(voice).suffix if voice else ".wav"): voice}
    for name, src in files.items():
        if src and Path(src).exists():
            shutil.copy2(src, folder / name)
    (folder / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    (folder / "caption.txt").write_text(metadata.get("caption", "") + "\n\n" + metadata.get("hashtags", ""), encoding="utf-8")
    zip_path = project_dir / "exports" / f"publish_package_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for p in folder.rglob("*"):
            z.write(p, arcname=p.relative_to(folder))
    return str(zip_path)
