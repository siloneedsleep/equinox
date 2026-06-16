import os
import asyncio
import discord
from flask import Flask
from threading import Thread

# ==============================================================================
# 🎛️ BỘ KHỞI TẠO WEB SERVER GIẢ LẬP ĐỂ ĐÁNH LỪA RENDER
# ==============================================================================
app = Flask('keep_alive')

@app.route('/')
def home():
    return "🚀 Equinox Network Ecosystem is Live and Running!"

def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_server)
    t.start()

# Kích hoạt mở cổng đánh lừa Render
keep_alive()

# ==============================================================================
# 🚀 GỘP TIẾN TRÌNH - CHẠY SONG SONG 2 BOT TRÊN CÙNG 1 LUỒNG ASYNC
# ==============================================================================
print("🚀 EQUINOX NETWORK - ASYNC BOOT SEQUENCE INITIATED 🚀\n")

# Import trực tiếp đối tượng bot từ 2 file main của ông
from luminous_main import bot as luminous_bot
from tenebris_main import bot as tenebris_bot
from config.settings import TOKENS

async def main():
    print("\033[93mĐang kích hoạt Luminous và Tenebris chung một dòng vạn tượng... \033[0m")
    
    # Chạy song song cả 2 con bot trong cùng 1 Event Loop, triệt tiêu 100% việc nghẽn CPU
    await asyncio.gather(
        luminous_bot.start(TOKENS["LUMINOUS"]),
        tenebris_bot.start(TOKENS["TENEBRIS"])
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 SHUTTING DOWN EQUINOX NETWORK...")
        print("✅ Đã tắt toàn bộ hệ thống.")
