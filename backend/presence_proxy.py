import json
import asyncio
import discord
from discord.ext import tasks
from backend.database import KeyDBClient

class PresenceProxy:
    def __init__(self, bot: discord.Client):
        self.bot = bot
        self.db = KeyDBClient()
        self.is_paused = False
        self.pubsub = None

    async def start_proxy(self):
        """Khởi động tiến trình lắng nghe Pub/Sub từ Redis"""
        self.pubsub = await self.db.subscribe_channel("presence:sync:events")
        self.listen_loop.start()
        print("[Presence Proxy] Đã kết nối WebSocket Gateway 24/7.")

    @tasks.loop(seconds=2)
    async def listen_loop(self):
        """Lắng nghe các thay đổi status từ Quản Gia (Render) điều khiển chéo"""
        if self.pubsub:
            message = await self.pubsub.get_message(ignore_subscribe_messages=True)
            if message:
                command = message['data']
                if command == "reload":
                    await self.reload_presence()
                elif command == "pause":
                    self.is_paused = True
                    await self.bot.change_presence(status=discord.Status.offline)
                elif command == "resume":
                    self.is_paused = False
                    await self.reload_presence()
                elif command == "delete":
                    await self.bot.change_presence(activity=None, status=discord.Status.online)

    async def reload_presence(self):
        """Tải lại cấu hình Presence từ Redis và cập nhật lên Discord API"""
        if self.is_paused:
            return

        app_name = await self.db.redis.get("presence:config:app_name")
        state = await self.db.redis.get("presence:config:state")
        
        if app_name and state:
            # Custom Activity hỗ trợ hiển thị Double-Modal UI của bạn
            activity = discord.CustomActivity(name=f"{app_name} | {state}")
            await self.bot.change_presence(activity=activity, status=discord.Status.online)

    @listen_loop.before_loop
    async def before_listen_loop(self):
        await self.bot.wait_until_ready()
