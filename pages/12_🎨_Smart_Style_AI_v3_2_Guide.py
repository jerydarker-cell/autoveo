import streamlit as st
st.set_page_config(page_title='Smart Style AI v3.2', page_icon='🎨', layout='wide')
st.title('🎨 Smart Style AI v3.2')
st.markdown('''
v3.2 thêm:

- AI đọc ảnh style reference bằng local heuristic
- Blend 3 phong cách
- Style ranking theo sản phẩm
- Apply suggestion 1 chạm
- Series prompt pack tự sinh

Cách dùng:
1. Upload style reference ở sidebar.
2. Chọn Global style, Secondary blend, Third blend.
3. Vào Viral Director.
4. Nhập sản phẩm và bấm **AI gợi ý style theo sản phẩm**.
5. Xem bảng ranking.
6. Bấm **Apply suggestion 1 chạm**.
7. Sinh Product Prompt hoặc Flow/Thumbnail như bình thường.
''')
