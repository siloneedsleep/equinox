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
        # Cấu hình chiến lược Retry
        retry_strategy = Retry(ExponentialBackoff(), 5)

        # Kết nối Redis thuần với cơ chế ổn định cao cho Valkey/Aiven
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
                        try:
                            data = json.loads(message["data"])
                            if data.get("action") == "shift_change":
                                await self.handle_shift_change(data.get("active_persona"))
                            self.dispatch("system_event", data)
                        except json.JSONDecodeError:
                            continue
            except (ConnectionError, TimeoutError, asyncio.TimeoutError) as e:
                print(f"[{self.bot_name}] Mất kết nối hoặc Timeout Redis ({type(e).__name__}). Đang thử kết nối lại...")
                await asyncio.sleep(5)
                try:
                    # Đảm bảo pubsub cũ được đóng và tạo cái mới nếu cần
                    await self.pubsub.subscribe("equinox_system")
                    print(f"[{self.bot_name}] Đã tái kết nối và re-subscribe thành công.")
                except Exception as resub_err:
                    print(f"[{self.bot_name}] Re-subscribe thất bại: {resub_err}")
            except Exception as e:
                print(f"[{self.bot_name}] Pub/Sub Listener Error: {e}")
                await asyncio.sleep(2)

    async def handle_shift_change(self, active_persona: str):
        if self.persona == active_persona:
            self.is_active_shift = True
            await self.change_presence(status=discord.Status.online, activity=discord.Game(name="Equinox Network V2 | Active"))
        else:
            self.is_active_shift = False
            await self.change_presence(status=discord.Status.invisible)

    async def on_ready(self):
        print(f"[{self.bot_name}] Hệ thống Identity {self.user.name} đã sẵn sàng.")

        # Tự động đồng bộ Slash Commands
        try:
            from config.settings import MAIN_GUILD_ID
            if MAIN_GUILD_ID:
                guild = discord.Object(id=MAIN_GUILD_ID)
                self.tree.copy_global_to(guild=guild)
                synced = await self.tree.sync(guild=guild)
                print(f"[{self.bot_name}] Đã đồng bộ {len(synced)} lệnh Slash tới Guild {MAIN_GUILD_ID}")
            else:
                synced = await self.tree.sync()
                print(f"[{self.bot_name}] Đã đồng bộ {len(synced)} lệnh Slash toàn cầu.")
        except Exception as e:
            print(f"[{self.bot_name}] Lỗi đồng bộ Slash Commands: {e}")

    async def close(self):
        if self.pubsub:
            await self.pubsub.unsubscribe("equinox_system")
            await self.pubsub.close()
        if self.redis:
            await self.redis.close()
        await super().close()
