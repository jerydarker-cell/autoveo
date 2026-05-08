from __future__ import annotations
from pathlib import Path
from datetime import datetime
import re, shutil
VIDEO_EXTS={'.mp4','.mov','.m4v','.webm'}
def parse_scene_number(name):
    stem=Path(name).stem.lower()
    for pat in [r'scene[_\-\s]*(\d+)',r'sc[_\-\s]*(\d+)',r'canh[_\-\s]*(\d+)',r'cảnh[_\-\s]*(\d+)',r'^(\d+)[_\-\s]',r'[_\-\s](\d+)$']:
        m=re.search(pat,stem)
        if m:
            try: return int(m.group(1))
            except Exception: pass
    return None
def inbox_dir(project_dir):
    f=project_dir/'flow_inbox'; f.mkdir(parents=True,exist_ok=True); return f
def clips_dir(project_dir):
    f=project_dir/'clips'; f.mkdir(parents=True,exist_ok=True); return f
def scan_inbox(project_dir):
    out=[]
    for p in inbox_dir(project_dir).iterdir():
        if p.is_file() and p.suffix.lower() in VIDEO_EXTS:
            sc=parse_scene_number(p.name)
            if sc: out.append({'scene':sc,'path':str(p),'name':p.name,'source':'inbox'})
    return sorted(out,key=lambda x:x['scene'])
def save_uploads(project_dir, uploaded_files):
    folder=clips_dir(project_dir); saved=[]
    for idx,up in enumerate(uploaded_files,1):
        sc=parse_scene_number(up.name) or idx; suffix=Path(up.name).suffix or '.mp4'; safe=re.sub(r'[^a-zA-Z0-9_.-]+','_',Path(up.name).stem)
        path=folder/f"scene_{sc:02d}_{safe}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}{suffix}"
        up.seek(0); path.write_bytes(up.read()); up.seek(0)
        saved.append({'scene':int(sc),'path':str(path),'name':path.name,'source':'upload'})
    return sorted(saved,key=lambda x:x['scene'])
def merge_clips(*lists):
    by={}
    for lst in lists:
        for it in lst or []:
            sc=int(it.get('scene') or 0)
            if sc>0: by[sc]=it
    return [by[k] for k in sorted(by)]
def missing_scenes(clips,expected):
    have={int(c.get('scene') or 0) for c in clips}
    return [i for i in range(1,int(expected)+1) if i not in have]
def normalize_names(clips,project_dir):
    folder=inbox_dir(project_dir); out=[]
    for c in sorted(clips,key=lambda x:int(x.get('scene') or 0)):
        sc=int(c['scene']); src=Path(c['path'])
        if not src.exists(): continue
        dest=folder/f"scene_{sc:02d}{src.suffix.lower()}"
        if src.resolve()!=dest.resolve():
            if dest.exists(): dest=folder/f"scene_{sc:02d}_{datetime.now().strftime('%H%M%S')}{src.suffix.lower()}"
            shutil.copy2(src,dest)
        out.append({'scene':sc,'path':str(dest),'name':dest.name,'source':'normalized'})
    return out
def write_prompt_txt(project_dir,rows):
    path=project_dir/'plans'/f"flow_prompts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"; path.parent.mkdir(parents=True,exist_ok=True)
    parts=[]
    for r in rows: parts.append(f"SCENE {r.get('scene')}\nNARRATION:\n{r.get('narration','')}\n\nPROMPT:\n{r.get('prompt','')}\n\n---\n")
    path.write_text('\n'.join(parts),encoding='utf-8'); return str(path)
