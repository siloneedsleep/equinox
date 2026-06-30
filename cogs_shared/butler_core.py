import discord
from discord.ext import commands
import json
import os
from backend.database import EquinoxDatabase
from config.settings import OWNER_ID

class ButlerCore(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = EquinoxDatabase(bot.redis)

    async def check_owner(self, ctx):
        if ctx.author.id != OWNER_ID:
            await ctx.send("❌ Chỉ có **Silo (Owner)** mới có quyền ra lệnh cho Quản Gia.", ephemeral=True)
            return False
        return True

    @commands.hybrid_command(name="butler_stats", description="[Owner] Thống kê số liệu toàn hệ thống")
    async def stats(self, ctx: commands.Context):
        if not await self.check_owner(ctx): return

        # Thống kê dòng tiền (giả lập duyệt qua keys để tính tổng - thực tế nên dùng Hash riêng)
        keys = await self.bot.redis.keys("user:*:economy")
        total_aequor = 0
        total_aequis = 0
        for k in keys:
            data = await self.bot.redis.hgetall(k)
            total_aequor += int(data.get("aequor", 0))
            total_aequis += int(data.get("aequis", 0))

        fund = await self.bot.redis.hget("system:system_family_fund", "aequor") or 0

        embed = discord.Embed(title="📊 THỐNG KÊ QUẢN GIA EQUINOX", color=0x3498DB)
        embed.add_field(name="💰 Tổng Aequor (Tiền sạch)", value=f"☀️ {total_aequor:,}", inline=True)
        embed.add_field(name="🌙 Tổng Aequis (Tiền bẩn)", value=f"💀 {total_aequis:,}", inline=True)
        embed.add_field(name="🏛️ Quỹ Gia Đình", value=f"💎 {int(fund):,}", inline=False)
        embed.add_field(name="👥 Số người dùng", value=f"{len(keys)}", inline=True)

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="emergency_stop", description="[Owner] Tắt toàn bộ bot ngay lập tức")
    async def stop_all(self, ctx: commands.Context):
        if not await self.check_owner(ctx): return
        await ctx.send("🚨 **LỆNH KHẨN CẤP:** Đang dập cầu dao toàn hệ thống...")
        payload = {"action": "emergency_shutdown"}
        await self.bot.redis.publish("equinox_system", json.dumps(payload))
        # Logic shutdown thực tế sẽ được xử lý trong listener của từng bot hoặc main process

    @commands.hybrid_command(name="kick_bot", description="[Owner] Kích hoạt thủ công một thực thể")
    async def kick_bot(self, ctx: commands.Context, persona: str):
        if not await self.check_owner(ctx): return
        payload = {"action": "shift_change", "active_persona": persona}
        await self.bot.redis.publish("equinox_system", json.dumps(payload))
        await ctx.send(f"✅ Đã ra lệnh kích hoạt thực thể: **{persona}**")

    # Bot Mod: Cơ chế tự động xóa link scam (giả lập)
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot: return
        scam_patterns = ["discord.gift/", "free nitro", "bit.ly/scam"]
        if any(p in message.content.lower() for p in scam_patterns):
            await message.delete()
            await message.channel.send(f"🛡️ **Quản Gia:** Đã chặn link nghi vấn từ {message.author.mention}", delete_after=5)

async def setup(bot):
    await bot.add_cog(ButlerCore(bot))
