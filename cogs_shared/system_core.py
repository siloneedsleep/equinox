import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from backend.database import EquinoxDatabase

class SystemCore(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = EquinoxDatabase(bot.redis)

    system_group = app_commands.Group(name="system", description="Lệnh quản trị hệ thống (Độc quyền Owner)")
    api_group = app_commands.Group(parent=system_group, name="api", description="Quản trị xoay tua API Key")
    key_group = app_commands.Group(parent=system_group, name="key", description="Quản trị Premium Key")

    async def check_owner(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != int(os.getenv("OWNER_ID", 0)):
            await interaction.response.send_message("❌ Từ chối truy cập. Chỉ Owner mới có quyền này.", ephemeral=True)
            return False
        return True

    @key_group.command(name="add", description="Tạo mã Premium Key mới")
    async def sys_add_key(self, interaction: discord.Interaction, duration_days: int):
        if not await self.check_owner(interaction): return
        token = await self.db.create_premium_key(duration_days)
        await interaction.response.send_message(f"✅ Đã tạo Key: `{token}` ({duration_days} ngày)", ephemeral=True)

    @api_group.command(name="add", description="Nạp API Key Gemini")
    async def api_add(self, interaction: discord.Interaction, token_id: str, key_content: str):
        if not await self.check_owner(interaction): return
        payload = {"key_content": key_content, "status": "active", "fail_count": 0, "cooldown_until": 0}
        await self.bot.redis.hset("api_keys", token_id, json.dumps(payload))
        await interaction.response.send_message(f"✅ Đã nạp API Key `{token_id}`", ephemeral=True)

    @system_group.command(name="force_shift", description="Cưỡng chế đổi ca lập tức")
    async def force_shift(self, interaction: discord.Interaction, persona: str):
        if not await self.check_owner(interaction): return
        payload = {"action": "shift_change", "active_persona": persona}
        await self.bot.redis.publish("equinox_system", json.dumps(payload))
        await interaction.response.send_message(f"🚀 Đã phát lệnh đổi ca khẩn cấp sang: {persona}", ephemeral=True)

    @app_commands.command(name="redeem", description="Kích hoạt Premium Key")
    async def redeem(self, interaction: discord.Interaction, token: str):
        success = await self.db.redeem_premium_key(interaction.user.id, token)
        if success:
            await interaction.response.send_message("🎉 Kích hoạt thành công! Bạn đã có đặc quyền VIP.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Key không hợp lệ hoặc đã sử dụng.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(SystemCore(bot))
