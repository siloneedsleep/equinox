import discord
from discord.ext import commands
from discord import app_commands
import time

from config.settings import LUMINOUS_ID, COLORS
from database.redis_client import get_redis_connection

class EconomyClean(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ==========================================
    # 💰 1. KIỂM TRA SỐ DƯ (BALANCE)
    # ==========================================
    @commands.hybrid_command(name="balance", aliases=["bal"], description="Kiểm tra ví tiền sạch và tài khoản tiết kiệm")
    async def check_balance(self, ctx, user: discord.Member = None):
        target_user = user or ctx.author
        r = await get_redis_connection()
        
        # Lấy dữ liệu từ Redis (nếu không có thì trả về 0)
        user_data = await r.hgetall(f"equinox:user:{target_user.id}")
        bal_clean = int(user_data.get("balance_clean", 0))
        bank_saving = int(user_data.get("bank_saving", 0))
        
        embed = discord.Embed(title="💳 TÀI KHOẢN CÔNG DÂN THẦN ĐIỆN", color=COLORS["luminous_main"])
        embed.set_thumbnail(url=target_user.display_avatar.url)
        embed.description = f"Hồ sơ tài chính của <@{target_user.id}> đã được xác thực minh bạch!"
        
        embed.add_field(name="🪙 Tiền Mặt (Aequor)", value=f"**{bal_clean:,} Star**", inline=True)
        embed.add_field(name="🏦 Tiết Kiệm (Ngân Hàng)", value=f"**{bank_saving:,} Star**", inline=True)
        embed.set_footer(text="Mạng lưới kinh tế vĩ mô Equinox Network")
        
        await ctx.send(embed=embed)

    # ==========================================
    # 💸 2. CHUYỂN TIỀN SẠCH (PAY)
    # ==========================================
    @commands.hybrid_command(name="pay", description="Chuyển tiền sạch cho công dân khác")
    @app_commands.describe(user="Người nhận", amount="Số tiền muốn chuyển")
    async def pay_money(self, ctx, user: discord.Member, amount: int):
        if amount <= 0:
            return await ctx.send("🚫 Số tiền giao dịch phải lớn hơn 0!", ephemeral=True)
            
        if user.id == ctx.author.id:
            return await ctx.send("🚫 Bạn không thể tự chuyển tiền cho chính mình!", ephemeral=True)

        if user.bot:
            return await ctx.send("🚫 Không thể thực hiện giao dịch với thực thể BOT!", ephemeral=True)

        r = await get_redis_connection()
        sender_key = f"equinox:user:{ctx.author.id}"
        receiver_key = f"equinox:user:{user.id}"
        
        # Lấy số dư hiện tại
        sender_bal = int(await r.hget(sender_key, "balance_clean") or 0)
        
        if sender_bal < amount:
            return await ctx.send(f"🚫 Giao dịch thất bại! Bạn chỉ có **{sender_bal:,} Star**, không đủ để chuyển **{amount:,} Star**.", ephemeral=True)

        # Tính thuế giao dịch (Mặc định 5%)
        tax_rate = 0.05
        
        # Check khế ước phu thê để giảm/miễn thuế
        sender_partner = await r.hget(sender_key, "partner_id")
        if sender_partner == str(user.id):
            ring_type = await r.hget(sender_key, "ring_type")
            if ring_type == "diamond":
                tax_rate = 0.0  # Miễn thuế 100%
            elif ring_type == "gold":
                tax_rate = 0.01 # Phí 1%
            elif ring_type == "silver":
                tax_rate = 0.02 # Phí 2%
                
        tax_amount = int(amount * tax_rate)
        final_amount = amount - tax_amount

        # Thực hiện chuyển tiền qua Redis Transaction (Pipeline)
        async with r.pipeline(transaction=True) as pipe:
            pipe.hincrby(sender_key, "balance_clean", -amount)
            pipe.hincrby(receiver_key, "balance_clean", final_amount)
            # Tùy chọn: Cộng tiền thuế vào quỹ Quốc khố ở đây
            await pipe.execute()

        embed = discord.Embed(title="✅ GIAO DỊCH THÀNH CÔNG", color=COLORS["luminous_info"])
        embed.description = f"<@{ctx.author.id}> đã chuyển thành công tiền sạch cho <@{user.id}>."
        embed.add_field(name="Số tiền chuyển", value=f"{amount:,} Star", inline=True)
        embed.add_field(name="Thuế giao dịch", value=f"{tax_amount:,} Star ({int(tax_rate*100)}%)", inline=True)
        embed.add_field(name="Thực nhận", value=f"**{final_amount:,} Star**", inline=False)
        
        await ctx.send(embed=embed)

    # ==========================================
    # 🏦 3. GỬI TIỀN VÀO NGÂN HÀNG (DEPOSIT)
    # ==========================================
    @commands.hybrid_command(name="deposit", aliases=["dep"], description="Gửi tiền mặt vào Ngân Hàng Tiết Kiệm")
    @app_commands.describe(amount="Số tiền muốn gửi (Nhập 'all' để gửi hết)")
    async def deposit_money(self, ctx, amount: str):
        r = await get_redis_connection()
        user_key = f"equinox:user:{ctx.author.id}"
        
        bal_clean = int(await r.hget(user_key, "balance_clean") or 0)
        
        if bal_clean <= 0:
            return await ctx.send("🚫 Bạn không có đồng Star nào để gửi tiết kiệm!", ephemeral=True)
            
        if amount.lower() == "all":
            dep_amount = bal_clean
        else:
            try:
                dep_amount = int(amount)
            except ValueError:
                return await ctx.send("🚫 Số lượng không hợp lệ!", ephemeral=True)
                
            if dep_amount <= 0:
                return await ctx.send("🚫 Số tiền gửi phải lớn hơn 0!", ephemeral=True)
                
            if dep_amount > bal_clean:
                return await ctx.send(f"🚫 Bạn chỉ có **{bal_clean:,} Star** tiền mặt!", ephemeral=True)

        async with r.pipeline(transaction=True) as pipe:
            pipe.hincrby(user_key, "balance_clean", -dep_amount)
            pipe.hincrby(user_key, "bank_saving", dep_amount)
            # Reset thời gian tính lãi khi có thay đổi gốc
            pipe.hset(user_key, "last_interest_claim", int(time.time()))
            await pipe.execute()

        embed = discord.Embed(title="🏦 GỬI TIẾT KIỆM THÀNH CÔNG", color=COLORS["luminous_main"])
        embed.description = f"<@{ctx.author.id}> đã gửi **{dep_amount:,} Star** vào ngân hàng vĩ mô. Tiền của bạn sẽ sinh lời an toàn theo thời gian!"
        await ctx.send(embed=embed)

    # ==========================================
    # 🏧 4. RÚT TIỀN TỪ NGÂN HÀNG (WITHDRAW)
    # ==========================================
    @commands.hybrid_command(name="withdraw", aliases=["with"], description="Rút tiền từ Ngân Hàng Tiết Kiệm")
    @app_commands.describe(amount="Số tiền muốn rút (Nhập 'all' để rút hết)")
    async def withdraw_money(self, ctx, amount: str):
        r = await get_redis_connection()
        user_key = f"equinox:user:{ctx.author.id}"
        
        bank_saving = int(await r.hget(user_key, "bank_saving") or 0)
        
        if bank_saving <= 0:
            return await ctx.send("🚫 Ngân hàng của bạn đang trống rỗng!", ephemeral=True)
            
        if amount.lower() == "all":
            with_amount = bank_saving
        else:
            try:
                with_amount = int(amount)
            except ValueError:
                return await ctx.send("🚫 Số lượng không hợp lệ!", ephemeral=True)
                
            if with_amount <= 0:
                return await ctx.send("🚫 Số tiền rút phải lớn hơn 0!", ephemeral=True)
                
            if with_amount > bank_saving:
                return await ctx.send(f"🚫 Bạn chỉ có **{bank_saving:,} Star** trong ngân hàng!", ephemeral=True)

        # Tính toán trả lãi trước khi rút tiền (Ví dụ: 0.1% mỗi giờ)
        last_claim = int(await r.hget(user_key, "last_interest_claim") or time.time())
        hours_passed = (int(time.time()) - last_claim) // 3600
        interest = 0
        
        if hours_passed > 0:
            interest = int(bank_saving * (0.001 * hours_passed)) # 0.1% / giờ
            
        final_withdraw = with_amount + interest

        async with r.pipeline(transaction=True) as pipe:
            pipe.hincrby(user_key, "bank_saving", -with_amount)
            pipe.hincrby(user_key, "balance_clean", final_withdraw)
            pipe.hset(user_key, "last_interest_claim", int(time.time()))
            await pipe.execute()

        embed = discord.Embed(title="🏧 RÚT TIỀN THÀNH CÔNG", color=COLORS["luminous_info"])
        desc = f"<@{ctx.author.id}> đã rút **{with_amount:,} Star** từ ngân hàng."
        if interest > 0:
            desc += f"\n📈 Lãi suất sinh lời cộng thêm: **+{interest:,} Star**"
        embed.description = desc
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(EconomyClean(bot))
