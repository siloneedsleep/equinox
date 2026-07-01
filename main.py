import asyncio
import signal
import sys
import redis.asyncio as redis
from core.bot import EquinoxBot
from backend.web_server import EquinoxWebServer
from backend.presence_proxy import ProxyPresenceManager
from config.settings import (
    LUMINOUS_TOKEN, TENEBRIS_TOKEN, QUANGIA_TOKEN, REDIS_URI,
    COLOR_LUMINOUS, COLOR_TENEBRIS, OAUTH2_REDIRECT_URI
)

class EquinoxEcosystem:
    def __init__(self):
        self.redis_client = None
        self.luminous = None
        self.tenebris = None
        self.butler = None
        self.web_server = None
        self.presence_manager = None
        self.is_running = True

    async def startup(self):
        print("="*50)
        print("   🪐 EQUINOX NETWORK V2 - PTERODACTYL EDITION")
        print("="*50)

        # 1. Khởi tạo Redis dùng chung cho các Services bên ngoài Bot
        try:
            self.redis_client = redis.from_url(REDIS_URI, decode_responses=True)
            await self.redis_client.ping()
            print("[System] Kết nối Redis trung tâm thành công.")
        except Exception as e:
            print(f"[Critical] Không thể kết nối Redis: {e}")
            sys.exit(1)

        # 2. Danh sách Extensions
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

        butler_exts = shared_exts + ["cogs_shared.butler_core", "cogs_shared.idea_system"]

        # 3. Khởi tạo Bots
        self.luminous = EquinoxBot("Luminous", "l!", COLOR_LUMINOUS, "Luminous", shared_exts)
        self.tenebris = EquinoxBot("Tenebris", "t!", COLOR_TENEBRIS, "Tenebris", shared_exts)
        self.butler = EquinoxBot("Quản Gia", "b!", 0x3498DB, "Butler", butler_exts)

        # 4. Khởi tạo Services
        self.web_server = EquinoxWebServer(self.redis_client)
        self.presence_manager = ProxyPresenceManager(self.redis_client)

        # 5. Chạy đa luồng
        print("[System] Đang khởi chạy toàn bộ thực thể...")

        tasks = [
            self.luminous.start(LUMINOUS_TOKEN),
            self.tenebris.start(TENEBRIS_TOKEN),
            self.butler.start(QUANGIA_TOKEN),
            self.presence_manager.sync_loop()
        ]

        # Tự động tắt Web Server nội bộ nếu cấu hình dùng Vercel
        if "vercel.app" not in OAUTH2_REDIRECT_URI:
            tasks.append(self.web_server.start())
        else:
            print("[System] Đang sử dụng Vercel Serverless cho OAuth2. Web Server nội bộ đã tắt.")

        await asyncio.gather(*tasks)

    async def shutdown(self):
        if not self.is_running: return
        self.is_running = False
        print("\n[System] Graceful Shutdown...")
        if self.luminous: await self.luminous.close()
        if self.tenebris: await self.tenebris.close()
        if self.butler: await self.butler.close()
        if self.redis_client: await self.redis_client.close()
        sys.exit(0)

if __name__ == "__main__":
    ecosystem = EquinoxEcosystem()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(ecosystem.shutdown()))

    try:
        loop.run_until_complete(ecosystem.startup())
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()
