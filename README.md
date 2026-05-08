# AUTO VEO Studio v3.2 — Flow Quick Controls

Bản v2.1 tập trung vào workflow Flow trên điện thoại giống ảnh bạn gửi.

## Có gì mới

- Cụm **Flow Quick Settings** trong Flow Assisted.
- Image / Video.
- Text / Frames / Ingredients.
- 9:16 / 16:9.
- 1x / 2x / 3x / 4x.
- Veo 3.1 Lite / Fast / Quality / Lower Priority.
- 4s / 6s / 8s.
- Generate / Extend / Insert / Remove / Camera.
- Ước tính credit/scene và tổng credit dự kiến.
- Tự thêm suffix setting vào prompt từng scene.
- Tải `flow_settings.json`.

## Cách dùng

1. Vào **Viral Director** tạo blueprint.
2. Vào **Flow Assisted** chọn setting giống Google Flow.
3. Copy prompt sang Flow.
4. Chọn đúng model/tỉ lệ/thời lượng/số bản như trong app.
5. Render bằng credit Flow.
6. Upload clip về app hoặc bỏ vào `flow_inbox`.
7. Build Final.

## Chạy local

Windows:

```bat
run_windows.bat
```

Mac:

```bash
chmod +x run_mac.command
./run_mac.command
```


## v2.2 — Product Prompt Studio

Thêm tab **Product Prompt Studio**:

```text
Upload ảnh sản phẩm
→ tự tạo concept
→ tự tạo kịch bản 8s
→ chọn mood nhạc
→ xuất 3 prompt Flow/Veo
→ gửi prompt sang Flow Assisted
```

Có các rule cố định:

- Dùng ảnh sản phẩm upload làm reference duy nhất.
- Giữ nguyên hình dáng, màu sắc, chất liệu, tỷ lệ, silhouette.
- Không tự vẽ lại, không biến tấu, không thay sản phẩm.
- Xoá sạch chữ trên sản phẩm để tránh lỗi text.
- Không text overlay.
- Không subtitle.
- Không chữ trong môi trường.
- Không chữ chạy, không chữ dính vào vật thể/người mẫu.

Mood nhạc:

- Năng động
- Hài hước
- Truyền cảm hứng

Output:

- Concept tổng
- Shot list 8s
- Voiceover tiếng Việt
- 3 prompt Flow/Veo
- Product Prompt Package ZIP


## v2.3 — Viral Product Flow

Đã đưa chức năng Product Upload vào ngay tab **Viral Director**.

Luồng mới:

```text
Viral Director
→ Upload ảnh sản phẩm
→ tạo concept/kịch bản 8s
→ chọn mood nhạc
→ xuất 3 prompt Flow/Veo
→ gửi prompt sang Flow Assisted
→ copy prompt sang Google Flow
```

Product Prompt Studio vẫn còn như tab riêng để dùng độc lập, nhưng luồng chính giờ nằm trong Viral Director.


## v2.4 — Product Inside Viral Director

Bản này sửa đúng lỗi: Product Upload đã nằm ngay trong tab **Viral Director**.

Có trong Viral Director:

- Upload ảnh sản phẩm gốc
- Tên sản phẩm
- Loại sản phẩm
- Khách hàng mục tiêu
- Mood nhạc/cảm xúc
- Mục tiêu video sản phẩm
- Có người mẫu sử dụng sản phẩm
- Xoá sạch chữ trên sản phẩm / cấm text overlay
- Tạo concept chiến lược sản phẩm
- Tạo shot list 8s
- Xuất 3 prompt Flow/Veo
- Gửi prompt 1 hoặc cả 3 prompt sang Flow Assisted

Luồng:

```text
Viral Director
→ Upload ảnh sản phẩm
→ Tạo Concept + Kịch bản 8s + 3 Prompt Flow
→ Gửi sang Flow Assisted
→ Copy prompt sang Google Flow
→ Render bằng credit Flow/Veo
→ Upload clip về app
→ Build Final
```


## v2.5 — Fix Product Upload

Sửa lỗi:

```text
NameError: name 're' is not defined
```

Nguyên nhân: khu Upload ảnh sản phẩm dùng `re.sub()` để làm sạch tên file nhưng thiếu `import re`.

Bản v2.5 đã thêm:

- `import re`
- `safe_filename()`
- thay các đoạn xử lý tên file upload sang helper an toàn hơn
- kiểm tra compile lại toàn bộ app và modules

Luồng Product Upload trong Viral Director giữ nguyên.


## v2.6 — Thumbnail Flow Panel

Nâng cấp tab **Thumbnail Lab** giống panel Google Flow Image:

