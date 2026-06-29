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
        # Kết nối Redis thuần với cơ chế tự động reconnect
        self.redis = redis.from_url(
            REDIS_URI,
            decode_responses=True,
            retry_on_timeout=True,
            health_check_interval=30,
            socket_connect_timeout=10
        )
        self.pubsub = self.redis.pubsub()

        try:
            await self.pubsub.subscribe("equinox_system")
            self.loop.create_task(self.pubsub_listener())
            print(f"[{self.bot_name}] Đã đăng ký Pub/Sub.")
        except Exception as e:
            print(f"[{self.bot_name}] Lỗi khởi tạo Pub/Sub: {e}")

    async def pubsub_listener(self):
        while True:
            try:
                async for message in self.pubsub.listen():
                    if message["type"] == "message":
                        data = json.loads(message["data"])
                        if data.get("action") == "shift_change":
                            await self.handle_shift_change(data.get("active_persona"))
                        self.dispatch("system_event", data)
            except redis.ConnectionError:
                print(f"[{self.bot_name}] Mất kết nối Redis. Đang thử kết nối lại sau 5 giây...")
                await asyncio.sleep(5)
                # Tự động subscribe lại sau khi reconnect
                try:
                    await self.pubsub.subscribe("equinox_system")
                except: pass
            except Exception as e:
                print(f"[{self.bot_name}] Pub/Sub Listener Error: {e}")
                await asyncio.sleep(1)

    async def handle_shift_change(self, active_persona: str):
        if self.persona == active_persona:
            self.is_active_shift = True
            await self.change_presence(status=discord.Status.online, activity=discord.Game(name="Equinox Network V2 | Active"))
        else:
            self.is_active_shift = False
            await self.change_presence(status=discord.Status.invisible)

    async def close(self):
        if self.pubsub:
            await self.pubsub.unsubscribe("equinox_system")
            await self.pubsub.close()
        if self.redis:
            await self.redis.close()
        await super().close()
