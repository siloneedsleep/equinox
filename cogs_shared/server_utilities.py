import os
import random
import discord
from discord import app_commands
from discord.ext import commands
from database.redis_client import get_redis_connection

class ServerUtilities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Hàm check quyền Admin/Owner nhanh
    async def _is_staff(self, interaction: discord.Interaction, r) -> bool:
        env_owner = os.getenv("OWNER_DISCORD_ID")
        if env_owner and interaction.user.id == int(env_owner):
            return True
        # Check trong Set owners hoặc Hash staff_roles tùy cấu trúc cũ của sếp
        is_owner = await r.sismember("equinox:staff:owners", interaction.user.id)
        if is_owner:
            return True
        return interaction.user.guild_permissions.manage_guild

    # ==============================================================================
    # 🌈 1. LỆNH SLASH: KIỂM TRA ĐỘ GAY NHÂN PHẨM (CHIA CA TẤU HÀI)
    # ==============================================================================
    @app_commands.command(name="gay-check", description="Đo lường mức độ Gay của bản thân hoặc một đối tượng trong server")
    @app_commands.describe(user="Đối tượng muốn đưa lên máy quét (Để trống nếu tự check bản thân)")
    async def gay_check(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user if user else interaction.user
        r = await get_redis_connection()

        # Đọc ca trực thực tế
        cycle_bytes = await r.hget("equinox:system:config", "current_cycle")
        cycle = cycle_bytes.decode('utf-8') if isinstance(cycle_bytes, bytes) else "DAY"

        # Dùng ID user làm seed để độ gay giữ nguyên trong ngày, tránh việc gõ lại ra số khác
        random.seed(int(target.id))
        rate = random.randint(0, 100)
        random.seed() # Reset seed về mặc định

        # Biện luận văn phong theo ca Ngày (Lumi) hoặc Đêm (Tenebris)
        if cycle == "DAY":
            bot_title = "☀️ MÁY QUÉT ÁNH SÁNG LUMINOUS ☀️"
            color = 0xFF66CC
            if rate < 20: comment = "Thẳng tắp như ánh mặt trời ban trưa sếp ơi, chuẩn men!"
            elif rate < 60: comment = "Có chút lung lay trước cái đẹp rồi nha, Lumi đang nghi ngờ đó."
            else: comment = "Hào quang 7 màu rực rỡ! Thần điện Luminous chính thức kết nạp người chị em này!"
        else:
            bot_title = "🔮 MÁY DÒ THÁM CHỢ ĐEN TENEBRIS 🔮"
            color = 0x4B0082
            if rate < 20: comment = "Gã trai cứng rắn của bóng đêm. Không có vết nứt danh dự."
            elif rate < 60: comment = "Tenebris ngửi thấy mùi 'dầu ăn' thoang thoảng ở đây rồi..."
            else: comment = "Trùm cuối Chợ Đen! Thao túng cả thế giới ngầm bằng độ cong tuyệt mỹ!"

        embed = discord.Embed(title=bot_title, color=color)
        embed.description = f"📡 Đối tượng đưa vào lồng kính: {target.mention}\n" \
                            f"📊 Kết quả phân tích hạch tâm: **`{rate}%` GAY**\n\n" \
                            f"💬 *Nhận xét:* {comment}"
        
        await interaction.response.send_message(embed=embed)

    # ==============================================================================
    # 🤖 2. HỆ THỐNG AUTO-RESPONSE (TỰ ĐỘNG PHẢN HỒI TIN NHẮN THEO TỪ KHÓA)
    # ==============================================================================
    @app_commands.command(name="autores-add", description="[STAFF] Thêm một từ khóa tự động trả lời cho Server")
    @app_commands.describe(tu_khoa="Từ khóa thành viên gõ (Viết chữ thường)", phan_hoi="Câu bot sẽ phản hồi lại")
    async def autores_add(self, interaction: discord.Interaction, tu_khoa: str, phan_hoi: str):
        r = await get_redis_connection()
        if not await self._is_staff(interaction, r):
            await interaction.response.send_message("❌ Sếp không có quyền cấu hình ma trận phản hồi!", ephemeral=True)
            return

        clean_key = tu_khoa.lower().strip()
        # Lưu vào Hash trên Redis theo guild_id
        await r.hset(f"equinox:autores:{interaction.guild.id}", clean_key, phan_hoi)
        await interaction.response.send_message(f"✅ Đã nạp từ khóa: `{clean_key}` -> `{phan_hoi}` vào bộ nhớ RAM.", ephemeral=True)

    @app_commands.command(name="autores-remove", description="[STAFF] Xóa một từ khóa tự động trả lời")
    @app_commands.describe(tu_khoa="Nhập chính xác từ khóa muốn xóa")
    async def autores_remove(self, interaction: discord.Interaction, tu_khoa: str):
        r = await get_redis_connection()
        if not await self._is_staff(interaction, r):
            await interaction.response.send_message("❌ Quyền lực không đủ!", ephemeral=True)
            return

        clean_key = tu_khoa.lower().strip()
        deleted = await r.hdel(f"equinox:autores:{interaction.guild.id}", clean_key)
        
        if deleted:
            await interaction.response.send_message(f"🗑️ Đã xóa từ khóa `{clean_key}` khỏi bộ não của Bot.", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ Không tìm thấy từ khóa `{clean_key}` trong hệ thống.", ephemeral=True)

    # Đón đầu đọc tin nhắn để phản hồi Auto-Res
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        r = await get_redis_connection()
        msg_content = message.content.lower().strip()

        # Thử bốc nội dung trả lời từ Hash Redis của riêng Server này
        response = await r.hget(f"equinox:autores:{message.guild.id}", msg_content)
        if response:
            await message.channel.send(response.decode('utf-8'))

    # ==============================================================================
    # 📢 3. HỆ THỐNG WELCOME MEMBER (CHÀO MỪNG THÀNH VIÊN MỚI - ĐIỀU CHỈNH ĐƯỢC)
    # ==============================================================================
    @app_commands.command(name="welcome-setup", description="[STAFF] Cấu hình hệ thống chào mừng thành viên mới")
    @app_commands.describe(
        trang_thai="Bật hoặc Tắt hệ thống chào mừng",
        kenh_gui="Kênh văn bản muốn Bot bắn tin nhắn chào mừng",
        cau_chao="Nội dung câu chào (Dùng {member} để tag tên, {guild} để hiện tên server)"
    )
    async def welcome_setup(
        self, 
        interaction: discord.Interaction, 
        trang_thai: bool, 
        kenh_gui: discord.TextChannel = None, 
        cau_chao: str = None
    ):
        r = await get_redis_connection()
        if not await self._is_staff(interaction, r):
            await interaction.response.send_message("❌ Lệnh này chỉ dành cho Ban Trị An điều hành server sếp ơi!", ephemeral=True)
            return

        config_key = f"equinox:welcome:config:{interaction.guild.id}"
        
        # Lưu cấu hình cơ bản
        await r.hset(config_key, "enabled", "ON" if trang_thai else "OFF")
        if kenh_gui:
            await r.hset(config_key, "channel_id", str(kenh_gui.id))
        if cau_chao:
            await r.hset(config_key, "message", cau_chao)

        # Đọc lại để hiển thị tổng quan cho sếp xem
        msg_bytes = await r.hget(config_key, "message") or b"Chào mừng {member} đã gia nhập vào ma trận {guild}!"
        ch_id_bytes = await r.hget(config_key, "channel_id")
        
        ch_mention = f"<#{ch_id_bytes.decode('utf-8')}>" if ch_id_bytes else "`Chưa chọn`"

        await interaction.response.send_message(
            f"⚙️ **CẬP NHẬT CẤU HÌNH CHÀO MỪNG THÀNH CÔNG:**\n"
            f"• Trạng thái hệ thống: **`{'BẬT 🟢' if trang_thai else 'TẮT 🔴'}`**\n"
            f"• Kênh gửi tin: {ch_mention}\n"
            f"• Mẫu câu chào: `{msg_bytes.decode('utf-8')}`",
            ephemeral=True
        )

    # Sự kiện bắt người dùng tham gia server để chào mừng
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        r = await get_redis_connection()
        config_key = f"equinox:welcome:config:{member.guild.id}"

        # Kiểm tra xem hệ thống có được bật không
        enabled_bytes = await r.hget(config_key, "enabled")
        if not enabled_bytes or enabled_bytes.decode('utf-8') != "ON":
            return

        # Lấy kênh nhận tin
        ch_id_bytes = await r.hget(config_key, "channel_id")
        if not ch_id_bytes:
            return

        channel = member.guild.get_channel(int(ch_id_bytes.decode('utf-8')))
        if channel:
            # Lấy mẫu câu chào và format các biến chuỗi {member} và {guild}
            raw_msg_bytes = await r.hget(config_key, "message") or b"Chào mừng {member} đã gia nhập vào ma trận {guild}!"
            raw_msg = raw_msg_bytes.decode('utf-8')
            
            # Format chuỗi an toàn
            formatted_msg = raw_msg.replace("{member}", member.mention).replace("{guild}", member.guild.name)

            try:
                await channel.send(formatted_msg)
            except Exception:
                pass

async def setup(bot):
    await bot.add_cog(ServerUtilities(bot))
