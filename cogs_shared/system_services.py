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

    @app_commands.command(name="warn", description="[Admin+] Phạt gậy thành viên")
    async def warn_user(self, interaction: discord.Interaction, target: discord.Member, reason: str):
        issuer_level = await self.db.get_user_level(interaction.user.id)
        target_level = await self.db.get_user_level(target.id)
        owner_id = int(os.getenv("OWNER_ID", 0))

        # ⚠️ Luật Bảo Vệ Cấp Trên
        if target_level >= issuer_level and interaction.user.id != owner_id:
            embed = discord.Embed(description="❌ **Phản phệ!** Bạn không có quyền phạt gậy cấp trên hoặc người cùng cấp.", color=0xFF0000)
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        await self.bot.redis.hincrby(f"user:{target.id}", "warns", 1)
        warn_count = await self.bot.redis.hget(f"user:{target.id}", "warns")

        embed = discord.Embed(title="⚖️ TÒA ÁN EQUINOX: CẤP LỆNH PHẠT", color=0xFF0000)
        embed.add_field(name="Bị cáo", value=target.mention, inline=True)
        embed.add_field(name="Thẩm phán", value=interaction.user.mention, inline=True)
        embed.add_field(name="Lý do", value=reason, inline=False)
        embed.add_field(name="Tổng số gậy", value=f"{warn_count} 🚩", inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="set-role", description="[Owner] Ánh xạ Role Discord với Level hệ thống")
    @app_commands.choices(level=[
        app_commands.Choice(name="Level 1 (Staff)", value=1),
        app_commands.Choice(name="Level 2 (Admin)", value=2),
        app_commands.Choice(name="Level 3 (Dev)", value=3)
    ])
    async def set_role_map(self, interaction: discord.Interaction, level: app_commands.Choice[int], role: discord.Role):
        owner_id = int(os.getenv("OWNER_ID", 0))
        if interaction.user.id != owner_id:
            return await interaction.response.send_message("❌ Chỉ Owner mới có quyền này.", ephemeral=True)

        await self.bot.redis.hset("role_mapping", str(role.id), level.value)
        embed = discord.Embed(description=f"✅ Đã cấu hình Role {role.mention} tương đương **Level {level.value}**", color=0x00FF00)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(SystemServices(bot))
