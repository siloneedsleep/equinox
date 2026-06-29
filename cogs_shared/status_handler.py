import discord
from discord.ext import commands
import json

class StatusHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_system_event(self, data: dict):
        # Lắng nghe các sự kiện hệ thống từ Pub/Sub (đã được bot.py dispatch)
        action = data.get("action")
        if action == "shift_change":
            # Có thể thực hiện thêm logic đồng bộ tại đây nếu cần
            pass

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        # Xử lý các tương tác toàn cục nếu có (ví dụ: các nút bấm trong trade)
        pass

async def setup(bot):
    await bot.add_cog(StatusHandler(bot))
