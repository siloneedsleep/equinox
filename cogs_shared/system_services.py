import discord
from discord.ext import commands
from discord import app_commands
import os
from backend.database import EquinoxDatabase

class SystemServices(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = EquinoxDatabase(bot.redis)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        # Tự động đồng bộ Level khi member được cấp Role trên Server Nhà Chính
        if before.roles == after.roles:
            return

        raw_mapping = await self.bot.redis.hgetall("role_mapping")
        if not raw_mapping:
            return

        highest_level = 0
        for role in after.roles:
            if str(role.id) in raw_mapping:
                level = int(raw_mapping[str(role.id)])
                if level > highest_level:
                    highest_level = level
        
        current_db_level = await self.db.get_user_level(after.id)
        if highest_level != current_db_level:
            await self.db.set_user_level(after.id, highest_level)
            print(f"[Level Sync] User {after.name} đã được cập nhật lên Level {highest_level}")

    @app_commands.command(name="warn", description="[Admin+] Phạt gậy thành viên")
    async def warn_user(self, interaction: discord.Interaction, target: discord.Member, reason: str):
        issuer_level = await self.db.get_user_level(interaction.user.id)
        target_level = await self.db.get_user_level(target.id)

        # ⚠️ Luật Bảo Vệ Cấp Trên
        if target_level >= issuer_level and interaction.user.id != int(os.getenv("OWNER_ID", 0)):
            return await interaction.response.send_message("❌ Phản phệ! Bạn không có quyền phạt gậy cấp trên hoặc người cùng cấp.", ephemeral=True)

        await self.bot.redis.hincrby(f"user:{target.id}", "warns", 1)
        warn_count = await self.bot.redis.hget(f"user:{target.id}", "warns")

        embed = discord.Embed(title="⚖️ TÒA ÁN EQUINOX: CẤP LỆNH PHẠT", color=0xFF0000)
        embed.add_field(name="Bị cáo", value=target.mention, inline=True)
        embed.add_field(name="Thẩm phán", value=interaction.user.mention, inline=True)
        embed.add_field(name="Lý do", value=reason, inline=False)
        embed.add_field(name="Tổng số gậy", value=f"{warn_count} 🚩", inline=False)

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(SystemServices(bot))
