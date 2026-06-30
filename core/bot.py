import discord
from discord.ext import commands
import redis.asyncio as redis
from redis.asyncio.retry import Retry
from redis.backoff import ExponentialBackoff
from redis.exceptions import ConnectionError, TimeoutError
import json
import asyncio
from config.settings import REDIS_URI

class EquinoxBot(commands.Bot):
    def __init__(self, bot_name: str, command_prefix: str, theme_color: int, persona: str, shared_extensions: list):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.presences = True

        super().__init__(command_prefix=command_prefix, intents=intents)

        self.bot_name = bot_name
        self.theme_color = theme_color
        self.persona = persona
        self.shared_extensions = shared_extensions
        self.redis = None
        self.pubsub = None
        self.is_active_shift = False

    async def setup_hook(self):
        # 1. Kết nối Redis thuần với cơ chế ổn định cao
        retry_strategy = Retry(ExponentialBackoff(), 5)
        self.redis = redis.from_url(
            REDIS_URI,
            decode_responses=True,
            retry=retry_strategy,
            retry_on_timeout=True,
            socket_keepalive=True,
            health_check_interval=15,
            socket_timeout=30.0,
            socket_connect_timeout=15
        )

        try:
            await self.redis.ping()
            print(f"[{self.bot_name}] Kết nối Redis thành công.")
        except Exception as e:
            print(f"[{self.bot_name}] Lỗi kết nối Redis: {e}")
            raise e

        # 2. Đăng ký Pub/Sub
        self.pubsub = self.redis.pubsub()
        try:
            await self.pubsub.subscribe("equinox_system")
            self.loop.create_task(self.pubsub_listener())
            print(f"[{self.bot_name}] Đã đăng ký Pub/Sub 'equinox_system'.")
        except Exception as e:
            print(f"[{self.bot_name}] Lỗi khởi tạo Pub/Sub: {e}")

        # 3. Load Cogs
        for ext in self.shared_extensions:
            try:
                await self.load_extension(ext)
                print(f"[{self.bot_name}] Loaded cog: {ext}")
            except Exception as e:
                print(f"[{self.bot_name}] Failed to load cog {ext}: {e}")

    async def pubsub_listener(self):
        while True:
            try:
                async for message in self.pubsub.listen():
                    if message["type"] == "message":
                        try:
                            data = json.loads(message["data"])
                            action = data.get("action")
                            if action == "shift_change":
                                await self.handle_shift_change(data.get("active_persona"))
                            elif action == "emergency_shutdown":
                                print(f"[{self.bot_name}] NHẬN LỆNH DẬP CẦU DAO KHẨN CẤP!")
                                await self.close()
                            self.dispatch("system_event", data)
                        except json.JSONDecodeError:
                            continue
            except (ConnectionError, TimeoutError, asyncio.TimeoutError) as e:
                print(f"[{self.bot_name}] Mất kết nối Redis trong Pub/Sub. Đang thử lại...")
                await asyncio.sleep(5)
                try:
                    await self.pubsub.subscribe("equinox_system")
                except: pass
            except Exception as e:
                print(f"[{self.bot_name}] Pub/Sub Listener Error: {e}")
                await asyncio.sleep(2)

    async def handle_shift_change(self, active_persona: str):
        if self.persona == "Butler":
            # Quản Gia luôn túc trực, không bị ảnh hưởng bởi giao ca
            if not self.is_active_shift:
                self.is_active_shift = True
                await self.change_presence(status=discord.Status.online, activity=discord.Activity(type=discord.ActivityType.listening, name="Mệnh lệnh của Silo 👑"))
            return

        if self.persona == active_persona:
            self.is_active_shift = True
            status = discord.Status.online if self.persona == "Luminous" else discord.Status.dnd
            activity_name = "Equinox Network | Ca Ngày ☀️" if self.persona == "Luminous" else "Equinox Network | Ca Đêm 🌙"
            await self.change_presence(status=status, activity=discord.Activity(type=discord.ActivityType.watching, name=activity_name))
        else:
            self.is_active_shift = False
            await self.change_presence(status=discord.Status.invisible)

    async def on_ready(self):
        print(f"[{self.bot_name}] Identity {self.user.name} đã sẵn sàng.")
        try:
            from config.settings import MAIN_GUILD_ID
            if MAIN_GUILD_ID:
                guild = discord.Object(id=MAIN_GUILD_ID)
                self.tree.copy_global_to(guild=guild)
                synced = await self.tree.sync(guild=guild)
                print(f"[{self.bot_name}] Synced {len(synced)} commands to {MAIN_GUILD_ID}")
            else:
                synced = await self.tree.sync()
                print(f"[{self.bot_name}] Synced {len(synced)} commands globally.")
        except Exception as e:
            print(f"[{self.bot_name}] Slash Sync Error: {e}")

    async def close(self):
        if self.pubsub:
            try:
                await self.pubsub.unsubscribe("equinox_system")
                await self.pubsub.close()
            except: pass
        if self.redis:
            await self.redis.close()
        await super().close()
