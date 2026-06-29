import asyncio
import redis.asyncio as redis
from core.bot import EquinoxBot
from backend.web_server import EquinoxWebServer
from backend.presence_proxy import ProxyPresenceManager
from config.settings import (
    LUMINOUS_TOKEN, TENEBRIS_TOKEN, REDIS_URI,
    COLOR_LUMINOUS, COLOR_TENEBRIS
)

async def run_ecosystem():
    # 1. Kết nối KeyDB tập trung
    redis_client = redis.from_url(REDIS_URI, decode_responses=True)
    
    # 2. Khởi tạo hai thực thể Bot đối lập
    luminous = EquinoxBot(
        bot_name="Luminous",
        command_prefix="l!",
        theme_color=COLOR_LUMINOUS,
        persona="Luminous"
    )
    
    tenebris = EquinoxBot(
        bot_name="Tenebris",
        command_prefix="t!",
        theme_color=COLOR_TENEBRIS,
        persona="Tenebris"
    )

    # 3. Khởi tạo Web Server và Presence Proxy
    web_server = EquinoxWebServer(redis_client)
    presence_manager = ProxyPresenceManager(redis_client)

    # 4. Danh sách các Extensions dùng chung
    shared_extensions = [
        "cogs_shared.status_ui",
        "cogs_shared.status_handler",
        "cogs_shared.economy_ui",
        "cogs_shared.shift_manager",
        "cogs_shared.interaction_labs",
        "cogs_shared.system_core",
        "cogs_shared.system_services",
        "cogs_shared.jules_control"
    ]

    async def setup_bot(bot):
        # Hook để load cogs sau khi bot sẵn sàng (hoặc trong setup_hook)
        for ext in shared_extensions:
            await bot.load_extension(ext)

    # Đăng ký setup task
    await setup_bot(luminous)
    await setup_bot(tenebris)

    print("[Equinox Core] --- HỆ SINH THÁI EQUINOX NETWORK V2 ĐANG KHỞI CHẠY ---")
    
    # 5. Chạy đa luồng asyncio.gather()
    await asyncio.gather(
        luminous.start(LUMINOUS_TOKEN),
        tenebris.start(TENEBRIS_TOKEN),
        web_server.start(),
        presence_manager.sync_loop()
    )

if __name__ == "__main__":
    try:
        asyncio.run(run_ecosystem())
    except KeyboardInterrupt:
        print("\n[Equinox Core] Đã dập cầu dao. Ngắt kết nối toàn bộ hệ sinh thái.")
    except Exception as e:
        print(f"\n[Equinox Core] Lỗi khởi động nghiêm trọng: {e}")
