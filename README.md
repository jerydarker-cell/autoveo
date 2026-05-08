# AUTO VEO Studio v1.6 — Personal AI Video Studio

Bản này nâng cấp từ prototype thành app cá nhân local-first.

## Có gì mới trong v1.5




### Tối ưu nhỏ v1.5

- Giao diện gọn hơn bằng tùy chọn **Giao diện gọn** ở sidebar.
- Tách thêm các page phụ trong thư mục `pages/`:
  - Deploy Guide
  - API Error Logs
  - Backup Guide
- Thêm backup sang thư mục Google Drive/iCloud/Dropbox/OneDrive local.
- Thêm preset prompt tiếng Việt chuyên ngành.
- Thêm log chi tiết lỗi API/render vào `logs/api_errors.jsonl`.
- Thêm tab Deploy để kiểm tra readiness, storage report và dọn export cũ.
- Thêm `packages.txt` để cài FFmpeg trên Streamlit Cloud.
- Thêm `.gitignore` để không push key/output/backups/logs.

Xem hướng dẫn deploy chi tiết trong `DEPLOY_STREAMLIT.md`.


### Nâng cấp độ bền v1.4

- **Auto backup project**: backup vào thư mục `backups/` khi export và tự tạo daily backup.
- **Retry timeline lỗi**: nếu một số scene lỗi, app lưu lại scene lỗi và có nút retry riêng rồi nối lại final.
- **Prompt quality checker**: chấm điểm prompt trước khi render và báo thiếu chủ thể/bối cảnh/camera/ánh sáng/chuyển động/negative prompt.
- **Final publish package**: đóng gói video final, thumbnail, caption, hashtag, metadata thành ZIP.
- **Model fallback tự động**: nếu model chính lỗi, app thử fast/lite/veo 3 fallback cho text video, timeline scene và script scene.


### Workflow Presets theo nền tảng

Có tab **Workflow Presets** để tạo timeline mẫu một nút:

- TikTok 30s
- YouTube Shorts 60s
- Product Ads 4 cảnh
- Trailer 45s
- Real Estate Tour 48s
- Food Reel 30s

Cách dùng:

1. Chọn preset.
2. Nhập chủ đề/sản phẩm/câu chuyện.
3. Bấm **Gửi sang Timeline Studio**.
4. Qua tab **Timeline Studio** kiểm tra prompt từng cảnh.
5. Bấm render để tạo từng cảnh và nối final video.


### Project Library
- Mỗi project có thư mục riêng trong `projects/`
- Lưu assets: ảnh, video, audio, frame, exports
- Có `project_manifest.json`
- Export ZIP toàn bộ project

### Prompt Library
- Save Prompt
- Favorite Prompt
- Copy Prompt
- Template theo ngành:
  - quảng cáo sản phẩm
  - nhân vật TikTok
  - phim ngắn
  - trailer
  - thời trang
  - bất động sản
  - đồ ăn
  - mỹ phẩm
  - âm nhạc/MV
  - giáo dục

### Retry / Queue / Batch
- Queue lưu SQLite, reload app không mất
- Batch render nhiều prompt
- Retry job
- Retry prompt từ asset cũ
- Chạy từng job hoặc chạy toàn bộ pending tuần tự

### Cost Estimate
- Nhập đơn giá USD/ảnh và USD/giây video
- App tự ước tính trước khi render
- Đây là estimate cá nhân, không phải giá chính thức của Google

### Timeline Video Studio
- Tạo nhiều cảnh
- Mỗi cảnh 4/6/8 giây
- Render từng cảnh
- Nối thành video final
- Có fade-in/fade-out nhẹ nếu máy có ffmpeg

### Auto Script → Shot List → Video
- Dán script dài
- App tự chia shot list
- Tạo keyframe ảnh nếu muốn
- Render từng scene
- Nối video final

### Character Bible nâng cao
- Lưu hồ sơ nhân vật
- Upload ảnh mặt
- Upload ảnh toàn thân
- Upload ảnh outfit/phụ kiện
- Khóa đặc điểm nhân vật để dùng lại

### Audio Studio
- Ghép nhạc nền
- Ghép voice-over
- Tạo SRT từ text
- Gắn phụ đề vào video
- Mix audio bằng ffmpeg

### Video Tools
- Upscale
- Crop center 16:9/9:16
- Blur background để đổi khung
- Compress
- Cắt frame thumbnail

## Cài đặt Windows

Chạy file:

```bat
run_windows.bat
```

Hoặc thủ công:

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Cài đặt MacBook

Chạy:

```bash
chmod +x run_mac.command
./run_mac.command
```

Hoặc thủ công:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## API Key

Tạo file `.env` từ `.env.example`:

```bash
GEMINI_API_KEY=your_key_here
```

Hoặc nhập trực tiếp trong sidebar.

## FFmpeg

Audio Studio, Timeline concat, Video Tools cần ffmpeg.

### Windows
Cách 1: chạy file:

```bat
install_ffmpeg_windows.bat
```

Cách 2: cài bằng winget:

```bat
winget install Gyan.FFmpeg
```

Hoặc tải FFmpeg và thêm vào PATH.

### Mac
Cách 1: chạy file:

```bash
chmod +x install_ffmpeg_mac.command
./install_ffmpeg_mac.command
```

Cách 2: cài bằng Homebrew:

```bash
brew install ffmpeg
```

## Lưu ý

- Chế độ Mock demo không gọi API, dùng để test giao diện.
- Extend Video hoạt động tốt nhất với video object sinh từ Veo trong cùng phiên chạy.
- Đây là app cá nhân local-first, không cần login/credit/admin phức tạp.


## v1.6 — Auto Content Machine

Mục tiêu chính:

```text
Nhập 1 đoạn text
→ tự tạo script/shot list
→ tự tạo voice-over
→ tự tạo subtitle SRT
→ render video từng cảnh
→ nối video final
→ ghép voice/subtitle
→ tạo thumbnail
→ xuất publish package
```

Tab mới: **Auto Content Machine**

Hỗ trợ:

- Tiếng Việt
- English
- Song ngữ Việt-Anh
- Video dọc 9:16
- Video ngang 16:9
- TikTok 30s
- YouTube Shorts 60s
- Reels 30s
- YouTube ngang 48s
- Product Ads 4 cảnh

Niche/style:

- Tài chính
- Lịch sử
- News
- AI/Tech
- Affiliate sản phẩm số
- Affiliate sản phẩm vật lý
- Giáo dục
- Mỹ phẩm

Voice dùng `edge-tts`. Nếu TTS lỗi, app tạo silent voice fallback để pipeline không chết giữa chừng.
