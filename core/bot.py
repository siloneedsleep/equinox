import discord
from discord.ext import commands
import redis.asyncio as redis
import json
import asyncio
from config.settings import REDIS_URI

class EquinoxBot(commands.Bot):
    def __init__(self, bot_name: str, command_prefix: str, theme_color: int, persona: str):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.presences = True

        super().__init__(command_prefix=command_prefix, intents=intents)

        self.bot_name = bot_name
        self.theme_color = theme_color
        self.persona = persona
        self.redis = None
        self.pubsub = None
        self.is_active_shift = False

    async def setup_hook(self):
        # Kết nối Redis đa luồng (KeyDB compatible)
        self.redis = redis.from_url(REDIS_URI, decode_responses=True)
        self.pubsub = self.redis.pubsub()
        await self.pubsub.subscribe("equinox_system")

        # Chạy listener Pub/Sub ngầm
        self.loop.create_task(self.pubsub_listener())

        print(f"[{self.bot_name}] Đang kết nối KeyDB và thiết lập Pub/Sub...")

    async def pubsub_listener(self):
        async for message in self.pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    action = data.get("action")

                    if action == "shift_change":
                        new_persona = data.get("active_persona")
                        await self.handle_shift_change(new_persona)

                    # Dispatch event nội bộ để các Cogs có thể lắng nghe
                    self.dispatch("system_event", data)
                except Exception as e:
                    print(f"[{self.bot_name}] Lỗi xử lý Pub/Sub: {e}")

    async def handle_shift_change(self, active_persona: str):
        if self.persona == active_persona:
            self.is_active_shift = True
            await self.change_presence(status=discord.Status.online, activity=discord.Game(name="Equinox Network V2 | Active"))
            print(f"[{self.bot_name}] Đã vào ca trực. Trạng thái: Online.")
        else:
            self.is_active_shift = False
            await self.change_presence(status=discord.Status.invisible)
            print(f"[{self.bot_name}] Đã hết ca trực. Trạng thái: Invisible.")

    async def load_module_cogs(self, extensions: list):
        for ext in extensions:
            try:
                await self.load_extension(ext)
                print(f"[{self.bot_name}] Loaded extension: {ext}")
            except Exception as e:
                print(f"[{self.bot_name}] Failed to load extension {ext}: {e}")

    async def on_ready(self):
        print(f"[{self.bot_name}] Hệ thống Identity {self.user.name} đã sẵn sàng.")
        # Kiểm tra ca trực ngay khi khởi động (logic này sẽ được shift_manager cập nhật sau)
        pass

    async def close(self):
        if self.pubsub:
            await self.pubsub.unsubscribe("equinox_system")
            await self.pubsub.close()
        if self.redis:
            await self.redis.close()
        await super().close()
