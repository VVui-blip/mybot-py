# Nhan — Discord Bot

Bot Discord đa chức năng: tra cứu ScriptBlox, Roblox, GitHub, Minecraft, tin tức,
YouTube, nhạc, hồ sơ Discord và trợ lý AI.

## Cấu trúc dự án

```
.
├── main.py                     # Điểm khởi chạy: khởi tạo bot & đăng ký slash command
├── bot/
│   ├── ai_assistant.py         # Trợ lý AI (Groq) — lệnh /assistant
│   ├── web_search.py           # Công cụ tìm kiếm web hỗ trợ AI assistant
│   └── views/                  # UI (Embed + View) cho từng lệnh
│       ├── scriptblox_view.py
│       ├── roblox_user_view.py
│       ├── roblox_asset_view.py
│       ├── roblox_animation_view.py
│       ├── github_view.py
│       ├── minecraft_view.py
│       ├── music_view.py
│       ├── news_view.py
│       ├── youtube_view.py
│       ├── discord_profile_view.py
│       ├── credit_view.py
│       └── help_view.py
├── config/                     # Dữ liệu cấu hình tĩnh (không chứa bí mật)
│   ├── credits.txt             # Danh sách team/role cho lệnh /credits
│   ├── emojis.txt              # Emoji dùng trong phản hồi AI
│   └── ai_functions.txt        # Mô tả function-calling cho AI
├── data/                       # Dữ liệu runtime
│   ├── animations.json         # Cơ sở dữ liệu animation Roblox
│   ├── conversations.json      # Lịch sử hội thoại AI theo user
│   └── cache/
│       └── music_cache.json    # Cache kết quả tìm nhạc
├── requirements.txt
├── .env.example                # Mẫu biến môi trường (copy thành .env)
├── .gitignore
└── token.txt                   # Token bot (KHÔNG commit — xem phần Bảo mật)
```

## Cài đặt

```bash
pip install -r requirements.txt
cp .env.example .env   # rồi điền giá trị thật vào .env
```

Biến môi trường cần thiết (xem `.env.example`):

| Biến             | Dùng cho                                   |
|------------------|---------------------------------------------|
| `DISCORD_TOKEN`  | Token bot Discord (bắt buộc)                |
| `GROQ_API_KEY`   | Trợ lý AI `/assistant` (bắt buộc)           |
| `SERPER_API_KEY` | Công cụ tìm kiếm web cho AI assistant       |
| `SERPAPI_KEY`    | Lệnh `/news` và `/youtubevideo`             |

## Chạy bot

```bash
python main.py
```

`DISCORD_TOKEN` được ưu tiên đọc từ biến môi trường. Nếu không có, bot sẽ
đọc từ file `token.txt` ở thư mục gốc (tiện cho phát triển local).

## Bảo mật — quan trọng

File zip gốc bạn gửi có chứa **token Discord thật** trong `token.txt` và
**2 API key SerpApi hardcode thẳng trong code** (`news_view.py`,
`youtube_view.py`). Cả ba đã bị lộ ra ngoài (nằm trong file bạn tải lên).

Bạn nên coi các key này là đã bị lộ và **thu hồi / tạo lại ngay**:
- Discord: Developer Portal → Application → Bot → Reset Token
- SerpApi: đổi API key trong dashboard SerpApi
- Groq: kiểm tra và xoay vòng key nếu từng bị commit lên nơi công khai

Trong bản chỉnh sửa này, hai key SerpApi đã được chuyển sang đọc từ biến
môi trường giống các key khác. `token.txt` và `.env` đã được thêm vào
`.gitignore` để không bao giờ bị commit lên Git.

## Ghi chú

- Cấu trúc này giữ nguyên toàn bộ logic gốc, chỉ đổi tên file/thư mục và
  đường dẫn import cho rõ ràng, dễ bảo trì hơn.
- Có thể tách tiếp các slash command trong `main.py` thành `bot/commands.py`
  hoặc dùng Cog của discord.py nếu muốn mở rộng thêm nhiều lệnh sau này.
