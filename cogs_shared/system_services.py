import discord
from discord.ext import commands
from backend.database import EquinoxDatabase
from config.settings import OWNER_ID

class SystemServices(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = EquinoxDatabase(bot.redis)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if before.roles == after.roles: return
        raw = await self.bot.redis.hgetall("role_mapping")
        if not raw: return
        lvl = 0
        for role in after.roles:
            if str(role.id) in raw:
                l = int(raw[str(role.id)])
                if l > lvl: lvl = l
        cur = await self.db.get_user_level(after.id)
        if lvl != cur: await self.db.set_user_level(after.id, lvl)

    @commands.hybrid_command(name="warn", description="[Admin+] Phạt gậy thành viên")
    async def warn_user(self, ctx: commands.Context, target: discord.Member, reason: str):
        if ctx.author.id != OWNER_ID:
            i_lvl = await self.db.get_user_level(ctx.author.id)
            t_lvl = await self.db.get_user_level(target.id)
            if t_lvl >= i_lvl:
                return await ctx.send("❌ Phản phệ! Không thể phạt cấp trên.", ephemeral=True)

        await self.bot.redis.hincrby(f"user:{target.id}", "warns", 1)
        w = await self.bot.redis.hget(f"user:{target.id}", "warns")
        emb = discord.Embed(title="⚖️ TÒA ÁN EQUINOX", color=0xFF0000)
        emb.add_field(name="Bị cáo", value=target.mention).add_field(name="Thẩm phán", value=ctx.author.mention)
        emb.add_field(name="Lý do", value=reason, inline=False)
        emb.set_footer(text=f"Tổng gậy: {w} 🚩")
        await ctx.send(embed=emb)

    @commands.hybrid_command(name="set-role", description="[Owner] Ánh xạ Role với Level")
    async def set_role_map(self, ctx: commands.Context, level: int, role: discord.Role):
        if ctx.author.id != OWNER_ID: return await ctx.send("❌ Chỉ Owner.", ephemeral=True)
        await self.bot.redis.hset("role_mapping", str(role.id), level)
        await ctx.send(f"✅ Role {role.name} -> Level {level}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(SystemServices(bot))
