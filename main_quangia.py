import os
import asyncio
import discord
from discord.ext import commands
import uvicorn
from api.web_server import app
from backend.presence_proxy import PresenceProxy
from config.settings import QUANGIA_TOKEN, PORT, MAIN_GUILD_ID

class QuanGiaBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="q!", intents=intents)
        # Loại bỏ lệnh help mặc định
        self.remove_command('help')
        # Nạp module giữ Status sáng đèn 24/7
        self.presence_proxy = PresenceProxy(self)

    async def setup_hook(self):
        print("[Render] Đang nạp hệ thống lõi Quản Gia...")
        await self.load_extension("cogs_shared.quan_gia_core")
        
        # Đồng bộ lệnh Slash lên Discord (Ưu tiên Main Guild để cập nhật lập tức)
        if MAIN_GUILD_ID:
            main_guild = discord.Object(id=MAIN_GUILD_ID)
            self.tree.copy_global_to(guild=main_guild)
            await self.tree.sync(guild=main_guild)
            print(f"[Render] Đã đồng bộ lệnh Slash cục bộ cho Guild ID: {MAIN_GUILD_ID}")
        else:
            await self.tree.sync()
            print("[Render] Đã đồng bộ lệnh Slash toàn cầu (Global)")
        
        # Kích hoạt vòng lặp lắng nghe Redis Pub/Sub
        await self.presence_proxy.start_proxy()
        
    async def on_ready(self):
        print(f"🪐 [Render] Quản Gia Equinox đã sẵn sàng điều phối: {self.user}")

bot = QuanGiaBot()

async def run_fastapi():
    """Khởi chạy Web Server bằng Uvicorn trên Port Render cấp"""
    config = uvicorn.Config(app, host="0.0.0.0", port=PORT, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

async def run_bot():
    """Khởi chạy Bot Discord"""
    await bot.start(QUANGIA_TOKEN)

async def main():
    """Chạy song song cả 2 dịch vụ trên cùng 1 Host (Unified Process)"""
    await asyncio.gather(
        run_fastapi(),
        run_bot()
    )

if __name__ == "__main__":
    # Khởi chạy vòng lặp bất đồng bộ trung tâm
    asyncio.run(main())
