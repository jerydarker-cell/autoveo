import streamlit as st
st.set_page_config(page_title='Video Grid Pro v3.4', page_icon='🎞️', layout='wide')
st.title('🎞️ Video Grid Pro v3.4')
st.markdown('''
v3.4 thêm:

- Copy Prompt cho từng ô
- Mở Flow cho từng ô
- Đổi thứ tự scene bằng bảng order
- Progress bar tự động
- Lọc ô lỗi / chưa làm / hoàn tất

Cách dùng:
1. Vào **Video Grid**.
2. Nạp prompt từ Viral/Flow hoặc nhập prompt riêng từng ô.
3. Bấm **Copy Prompt** rồi dán vào Google Flow.
4. Bấm **Mở Flow** để mở Flow nhanh.
5. Upload video về đúng từng ô.
6. Bấm **Lưu 10 ô sang Flow Assisted** để build final.
''')
