import os
from dotenv import load_dotenv

load_dotenv()

# Discord Bot Tokens
LUMINOUS_TOKEN = os.getenv("LUMINOUS_TOKEN")
TENEBRIS_TOKEN = os.getenv("TENEBRIS_TOKEN")

# OAuth2 Credentials
LUMINOUS_CLIENT_ID = os.getenv("LUMINOUS_CLIENT_ID")
LUMINOUS_CLIENT_SECRET = os.getenv("LUMINOUS_CLIENT_SECRET")

TENEBRIS_CLIENT_ID = os.getenv("TENEBRIS_CLIENT_ID")
TENEBRIS_CLIENT_SECRET = os.getenv("TENEBRIS_CLIENT_SECRET")

OAUTH2_REDIRECT_URI = os.getenv("OAUTH2_REDIRECT_URI")

# Infrastructure
REDIS_URI = os.getenv("REDIS_URI", "redis://localhost:6379")
PORT = int(os.getenv("PORT", 8000))

# System Configuration
OWNER_ID = int(os.getenv("OWNER_ID", 0))
MAIN_GUILD_ID = int(os.getenv("MAIN_GUILD_ID", 0))

# Default Links
DEFAULT_MAIN_SERVER_LINK = os.getenv("DEFAULT_MAIN_SERVER_LINK", "https://discord.gg/equinox")

# Shift Times (HH:MM)
LUMINOUS_SHIFT_START = "06:00"
TENEBRIS_SHIFT_START = "18:00"

# Colors
COLOR_LUMINOUS = 0xFCE883  # Vàng hoàng gia
COLOR_TENEBRIS = 0x2B2D31  # Đen xám giang hồ
