from __future__ import annotations
from datetime import datetime
import json, zipfile
NICHES={
'AI/marketing/kinh doanh': {'pain':'thiếu ý tưởng, làm nhiều nhưng không có kết quả, sợ tụt lại vì AI','promise':'workflow đơn giản để tạo content nhanh và có chiến lược','visual_style':'studio hiện đại, tone xanh đen, hologram, laptop, dashboard, faceless B-roll'},
'Tài chính cá nhân': {'pain':'mất tiền vì tiêu sai, đầu tư theo cảm xúc, thiếu kế hoạch','promise':'hiểu tiền bạc dễ hơn và tránh lỗi phổ biến','visual_style':'chart tài chính, ví tiền, thành phố, navy/yellow, clean infographic'},
'Lịch sử': {'pain':'muốn hiểu sự kiện lớn nhưng không thích nội dung dài khô','promise':'biến lịch sử thành câu chuyện điện ảnh dễ nhớ','visual_style':'historical reenactment, bản đồ cổ, dramatic lighting, cinematic texture'},
'News': {'pain':'quá nhiều thông tin, không biết điểm chính','promise':'tóm tắt ngắn, trung lập, dễ hiểu, có bối cảnh','visual_style':'newsroom hiện đại, city B-roll, abstract graphics, documentary style'},
'AFF sản phẩm số': {'pain':'mất thời gian, tool rời rạc, không biết chọn gì','promise':'review/workflow giúp tiết kiệm thời gian và tăng hiệu suất','visual_style':'dashboard mockup, laptop, workspace creator, clean UI'},
'AFF sản phẩm vật lý': {'pain':'không biết sản phẩm có đáng tiền không','promise':'review tự nhiên theo vấn đề-lợi ích-kết quả','visual_style':'product close-up, lifestyle usage, macro detail, commercial lighting'},
}
FORMATS=['kể chuyện','danh sách','hướng dẫn','case study','so sánh trước-sau','myth busting','review','giải thích đơn giản']
def score_idea(idea):
    hook=idea.get('first_3s_hook',''); retention=idea.get('retention_reason',''); fmt=idea.get('content_format',''); thumb=idea.get('thumbnail_idea',''); insight=idea.get('psychological_insight','')
    hook_score=50+min(30,len(hook)*.9)+(12 if any(x in hook.lower() for x in ['đừng','sai','lỗi','99','bỏ qua']) else 0)
    retention_score=45+min(35,len(retention)*.35)+(12 if any(x in retention.lower() for x in ['ví dụ','loop','tò mò','ngắt']) else 0)
    faceless_score=92 if idea.get('faceless') or 'faceless' in fmt.lower() else 58
    diff=max(10,min(100,38-(10 if any(x in fmt.lower() for x in ['faceless','danh sách','hướng dẫn']) else 0)))
    thumbnail_score=45+min(35,len(thumb)*.25)+(10 if any(x in thumb.lower() for x in ['đừng','3','sai']) else 0)
    insight_score=45+min(40,len(insight)*.25)+(10 if any(x in insight.lower() for x in ['sợ','muốn','pain','quan tâm']) else 0)
    viral=hook_score*.28+retention_score*.24+faceless_score*.14+thumbnail_score*.14+insight_score*.16+(100-diff)*.04
    return {'hook_score':round(min(100,hook_score),1),'retention_score':round(min(100,retention_score),1),'faceless_ease_score':round(min(100,faceless_score),1),'production_difficulty':round(diff,1),'thumbnail_score':round(min(100,thumbnail_score),1),'insight_score':round(min(100,insight_score),1),'viral_potential':round(min(100,viral),1)}
def make_ideas(topic, platform, niche, faceless=True):
    pack=NICHES[niche]; hooks=['Đừng làm điều này nếu bạn mới bắt đầu.','99% người mới bỏ qua điểm này.','Một lỗi nhỏ có thể khiến bạn mất rất nhiều thời gian.','Nếu chỉ có 30 giây, hãy nhớ điều này.','Đây là phần người ta thường không nói với bạn.','Trước khi bạn thử, hãy xem ví dụ này.','Điều này nghe đơn giản nhưng cực kỳ dễ sai.','Tôi sẽ giải thích bằng một ví dụ rất dễ hiểu.','Nếu muốn kết quả nhanh hơn, bắt đầu từ đây.','Một thay đổi nhỏ tạo khác biệt rất lớn.']
    titles=[f'Đừng mắc lỗi này khi làm {topic}',f'3 sự thật về {topic} mà người mới thường bỏ qua',f'Cách hiểu {topic} trong 60 giây',f'{topic}: ví dụ đơn giản khiến bạn nhớ ngay',f'Trước khi bắt đầu {topic}, hãy xem điều này',f'Vì sao nhiều người làm {topic} nhưng không có kết quả',f'Một framework ngắn để làm {topic} tốt hơn',f'So sánh cách cũ và cách mới khi làm {topic}',f'Bài học đắt giá từ {topic}',f'Nếu bắt đầu lại với {topic}, tôi sẽ làm 3 việc này']
    ideas=[]
    for i in range(10):
        idea={'id':i+1,'title':titles[i],'psychological_insight':f"Người xem quan tâm vì họ đang {pack['pain']} và muốn {pack['promise']}.",'first_3s_hook':hooks[i],'content_format':FORMATS[i%len(FORMATS)]+(' / faceless B-roll' if faceless else ' / AI host'),'retention_reason':'Hook gây tò mò, đoạn ngắn, thay đổi hình ảnh liên tục, có ví dụ thực tế và loop ending.','thumbnail_idea':f"Chữ nổi: ‘ĐỪNG LÀM SAI’, ‘3 ĐIỀU CẦN BIẾT’; visual: {pack['visual_style']}.",'faceless':faceless,'platform':platform,'niche':niche}
        idea.update(score_idea(idea)); ideas.append(idea)
    return sorted(ideas,key=lambda x:x['viral_potential'],reverse=True)
