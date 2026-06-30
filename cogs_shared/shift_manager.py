import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import datetime
import pytz
import os
from config.settings import OWNER_ID

class ShiftManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.timezone = pytz.timezone('Asia/Ho_Chi_Minh')
        self.auto_shift_checker.start()

    def cog_unload(self):
        self.auto_shift_checker.cancel()

    @tasks.loop(seconds=30)
    async def auto_shift_checker(self):
        if self.bot.persona != "Luminous": return
        now = datetime.datetime.now(self.timezone)
        target = "Luminous" if 6 <= now.hour < 18 else "Tenebris"
        cur = await self.bot.redis.get("system:active_persona")
        if cur != target:
            payload = {"action": "shift_change", "active_persona": target}
            await self.bot.redis.publish("equinox_system", json.dumps(payload))
            await self.bot.redis.set("system:active_persona", target)

    @auto_shift_checker.before_loop
    async def before_auto_shift(self):
        await self.bot.wait_until_ready()

    @commands.hybrid_command(name="doica", description="[Staff+] Đổi ca thủ công")
    @app_commands.choices(persona=[app_commands.Choice(name="Luminous", value="Luminous"), app_commands.Choice(name="Tenebris", value="Tenebris")])
    async def manual_shift_change(self, ctx: commands.Context, persona: str):
        if ctx.author.id != OWNER_ID:
            lvl = int(await self.bot.redis.hget(f"user:{ctx.author.id}", "level") or 0)
            if lvl < 1: return await ctx.send("❌ Thiếu quyền.", ephemeral=True)

        payload = {"action": "shift_change", "active_persona": persona}
        await self.bot.redis.publish("equinox_system", json.dumps(payload))
        await self.bot.redis.set("system:active_persona", persona)
        await ctx.send(f"🔄 Đã chuyển sang: **{persona}**")

async def setup(bot):
    await bot.add_cog(ShiftManager(bot))
