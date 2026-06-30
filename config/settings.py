import os
import json
from dotenv import load_dotenv

# Ưu tiên load .env nếu có
load_dotenv()

def get_config():
    # Thử đọc từ config.json trước (Tiện cho Pterodactyl File Manager)
    config_path = "config.json"
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                content = f.read()
                # Loại bỏ khoảng trắng thừa và xử lý lỗi ký tự điều khiển
                return json.loads(content, strict=False)
        except Exception as e:
            print(f"[Warning] Lỗi định dạng config.json tại '{config_path}': {e}")
            print("[System] Hệ thống sẽ chuyển sang sử dụng Biến môi trường (Environment Variables).")
            return {}
    return {}

_c = get_config()

# Discord Bot Tokens
LUMINOUS_TOKEN = os.getenv("LUMINOUS_TOKEN") or _c.get("luminous_token")
TENEBRIS_TOKEN = os.getenv("TENEBRIS_TOKEN") or _c.get("tenebris_token")
QUANGIA_TOKEN = os.getenv("QUANGIA_TOKEN") or _c.get("quangia_token")
JULES_TOKEN = os.getenv("JULES_TOKEN") or _c.get("jules_token")

# OAuth2 Credentials
LUMINOUS_CLIENT_ID = os.getenv("LUMINOUS_CLIENT_ID") or _c.get("luminous_client_id")
LUMINOUS_CLIENT_SECRET = os.getenv("LUMINOUS_CLIENT_SECRET") or _c.get("luminous_client_secret")
TENEBRIS_CLIENT_ID = os.getenv("TENEBRIS_CLIENT_ID") or _c.get("tenebris_client_id")
TENEBRIS_CLIENT_SECRET = os.getenv("TENEBRIS_CLIENT_SECRET") or _c.get("tenebris_client_secret")

OAUTH2_REDIRECT_URI = os.getenv("OAUTH2_REDIRECT_URI") or _c.get("oauth2_redirect_uri")

# Infrastructure (Hỗ trợ Render, Railway, Pterodactyl)
REDIS_URI = os.getenv("REDIS_URI") or _c.get("redis_uri", "redis://localhost:6379")
# Ưu tiên PORT (Render/Railway), sau đó SERVER_PORT (Pterodactyl), mặc định 3000
PORT = int(os.getenv("PORT") or os.getenv("SERVER_PORT") or _c.get("port", 3000))

# System Configuration
OWNER_ID = int(os.getenv("OWNER_ID") or _c.get("owner_id", 0))
MAIN_GUILD_ID = int(os.getenv("MAIN_GUILD_ID") or _c.get("main_guild_id", 0))

# Colors & Shifts
COLOR_LUMINOUS = 0xFCE883
COLOR_TENEBRIS = 0x2B2D31
LUMINOUS_SHIFT_START = "06:00"
TENEBRIS_SHIFT_START = "18:00"
