import asyncio
import signal
import sys
import redis.asyncio as redis
from core.bot import EquinoxBot
from backend.web_server import EquinoxWebServer
from backend.presence_proxy import ProxyPresenceManager
from config.settings import (
    LUMINOUS_TOKEN, TENEBRIS_TOKEN, REDIS_URI,
    COLOR_LUMINOUS, COLOR_TENEBRIS
)

class EquinoxEcosystem:
    def __init__(self):
        self.redis_client = None
        self.luminous = None
        self.tenebris = None
        self.web_server = None
        self.presence_manager = None
        self.is_running = True

    async def startup(self):
        print("="*50)
        print("   🪐 EQUINOX NETWORK V2 - PTERODACTYL EDITION")
        print("="*50)

        # 1. Khởi tạo Redis với cơ chế retry
        retry_count = 0
        while retry_count < 5:
            try:
                self.redis_client = redis.from_url(REDIS_URI, decode_responses=True)
                await self.redis_client.ping()
                print("[System] Kết nối Redis thành công.")
                break
            except Exception as e:
                retry_count += 1
                print(f"[Warning] Thử kết nối Redis lần {retry_count}/5 thất bại: {e}")
                if retry_count == 5:
                    print("[Critical] KHÔNG THỂ KẾT NỐI REDIS. Vui lòng kiểm tra lại REDIS_URI trong config.json.")
                    sys.exit(1)
                await asyncio.sleep(5)

        # 2. Khởi tạo Bots
        self.luminous = EquinoxBot("Luminous", "l!", COLOR_LUMINOUS, "Luminous")
        self.tenebris = EquinoxBot("Tenebris", "t!", COLOR_TENEBRIS, "Tenebris")

        # 3. Khởi tạo Services
        self.web_server = EquinoxWebServer(self.redis_client)
        self.presence_manager = ProxyPresenceManager(self.redis_client)

        # 4. Load Extensions
        shared_exts = [
            "cogs_shared.status_ui",
            "cogs_shared.status_handler",
            "cogs_shared.economy_ui",
            "cogs_shared.shift_manager",
            "cogs_shared.interaction_labs",
            "cogs_shared.system_core",
            "cogs_shared.system_services",
            "cogs_shared.jules_control"
        ]

        for bot in [self.luminous, self.tenebris]:
            for ext in shared_exts:
                await bot.load_extension(ext)
            print(f"[{bot.bot_name}] Đã nạp {len(shared_exts)} module thành công.")

        # 5. Chạy đa luồng
        print("[System] Đang khởi chạy toàn bộ thực thể...")

        tasks = [
            self.luminous.start(LUMINOUS_TOKEN),
            self.tenebris.start(TENEBRIS_TOKEN),
            self.web_server.start(),
            self.presence_manager.sync_loop()
        ]

        await asyncio.gather(*tasks)

    async def shutdown(self):
        if not self.is_running: return
        self.is_running = False

        print("\n[System] Đang thực hiện quy trình tắt bot an toàn (Graceful Shutdown)...")
        if self.luminous: await self.luminous.close()
        if self.tenebris: await self.tenebris.close()
        if self.redis_client: await self.redis_client.close()
        print("[System] Đã ngắt toàn bộ kết nối. Tạm biệt!")
        sys.exit(0)

def handle_signal(ecosystem):
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(ecosystem.shutdown()))

if __name__ == "__main__":
    ecosystem = EquinoxEcosystem()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Đăng ký signal handlers cho Pterodactyl Panel
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(ecosystem.shutdown()))

    try:
        loop.run_until_complete(ecosystem.startup())
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()
