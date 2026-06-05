import discord
from discord.ext import commands
from discord import app_commands
import json

# ==============================================================================
# 🧰 HÀM TIỆN ÍCH DATABASE & NHẬN DIỆN PHÂN QUYỀN
# ==============================================================================
def load_db():
    try:
        with open("storage.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def get_user_level(user_id, data, bot_owner_id):
    """Xác định cấp bậc quyền lực của User để giấu/hiện Menu Lệnh"""
    sys_data = data.get("system", {})
    if user_id == sys_data.get("owner_id", bot_owner_id) or user_id == sys_data.get("developer"):
        return 4 # 👑 Owner/Dev
    if user_id in sys_data.get("admins", []):
        return 3 # 💼 Admin
    if user_id in sys_data.get("staffs", []):
        return 2 # 🛡️ Staff
    return 1 # 🌍 Dân Đen

# ==============================================================================
# 📚 GIAO DIỆN SELECT MENU: SỔ TAY ĐỘNG THEO CHỨC VỤ
# ==============================================================================
class HelpSelect(discord.ui.Select):
    def __init__(self, user_level):
        options = [
            discord.SelectOption(label="Sổ Tay Dân Đen (Cơ bản)", description="Kinh tế, Sòng bạc, AI, Thế giới ngầm", emoji="🌍", value="member")
        ]
        
        # Chỉ hiện thêm Menu nếu người dùng đủ cấp bậc
        if user_level >= 2:
            options.append(discord.SelectOption(label="Sổ Tay Trị An (Staff)", description="Phạt gậy cảnh cáo, Xin ân xá, Quét rác", emoji="🛡️", value="staff"))
        if user_level >= 3:
            options.append(discord.SelectOption(label="Sổ Tay Quản Trị (Admin)", description="Sự kiện, Sòng bạc, Ngoại giao mạng lưới", emoji="💼", value="admin"))
        if user_level >= 4:
            options.append(discord.SelectOption(label="Hạch Tâm Tối Cao (Owner/Dev)", description="Shutdown, Phân quyền, Key AI, Phát sóng", emoji="👑", value="supreme"))

        super().__init__(placeholder="👇 Bấm để chọn khu vực sổ tay lệnh...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        val = self.values[0]
        embed = discord.Embed(color=discord.Color.blue())

        # 🌍 1. KHU VỰC DÂN ĐEN
        if val == "member":
            embed.title = "🌍 SỔ TAY DÂN ĐEN & CÀY CUỐC"
            embed.color = discord.Color.green()
            embed.add_field(name="💰 Kinh Tế Vĩ Mô", value="`l!bal`: Xem ví\n`l!pay`: Chuyển tiền\n`l!dep`: Gửi tiết kiệm\n`/shop`: Siêu cửa hàng", inline=False)
            embed.add_field(name="🎲 Sòng Bạc", value="`l!tx`: Tài xỉu siêu tốc\n`l!bj`: Xì dách Blackjack", inline=False)
            embed.add_field(name="🔫 Thế Giới Ngầm", value="`l!sm`: Buôn lậu\n`l!bm`: Rửa tiền bẩn\n`l!hm`: Thuê sát thủ", inline=False)
            embed.add_field(name="🤖 Trạm Thí Nghiệm AI", value="`/ai-create`: Đúc AI riêng\n`/ai-chat`: Trò chuyện\n`/ai-share`: Đăng AI lên chợ", inline=False)
            embed.add_field(name="🎭 Xã Hội & Tương Tác", value="`l!marry` / `l!divorce`: Kết hôn & Ly hôn\n`/vote-create`: Trưng cầu dân ý", inline=False)

        # 🛡️ 2. KHU VỰC TRỊ AN (STAFF)
        elif val == "staff":
            embed.title = "🛡️ SỔ TAY LỰC LƯỢNG TRỊ AN (STAFF)"
            embed.color = discord.Color.orange()
            embed.add_field(name="Cảnh cáo & Kỷ luật", value="`l!warn @user <lý_do>`: Phạt 1 gậy (3 gậy khóa nick)\n`/staff-unblacklist`: Gửi đơn xin Sếp ân xá cho mem", inline=False)
            embed.add_field(name="Tra cứu Nhật Ký", value="`l!log`: Tra cứu hộp đen 10 log phạt gần nhất", inline=False)
            embed.add_field(name="AutoMod Ngầm (Bị Động)", value="*Bot tự động chém Anti-Spam (5 tin/3s), Quét Link cấm, Banned Words.*", inline=False)

        # 💼 3. KHU VỰC QUẢN TRỊ (ADMIN)
        elif val == "admin":
            embed.title = "💼 SỔ TAY QUẢN TRỊ MÁY CHỦ (ADMIN)"
            embed.color = discord.Color.purple()
            embed.add_field(name="Tổ Chức Sự Kiện", value="`/giveaway-start`: Tạo rút thăm may mắn chống sập\n`/casino-license`: Đấu thầu mở sòng bạc tại Server", inline=False)
            embed.add_field(name="Ngoại Giao Liên Minh", value="`/partner-request`: Xin gia nhập mạng lưới Luminous\n`/partner-webhook`: Custom Avatar Trạm Phát Sóng", inline=False)

        # 👑 4. KHU VỰC TỐI CAO (OWNER/DEV)
        elif val == "supreme":
            embed.title = "👑 HẠCH TÂM ĐIỀU HÀNH TỐI CAO (SẾP)"
            embed.color = discord.Color.red()
            embed.add_field(name="Kiểm Soát Nguồn Điện", value="`/system-shutdown`: Đóng băng mạng lưới ngầm\n`/system-boot`: Gỡ bảo trì\n`/system-hq`: Sắc phong Nhà Chính", inline=False)
            embed.add_field(name="Quản Trị Nhân Sự & Lõi AI", value="`/system-staff`: Phân bổ Slot Admin/Staff\n`/system-addkey` / `/system-listkeys`: Nạp API Key AI", inline=False)
            embed.add_field(name="Điều Phối Liên Minh", value="`/partner-approve`: Duyệt đối tác\n`/partner-upgrade`: Thăng hạng VIP Premium\n`/partner-terminate`: Trục xuất Server\n`/partner-broadcast`: Phóng tin tức toàn cầu", inline=False)

        await interaction.response.edit_message(embed=embed, view=self.view)

class HelpView(discord.ui.View):
    def __init__(self, user_level):
        super().__init__(timeout=120)
        self.add_item(HelpSelect(user_level))

# ==============================================================================
# 📚 COG: SỔ TAY HƯỚNG DẪN (HELP)
# ==============================================================================
class GlobalHelp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Mở sổ tay hướng dẫn toàn thư của Luminous")
    async def help_command(self, interaction: discord.Interaction):
        data = load_db()
        
        # Nếu chưa cấu hình ID chủ thì lấy ID của người tạo Bot trên Discord Developer
        bot_owner_id = self.bot.owner_id if self.bot.owner_id else interaction.client.application.owner.id
        
        user_level = get_user_level(interaction.user.id, data, bot_owner_id)

        embed = discord.Embed(title="📚 TÀI LIỆU VẬN HÀNH LUMINOUS", description="Chào mừng đến với hệ thống vĩ mô. Hãy chọn phân khu quyền hạn của bạn ở Menu thả xuống bên dưới để tra cứu mật mã!", color=discord.Color.blue())
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        view = HelpView(user_level)
        
        # Tin nhắn ẩn ephemeral để không làm rác kênh chat
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(GlobalHelp(bot))
