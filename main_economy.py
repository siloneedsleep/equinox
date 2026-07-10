import asyncio
import discord
from discord.ext import commands, tasks
from config.settings import LUMINOUS_TOKEN, TENEBRIS_TOKEN
from backend.database import KeyDBClient

class EconomyCluster(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="e!", intents=intents)
        self.db = KeyDBClient()
        self.current_persona = "Luminous" # Ca trực mặc định

    async def setup_hook(self):
        print("[Wispbyte] Đang nạp Economy Engine & Couple Systems...")
        await self.load_extension("cogs_shared.economy_couple")
        
        await self.tree.sync()
        
        # Kích hoạt các luồng giám sát ngầm
        self.heartbeat_loop.start()
        self.listen_quangia_commands.start()

    @tasks.loop(seconds=5)
    async def heartbeat_loop(self):
        """Bơm nhịp tim lên Redis để Quản Gia (Render) biết cụm này chưa sập"""
        await self.db.redis.set("host:wispbyte:status", "alive", ex=10)

    @tasks.loop(seconds=2)
    async def listen_quangia_commands(self):
        """Lắng nghe sự chỉ đạo khẩn cấp từ Quản Gia qua nút bấm /owner"""
        pubsub = await self.db.subscribe_channel("quangia:command")
        message = await pubsub.get_message(ignore_subscribe_messages=True)
        if message:
            cmd = message['data']
            if cmd == "shift_persona":
                print("⚠️ [Wispbyte] Nhận lệnh đổi ca thủ công từ Quản Gia!")
                # Logic đổi Token Luminous <-> Tenebris sẽ được thi công tại đây
            elif cmd == "restart_wispbyte":
                print("🛑 [Wispbyte] Nhận lệnh khởi động lại khẩn cấp từ Quản Gia! Tắt hệ thống...")
                await self.close()

    @listen_quangia_commands.before_loop
    async def before_listen(self):
        await self.wait_until_ready()

    async def on_ready(self):
        print(f"💰 [Wispbyte] Cụm Economy ({self.current_persona}) đang trực ca: {self.user}")

bot = EconomyCluster()

if __name__ == "__main__":
    # Khởi chạy luồng tiền tệ với Luminous làm thực thể chính
    bot.run(LUMINOUS_TOKEN)
