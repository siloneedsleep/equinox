import discord
from discord.ext import commands
from discord import app_commands

from config.settings import LUMINOUS_ID, COLORS
from database.redis_client import get_redis_connection

class SystemChannel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="system-channel", description="[Admin+] Quản lý phân khu lệnh tại kênh chat")
    @app_commands.describe(
        action="Mở khóa hay Khóa chặn", 
        channel="Kênh tác động", 
        category="Phân khu lệnh", 
        except_cmd="Lệnh ngoại lệ (nếu có)"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="ALLOW (Mở khóa)", value="ALLOW"),
        app_commands.Choice(name="BLOCK (Khóa chặn)", value="BLOCK")
    ], category=[
        app_commands.Choice(name="Kinh Tế Công Khai", value="ECONOMY"),
        app_commands.Choice(name="Thế Giới Ngầm & Casino", value="CASINO"),
        app_commands.Choice(name="Tất Cả Lệnh", value="ALL")
    ])
    async def sys_channel(self, ctx, action: str, channel: discord.TextChannel, category: str, except_cmd: str = None):
        r = await get_redis_connection()
        user_id = str(ctx.author.id)
        
        is_admin = await r.sismember("equinox:staff:admins", user_id)
        is_em = await r.sismember("equinox:staff:event_managers", user_id)
        is_dev = await r.sismember("equinox:staff:devs", user_id)
        is_owner = await r.sismember("equinox:staff:owners", user_id)
        
        if not (is_admin or is_em or is_dev or is_owner or ctx.author.guild_permissions.manage_channels):
            return await ctx.send("🚫 Quyền truy cập bị từ chối!", ephemeral=True)
        
        key = f"equinox:channel_lock:{channel.id}"
        
        if action == "BLOCK":
            await r.hset(key, category, except_cmd or "NONE")
            msg = f"🔒 Đã KHÓA phân khu `{category}` tại <#{channel.id}>."
            if except_cmd: 
                msg += f" (Ngoại trừ lệnh: `{except_cmd}`)"
        else:
            await r.hdel(key, category)
            msg = f"✅ Đã MỞ KHÓA phân khu `{category}` tại <#{channel.id}>."
            
        color = COLORS["luminous_info"] if self.bot.user.id == LUMINOUS_ID else COLORS["tenebris_action"]
        embed = discord.Embed(title="📺 QUẢN LÝ PHÂN KHU KÊNH CHAT", description=msg, color=color)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(SystemChannel(bot))
