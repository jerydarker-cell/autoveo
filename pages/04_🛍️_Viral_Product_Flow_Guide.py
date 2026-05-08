import streamlit as st
st.set_page_config(page_title="Viral Product Flow", page_icon="🛍️", layout="wide")
st.title("🛍️ Viral Product Flow Guide")
st.markdown("""
Luồng mới v2.3:

1. Vào **Viral Director**.
2. Upload ảnh sản phẩm ngay trong Viral Director.
3. Chọn mood nhạc: Năng động / Hài hước / Truyền cảm hứng.
4. Bấm tạo Product Concept + 3 Prompt.
5. Xem concept, shot list, voiceover.
6. Gửi prompt sang **Flow Assisted**.
7. Copy prompt sang Google Flow.
8. Trong Flow, upload ảnh sản phẩm làm Ingredients/reference image.
9. Render video bằng credit Flow/Veo.
10. Tải clip về và build final trong app.
""")
