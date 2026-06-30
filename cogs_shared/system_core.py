import discord
from discord.ext import commands
import json
import os
from backend.database import EquinoxDatabase
from config.settings import OWNER_ID

class HelpSelect(discord.ui.Select):
    def __init__(self, bot):
        self.bot = bot
        options = [
            discord.SelectOption(label="Người dùng (Member)", emoji="👥"),
            discord.SelectOption(label="Đặc quyền VIP", emoji="💎"),
            discord.SelectOption(label="Kinh tế & Drama", emoji="💰"),
            discord.SelectOption(label="Quản trị (Admin/Staff)", emoji="🛡️"),
            discord.SelectOption(label="Chủ sở hữu (Owner)", emoji="👑"),
        ]
        super().__init__(placeholder="Chọn danh mục lệnh...", options=options)

    async def callback(self, interaction: discord.Interaction):
        selection = self.values[0]
        embed = discord.Embed(color=self.bot.theme_color)
        if "Member" in selection:
            embed.title = "👥 LỆNH NGƯỜI DÙNG"
            embed.description = "`/help`, `/redeem [key]`, `/bag`"
        elif "VIP" in selection:
            embed.title = "💎 ĐẶC QUYỀN VIP"
            embed.description = "`/status add`, `/livestatus [on/off]`"
        elif "Kinh tế" in selection:
            embed.title = "💰 KINH TẾ & DRAMA"
            embed.description = "`/open`, `/launder`, `/set_will`, `/assassinate`"
        elif "Quản trị" in selection:
            embed.title = "🛡️ QUẢN TRỊ"
            embed.description = "`/warn`, `/set-role`, `/doica`"
        elif "Chủ sở hữu" in selection:
            embed.title = "👑 CHỦ SỞ HỮU"
            embed.description = "`/system`, `/chat`, `/jules`"
        await interaction.response.edit_message(embed=embed)

class SystemCore(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = EquinoxDatabase(bot.redis)

    @commands.hybrid_command(name="help", description="Xem hướng dẫn sử dụng")
    async def help_cmd(self, ctx: commands.Context):
        embed = discord.Embed(title="🪐 EQUINOX NETWORK CENTER", description="Vui lòng chọn danh mục bên dưới.", color=self.bot.theme_color)
        view = discord.ui.View().add_item(HelpSelect(self.bot))
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_group(name="system", description="Lệnh quản trị hệ thống")
    async def system_group(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @system_group.command(name="force_shift", description="Cưỡng chế đổi ca")
    async def force_shift(self, ctx: commands.Context, persona: str):
        if ctx.author.id != OWNER_ID: return await ctx.send("❌ Chỉ Owner.", ephemeral=True)
        payload = {"action": "shift_change", "active_persona": persona}
        await self.bot.redis.publish("equinox_system", json.dumps(payload))
        await ctx.send(f"🚀 Lệnh cưỡng chế: Chuyển sang **{persona}**", ephemeral=True)

    @system_group.command(name="key_add", description="Tạo mã Premium Key mới")
    async def sys_add_key(self, ctx: commands.Context, duration_days: int):
        if ctx.author.id != OWNER_ID: return await ctx.send("❌ Chỉ Owner.", ephemeral=True)
        token = await self.db.create_premium_key(duration_days)
        await ctx.send(f"🔑 Đã tạo Key: `{token}` ({duration_days} ngày)", ephemeral=True)

    @system_group.command(name="api_add", description="Nạp API Key Gemini vào hệ thống")
    async def api_add(self, ctx: commands.Context, token_id: str, key_content: str):
        if ctx.author.id != OWNER_ID: return await ctx.send("❌ Chỉ Owner.", ephemeral=True)
        payload = {"key_content": key_content, "status": "active", "fail_count": 0, "cooldown_until": 0}
        await self.bot.redis.hset("api_keys", token_id, json.dumps(payload))
        await ctx.send(f"✅ Đã nạp API Key `{token_id}` vào hệ thống xoay tua thành công.", ephemeral=True)

    @commands.hybrid_command(name="redeem", description="Kích hoạt Premium Key")
    async def redeem(self, ctx: commands.Context, token: str):
        success = await self.db.redeem_premium_key(ctx.author.id, token)
        if success:
            await ctx.send("🎉 Kích hoạt thành công! Bạn đã có đặc quyền VIP.", ephemeral=True)
        else:
            await ctx.send("❌ Key không hợp lệ hoặc đã sử dụng.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(SystemCore(bot))
