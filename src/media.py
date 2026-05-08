from __future__ import annotations
from pathlib import Path
from datetime import datetime
import subprocess, shutil, zipfile, json, wave, struct
from PIL import Image
import numpy as np
try:
    import cv2
except Exception:
    cv2=None
def ffmpeg_path(): return shutil.which('ffmpeg')
def run_cmd(cmd,timeout=1200):
    try:
        p=subprocess.run(cmd,capture_output=True,text=True,timeout=timeout)
        return p.returncode==0,(p.stdout or '')+(p.stderr or '')
    except Exception as e: return False,str(e)
def concat_videos(project_dir,clips,output_name='final.mp4',add_fade=False):
    if not clips: raise RuntimeError('Chưa có clip để nối.')
    out=project_dir/'exports'/output_name; out.parent.mkdir(parents=True,exist_ok=True)
    if len(clips)==1: shutil.copy2(clips[0],out); return str(out)
    ff=ffmpeg_path()
    if not ff: shutil.copy2(clips[0],out); return str(out)
    work=project_dir/'exports'/f"concat_{datetime.now().strftime('%H%M%S')}"; work.mkdir(parents=True,exist_ok=True)
    lf=work/'concat.txt'; lf.write_text('\n'.join([f"file '{Path(c).resolve().as_posix()}'" for c in clips]),encoding='utf-8')
    ok,msg=run_cmd([ff,'-y','-f','concat','-safe','0','-i',str(lf),'-c','copy',str(out)])
    if not ok: ok,msg=run_cmd([ff,'-y','-f','concat','-safe','0','-i',str(lf),'-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac',str(out)])
    if not ok: raise RuntimeError(msg)
    return str(out)
def make_srt(project_dir,lines,seconds_per_caption=4):
    path=project_dir/'audio'/f"subtitle_{datetime.now().strftime('%Y%m%d_%H%M%S')}.srt"; path.parent.mkdir(parents=True,exist_ok=True)
    def ts(sec): return f"{sec//3600:02d}:{(sec%3600)//60:02d}:{sec%60:02d},000"
    t=0; blocks=[]
    for i,line in enumerate([x for x in lines if str(x).strip()] or ['Caption'],1):
        blocks.append(f"{i}\n{ts(t)} --> {ts(t+seconds_per_caption)}\n{str(line).strip()}\n"); t+=seconds_per_caption
    path.write_text('\n'.join(blocks),encoding='utf-8'); return str(path)
def silent_voice(project_dir,seconds=12):
    path=project_dir/'audio'/f"silent_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"; path.parent.mkdir(parents=True,exist_ok=True); rate=24000
    with wave.open(str(path),'w') as wav:
        wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(rate); wav.writeframes(struct.pack('<h',0)*rate*max(1,seconds))
    return str(path)
def thumbnail_from_video(project_dir,video):
    if cv2 is None or not Path(video).exists(): return None
    cap=cv2.VideoCapture(video); total=int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    if total<=0: return None
    best=None
    for idx in np.linspace(0,total-1,min(36,total)).astype(int):
        cap.set(cv2.CAP_PROP_POS_FRAMES,int(idx)); ok,frame=cap.read()
        if not ok: continue
        rgb=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB); gray=cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY); score=cv2.Laplacian(gray,cv2.CV_64F).var()+(100-abs(float(np.mean(gray))-128))*2
        if best is None or score>best[0]: best=(score,rgb)
    cap.release()
    if best is None: return None
    out=project_dir/'frames'/f"thumb_base_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"; out.parent.mkdir(parents=True,exist_ok=True); Image.fromarray(best[1]).save(out); return str(out)
def mix_audio_subtitles(project_dir,video,voice,srt,burn_subtitles=True):
    ff=ffmpeg_path()
    if not ff: return video
    out=project_dir/'exports'/f"final_mix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"; cmd=[ff,'-y','-i',video]
    if voice: cmd += ['-i',voice]
    if voice and burn_subtitles and srt:
        esc=Path(srt).resolve().as_posix().replace(':','\\:'); cmd += ['-vf',f"subtitles='{esc}'",'-map','0:v','-map','1:a','-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac','-shortest',str(out)]
    elif voice: cmd += ['-map','0:v','-map','1:a','-c:v','copy','-c:a','aac','-shortest',str(out)]
    else: return video
    ok,msg=run_cmd(cmd); return str(out) if ok else video
