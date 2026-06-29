import discord
from discord import app_commands
from discord.ext import commands, tasks
import json
import datetime
import pytz
import os
from config.settings import LUMINOUS_SHIFT_START, TENEBRIS_SHIFT_START

class ShiftManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.timezone = pytz.timezone('Asia/Ho_Chi_Minh')
        self.auto_shift_checker.start()

    def cog_unload(self):
        self.auto_shift_checker.cancel()

    @tasks.loop(seconds=30)
    async def auto_shift_checker(self):
        """Hệ thống tự động kiểm tra và duy trì ca trực theo thời gian thực (GMT+7)"""
        # Chỉ một bot (ưu tiên Luminous) làm nhiệm vụ phát tín hiệu để tránh xung đột Pub/Sub
        if self.bot.persona != "Luminous":
            return

        now = datetime.datetime.now(self.timezone)
        current_hour = now.hour

        # Luminous: 06:00 - 17:59 | Tenebris: 18:00 - 05:59
        target_persona = "Luminous" if 6 <= current_hour < 18 else "Tenebris"

        # Kiểm tra trạng thái hiện tại từ Redis để tránh spam tín hiệu nếu đã đúng ca
        current_active = await self.bot.redis.get("system:active_persona")

        if current_active != target_persona:
            payload = {
                "action": "shift_change",
                "active_persona": target_persona,
                "timestamp": now.isoformat(),
                "reason": "Automatic Scheduled Shift Change"
            }
            await self.bot.redis.publish("equinox_system", json.dumps(payload))
            await self.bot.redis.set("system:active_persona", target_persona)
            print(f"[Auto Shift] Đã kích hoạt ca trực cho: {target_persona}")

    @auto_shift_checker.before_loop
    async def before_auto_shift(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="doica", description="[Staff] Thực hiện đổi ca thủ công giữa các thực thể")
    @app_commands.choices(persona=[
        app_commands.Choice(name="Luminous (Ca Ngày)", value="Luminous"),
        app_commands.Choice(name="Tenebris (Ca Đêm)", value="Tenebris")
    ])
    async def manual_shift_change(self, interaction: discord.Interaction, persona: app_commands.Choice[str]):
        user_level = await self.bot.redis.hget(f"user:{interaction.user.id}", "level")
        user_level = int(user_level) if user_level else 0
        owner_id = int(os.getenv("OWNER_ID", 0))

        if user_level < 1 and interaction.user.id != owner_id:
            embed = discord.Embed(description="❌ Bạn không có quyền thực hiện lệnh đổi ca.", color=0xFF0000)
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        payload = {
            "action": "shift_change",
            "active_persona": persona.value,
            "timestamp": datetime.datetime.now(self.timezone).isoformat(),
            "issuer": interaction.user.name,
            "reason": "Manual Override"
        }

        await self.bot.redis.publish("equinox_system", json.dumps(payload))
        await self.bot.redis.set("system:active_persona", persona.value)
        await self.bot.redis.lpush("shift_logs", json.dumps(payload))
        await self.bot.redis.ltrim("shift_logs", 0, 99)

        embed = discord.Embed(
            title="🔄 XÁC NHẬN ĐỔI CA THỦ CÔNG",
            description=f"Thực thể được kích hoạt: **{persona.name}**\nNgười thực hiện: {interaction.user.mention}",
            color=0x00FF00
        )
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(ShiftManager(bot))
