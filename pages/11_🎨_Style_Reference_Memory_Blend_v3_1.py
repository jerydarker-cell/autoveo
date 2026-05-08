import streamlit as st
st.set_page_config(page_title='Style Reference + Memory Blend', page_icon='🎨', layout='wide')
st.title('🎨 Style Reference + Memory Blend v3.1')
st.markdown('''
Trong v3.1, app có thêm:

- Style reference upload riêng cho từng project
- AI gợi ý style theo sản phẩm
- Auto map style → prompt wording
- Blend 2 phong cách
- Style memory cho project / video series

Cách dùng nhanh:
1. Upload style references ở sidebar.
2. Chọn style chính và secondary blend style.
3. Lưu style project nếu cần.
4. Trong Viral Director, bấm **AI gợi ý style theo sản phẩm**.
5. Lưu style memory theo series/campaign.
6. Dùng lại style này cho Flow Assisted và Thumbnail Lab.
''')
