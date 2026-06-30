import discord
from discord.ext import commands
from backend.database import EquinoxDatabase
from backend.economy_engine import EconomyEngine

class EconomyUI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = EquinoxDatabase(bot.redis)
        self.engine = EconomyEngine(self.db)

    @commands.hybrid_command(name="bag", description="Xem túi đồ và tài sản hiện có")
    async def view_bag(self, ctx: commands.Context):
        user_id = ctx.author.id
        balance = await self.db.get_balance(user_id)
        bag = await self.db.get_bag(user_id)
        
        embed = discord.Embed(title=f"🎒 TÚI ĐỒ CỦA {ctx.author.display_name}", color=self.bot.theme_color)
        embed.add_field(name="Tiền Sạch (Aequor)", value=f"☀️ {balance['aequor']:,}", inline=True)
        embed.add_field(name="Tiền Bẩn (Aequis)", value=f"🌙 {balance['aequis']:,}", inline=True)
        
        if bag:
            items_str = ""
            for item_id, item in bag.items():
                items_str += f"• **{item['type']}** | ID: `{item_id[:8]}`\n"
            embed.add_field(name="Vật Phẩm", value=items_str, inline=False)
        else:
            embed.add_field(name="Vật Phẩm", value="Trống rỗng.", inline=False)
            
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="open", description="Mở Star Pouch (Túi mù tiền tệ)")
    async def open_pouch(self, ctx: commands.Context, item_id: str):
        user_id = ctx.author.id
        bag = await self.db.get_bag(user_id)
        
        target_id = None
        for full_id in bag:
            if full_id.startswith(item_id):
                target_id = full_id
                break

        if not target_id or bag[target_id]["type"] != "Star Pouch":
            return await ctx.send("❌ Không tìm thấy Star Pouch này trong túi.", ephemeral=True)
            
        result = await self.engine.open_star_pouch(user_id, self.bot.persona)
        await self.db.remove_item_from_bag(user_id, target_id)
        
        icon = "☀️" if result["currency"] == "aequor" else "🌙"
        name = "Tiền Sạch" if result["currency"] == "aequor" else "Tiền Bẩn"
        
        embed = discord.Embed(title="✨ KẾT QUẢ MỞ TÚI MÙ", color=self.bot.theme_color)
        embed.description = f"Bạn đã nhận được: **{result['amount']:,}** {icon} {name}\n\n*(Nội suy theo ca trực của {self.bot.persona})*"
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="launder", description="Rửa tiền bẩn (Phí 15-25%)")
    async def launder(self, ctx: commands.Context, amount: int):
        if amount <= 0: return await ctx.send("❌ Số tiền không hợp lệ.", ephemeral=True)

        result = await self.engine.launder_money(ctx.author.id, amount)
        if not result["success"]:
            return await ctx.send(f"❌ {result['reason']}", ephemeral=True)

        embed = discord.Embed(title="🏦 TRẠM RỬA TIỀN CÔNG TÂM", color=0x2ECC71)
        embed.add_field(name="Số tiền đã rửa", value=f"{amount:,} Aequis", inline=False)
        embed.add_field(name="Tiền sạch thực nhận", value=f"{result['clean_received']:,} Aequor", inline=False)
        embed.add_field(name="Phí nộp Quỹ Gia Đình", value=f"{result['fee_paid']:,} Aequor ({result['fee_percent']}%)", inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(EconomyUI(bot))
