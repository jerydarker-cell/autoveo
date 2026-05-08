import streamlit as st
st.set_page_config(page_title='Prompt Sync Guide', page_icon='🔄', layout='wide')
st.title('🔄 Prompt Sync Guide')
st.markdown('''
Bản v3.2.1 sửa lỗi session_state và thêm Prompt Sync.

Cách dùng:
1. Chuyển sang Advanced.
2. Vào tab **Prompt Sync**.
3. Dán prompt từ ChatGPT/Gemini hoặc upload file prompt.
4. Lưu vào Prompt Bank.
5. Tạo prompt local hoặc gọi Gemini API bằng API key chính thức.
6. Gửi output sang Flow Assisted.

Lưu ý:
- Không lấy cookie tài khoản.
- ChatGPT: copy/paste prompt hoặc upload file export.
- Gemini: dùng GEMINI_API_KEY nếu muốn app gọi API.
''')