def publish_package(project_dir,final_video,thumbnail,srt,voice,metadata):
    folder=project_dir/'exports'/f"publish_package_{datetime.now().strftime('%Y%m%d_%H%M%S')}"; folder.mkdir(parents=True,exist_ok=True)
    files={'final_video.mp4':final_video,'thumbnail.png':thumbnail,'subtitle.srt':srt,'voiceover'+(Path(voice).suffix if voice else '.wav'):voice}
    for name,src in files.items():
        if src and Path(src).exists(): shutil.copy2(src,folder/name)
    (folder/'metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
    (folder/'caption.txt').write_text(metadata.get('caption','')+'\n\n'+metadata.get('hashtags',''),encoding='utf-8')
    zp=project_dir/'exports'/f"publish_package_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    with zipfile.ZipFile(zp,'w',zipfile.ZIP_DEFLATED) as z:
        for p in folder.rglob('*'): z.write(p,arcname=p.relative_to(folder))
    return str(zp)


def _even_dim(value):
    """Return a positive even integer for H.264/FFmpeg compatibility."""
    v = int(round(float(value)))
    if v < 2:
        v = 2
    return v if v % 2 == 0 else v + 1

def video_target_size(aspect_ratio='9:16', resolution='1080'):
    """Return even width,height from aspect + long-edge resolution.

    H.264 encoders commonly require even dimensions. This prevents failures
    for settings like 9:16 + 720 or 9:16 + 2000.
    """
    res = _even_dim(str(resolution).replace('p','').strip() or 1080)
    if aspect_ratio == '9:16':
        return _even_dim(res * 9 / 16), res
    if aspect_ratio == '16:9':
        return res, _even_dim(res * 9 / 16)
    if aspect_ratio == '1:1':
        return res, res
    if aspect_ratio == '4:5':
        return _even_dim(res * 4 / 5), res
    if aspect_ratio == '3:4':
        return _even_dim(res * 3 / 4), res
    return _even_dim(res * 9 / 16), res

def process_clip_for_final(project_dir, clip, index, seconds_per_clip=0, aspect_ratio='9:16', resolution='1080', fps=30, fit_mode='pad'):
    """Normalize one clip to target duration/aspect/resolution/fps for stable concatenation."""
    ff = ffmpeg_path()
    if not ff:
        return str(clip)
    w, h = video_target_size(aspect_ratio, resolution)
    clip = str(clip)
    out_dir = project_dir / 'exports' / 'processed_clips'
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"segment_{index:02d}_{w}x{h}_{fps}fps.mp4"

    if fit_mode == 'crop':
        vf = f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},fps={fps},format=yuv420p"
    else:
        vf = f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,fps={fps},format=yuv420p"

    cmd = [ff, '-y', '-i', clip]
    if seconds_per_clip and float(seconds_per_clip) > 0:
        # tpad keeps short clips from ending too early; -t cuts to exact duration.
        vf = vf + f",tpad=stop_mode=clone:stop_duration={float(seconds_per_clip):.2f}"
        cmd += ['-vf', vf, '-t', f"{float(seconds_per_clip):.2f}"]
    else:
        cmd += ['-vf', vf]

    cmd += [
        '-c:v', 'libx264',
        '-preset', 'veryfast',
        '-crf', '20',
        '-pix_fmt', 'yuv420p',
        '-movflags', '+faststart',
        '-an',
        str(out)
    ]
    ok, msg = run_cmd(cmd, timeout=1200)
    if not ok:
        raise RuntimeError(msg)
    return str(out)

def concat_videos_studio(project_dir, clips, output_name='final.mp4', add_fade=False, seconds_per_clip=0, aspect_ratio='9:16', resolution='1080', fps=30, fit_mode='pad'):
    """Process clips to same duration/aspect/resolution/fps and concatenate.
    This is more stable than concat copy for mixed Flow downloads.
    """
    if not clips:
        raise RuntimeError('Chưa có clip để nối.')
    ff = ffmpeg_path()
    if not ff:
        return concat_videos(project_dir, clips, output_name, add_fade)

    processed = []
    for i, clip in enumerate(clips, 1):
        if Path(clip).exists():
            processed.append(process_clip_for_final(
                project_dir,
                clip,
                i,
                seconds_per_clip=seconds_per_clip,
                aspect_ratio=aspect_ratio,
                resolution=resolution,
                fps=fps,
                fit_mode=fit_mode,
            ))

    if not processed:
        raise RuntimeError('Không có clip hợp lệ sau xử lý.')

    out = project_dir / 'exports' / output_name
    out.parent.mkdir(parents=True, exist_ok=True)

    work = project_dir / 'exports' / f"concat_studio_{datetime.now().strftime('%H%M%S')}"
    work.mkdir(parents=True, exist_ok=True)
    lf = work / 'concat.txt'
    lf.write_text('\n'.join([f"file '{Path(c).resolve().as_posix()}'" for c in processed]), encoding='utf-8')

    ok, msg = run_cmd([ff, '-y', '-f', 'concat', '-safe', '0', '-i', str(lf), '-c', 'copy', str(out)], timeout=1200)
    if not ok:
        ok, msg = run_cmd([
            ff, '-y', '-f', 'concat', '-safe', '0', '-i', str(lf),
            '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20',
            '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
            str(out)
        ], timeout=1200)
    if not ok:
        raise RuntimeError(msg)
    return str(out)