- Image / Video
- Text / Reference image
- 16:9 / 4:3 / 1:1 / 3:4 / 9:16
- 1x / 2x / 3x / 4x
- Nano Banana Pro
- Nano Banana 2
- Imagen 4
- Imagen 4 Ultra
- Ước tính credit
- Tạo prompt thumbnail cho Flow Image
- Tải `thumbnail_flow_settings.json`
- Vẫn tạo được thumbnail local bằng template có sẵn

Mục tiêu: chuẩn bị nhanh prompt + setting cho thumbnail trong Google Flow.


## v2.7 — Style Presets

Thêm **Phong cách tạo ảnh** trong tab **Thumbnail Lab**.

Style mới:

- Cyberpunk
- Realistic Commercial
- Luxury Premium
- Minimal Clean
- Cute Pastel
- Futuristic Tech
- Cinematic Dark
- Street Hype

Ngoài ra, local thumbnail templates cũng được thêm:

- cyberpunk neon
- futuristic blue
- luxury gold
- minimal clean
- cute pastel

Prompt thumbnail cho Google Flow giờ sẽ bám theo style preset đã chọn.


## v2.8 — Global Style Sync

Đã đồng bộ style toàn app.

### Mới trong sidebar
- `Global style preset`

### Áp dụng cho
- Product Upload trong Viral Director
- Flow Assisted / Flow Quick Settings
- Thumbnail Lab

### Các style
- Cyberpunk
- Realistic Commercial
- Luxury Premium
- Minimal Clean
- Cute Pastel
- Futuristic Tech
- Cinematic Dark
- Street Hype

### Kết quả
- Prompt sản phẩm tự bám theo style đã chọn
- Flow settings suffix tự kèm style preset
- Thumbnail prompt tự kèm style preset


## v2.9 — Style Lock + Preview Cards

Thêm nâng cấp style rất đáng làm:
- Style preview card trực quan
- Mỗi style có preview mini và palette màu mẫu
- Preset màu theo style
- Lock style cho toàn bộ project
- Lưu style vào `project_style.json`

Áp dụng cho:
- Viral Director
- Product Upload
- Flow Assisted
- Thumbnail Lab
- Project tab


## v3.0 — Style Gallery + UI Theme Sync

Đã thêm:
- style gallery đẹp hơn
- preset ảnh mẫu cho từng style
- nút apply style 1 chạm
- style consistency score
- project theme full UI đồng bộ theo style

Điểm nổi bật:
- tab **Style Gallery** mới
- ảnh mẫu preset được tạo tự động trong thư mục `style_samples/`
- có nút **Apply** và **Apply + Lock** cho từng style
- có `style consistency score` để kiểm tra độ đồng bộ giữa Project / Flow / Product / Thumbnail
- giao diện app tự đổi theme theo style đang chọn


## v3.1 — Style Reference + Memory Blend

Đã thêm:

- style reference upload riêng cho từng project
- AI tự gợi ý style phù hợp theo sản phẩm
- auto map style → prompt wording
- style blend 2 phong cách
- style memory cho từng project / video series

### Điểm mới chính

**1. Style reference upload**
- Upload nhiều ảnh style reference vào project
- Lưu trong thư mục `style_references/`
- Prompt có thể tự chèn phần mô tả sử dụng style references như nguồn cảm hứng visual

**2. AI gợi ý style theo sản phẩm**
- Dựa vào tên sản phẩm, loại sản phẩm, mood và target
- Gợi ý cặp style ví dụ:
  - Cyberpunk + Futuristic Tech
  - Luxury Premium + Minimal Clean
  - Street Hype + Luxury Premium

**3. Auto map style → prompt wording**
- Tự chèn style wording, palette wording và reference summary vào:
  - Product Prompt
  - Flow Assisted suffix
  - Thumbnail Lab prompt

**4. Style blend 2 phong cách**
- Có `Global style preset` + `Secondary blend style`
- Áp dụng blend cho toàn app

**5. Style memory**
- Lưu style theo `series / campaign`
- Ghi nhớ primary style, secondary style, notes, lock state, reference files
- Lưu trong `style_memory.json`


## v3.2 — Smart Style AI + 3-Way Blend

Đã thêm:

- AI đọc ảnh style reference theo cách local heuristic để gợi ý style chính xác hơn
- Blend 3 phong cách: primary + secondary + third style
- Style ranking theo sản phẩm
- Nút Apply suggestion 1 chạm
- Tự sinh prompt mẫu theo từng series

### Style reference vision
App phân tích ảnh reference đã upload bằng các tín hiệu:
- brightness
- saturation
- dark / clean / pastel / neon / luxury hints

### Style ranking
Trong Viral Director, khi bấm **AI gợi ý style theo sản phẩm**, app hiển thị bảng ranking style với điểm và lý do.

### Apply suggestion 1 chạm
Nút **Apply suggestion 1 chạm** lưu ngay combo style gợi ý vào project.

### Series prompt pack
Sidebar có nút sinh `series_prompt_pack.json` theo style hiện tại và series/campaign đang chọn.
