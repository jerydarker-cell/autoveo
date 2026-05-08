from __future__ import annotations
import re
from pathlib import Path

def safe_filename(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", name or "uploaded_file")

import json
import streamlit as st
from src.project import project_dir, list_projects, export_zip, backup_project, storage_report, read_errors, log_error, now
from src.viral import NICHES, FORMATS, make_blueprint, export_blueprint_zip
from src.flow import inbox_dir, scan_inbox, save_uploads, merge_clips, missing_scenes, normalize_names, write_prompt_txt
from src.media import concat_videos, make_srt, thumbnail_from_video, mix_audio_subtitles, publish_package, ffmpeg_path
from src.tts import VOICE_PRESETS, tts_edge
from src.thumbnails import TEMPLATES, make_thumbnail
from src.product_prompt import PRODUCT_MOODS, PRODUCT_TYPES, build_product_prompts, export_product_prompt_package
APP_VERSION='2.5.0 Fix Product Upload'
FLOW_URL='https://labs.google/fx/tools/flow'
FLOW_MODEL_CREDITS={'Veo 3.1 - Lite':8,'Veo 3.1 - Fast':10,'Veo 3.1 - Quality':15,'Veo 3.1 - Lite [Lower Priority]':6,'Veo 3.1 - Fast [Lower Priority]':8}
def estimate_flow_credits(settings):
    base=FLOW_MODEL_CREDITS.get(settings.get('model'),10); factor={4:.65,6:.82,8:1.0}.get(int(settings.get('duration',8)),1.0); variants=int(str(settings.get('variants','1x')).replace('x','') or 1)
    return max(1,int(round(base*factor*variants)))
def flow_settings_suffix(settings):
    action=settings.get('action_mode','Generate'); source=settings.get('source_mode','Text')
    parts=[f"Flow mode: {settings.get('media_mode','Video')}.",f"Source: {source}.",f"Action: {action}.",f"Aspect ratio: {settings.get('aspect_ratio','9:16')}.",f"Model target: {settings.get('model','Veo 3.1 - Fast')}.",f"Duration: {settings.get('duration',8)}s.",f"Generate variants: {settings.get('variants','1x')}."]
    if action=='Extend': parts.append('Continue the previous shot naturally, preserve identity, lighting, style and motion continuity.')
    elif action=='Insert': parts.append('Insert a new visual beat that matches the previous and next shot, seamless continuity.')
    elif action=='Remove': parts.append('Remove unwanted object/element cleanly while keeping background and motion natural.')
    elif action=='Camera': parts.append('Focus on camera movement and cinematic framing.')
    if source=='Frames': parts.append('Use start/end frame logic if images are provided in Flow.')
    elif source=='Ingredients': parts.append('Use reference ingredients/images to preserve character, product, object and style.')
    if settings.get('camera_note'): parts.append('Camera instruction: '+settings.get('camera_note'))
    parts.append('No watermark, no unreadable text, clean composition.')
    return ' '.join(parts)
st.set_page_config(page_title='AUTO VEO Studio v2.4',page_icon='🎬',layout='wide')
st.markdown('''<style>.block-container{padding-top:.85rem;max-width:1320px}.hero{padding:22px 26px;border-radius:26px;background:linear-gradient(135deg,rgba(90,80,255,.18),rgba(255,255,255,.035));border:1px solid rgba(255,255,255,.14);margin-bottom:18px}.hero h1{margin:0;font-size:2rem}.badge{display:inline-block;padding:6px 11px;border-radius:999px;background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.14);margin:5px 6px 0 0;font-size:.86rem}</style>''',unsafe_allow_html=True)
for k,v in {'viral_blueprint':None,'flow_rows':[],'flow_clips':[],'flow_quick_settings':{},'viral_product_prompt_data':None}.items():
    if k not in st.session_state: st.session_state[k]=v.copy() if isinstance(v,(list,dict)) else v
with st.sidebar:
    st.markdown('## 🎬 AUTO VEO Studio'); st.caption(APP_VERSION); compact=st.checkbox('Giao diện gọn',value=True); ui_mode=st.radio('Chế độ',['Simple','Advanced'],horizontal=True,index=0)
    st.divider(); st.markdown('### 📁 Project'); projects=list_projects(); selected=st.selectbox('Chọn project',projects,index=0); new_project=st.text_input('Tạo/chọn tên project mới',value='')
    if st.button('➕ Tạo/mở project',use_container_width=True):
        if new_project.strip(): selected=new_project.strip(); project_dir(selected); st.success('Đã tạo/mở project.'); st.rerun()
    project_name=selected; pdir=project_dir(project_name); st.caption(f'Folder: `{pdir.name}`')
    st.divider(); st.markdown('### ⚙️ Runtime'); st.caption(f"FFmpeg: {'OK' if ffmpeg_path() else 'Chưa thấy'}")
    if not ffmpeg_path(): st.warning('Cần FFmpeg để nối video/ghép subtitle/audio.'); st.code('Windows: winget install Gyan.FFmpeg\nMac: brew install ffmpeg')
    st.divider(); default_thumb_template=st.selectbox('Template thumbnail',list(TEMPLATES.keys()),index=0)
st.markdown(f'''<div class="hero"><h1>🎬 AUTO VEO Studio v2.5 — Fix Product Upload</h1><p>Viral Director + Product Upload · Concept · Script 8s · 3 Flow Prompts · Flow Assisted</p><span class="badge">📁 {project_name}</span><span class="badge">⚙️ Flow settings</span><span class="badge">💳 credit estimate</span><span class="badge">📱 giống Google Flow mobile</span></div>''',unsafe_allow_html=True)
SIMPLE_TABS=['🎯 Viral Director','🌊 Flow Assisted','🏠 Project','📊 Dashboard']; ADVANCED_TABS=SIMPLE_TABS+['🖼️ Thumbnail Lab','🧾 Logs','🚀 Deploy']; names=SIMPLE_TABS if ui_mode=='Simple' else ADVANCED_TABS; tabs=st.tabs(names)
def tab(name): return tabs[names.index(name)]
def has_tab(name): return name in names
with tab('🎯 Viral Director'):
    st.markdown('## 🎯 Viral Content Director')
    c1,c2=st.columns([1.05,.95])
    with c1:
        topic=st.text_area('Chủ đề/kênh/ngách muốn làm video',height=120,value='AI/marketing/kinh doanh cho Shorts/Reels'); platform=st.selectbox('Nền tảng',['TikTok/Reels 9:16','YouTube Shorts 9:16','YouTube ngang 16:9','Facebook Reels']); niche=st.selectbox('Ngách viral',list(NICHES.keys())); faceless=st.checkbox('Ưu tiên faceless',value=True)
    with c2:
        host=st.text_area('AI host cố định nếu cần',value='Nam 28 tuổi, smart casual, background studio hiện đại, tone xanh đen, nói nhanh – rõ – chuyên gia.',height=90); minutes=st.selectbox('Độ dài blueprint',[3,4,5],index=0); st.info('Có chấm điểm Viral Potential, Hook, Retention, Faceless Ease, Difficulty.')

    st.divider()
    st.markdown('### 🛍️ Upload ảnh sản phẩm ngay trong Viral Director')
    st.caption('Tạo concept + kịch bản 8s + 3 prompt Flow/Veo từ ảnh sản phẩm, rồi gửi sang Flow Assisted để copy prompt và build final.')

    pc1, pc2 = st.columns([1.05, .95])
    with pc1:
        viral_product_upload = st.file_uploader('Upload ảnh sản phẩm gốc', type=['png','jpg','jpeg','webp'], key='viral_product_upload')
        viral_product_name = st.text_input('Tên sản phẩm', value='sản phẩm trong ảnh gốc', key='viral_product_name')
        viral_product_type = st.selectbox('Loại sản phẩm', PRODUCT_TYPES, key='viral_product_type')
        viral_product_target = st.text_area('Khách hàng mục tiêu', value='người xem mạng xã hội thích sản phẩm đẹp, chân thực, dễ dùng và đáng tin', height=80, key='viral_product_target')
    with pc2:
        viral_product_mood = st.selectbox('Mood nhạc / cảm xúc', list(PRODUCT_MOODS.keys()), index=0, key='viral_product_mood')
        viral_product_objective = st.text_area('Mục tiêu video sản phẩm', value='Hiệu suất cao, giữ chân người xem, tăng thời gian xem, tăng tương tác và khiến người xem muốn thử sản phẩm.', height=80, key='viral_product_objective')
        viral_product_model = st.checkbox('Có người mẫu sử dụng sản phẩm', value=True, key='viral_product_model')
        viral_product_clean_text = st.checkbox('Xoá sạch chữ trên sản phẩm / cấm text overlay', value=True, key='viral_product_clean_text')

    viral_product_image_path = None
    if viral_product_upload:
        product_ref_dir = pdir / 'product_refs'
        product_ref_dir.mkdir(parents=True, exist_ok=True)
        safe_product_file = safe_filename(viral_product_upload.name)
        viral_product_image_path = product_ref_dir / safe_product_file
        viral_product_upload.seek(0)
        viral_product_image_path.write_bytes(viral_product_upload.read())
        viral_product_upload.seek(0)
        st.image(str(viral_product_image_path), caption='Ảnh sản phẩm gốc dùng làm reference trong Google Flow Ingredients', use_container_width=True)

    st.info('Prompt sẽ khóa sản phẩm theo ảnh gốc, giữ nguyên hình dáng/màu/chất liệu, cấm tự vẽ lại, cấm chữ overlay, cấm chữ môi trường, và yêu cầu xoá chữ trên sản phẩm để giảm lỗi Flow.')

    cp1, cp2 = st.columns([1, 1])
    with cp1:
        make_product_prompts = st.button('🛍️ Tạo Concept + Kịch bản 8s + 3 Prompt Flow', type='primary', use_container_width=True)
    with cp2:
        st.markdown(
            f"""
<div class="card">
<b>Music mood:</b><br>{PRODUCT_MOODS[viral_product_mood]['music']}<br><br>
<b>Camera:</b><br>{PRODUCT_MOODS[viral_product_mood]['camera']}<br><br>
<b>Voice:</b><br>{PRODUCT_MOODS[viral_product_mood]['voice_style']}
</div>
""",
            unsafe_allow_html=True,
        )

    if make_product_prompts:
        if not viral_product_upload:
            st.error('Hãy upload ảnh sản phẩm gốc trước.')
        else:
            pdata = build_product_prompts(
                viral_product_name,
                viral_product_type,
                viral_product_mood,
                viral_product_target,
                viral_product_objective,
                viral_product_model,
                viral_product_clean_text,
                3,
            )
            pdata['viral_context'] = {'topic': topic, 'platform': platform, 'niche': niche, 'faceless': faceless, 'host': host}
            if viral_product_image_path:
                pdata['product_reference_image'] = str(viral_product_image_path)
            st.session_state.viral_product_prompt_data = pdata
            z = export_product_prompt_package(pdir, pdata, str(viral_product_image_path) if viral_product_image_path else None)
            st.success('Đã tạo Product Concept + Kịch bản 8s + 3 Prompt Flow.')
            st.download_button('📦 Tải Product Prompt Package ZIP', Path(z).read_bytes(), Path(z).name, use_container_width=True)

    vpdata = st.session_state.get('viral_product_prompt_data')
    if vpdata:
        st.markdown('#### ✅ Product Concept')
        with st.expander('Xem concept chiến lược sản phẩm', expanded=False):
            st.json(vpdata['concept'])

        st.markdown('#### 🎬 Shot list 8s')
        st.dataframe(vpdata['shots'], use_container_width=True)

        st.markdown('#### 🧾 3 Prompt Flow/Veo từ ảnh sản phẩm')
        for pr in vpdata['prompts']:
            with st.expander(f"Prompt {pr['variant']} · {pr['mood']} · Voiceover", expanded=pr['variant'] == 1):
                st.markdown('**Voiceover tiếng Việt:**')
                st.write(pr['voiceover'])
                st.markdown('**Prompt Flow/Veo:**')
                st.text_area('Prompt', value=pr['prompt'], height=320, key=f"viral_product_prompt_{pr['variant']}")
                st.code(pr['prompt'])
                st.json(pr['estimated_flow_setting'])

        send1, sendall, downloadall = st.columns(3)
        with send1:
            if st.button('➡️ Gửi prompt 1 sang Flow Assisted', use_container_width=True, key='send_vproduct_1_fixed'):
                p0 = vpdata['prompts'][0]
                st.session_state.flow_rows = [{'scene': 1, 'status': 'Chưa làm', 'narration': p0['voiceover'], 'prompt': p0['prompt'], 'note': 'Viral Director Product Upload'}]
                st.success('Đã gửi prompt 1 sang Flow Assisted.')
        with sendall:
            if st.button('➡️ Gửi cả 3 prompt sang Flow Assisted', use_container_width=True, key='send_vproduct_all_fixed'):
                st.session_state.flow_rows = [
                    {'scene': p['variant'], 'status': 'Chưa làm', 'narration': p['voiceover'], 'prompt': p['prompt'], 'note': 'Viral Director Product Upload'}
                    for p in vpdata['prompts']
                ]
                st.success('Đã gửi cả 3 prompt sang Flow Assisted.')
        with downloadall:
            all_prompts = '\n\n====================\n\n'.join([p['prompt'] for p in vpdata['prompts']])
            st.download_button('⬇️ Tải 3 prompt TXT', all_prompts.encode('utf-8'), 'viral_product_flow_prompts.txt', use_container_width=True)

    st.divider()


    if st.button('🚀 Tạo Viral Blueprint',type='primary',use_container_width=True):
        bp=make_blueprint(topic,platform,niche,faceless,host,minutes); st.session_state.viral_blueprint=bp; z=export_blueprint_zip(pdir,bp); st.success('Đã tạo Viral Blueprint.'); st.download_button('📦 Tải Viral Blueprint ZIP',Path(z).read_bytes(),Path(z).name,use_container_width=True)
    bp=st.session_state.get('viral_blueprint')
    if bp:
        st.divider(); st.markdown('### 10 ý tưởng viral đã chấm điểm'); st.dataframe(bp['ideas'],use_container_width=True,column_order=['id','viral_potential','hook_score','retention_score','faceless_ease_score','production_difficulty','thumbnail_score','insight_score','title','first_3s_hook','content_format'])
        top=bp['ideas'][0]; a,b,c,d=st.columns(4); a.metric('Viral Potential',top['viral_potential']); b.metric('Hook',top['hook_score']); c.metric('Retention',top['retention_score']); d.metric('Difficulty',top['production_difficulty'])
        st.markdown('### Kịch bản'); st.text_area('Voiceover',value=bp['script']['voiceover'],height=220)
        st.markdown('### Shot prompts'); st.dataframe(bp['shots'],use_container_width=True)
        if st.button('➡️ Gửi prompt sang Flow Assisted',use_container_width=True):
            suffix=flow_settings_suffix(st.session_state.get('flow_quick_settings',{})); st.session_state.flow_rows=[{'scene':s['scene'],'status':'Chưa làm','narration':s['voiceover'],'prompt':s['flow_prompt']+'\n\n'+suffix,'note':''} for s in bp['shots']]; st.success('Đã gửi prompt sang Flow Assisted.')
        st.markdown('### Gói tối ưu'); st.json(bp['optimization'])
with tab('🌊 Flow Assisted'):
    st.markdown('## 🌊 Flow Assisted Mode + Flow Quick Settings')
    rows=st.session_state.get('flow_rows',[])
    c1,c2=st.columns([1.05,.95])
    with c1:
        if not rows: st.info('Chưa có prompt. Tạo ở Viral Director hoặc nhập nhanh bên dưới.')
        quick_topic=st.text_area('Tạo prompt nhanh nếu chưa có',height=90,placeholder='Nhập brief ngắn...')
    with c2:
        expected=st.number_input('Số scene dự kiến',min_value=1,max_value=50,value=max(1,len(rows) or 5)); voice_label=st.selectbox('Voice hậu kỳ',list(VOICE_PRESETS.keys())); burn_sub=st.checkbox('Burn subtitle vào final',value=True); add_fade=st.checkbox('Nối có fade nhẹ',value=True); thumb_template=st.selectbox('Thumbnail template',list(TEMPLATES.keys()),index=list(TEMPLATES.keys()).index(default_thumb_template)); st.link_button('🌊 Mở Google Flow',FLOW_URL,use_container_width=True)
    st.markdown('### ⚙️ Flow Quick Settings giống Google Flow')
    q1,q2,q3,q4=st.columns(4)
    with q1: media_mode=st.radio('Loại',['Image','Video'],index=1,horizontal=True); source_mode=st.radio('Nguồn',['Text','Frames','Ingredients'],index=0,horizontal=True)
    with q2: aspect_ratio=st.radio('Tỉ lệ',['9:16','16:9'],index=0,horizontal=True); variants=st.radio('Số bản',['1x','2x','3x','4x'],index=0,horizontal=True)
    with q3: model_flow=st.selectbox('Model Flow',['Veo 3.1 - Lite','Veo 3.1 - Fast','Veo 3.1 - Quality','Veo 3.1 - Lite [Lower Priority]','Veo 3.1 - Fast [Lower Priority]'],index=1); duration_flow=st.radio('Thời lượng',[4,6,8],index=2,horizontal=True)
    with q4: action_mode=st.selectbox('Action',['Generate','Extend','Insert','Remove','Camera'],index=0); camera_note=st.text_input('Camera note',value='',placeholder='slow dolly in, orbit...')
    flow_settings={'media_mode':media_mode,'source_mode':source_mode,'aspect_ratio':aspect_ratio,'variants':variants,'model':model_flow,'duration':int(duration_flow),'action_mode':action_mode,'camera_note':camera_note}; st.session_state.flow_quick_settings=flow_settings; credit=estimate_flow_credits(flow_settings); st.info(f'Ước tính: **{credit} credit/scene**, tổng **{credit*int(expected)} credit** cho {int(expected)} scene.')
    with st.expander('Prompt suffix tự thêm vào mỗi scene',expanded=False):
        st.text_area('Flow settings suffix',value=flow_settings_suffix(flow_settings),height=120); st.download_button('⬇️ Tải flow_settings.json',json.dumps({**flow_settings,'estimated_credits_per_scene':credit},ensure_ascii=False,indent=2).encode('utf-8'),'flow_settings.json',mime='application/json',use_container_width=True)
    if st.button('🧠 Tạo prompt nhanh 5 cảnh',use_container_width=True):
        if quick_topic.strip(): st.session_state.flow_rows=[{'scene':i,'status':'Chưa làm','narration':f'Cảnh {i}: {quick_topic}','prompt':f'{quick_topic}. Scene {i}. Cinematic short-form video, clear subject, smooth motion. '+flow_settings_suffix(flow_settings),'note':''} for i in range(1,6)]; st.rerun()
    rows=st.session_state.get('flow_rows',[])
    if rows:
        st.markdown('### 1) Checklist + prompt'); edited=st.data_editor(rows,num_rows='dynamic',use_container_width=True,key='flow_rows_editor_clean',column_config={'scene':st.column_config.NumberColumn('Scene',min_value=1),'status':st.column_config.SelectboxColumn('Trạng thái',options=['Chưa làm','Đã copy prompt','Đang render Flow','Đã tải video','Lỗi cần làm lại','Hoàn tất']),'narration':st.column_config.TextColumn('Narration'),'prompt':st.column_config.TextColumn('Prompt dán vào Flow'),'note':st.column_config.TextColumn('Ghi chú')}); st.session_state.flow_rows=edited; txt=write_prompt_txt(pdir,edited); st.download_button('⬇️ Tải toàn bộ prompt TXT',Path(txt).read_bytes(),Path(txt).name,use_container_width=True)
    st.markdown('### 2) Upload hàng loạt hoặc quét Flow Inbox'); inbox=inbox_dir(pdir); st.code(str(inbox),language='text')
    u1,u2,u3=st.columns(3)
    with u1:
        uploaded=st.file_uploader('Upload nhiều clip Flow',type=['mp4','mov','m4v','webm'],accept_multiple_files=True)
        if uploaded and st.button('💾 Lưu + auto map upload',use_container_width=True): saved=save_uploads(pdir,uploaded); st.session_state.flow_clips=merge_clips(st.session_state.get('flow_clips',[]),saved); st.success(f'Đã lưu {len(saved)} clip.')
    with u2:
        if st.button('🔍 Quét flow_inbox',use_container_width=True): scanned=scan_inbox(pdir); st.session_state.flow_clips=merge_clips(st.session_state.get('flow_clips',[]),scanned); st.success(f'Đã quét {len(scanned)} clip.')
    with u3:
        if st.button('🏷️ Chuẩn hóa tên scene_XX',use_container_width=True): st.session_state.flow_clips=normalize_names(st.session_state.get('flow_clips',[]),pdir); st.success('Đã chuẩn hóa tên clip vào flow_inbox.')
    clips=merge_clips(scan_inbox(pdir),st.session_state.get('flow_clips',[])); miss=missing_scenes(clips,int(expected))
    if clips: st.dataframe(clips,use_container_width=True)
    st.warning('Còn thiếu scene: '+', '.join(map(str,miss))) if miss else st.success('Đủ scene theo số lượng dự kiến.')
    with st.expander('📋 Bảng cấu hình Flow để thao tác trên điện thoại giống ảnh',expanded=False): st.json(flow_settings)
    st.markdown('### 3) Build Final'); output_name=st.text_input('Tên final',value='flow_final.mp4'); vertical=st.checkbox('Thumbnail dọc 9:16',value=True); title_text=st.text_input('Text thumbnail/title',value=(rows[0]['narration'][:60] if rows else 'Flow Assisted Video'))
    if st.button('⚡ Build Final từ clip đã map',type='primary',use_container_width=True):
        try:
            clip_paths=[c['path'] for c in clips if Path(c['path']).exists()]
            if not clip_paths: st.error('Chưa có clip hợp lệ.')
            else:
                raw=concat_videos(pdir,clip_paths,output_name,add_fade); narr=[r.get('narration','') for r in rows] if rows else [title_text]; voice_text=' '.join(narr); voice=tts_edge(pdir,voice_text,voice_label); srt=make_srt(pdir,narr,4); final=mix_audio_subtitles(pdir,raw,voice,srt,burn_sub); base_thumb=thumbnail_from_video(pdir,final); thumb=make_thumbnail(pdir,base_thumb,title_text,thumb_template,vertical); meta={'title':title_text,'caption':voice_text[:400],'hashtags':'#AIVideo #Veo #Shorts #Reels #ViralContent','clips':clips,'created_at':now(),'template':thumb_template,'flow_settings':flow_settings}; package=publish_package(pdir,final,thumb,srt,voice,meta); st.success('Đã build xong final video.'); st.video(final); st.download_button('⬇️ Tải final video',Path(final).read_bytes(),Path(final).name,use_container_width=True); st.image(thumb,caption='Thumbnail',use_container_width=True); st.download_button('📦 Tải publish package',Path(package).read_bytes(),Path(package).name,use_container_width=True)
        except Exception as e: log_error('build_flow_final',e,{'project':project_name}); st.exception(e)
with tab('🏠 Project'):
    st.markdown('## 🏠 Project'); rep=storage_report(project_name); a,b=st.columns(2); a.metric('Project size',f"{rep['total_mb']} MB"); b.metric('Files',rep['files']); c,d=st.columns(2)
    with c:
        if st.button('📦 Export ZIP project',type='primary',use_container_width=True): z=export_zip(project_name); st.download_button('⬇️ Tải ZIP',Path(z).read_bytes(),Path(z).name,use_container_width=True)
    with d:
        if st.button('🛡️ Backup project',use_container_width=True): z=backup_project(project_name); st.download_button('⬇️ Tải backup',Path(z).read_bytes(),Path(z).name,use_container_width=True)
    with st.expander('File lớn nhất',expanded=False): st.json(rep['largest'])
with tab('📊 Dashboard'):
    st.markdown('## 📊 Dashboard'); st.json(storage_report(project_name)); errors=read_errors(50); st.markdown('### Logs'); st.dataframe(errors,use_container_width=True) if errors else st.info('Chưa có log lỗi.')
if has_tab('🖼️ Thumbnail Lab'):
    with tab('🖼️ Thumbnail Lab'):
        st.markdown('## 🖼️ Thumbnail Lab'); upload=st.file_uploader('Ảnh nền hoặc thumbnail base',type=['png','jpg','jpeg','webp']); text=st.text_input('Text thumbnail',value='ĐỪNG LÀM SAI'); template=st.selectbox('Template',list(TEMPLATES.keys())); vertical=st.checkbox('Dọc 9:16',value=True,key='thumb_lab_vertical')
        if st.button('Tạo thumbnail',type='primary'):
            base_path=None
            if upload: base_path=str(pdir/'frames'/upload.name); Path(base_path).parent.mkdir(parents=True,exist_ok=True); upload.seek(0); Path(base_path).write_bytes(upload.read()); upload.seek(0)
            thumb=make_thumbnail(pdir,base_path,text,template,vertical); st.image(thumb,use_container_width=True); st.download_button('⬇️ Tải thumbnail',Path(thumb).read_bytes(),Path(thumb).name)
if has_tab('🧾 Logs'):
    with tab('🧾 Logs'): st.markdown('## 🧾 Logs'); st.dataframe(read_errors(200),use_container_width=True)
if has_tab('🚀 Deploy'):
    with tab('🚀 Deploy'):
        st.markdown('## 🚀 Deploy checklist'); st.json({'app.py':Path('app.py').exists(),'requirements.txt':Path('requirements.txt').exists(),'packages.txt':Path('packages.txt').exists(),'.streamlit/config.toml':Path('.streamlit/config.toml').exists(),'.gitignore':Path('.gitignore').exists()}); st.code('git init\ngit add .\ngit commit -m "AUTO VEO Studio v2.1"\ngit branch -M main\ngit remote add origin https://github.com/YOUR_USERNAME/auto-veo-studio.git\ngit push -u origin main',language='bash')
st.caption('v2.5 Fix Product Upload: thêm setting giống Google Flow mobile để copy prompt và chọn model/tỉ lệ/thời lượng/credit nhanh hơn.')
