import streamlit as st
st.set_page_config(page_title="Product Prompt Studio", page_icon="🛍️", layout="wide")
st.title("🛍️ Product Prompt Studio Guide")
st.markdown("""
Luồng dùng:

1. Upload ảnh sản phẩm gốc.
2. Chọn mood: Năng động / Hài hước / Truyền cảm hứng.
3. Bật “Có người mẫu sử dụng sản phẩm”.
4. Bật “Xoá sạch chữ trên sản phẩm”.
5. Bấm tạo package.
6. Copy prompt sang Google Flow.
7. Trong Flow, dùng ảnh sản phẩm làm Ingredients/reference image.
8. Chọn Video, 9:16, Veo 3.1 Fast hoặc Quality, 8s.
9. Render, tải clip về, đưa sang Flow Assisted để build final.
""")
