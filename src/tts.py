from __future__ import annotations
from pathlib import Path
from datetime import datetime
import asyncio
from .media import silent_voice

VOICE_PRESETS = {
    "Tiếng Việt - Nam": "vi-VN-NamMinhNeural",
    "Tiếng Việt - Nữ": "vi-VN-HoaiMyNeural",
    "English - Male": "en-US-GuyNeural",
    "English - Female": "en-US-JennyNeural",
}

def tts_edge(project_dir: Path, text: str, voice_label: str, mock: bool = False) -> str:
    if mock:
        return silent_voice(project_dir, max(8, min(180, len(text)//12)))
    try:
        import edge_tts
        out = project_dir / "audio" / f"voice_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
        out.parent.mkdir(parents=True, exist_ok=True)
        async def _run():
            communicate = edge_tts.Communicate(text, VOICE_PRESETS.get(voice_label, "vi-VN-NamMinhNeural"))
            await communicate.save(str(out))
        asyncio.run(_run())
        return str(out)
    except Exception:
        return silent_voice(project_dir, max(8, min(180, len(text)//12)))