def make_blueprint(topic, platform, niche, faceless, host, minutes):
    ideas=make_ideas(topic,platform,niche,faceless); selected=ideas[0]
    beats=[{'time':'0:00-0:05','type':'HOOK','text':f"{selected['first_3s_hook']} Nếu hiểu sai điểm này, toàn bộ chiến lược về {topic} có thể đi lệch."},{'time':'0:05-0:25','type':'VẤN ĐỀ','text':f'Hầu hết mọi người tiếp cận {topic} bằng cảm tính.'},{'time':'0:25-0:50','type':'VÍ DỤ','text':f'Hai người cùng làm {topic}: một người copy công thức, một người hiểu insight.'},{'time':'0:50-1:15','type':'NGẮT NHỊP','text':'Điểm ngắt nhịp: thứ tạo ra kết quả thường không phải công cụ, mà là cách bạn đặt vấn đề.'},{'time':'1:15-1:50','type':'GIẢI PHÁP','text':'Viết rõ người xem là ai, họ đau ở đâu và cần câu trả lời nào nhanh nhất.'},{'time':'1:50-2:20','type':'GIẢI PHÁP','text':'Chia nội dung thành đoạn ngắn. Mỗi 20-30 giây phải có hình ảnh mới hoặc ví dụ mới.'},{'time':'2:20-2:45','type':'CTA','text':'Lưu video này lại nếu bạn muốn dùng cấu trúc này cho nhiều nội dung.'},{'time':'2:45-3:10','type':'LOOP ENDING','text':f'Quay lại câu đầu tiên: đừng làm {topic} nếu chưa biết người xem quan tâm điều gì.'}]
    motions=['fast push-in','slow dolly','macro close-up','side tracking','top-down insert','wide establishing']; trans=['whip pan','match cut','zoom cut','glitch light','soft fade','speed ramp']; visual=NICHES[niche]['visual_style']
    shots=[]
    for idx,b in enumerate(beats,1):
        broll='abstract B-roll, kinetic text, icons, UI mockups, hands typing, charts' if faceless else f'AI host: {host}'
        shots.append({'scene':idx,'time':b['time'],'beat_type':b['type'],'voiceover':b['text'],'camera_motion':motions[idx%len(motions)],'transition':trans[idx%len(trans)],'text_overlay':b['type']+' · '+b['text'][:52],'broll_or_host':broll,'flow_prompt':f"{b['text']}\nVisual: {visual}. {broll}. Camera: cinematic {motions[idx%len(motions)]}. No watermark, no unreadable text."})
    script={'title':selected['title'],'beats':beats,'voiceover':'\n'.join(b['text'] for b in beats),'loop_ending':beats[-1]['text']}
    opt={'top_3_titles':[f'Đừng làm {topic} nếu chưa biết điều này',f'3 lỗi khiến {topic} không có kết quả',f'Cách làm {topic} dễ hiểu hơn trong 3 phút'],'hashtags':['#AIVideo','#ContentStrategy','#Shorts','#Reels','#Marketing','#ViralContent'],'ab_hooks':[f'Đừng bắt đầu {topic} nếu chưa trả lời câu này.',f'Đây là lý do 90% người làm {topic} bị kẹt.',f'Một thay đổi nhỏ làm {topic} dễ hơn rất nhiều.']}
    return {'created_at':datetime.now().isoformat(timespec='seconds'),'topic':topic,'platform':platform,'niche':niche,'ideas':ideas,'selected_idea':selected,'script':script,'shots':shots,'optimization':opt}
def export_blueprint_zip(project_dir, blueprint):
    out_dir=project_dir/'exports'/f"viral_blueprint_{datetime.now().strftime('%Y%m%d_%H%M%S')}"; out_dir.mkdir(parents=True,exist_ok=True)
    (out_dir/'viral_blueprint.json').write_text(json.dumps(blueprint,ensure_ascii=False,indent=2),encoding='utf-8')
    (out_dir/'script_voiceover.txt').write_text(blueprint['script']['voiceover'],encoding='utf-8')
    (out_dir/'flow_prompts.txt').write_text('\n\n---\n\n'.join(s['flow_prompt'] for s in blueprint['shots']),encoding='utf-8')
    zp=project_dir/'exports'/f"viral_blueprint_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    with zipfile.ZipFile(zp,'w',zipfile.ZIP_DEFLATED) as z:
        for p in out_dir.rglob('*'): z.write(p,arcname=p.relative_to(out_dir))
    return str(zp)
