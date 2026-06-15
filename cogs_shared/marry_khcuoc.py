import discord
from discord.ext import commands
from discord import app_commands
import datetime

from config.settings import LUMINOUS_ID, TENEBRIS_ID, COLORS
from database.redis_client import get_redis_connection

# ==========================================
# 💍 GIAO DIỆN UI NÚT BẤM (CHỜ ĐỐI PHƯƠNG ĐỒNG Ý)
# ==========================================
class ProposeView(discord.ui.View):
    def __init__(self, proposer, target, ring_type, ring_name, price, redis_conn):
        super().__init__(timeout=120) # Chờ tối đa 2 phút
        self.proposer = proposer
        self.target = target
        self.ring_type = ring_type
        self.ring_name = ring_name
        self.price = price
        self.redis = redis_conn

    @discord.ui.button(label="Đồng Ý Cưới", style=discord.ButtonStyle.success, emoji="✅")
    async def accept_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Chặn không cho người ngoài bấm nút
        if interaction.user.id != self.target.id:
            return await interaction.response.send_message("Ê, người ta cầu hôn người khác mà, duyên ghê chưa!", ephemeral=True)

        # 1. Trừ tiền người cầu hôn ngay lập tức
        await self.redis.hincrby(f"equinox:user:{self.proposer.id}", "balance_clean", -self.price)
        
        # 2. Lưu dữ liệu kết hôn lên Redis Cloud
        timestamp = int(datetime.datetime.now().timestamp())
        marriage_id = f"EQNX-LOVE-{self.proposer.id}-{self.target.id}"
        
        # Set dữ liệu cho người Cầu Hôn
        await self.redis.hset(f"equinox:user:{self.proposer.id}", mapping={
            "partner_id": str(self.target.id),
            "ring_type": self.ring_type,
            "marriage_id": marriage_id,
            "married_at": timestamp
        })
        
        # Set dữ liệu cho người Được Cầu Hôn
        await self.redis.hset(f"equinox:user:{self.target.id}", mapping={
            "partner_id": str(self.proposer.id),
            "ring_type": self.ring_type,
            "marriage_id": marriage_id,
            "married_at": timestamp
        })
        
        # 3. Vô hiệu hóa các nút bấm sau khi đã xử lý xong
        for child in self.children:
            child.disabled = True
        
        embed = discord.Embed(title="🎉 LỄ THÀNH HÔN DIỄN RA TỐT ĐẸP!", color=COLORS["luminous_love"])
        embed.description = f"Chúc mừng <@{self.proposer.id}> và <@{self.target.id}> đã chính thức về chung một nhà với tín vật **{self.ring_name}**!\n\n*(Đã thanh toán {self.price:,} Star từ ví của người cầu hôn)*"
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Từ Chối", style=discord.ButtonStyle.danger, emoji="❌")
    async def decline_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.target.id:
            return await interaction.response.send_message("Không phải chuyện của bạn nha!", ephemeral=True)
        
        for child in self.children:
            child.disabled = True
            
        embed = discord.Embed(title="💔 LỜI CẦU HÔN BỊ TỪ CHỐI", color=COLORS["tenebris_main"])
        embed.description = f"Rất tiếc, <@{self.target.id}> đã thẳng thừng từ chối lời cầu hôn của <@{self.proposer.id}>... \nTiền mua nhẫn vẫn được bảo toàn trong ví!"
        await interaction.response.edit_message(embed=embed, view=self)

