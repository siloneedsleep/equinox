import discord
from discord.ext import commands
import json

class StatusHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type != discord.InteractionType.component:
            return
            
        custom_id = interaction.data.get("custom_id", "")
        if not custom_id.startswith("trade_"):
            return

        # Đoạn code này để giữ chỗ cho logic xử lý nút bấm giao dịch công khai
        # Khi user bấm Chấp nhận/Từ chối trên Embed /trade
        await interaction.response.send_message("⚙️ Tính năng đang đồng bộ...", ephemeral=True)

    @commands.Cog.listener()
    async def on_system_event(self, event_data: str):
        # Bộ lắng nghe Pub/Sub Redis được dispathed từ core/bot.py
        # Giúp 2 bot nhận tín hiệu đồng bộ ngay lập tức khi Owner gọi lệnh khẩn cấp
        try:
            payload = json.loads(event_data)
            action = payload.get("action")
            
            if action == "sync_roles":
                print(f"[{self.bot.bot_name}] Đang nạp lại bảng ánh xạ Role tự động...")
        except Exception as e:
            print(f"Error handling system event: {e}")

async def setup(bot):
    await bot.add_cog(StatusHandler(bot))
