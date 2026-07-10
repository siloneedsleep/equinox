import os

# ==========================================
# 1. TOKENS & CẤU HÌNH BOT
# ==========================================
QUANGIA_TOKEN = os.getenv("QUANGIA_TOKEN")
LUMINOUS_TOKEN = os.getenv("LUMINOUS_TOKEN")
TENEBRIS_TOKEN = os.getenv("TENEBRIS_TOKEN")

# ==========================================
# 2. BẢO MẬT & QUYỀN HẠN
# ==========================================
# ID Discord của bạn (Dành cho lệnh /owner và /bypass)
OWNER_ID = int(os.getenv("OWNER_ID", 0))

# ID Server chính (Bot sẽ tự động ngắt nếu user xài lệnh ở server khác)
MAIN_GUILD_ID = int(os.getenv("MAIN_GUILD_ID", 0))

# ==========================================
# 3. KẾT NỐI KEYDB / REDIS (ĐỒNG BỘ 2 HOST)
# ==========================================
REDIS_URI = os.getenv("REDIS_URI", "redis://localhost:6379")

# ==========================================
# 4. FASTAPI & DISCORD OAUTH2 (CHẠY TRÊN RENDER)
# ==========================================
# Port động do Render cấp (Mặc định 8080 nếu chạy local)
PORT = int(os.getenv("PORT", 8080))

OAUTH2_REDIRECT_URI = os.getenv("OAUTH2_REDIRECT_URI")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
