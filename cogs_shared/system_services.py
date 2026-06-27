import discord
from discord.ext import commands
from discord import app_commands
import os
from backend.database import EquinoxDatabase
from backend.presence_proxy import ProxyPresenceManager

class SystemServices(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = EquinoxDatabase(bot.redis)
        self.proxy_manager = ProxyPresenceManager(bot.redis)
        self.proxy_task = None

    async def cog_load(self):
        if self.bot.persona == "Luminous":
            self.proxy_task = self.bot.loop.create_task(self.proxy_manager.sync_loop())

    async def cog_unload(self):
        if self.proxy_task:
            self.proxy_task.cancel()

    @app_commands.command(name="set-role", description="Đồng bộ Role Discord với Level hệ thống (Độc quyền Owner)")
    @app_commands.choices(level=[
        app_commands.Choice(name="Level 1 (Staff / Event)", value=1),
        app_commands.Choice(name="Level 2 (Admin / Tòa Án)", value=2),
        app_commands.Choice(name="Level 3 (Manager)", value=3)
    ])
    async def set_role_map(self, interaction: discord.Interaction, level: app_commands.Choice[int], role: discord.Role):
        owner_id = int(os.environ.get("OWNER_ID", 0))
        if interaction.user.id != owner_id:
            await interaction.response.send_message("❌ Từ chối truy cập. Chỉ Owner mới có quyền phân cấp hệ thống.", ephemeral=True)
            return
        
        await self.bot.redis.hset("role_mapping", str(role.id), level.value)
        await interaction.response.send_message(f"✅ Đã cấu hình Role {role.mention} tương đương **Level {level.value}** trên toàn hệ sinh thái.", ephemeral=True)

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
        if highest_level > current_db_level:
            await self.db.set_user_level(after.id, highest_level)

async def setup(bot):
    await bot.add_cog(SystemServices(bot))
