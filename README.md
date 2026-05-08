# AUTO VEO Studio v2.0 — Clean UX

Bản v2.0 tập trung vào dùng hằng ngày thật mượt:

- Tách code thật ra `src/`
- Giao diện Simple / Advanced
- Viral Director có chấm điểm idea
- Flow Assisted Mode + Flow Inbox thông minh hơn
- Upload nhiều clip, auto map `scene_01.mp4`
- Báo thiếu scene
- Chuẩn hóa tên file
- Thumbnail template đẹp hơn
- Build final video + voice + subtitle + thumbnail + publish package

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

## Quy trình tốt nhất

1. Vào **Viral Director**.
2. Tạo blueprint viral.
3. Bấm gửi prompt sang Flow Assisted.
4. Copy prompt sang Google Flow.
5. Render bằng credit Flow/Veo.
6. Tải clip về, đặt tên `scene_01.mp4`, `scene_02.mp4`.
7. Upload nhiều clip hoặc bỏ vào `flow_inbox`.
8. Build Final.

## Cấu trúc code

```text
src/
  project.py
  viral.py
  flow.py
  media.py
  tts.py
  thumbnails.py
app.py
```

Bản này cố ý lược bớt các tab API nặng để chạy mượt, dễ bảo trì và dễ dùng hơn.
