import streamlit as st
st.set_page_config(page_title='Video Grid Guide', page_icon='🎞️', layout='wide')
st.title('🎞️ Video Grid Guide')
st.markdown('''
Bản v3.3 thêm **10 ô video riêng biệt**.

Cách dùng:
1. Vào tab **Video Grid**.
2. Bấm **Nạp prompt từ Viral/Flow** nếu đã tạo prompt trước.
3. Mỗi ô sẽ có prompt riêng, narration riêng, trạng thái riêng.
4. Upload video cho từng ô nếu đã render từ Flow.
5. Bấm **Lưu 10 ô sang Flow Assisted** để build final.
6. Sang tab **Flow Assisted** để nối clip, voice, subtitle, thumbnail.

Màu trạng thái:
- Xám = Chưa làm
- Xanh dương = Sẵn sàng copy
- Vàng = Đang render
- Xanh ngọc = Đã có video
- Đỏ = Lỗi
- Xanh lá = Hoàn tất
''')
