import streamlit as st
st.set_page_config(page_title="Thumbnail Flow Panel", page_icon="🖼️", layout="wide")
st.title("🖼️ Thumbnail Flow Panel Guide")
st.markdown("""
Tab Thumbnail Lab có panel giống Google Flow Image:

1. Upload ảnh sản phẩm/reference nếu có.
2. Chọn Image.
3. Chọn tỉ lệ: 16:9 / 4:3 / 1:1 / 3:4 / 9:16.
4. Chọn số bản: 1x-4x.
5. Chọn model: Nano Banana Pro, Nano Banana 2, Imagen 4.
6. Copy prompt thumbnail sang Google Flow.
7. Tải setting JSON để lưu cấu hình.
8. Có thể tạo thumbnail local ngay trong app.
""")
