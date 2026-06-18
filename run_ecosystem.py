import asyncio
import os
from keep_alive import keep_alive
from config.settings import TOKENS

# Load các object bot (đã bị xóa bot.run() ở cuối file)
from luminous_main import bot as luminous_bot
from tenebris_main import bot as tenebris_bot

# FIX LỖI 2: XÓA SẠCH CODE FLASK Ở ĐÂY, CHỈ GỌI keep_alive()
async def main():
    keep_alive()
    print("⚡ MẠNG LƯỚI HẠCH TÂM EQUINOX ĐANG KHỞI ĐỘNG...")
    
    # FIX LỖI 8: Chống Race Condition chết chùm bằng return_exceptions và try-except
    try:
        await asyncio.gather(
            luminous_bot.start(TOKENS["LUMINOUS"]),
            tenebris_bot.start(TOKENS["TENEBRIS"]),
            return_exceptions=True
        )
    except Exception as e:
        print(f"❌ CRITICAL: Hệ sinh thái crash: {e}")

if __name__ == "__main__":
    asyncio.run(main())