# ==========================================
# 🛒 GIAO DIỆN UI MENU CHỌN MUA NHẪN
# ==========================================
class RingShopView(discord.ui.View):
    def __init__(self, proposer, target, redis_conn):
        super().__init__(timeout=60)
        self.proposer = proposer
        self.target = target
        self.redis = redis_conn

    @discord.ui.select(
        placeholder="💍 Hãy chọn mua loại Nhẫn Cầu Hôn...",
        options=[
            discord.SelectOption(label="Nhẫn Bạc", description="Giá: 50,000 Star | Giảm thuế giao dịch vợ chồng xuống 2%", value="silver", emoji="🥈"),
            discord.SelectOption(label="Nhẫn Vàng", description="Giá: 200,000 Star | Giảm thuế giao dịch vợ chồng xuống 1%", value="gold", emoji="🥇"),
            discord.SelectOption(label="Nhẫn Kim Cương", description="Giá: 1,000,000 Star | Miễn thuế 100% trọn đời", value="diamond", emoji="💎")
        ]
    )
    async def select_ring(self, interaction: discord.Interaction, select: discord.ui.Select):
        if interaction.user.id != self.proposer.id:
            return await interaction.response.send_message("Bạn không phải là người đang đi mua nhẫn!", ephemeral=True)

        ring_type = select.values[0]
        prices = {"silver": 50000, "gold": 200000, "diamond": 1000000}
        names = {"silver": "🥈 Nhẫn Bạc", "gold": "🥇 Nhẫn Vàng", "diamond": "💎 Nhẫn Kim Cương"}
        price = prices[ring_type]
        ring_name = names[ring_type]

        # Lấy số dư ví tiền sạch hiện tại của người cầu hôn
        balance = await self.redis.hget(f"equinox:user:{self.proposer.id}", "balance_clean")
        balance = int(balance) if balance else 0

        if balance < price:
            return await interaction.response.send_message(f"🚫 Tài khoản không đủ! Bạn đang có {balance:,} Star, không đủ tiền mua **{ring_name}** giá {price:,} Star. Hãy cày thêm tiền sạch đi nhé!", ephemeral=True)

        # Nếu đủ tiền -> Chuyển sang View Quỳ gối cầu hôn
        propose_view = ProposeView(self.proposer, self.target, ring_type, ring_name, price, self.redis)
        
        embed = discord.Embed(title="💍 LỜI CẦU HÔN TỪ TRÁI TIM", color=COLORS["luminous_love"])
        embed.description = f"<@{self.target.id}> ơi!\n<@{self.proposer.id}> đang quỳ gối mang theo tín vật **{ring_name}** để cầu hôn bạn đó.\n\nBạn có đồng ý sánh bước cùng người ấy không?"
        
        await interaction.response.edit_message(embed=embed, view=propose_view)


