import discord
from discord.ext import commands
from discord import app_commands

from config.settings import LUMINOUS_ID, COLORS
from database.redis_client import get_redis_connection

class AdvancedPunish(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def is_authorized(self, user_id):
        r = await get_redis_connection()
        for role in ["owners", "devs", "admins", "event_managers", "moderators"]:
            if await r.sismember(f"equinox:staff:{role}", str(user_id)):
                return True
        return False

    @commands.hybrid_command(name="system-punish", description="[Staff+] Lệnh cưỡng chế trị an thủ công")
    @app_commands.describe(action="Hình thức", member="Người vi phạm", duration="Thời gian (Giờ)", reason="Lý do")
    @app_commands.choices(action=[
        app_commands.Choice(name="Cảnh cáo (Warn)", value="warn"),
        app_commands.Choice(name="Cách ly (Mute)", value="mute"),
        app_commands.Choice(name="Trục xuất (Ban)", value="ban"),
        app_commands.Choice(name="Gỡ phạt (Unpunish)", value="unpunish")
    ])
    async def sys_punish(self, ctx, action: str, member: discord.Member, duration: int = 0, *, reason: str = "Không có lý do"):
        if not await self.is_authorized(ctx.author.id) and not ctx.author.guild_permissions.administrator:
            return await ctx.send("🚫 Từ chối truy cập! Lệnh dành cho cán bộ trị an.", ephemeral=True)

        r = await get_redis_connection()
        log_msg = f"[{action.upper()}] Cán bộ {ctx.author.name} thi hành xử lý với {member.name} | Lý do: {reason}"
        await r.lpush("equinox:punish:logs", log_msg)
        await r.ltrim("equinox:punish:logs", 0, 9)
        
        color = COLORS["luminous_error"] if self.bot.user.id == LUMINOUS_ID else COLORS["tenebris_error"]
        embed = discord.Embed(title="🪓 CƯỠNG CHẾ TRỊ AN", color=color)
        embed.description = f"**Đối tượng:** <@{member.id}>\n**Hình thức:** {action.upper()}\n**Lý do:** {reason}"
        
        if duration > 0 and action == "mute":
            embed.description += f"\n**Thời gian cách ly:** {duration} tiếng"
            
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="staff-unblacklist", description="[Staff+] Trình đơn xin ân xá cho tài khoản bị khóa")
    @app_commands.describe(target_id="ID của người bị khóa", reason="Lý do xin ân xá")
    async def staff_unblacklist(self, ctx, target_id: str, *, reason: str):
        if not await self.is_authorized(ctx.author.id):
            return await ctx.send("🚫 Tính năng dành riêng cho lực lượng điều phối viên!", ephemeral=True)

        embed = discord.Embed(title="📩 ĐƠN XIN ÂN XÁ KHẨN CẤP", color=0xFFFF00)
        embed.description = (
            f"**Từ Cán Bộ Trị An:** <@{ctx.author.id}>\n"
            f"**Yêu cầu mở khóa cho User ID:** `{target_id}`\n"
            f"**Lời biện hộ:**\n> *\"{reason}\"*"
        )
        embed.set_footer(text="Đơn đã được chuyển thẳng vào DMs của Owner chờ duyệt real-time.")
        
        await ctx.send(embed=embed, ephemeral=True)
        # TODO: Logic gửi thẳng tin nhắn sang DM của User ID Owner kèm UI View 2 nút bấm [Duyệt] / [Từ Chối]

async def setup(bot):
    await bot.add_cog(AdvancedPunish(bot))
