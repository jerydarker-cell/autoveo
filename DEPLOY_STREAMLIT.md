# Hướng dẫn đưa AUTO VEO Studio lên GitHub + Streamlit Community Cloud

## 0. Bản này đã chuẩn bị sẵn gì?

Repo có sẵn:

```text
app.py
requirements.txt
packages.txt
README.md
DEPLOY_STREAMLIT.md
.gitignore
.env.example
.streamlit/config.toml
pages/
src/
```

Trong đó:

- `requirements.txt`: Python dependencies.
- `packages.txt`: system package cho Streamlit Cloud, có `ffmpeg`.
- `.gitignore`: tránh đưa `.env`, output, backups, logs lên GitHub.
- `pages/`: các page phụ, giúp app gọn hơn.

Theo tài liệu Streamlit, app deploy cần dependency file như `requirements.txt`; system dependencies có thể khai báo trong `packages.txt`; secrets nên cấu hình qua giao diện Secrets của Community Cloud, không hard-code trong repo.

## 1. Test local trước

### Windows

```bat
run_windows.bat
```

### MacBook

```bash
chmod +x run_mac.command
./run_mac.command
```

Mở sidebar, kiểm tra:

```text
google-genai: OK
ffmpeg: OK
```

Nếu FFmpeg chưa có:

Windows:

```bat
install_ffmpeg_windows.bat
```

Mac:

```bash
chmod +x install_ffmpeg_mac.command
./install_ffmpeg_mac.command
```

## 2. Tạo repo GitHub

1. Vào GitHub.
2. Bấm **New repository**.
3. Đặt tên, ví dụ: `auto-veo-studio`.
4. Chọn **Private** nếu chỉ dùng cá nhân.
5. Không cần tick README/gitignore vì project đã có.
6. Bấm **Create repository**.

## 3. Đẩy code lên GitHub

Mở Terminal/CMD trong thư mục project:

```bash
git init
git add .
git commit -m "Initial AUTO VEO Studio"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/auto-veo-studio.git
git push -u origin main
```

Thay `YOUR_USERNAME` bằng username GitHub của bạn.

Nếu Git hỏi login, dùng GitHub login hoặc personal access token.

## 4. Deploy trên Streamlit Community Cloud

1. Vào Streamlit Community Cloud.
2. Đăng nhập bằng GitHub.
3. Bấm **Create app** hoặc **New app**.
4. Chọn repo `auto-veo-studio`.
5. Branch: `main`.
6. Main file path: `app.py`.
7. App URL: đặt tên tùy ý.
8. Python version: chọn **3.11** hoặc **3.12** nếu giao diện có tùy chọn.
9. Bấm **Deploy**.

## 5. Thêm Gemini API key vào Secrets

Không commit `.env` lên GitHub.

Trong Streamlit Cloud:

1. Mở app.
2. Vào **Settings**.
3. Chọn **Secrets**.
4. Thêm:

```toml
GEMINI_API_KEY = "your_gemini_api_key_here"
```

5. Save.
6. Reboot app.

## 6. Lưu ý khi chạy trên Streamlit Cloud

Streamlit Cloud phù hợp demo/cá nhân nhẹ, nhưng không phải ổ lưu trữ video lâu dài.

Nên nhớ:

- Render video có thể tốn tài nguyên và thời gian.
- Không render quá nhiều job song song.
- File local trên cloud có thể mất khi app ngủ/redeploy.
- Luôn dùng **Export ZIP project** hoặc backup sang Drive/iCloud khi chạy local.
- Nếu FFmpeg lỗi, kiểm tra `packages.txt` có đúng dòng `ffmpeg`.

## 7. Cập nhật app sau này

Sau khi sửa code:

```bash
git add .
git commit -m "Update AUTO VEO Studio"
git push
```

Streamlit Cloud thường tự redeploy khi repo có commit mới.

## 8. Lỗi thường gặp

### ModuleNotFoundError

Thiếu package trong `requirements.txt`.

Sửa bằng cách thêm package còn thiếu vào `requirements.txt`, commit và push lại.

### FFmpeg not found

Đảm bảo có file `packages.txt` ở root repo:

```text
ffmpeg
```

Sau đó reboot/redeploy.

### API key không đọc được

Kiểm tra Secrets:

```toml
GEMINI_API_KEY = "..."
```

Không để dấu phẩy, không dùng `.env` trên Cloud.

### App nặng/chậm

Dọn:

- project exports cũ
- video mock cũ
- backup cũ
- logs cũ

Trong app có tab **Deploy** để xem storage report và dọn ZIP export cũ.
