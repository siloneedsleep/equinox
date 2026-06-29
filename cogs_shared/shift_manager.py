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
        self.check_shift.start()

    def cog_unload(self):
        self.check_shift.cancel()

    @tasks.loop(minutes=1)
    async def check_shift(self):
        # Chỉ bot Luminous làm nhiệm vụ điều phối thời gian để tránh lặp tín hiệu
        if self.bot.persona != "Luminous":
            return

        now = datetime.datetime.now(self.timezone)
        current_time = now.strftime("%H:%M")

        target_persona = None
        if current_time == LUMINOUS_SHIFT_START:
            target_persona = "Luminous"
        elif current_time == TENEBRIS_SHIFT_START:
            target_persona = "Tenebris"

        if target_persona:
            payload = {
                "action": "shift_change",
                "active_persona": target_persona,
                "timestamp": now.isoformat()
            }
            await self.bot.redis.publish("equinox_system", json.dumps(payload))
            print(f"[Shift Manager] Đã bắn tín hiệu giao ca: {target_persona}")

    @check_shift.before_loop
    async def before_check_shift(self):
        await self.bot.wait_until_ready()
        # Xác định ca trực hiện tại ngay khi khởi động
        now = datetime.datetime.now(self.timezone)
        hour = now.hour

        current_persona = "Luminous" if 6 <= hour < 18 else "Tenebris"

        payload = {
            "action": "shift_change",
            "active_persona": current_persona,
            "timestamp": now.isoformat()
        }
        # Tự gửi cho chính mình và các bot khác qua Redis
        try:
            await self.bot.redis.publish("equinox_system", json.dumps(payload))
        except: pass

    @app_commands.command(name="doica", description="[Staff] Thực hiện đổi ca thủ công giữa các thực thể")
    @app_commands.choices(persona=[
        app_commands.Choice(name="Luminous (Ca Ngày)", value="Luminous"),
        app_commands.Choice(name="Tenebris (Ca Đêm)", value="Tenebris")
    ])
    async def manual_shift_change(self, interaction: discord.Interaction, persona: app_commands.Choice[str]):
        # Check quyền Staff (Level >= 1)
        # Giả định Level quản lý qua Redis hget user:id level
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
            "issuer": interaction.user.name
        }

        await self.bot.redis.publish("equinox_system", json.dumps(payload))
        # Lưu log đổi ca vào Redis
        await self.bot.redis.lpush("shift_logs", json.dumps(payload))
        await self.bot.redis.ltrim("shift_logs", 0, 99) # Giữ 100 log gần nhất

        embed = discord.Embed(
            title="🔄 XÁC NHẬN ĐỔI CA THỦ CÔNG",
            description=f"Thực thể được kích hoạt: **{persona.name}**\nNgười thực hiện: {interaction.user.mention}",
            color=0x00FF00
        )
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(ShiftManager(bot))
