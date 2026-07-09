import asyncio
import signal
import sys
import redis.asyncio as redis
from core.bot import EquinoxBot
from core.persona_scheduler import PersonaScheduler
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
        self.scheduler = None
        self.presence_manager = None
        self.is_running = True

    async def startup(self):
        print("="*50)
        print("   🪐 EQUINOX NETWORK - UNIFIED MONOREPO")
        print("="*50)

        # 1. Khởi tạo Redis dùng chung
        try:
            self.redis_client = redis.from_url(REDIS_URI, decode_responses=True)
            await self.redis_client.ping()
            print("[System] Kết nối Redis trung tâm thành công.")
        except Exception as e:
            print(f"[Critical] Không thể kết nối Redis: {e}")
            sys.exit(1)

        # 2. Danh sách Extensions Mới
        shared_exts = [
            "cogs_shared.general",
            "cogs_shared.shift_manager",
            "cogs_shared.system_services",           # Interactive Help Command
            "cogs_shared.giveaway",          # Persistent Giveaways
            "cogs_shared.roles",             # Emoji Pick Roles
            "cogs_shared.status_ui",         # Advanced Presence UI
            "cogs_shared.ai_circuit_breaker",# Cross-Core 429 handler
            "cogs_shared.economy_ui",
            "cogs_shared.system_core",
            "cogs_shared.jules_control",
            "cogs_shared.ai_chat"
        ]

        butler_exts = shared_exts + ["cogs_shared.butler_core"]

        # 3. Khởi tạo Bots
        self.luminous = EquinoxBot("Luminous", "l!", COLOR_LUMINOUS, "Luminous", shared_exts)
        self.tenebris = EquinoxBot("Tenebris", "t!", COLOR_TENEBRIS, "Tenebris", shared_exts)
        self.butler = EquinoxBot("Quản Gia", "b!", 0x3498DB, "Butler", butler_exts)

        # 4. Khởi tạo Services
        self.scheduler = PersonaScheduler(self.redis_client)
        self.presence_manager = ProxyPresenceManager(self.redis_client)

        # 5. Chạy đa luồng
        print("[System] Đang khởi chạy toàn bộ thực thể...")

        # Kiểm tra Vercel Configuration Checkpoint
        if "vercel.app" in OAUTH2_REDIRECT_URI or "localhost" not in OAUTH2_REDIRECT_URI:
            print("[System] 🚀 Chạy chế độ Hybrid: Web Serverless ủy quyền cho Vercel/FastAPI qua /api/index.py")
        else:
            print("[System] ⚠️ Vui lòng cấu hình Vercel OAuth2 (Monorepo architecture) để bật tính năng thay đổi Status.")

        tasks = [
            self.luminous.start(LUMINOUS_TOKEN),
            self.tenebris.start(TENEBRIS_TOKEN),
            self.butler.start(QUANGIA_TOKEN),
            self.scheduler.start(),
            self.presence_manager.sync_loop()
        ]

        await asyncio.gather(*tasks)

    async def shutdown(self):
        if not self.is_running: return
        self.is_running = False
        print("\n[System] Graceful Shutdown...")
        if self.scheduler: await self.scheduler.stop()
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
