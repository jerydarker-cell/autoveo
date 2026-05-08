import streamlit as st
st.set_page_config(page_title='Final Render Settings v3.5', page_icon='🎬', layout='wide')
st.title('🎬 Final Render Settings v3.5')
st.markdown('''
v3.5 thêm cấu hình khi nối nhiều clip:

- Mỗi clip bao nhiêu giây
- Tỉ lệ khung: 9:16, 16:9, 1:1, 4:5, 3:4
- Độ phân giải: 720, 1080, 2000
- FPS: 24, 30, 60
- Chế độ khung: giữ đủ hình hoặc crop kín khung
- Chuẩn hóa clip trước khi nối

Luồng:
1. Render clip trong Google Flow.
2. Upload clip vào app.
3. Chọn final render settings.
4. Build Final.
''')