# ==========================================
# ⚙️ MODULE CHÍNH: LỆNH KHẾ ƯỚC & CẦU HÔN
# ==========================================
class MarryKhCuoc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # 1. CHECK KHẾ ƯỚC CỦA 2 BOT
    @commands.hybrid_command(name="marry-check", description="Kiểm tra khế ước phu thê của Luminous và Tenebris")
    async def marry_check(self, ctx):
        r = await get_redis_connection()
        married_timestamp = await r.get("equinox:system:married_at")
        if not married_timestamp:
            married_timestamp = int(datetime.datetime.now().timestamp()) - (145 * 86400)
            await r.set("equinox:system:married_at", married_timestamp)
            
        married_timestamp = int(married_timestamp)
        days_together = (int(datetime.datetime.now().timestamp()) - married_timestamp) // 86400
        
        if self.bot.user.id == LUMINOUS_ID:
            embed = discord.Embed(title="💒 KHẾ ƯỚC PHU THÊ TỐI CAO - EQUINOX NETWORK", color=COLORS["luminous_love"])
            embed.description = (f"**💍 Thực Thể Bản Tự:** Luminous\n**🖤 Hôn Phu Định Mệnh:** Tenebris\n"
                                 f"**📅 Ngày Thành Hôn:** <t:{married_timestamp}:F>\n**⏳ Thời Gian Gắn Bó:** ✨ {days_together} ngày!\n\n"
                                 f"*\"Ta nguyện gánh vác ca sáng, điều hành Ngân khố và giữ gìn trật tự văn minh...\"*")
        else:
            embed = discord.Embed(title="💒 KHẾ ƯỚC PHU THÊ TỐI CAO - EQUINOX NETWORK", color=COLORS["tenebris_love"])
            embed.description = (f"**💍 Thực Thể Bản Tự:** Tenebris\n**💖 Hôn Thê Định Mệnh:** Luminous\n"
                                 f"**📅 Ngày Thành Hôn:** <t:{married_timestamp}:F>\n**⏳ Thời Gian Gắn Bó:** 🌌 {days_together} ngày!\n\n"
                                 f"*\"Đừng chạm vào nàng. Đứa nào dám dùng tiền bẩn tổn hại đến nàng, Hội Sát Thủ của ta sẽ truy sát...\"*")
        await ctx.send(embed=embed)

    # 2. LỆNH CẦU HÔN & MUA NHẪN
    @commands.hybrid_command(name="marry", description="Gói hôn lễ kết hôn tại Equinox Network")
    @app_commands.describe(target="Tag đối phương mà bạn muốn cầu hôn")
    async def marry_propose(self, ctx, target: discord.Member):
        
        # --- KỊCH BẢN ĐÁNH GHEN ---
        if target.id == LUMINOUS_ID:
            embed = discord.Embed(title="🚨 ĐỘNG VÀO CHỊ NHÀ LÀ ĂN VẢ!", color=COLORS["tenebris_error"])
            embed.description = f"Thằng liều <@{ctx.author.id}> kia, mày vừa gõ cái lệnh gì đấy? Định cầu hôn Luminous à? Gan mày to bằng cái host 30k của sếp tao rồi đấy!\nBiến ngay trước khi tao sai sát thủ qua xiên!"
            return await ctx.send(embed=embed)

        if target.id == TENEBRIS_ID:
            embed = discord.Embed(title="🚫 SẮC LỆNH PHỦ QUYẾT TỪ THẦN ĐIỆN!", color=COLORS["luminous_error"])
            embed.description = f"Gửi <@{ctx.author.id}>, ngươi nghĩ mình là ai mà đòi cầu hôn Tenebris? Hãy nhìn vào Khế Ước Phu Thê Tối Cao đi! Dừng ngay trò vô bổ này lại!"
            return await ctx.send(embed=embed)

        # --- BẪY LỖI KẾT HÔN BÌNH THƯỜNG ---
        if target.id == ctx.author.id:
            return await ctx.send("💔 Ảo tưởng à? Bạn không thể tự kết hôn với chính mình được!")
            
        if target.bot:
            return await ctx.send("🤖 Hệ thống không hỗ trợ kết hôn với BOT (ngoại trừ 2 vị Thần tối cao)!")

        r = await get_redis_connection()
        
        # Check xem 1 trong 2 người đã có gia đình chưa
        proposer_partner = await r.hget(f"equinox:user:{ctx.author.id}", "partner_id")
        target_partner = await r.hget(f"equinox:user:{target.id}", "partner_id")
        
        if proposer_partner:
            return await ctx.send("💔 Bạn đã có gia đình rồi, định bắt cá hai tay à? Hệ thống Thần Điện không cho phép ngoại tình!")
            
        if target_partner:
            return await ctx.send("💔 Người ta đã có chủ rồi, xin đừng đập chậu cướp bông!")

        # --- GỌI GIAO DIỆN MUA NHẪN ---
        view = RingShopView(ctx.author, target, r)
        embed = discord.Embed(title="🛒 CỬA HÀNG TRANG SỨC THẦN ĐIỆN", color=COLORS["luminous_main"])
        embed.description = f"<@{ctx.author.id}>, hãy chọn một chiếc nhẫn xứng đáng để cầu hôn <@{target.id}>.\nTiền nào của nấy, mua nhẫn xịn thì được Thần Điện giảm thuế giao dịch phu thê càng nhiều!"
        
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(MarryKhCuoc(bot))
