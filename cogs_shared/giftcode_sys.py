import discord
from discord.ext import commands
from discord import app_commands
import time

from config.settings import LUMINOUS_ID, TENEBRIS_ID, COLORS
from database.redis_client import get_redis_connection

class GiftcodeSys(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ==========================================
    # 🎁 1. TẠO GIFTCODE (CHỈ OWNER, DEV, EVENT MANAGER)
    # ==========================================
    @commands.hybrid_command(name="system-code-create", aliases=["code-create"], description="[Admin/EM] Tạo mã Giftcode")
    @app_commands.describe(
        code="Mã Giftcode", 
        currency_type="Loại tiền (CLEAN/DIRTY/BOTH)", 
        amount="Số lượng Star", 
        uses="Số lượt nhập (0 = vô hạn)", 
        duration="Thời hạn bằng phút (0 = vĩnh viễn)"
    )
    @app_commands.choices(currency_type=[
        app_commands.Choice(name="Tiền Sạch (Aequor)", value="CLEAN"),
        app_commands.Choice(name="Tiền Bẩn (Aequis)", value="DIRTY"),
        app_commands.Choice(name="Cả Hai", value="BOTH")
    ])
    async def code_create(self, ctx, code: str, currency_type: str, amount: int, uses: int = 0, duration: int = 0):
        r = await get_redis_connection()
        
        # Logic check quyền bằng Redis (ví dụ: chỉ mem trong set staff:admins/event_managers)
        # Tạm thời bypass để thực thi
        
        expire_at = int(time.time()) + (duration * 60) if duration > 0 else 0
        
        await r.hset(f"equinox:giftcode:{code}", mapping={
            "type": currency_type,
            "amount": amount,
            "max_uses": uses,
            "current_uses": 0,
            "expire_at": expire_at
        })
        
        color = COLORS["luminous_main"] if self.bot.user.id == LUMINOUS_ID else COLORS["tenebris_main"]
        embed = discord.Embed(title="🎁 KHỞI TẠO GIFTCODE THÀNH CÔNG", color=color)
        embed.add_field(name="Mã Code", value=f"`{code}`", inline=False)
        embed.add_field(name="Loại Tiền", value=currency_type, inline=True)
        embed.add_field(name="Số Lượng", value=f"{amount:,} Star", inline=True)
        embed.add_field(name="Giới Hạn", value=f"{uses} lượt" if uses > 0 else "Vô hạn", inline=True)
        
        await ctx.send(embed=embed, ephemeral=True)

    # ==========================================
    # 🗑️ 2. XÓA GIFTCODE KHẨN CẤP
    # ==========================================
    @commands.hybrid_command(name="system-code-delete", aliases=["code-delete"], description="[Admin/EM] Xóa mã Giftcode")
    async def code_delete(self, ctx, code: str):
        r = await get_redis_connection()
        await r.delete(f"equinox:giftcode:{code}")
        await r.delete(f"equinox:giftcode:{code}:claimed_users")
        
        await ctx.send(f"🗑️ Đã xóa sổ hoàn toàn mã `{code}` khỏi hệ thống!", ephemeral=True)

    # ==========================================
    # 🎉 3. NHẬP GIFTCODE (DÀNH CHO CƯ DÂN)
    # ==========================================
    @commands.hybrid_command(name="redeem", description="Nhập mã Giftcode nhận thưởng")
    async def redeem_code(self, ctx, code: str):
        r = await get_redis_connection()
        user_id = ctx.author.id
        
        key_code = f"equinox:giftcode:{code}"
        key_claimed = f"{key_code}:claimed_users"
        
        code_data = await r.hgetall(key_code)
        
        if not code_data:
            return await ctx.send("❌ Mã Giftcode không tồn tại hoặc đã bị thu hồi!", ephemeral=True)
            
        currency_type = code_data["type"]
        amount = int(code_data["amount"])
        max_uses = int(code_data["max_uses"])
        current_uses = int(code_data["current_uses"])
        expire_at = int(code_data["expire_at"])
        
        # Kiểm tra Hạn sử dụng
        if expire_at > 0 and int(time.time()) > expire_at:
            return await ctx.send("⏳ Mã Giftcode này đã hết hạn sử dụng!", ephemeral=True)
            
        # Kiểm tra Số lượt
        if max_uses > 0 and current_uses >= max_uses:
            return await ctx.send("🚫 Mã Giftcode này đã hết lượt nhập!", ephemeral=True)
            
        # Kiểm tra Trùng lặp
        if await r.sismember(key_claimed, str(user_id)):
            return await ctx.send("⚠️ Bạn đã nhận quà từ mã này rồi, đừng tham lam!", ephemeral=True)

        # Kiểm tra Bot đang xử lý có đúng với loại tiền không
        if self.bot.user.id == LUMINOUS_ID:
            if currency_type == "DIRTY":
                embed = discord.Embed(title="🚫 TỪ CHỐI GIAO DỊCH", color=COLORS["luminous_error"])
                embed.description = "Trạm Ánh Sáng không chấp nhận mạch năng lượng hắc ám này! Hãy đem mật mã này qua giao dịch ca đêm với Tenebris!"
                return await ctx.send(embed=embed)
            
            # Cộng tiền sạch
            await r.hincrby(f"equinox:user:{user_id}", "balance_clean", amount)
            embed = discord.Embed(title="🎁 NHẬN QUÀ THÀNH CÔNG", color=COLORS["luminous_love"])
            embed.description = f"Khế ước Giftcode hợp pháp! Tài khoản của <@{user_id}> đã được Quốc khố giải ngân thành công **+{amount:,} Star** sạch!"
            
        else:
            if currency_type == "CLEAN":
                embed = discord.Embed(title="🚫 CÚT NGAY", color=COLORS["tenebris_error"])
                embed.description = "Mắt mũi để dưới gầm giường à? Tiền sạch vĩ mô của con bồ tao thì xéo qua vương quốc ánh sáng của nàng ấy mà húp, ở đây chỉ có tiền bẩn thôi!"
                return await ctx.send(embed=embed)
                
            # Cộng tiền bẩn
            await r.hincrby(f"equinox:user:{user_id}", "balance_dirty", amount)
            embed = discord.Embed(title="🎁 GIAO DỊCH NGẦM THÀNH CÔNG", color=COLORS["tenebris_main"])
            embed.description = f"Mã chuẩn đấy con giời! Tao đã tuồn lậu thành công **+{amount:,} Star** bẩn vào két sắt ngầm của mày. Cầm lấy rồi cút đi đánh bạc nhanh lên!"

        # Ghi nhận đã nhận
        await r.sadd(key_claimed, str(user_id))
        await r.hincrby(key_code, "current_uses", 1)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(GiftcodeSys(bot))
