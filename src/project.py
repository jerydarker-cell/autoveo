from __future__ import annotations
from pathlib import Path
from datetime import datetime
import json, re, shutil, zipfile

ROOT = Path(__file__).resolve().parents[1]
PROJECTS_DIR = ROOT / "projects"
BACKUPS_DIR = ROOT / "backups"
LOGS_DIR = ROOT / "logs"
for d in [PROJECTS_DIR, BACKUPS_DIR, LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def slugify(text: str, fallback: str = "project") -> str:
    s = re.sub(r"[^a-zA-Z0-9_-]+", "_", text.strip().lower()).strip("_")
    return s[:70] or fallback

def project_dir(project_name: str) -> Path:
    folder = PROJECTS_DIR / slugify(project_name, "default_project")
    for sub in ["flow_inbox", "clips", "audio", "frames", "exports", "plans", "thumbs"]:
        (folder / sub).mkdir(parents=True, exist_ok=True)
    return folder

def list_projects() -> list[str]:
    items = [p.name for p in PROJECTS_DIR.iterdir() if p.is_dir()]
    return sorted(items) or ["default_project"]

def ensure_project(name: str) -> Path:
    return project_dir(name)

def save_json(path: str | Path, data: dict) -> str:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)

def export_zip(project_name: str, reason: str = "export") -> str:
    pdir = project_dir(project_name)
    out = pdir / "exports" / f"{slugify(project_name)}_{reason}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for p in pdir.rglob("*"):
            if p.is_file() and p != out:
                z.write(p, arcname=p.relative_to(pdir))
    return str(out)

def backup_project(project_name: str) -> str:
    pdir = project_dir(project_name)
    bdir = BACKUPS_DIR / slugify(project_name)
    bdir.mkdir(parents=True, exist_ok=True)
    out = bdir / f"{slugify(project_name)}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for p in pdir.rglob("*"):
            if p.is_file():
                z.write(p, arcname=p.relative_to(pdir))
    return str(out)

def storage_report(project_name: str) -> dict:
    pdir = project_dir(project_name)
    total, files, largest = 0, 0, []
    for p in pdir.rglob("*"):
        if p.is_file():
            size = p.stat().st_size
            total += size
            files += 1
            largest.append({"mb": round(size/1024/1024, 2), "path": str(p)})
    largest.sort(key=lambda x: x["mb"], reverse=True)
    return {"total_mb": round(total/1024/1024, 2), "files": files, "largest": largest[:10]}

def log_error(context: str, error: Exception | str, meta: dict | None = None) -> str:
    path = LOGS_DIR / "errors.jsonl"
    row = {"time": now(), "context": context, "error": str(error), "meta": meta or {}}
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return str(path)

def read_errors(limit: int = 100) -> list[dict]:
    path = LOGS_DIR / "errors.jsonl"
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines()[-limit:]:
        try:
            rows.append(json.loads(line))
        except Exception:
            rows.append({"raw": line})
    return list(reversed(rows))
