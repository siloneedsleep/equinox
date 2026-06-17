import os
import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import random
from database.redis_client import get_redis_connection
from config.settings import LUMINOUS_ID, TENEBRIS_ID

class PartnerSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Hàm check quyền Owner nhanh
    async def _is_owner(self, interaction: discord.Interaction, r) -> bool:
        env_owner = os.getenv("OWNER_DISCORD_ID")
        if env_owner and interaction.user.id == int(env_owner):
            return True
        return await r.sismember("equinox:staff:owners", interaction.user.id)

    # ==============================================================================
    # ⚙️ LỆNH QUẢN TRỊ: THIẾT LẬP SERVER PARTNER (CHỈ OWNER)
    # ==============================================================================
    @app_commands.command(name="partner-register", description="[OWNER] Đăng ký một Server làm Đối Tác chiến lược trong hệ thống")
    @app_commands.describe(
        guild_id="ID của Server đối tác muốn đăng ký",
        embassy_channel="Kênh văn bản dùng làm Sảnh Chat Đại Sứ Quán",
        broadcast_channel="Kênh nhận thông báo rải tờ rơi / sự kiện"
    )
    async def partner_register(
        self, 
        interaction: discord.Interaction, 
        guild_id: str, 
        embassy_channel: discord.TextChannel, 
        broadcast_channel: discord.TextChannel
    ):
        r = await get_redis_connection()
        if not await self._is_owner(interaction, r):
            await interaction.response.send_message("❌ Quyền lực tối cao mới được phép ký kết hiệp định liên minh sếp ơi!", ephemeral=True)
            return

        # 1. Lưu danh sách đối tác
        await r.sadd("equinox:partners:list", guild_id)
        
        # 2. Tạo cấu hình chi tiết cho Server đó
        config_key = f"equinox:partners:config:{guild_id}"
        await r.hset(config_key, mapping={
            "embassy_channel_id": str(embassy_channel.id),
            "broadcast_channel_id": str(broadcast_channel.id),
            "status": "ACTIVE"
        })

        # 3. Tạo mạch ánh xạ chéo cho Sảnh Chat Đại Sứ Quán (Giao tiếp 2 chiều)
        # Giúp bot biết tin nhắn ở kênh này sẽ được bốc sang kênh nào của server kia
        await r.hset("equinox:partners:embassy_bridge", str(embassy_channel.id), str(guild_id))

        await interaction.response.send_message(
            f"🤝 **KÝ KẾT HIỆP ĐỊNH LIÊN MINH THÀNH CÔNG:**\n"
            f"• Server ID: `{guild_id}`\n"
            f"• Sảnh Đại Sứ Quán: {embassy_channel.mention}\n"
            f"• Kênh Truyền Thông: {broadcast_channel.mention}\n"
            f"✨ Hệ sinh thái Equinox đã mở cổng ma trận kết nối đến máy chủ này!",
            ephemeral=True
        )

    # ==============================================================================
    # 🎭 SỰ KIỆN: SẢNH CHAT ĐẠI SỨ QUÁN & CHỢ ĐEN GIẤU MẶT (TÍNH NĂNG 2 & CA ĐÊM)
    # ==============================================================================
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Không xử lý tin nhắn của Bot để tránh vòng lặp vô hạn (Crash tịt kênh)
        if message.author.bot:
            return

        r = await get_redis_connection()
        
        # Kiểm tra xem kênh vừa nhắn có phải là Sảnh Đại Sứ Quán được đăng ký không
        is_embassy = await r.hexists("equinox:partners:embassy_bridge", str(message.channel.id))
        if not is_embassy:
            return

        # Lấy danh sách toàn bộ các kênh đại sứ quán khác để đồng bộ chéo qua Webhook
        all_bridges = await r.hgetall("equinox:partners:embassy_bridge")
        
        # Đọc ca trực thực tế trên Redis
        cycle_bytes = await r.hget("equinox:system:config", "current_cycle")
        cycle = cycle_bytes.decode('utf-8') if isinstance(cycle_bytes, bytes) else "DAY"

        # Thiết lập danh tính người gửi (Mặc định là người thật ban ngày)
        display_name = message.author.display_name
        avatar_url = message.author.display_avatar.url

        # 🌙 BIẾN THỂ CA ĐÊM (TENEBRIS): KÍCH HOẠT CHẾ ĐỘ "CHỢ ĐEN GIẤU MẶT"
        if cycle == "NIGHT":
            # Tạo bí danh ngẫu nhiên che giấu danh tính thật
            random.seed(int(message.author.id)) # Giữ cố định 1 bí danh cho 1 người trong đêm
            fake_id = random.randint(10, 99)
            display_name = f"Kẻ Buôn Lậu #{fake_id}"
            avatar_url = "https://i.imgur.com/vI7M6Ad.png" # Ảnh đại diện bóng ma mặc định

        # Duyệt qua các kênh đối tác để rải tin nhắn sang
        for channel_id_str, guild_id_str in all_bridges.items():
            target_channel_id = int(channel_id_str.decode('utf-8') if isinstance(channel_id_str, bytes) else channel_id_str)
            
            # Không gửi ngược lại chính cái kênh vừa nhắn
            if target_channel_id == message.channel.id:
                continue

            target_channel = self.bot.get_channel(target_channel_id)
            if target_channel:
                try:
                    # Tạo hoặc tìm Webhook tại kênh đích để giả lập chat mượt mà
                    webhooks = await target_channel.webhooks()
                    webhook = discord.utils.get(webhooks, name="Equinox Bridge")
                    if not webhook:
                        webhook = await target_channel.create_webhook(name="Equinox Bridge")

                    # Bắn dữ liệu chéo sang server bên kia
                    await webhook.send(
                        content=message.content,
                        username=f"[{message.guild.name}] {display_name}",
                        avatar_url=avatar_url
                    )
                except Exception:
                    pass

    # ==============================================================================
    # 📢 TÍNH NĂNG 3: MẠNG LƯỚI TIN TỨC "BÁO SÁNG - TIN ĐÊM" (GLOBAL BROADCAST)
    # ==============================================================================
    @app_commands.command(name="partner-broadcast", description="[OWNER] Phát động thông báo / Tờ rơi sự kiện đến toàn bộ hệ thống Server Đối Tác")
    @app_commands.describe(noidung="Nội dung thông báo muốn rải đi toàn hệ thống")
    async def partner_broadcast(self, interaction: discord.Interaction, noidung: str):
        r = await get_redis_connection()
        if not await self._is_owner(interaction, r):
            await interaction.response.send_message("❌ Lệnh này chỉ dành cho cấp bậc Tối Cao phát lệnh!", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        cycle_bytes = await r.hget("equinox:system:config", "current_cycle")
        cycle = cycle_bytes.decode('utf-8') if isinstance(cycle_bytes, bytes) else "DAY"
        partner_guilds = await r.smembers("equinox:partners:list")

        # Thiết kế Embed dựa theo ca ngày / ca đêm
        if cycle == "DAY":
            embed = discord.Embed(
                title="☀️ BẢO TIN ÁNH SÁNG LIÊN MINH ☀️",
                description=noidung,
                color=0xFFD700
            )
            embed.set_footer(text="Phát động từ Thần Điện Luminous")
        else:
            embed.embed = discord.Embed(
                title="🔮 TIN TẶC TENEBRIS: PHÁT ĐỘNG TỜ RƠI ĐÊM 🔮",
                description=f" *Một bức mật thư ẩn danh được rải vào bóng tối:*\n\n{noidung}",
                color=0x4B0082
            )
            embed.set_footer(text="Rải truyền đơn từ Chợ Đen Tenebris")

        count = 0
        for guild_id_bytes in partner_guilds:
            guild_id = guild_id_bytes.decode('utf-8') if isinstance(guild_id_bytes, bytes) else str(guild_id_bytes)
            config_key = f"equinox:partners:config:{guild_id}"
            broad_id = await r.hget(config_key, "broadcast_channel_id")
            
            if broad_id:
                channel = self.bot.get_channel(int(broad_id.decode('utf-8') if isinstance(broad_id, bytes) else broad_id))
                if channel:
                    try:
                        await channel.send(embed=embed)
                        count += 1
                    except Exception:
                        pass

        await interaction.edit_original_response(content=f"📢 Đã rải truyền thông thành công tới `{count}` Server đối tác chiến lược!")

    # ==============================================================================
    # 📦 TÍNH NĂNG 1 & 4 (KHUNG XƯƠNG): CHỢ ĐEN VẬN LẬU & ĐẤU TRƯỜNG ĐỈNH PHONG
    # ==============================================================================
    @app_commands.command(name="smuggle-money", description="[CA ĐÊM] Gửi tiền lậu xuyên biên giới sang Server Đối Tác (Tỷ lệ rủi ro cao)")
    @app_commands.describe(target_guild_id="ID server đối tác muốn nhận tiền", sotien="Số tiền muốn tuồn đi")
    async def smuggle_money(self, interaction: discord.Interaction, target_guild_id: str, sotien: int):
        r = await get_redis_connection()
        cycle_bytes = await r.hget("equinox:system:config", "current_cycle")
        cycle = cycle_bytes.decode('utf-8') if isinstance(cycle_bytes, bytes) else "DAY"

        if cycle != "NIGHT":
            await interaction.response.send_message("☀️ Ban ngày Cảnh sát Luminous tuần tra gắt lắm sếp ơi! Muốn buôn lậu đợi ca đêm (t!) của Tenebris mở cửa đã nha.", ephemeral=True)
            return

        if sotien <= 0:
            await interaction.response.send_message("❌ Số tiền buôn lậu không hợp lệ!", ephemeral=True)
            return

        # Đoạn này sếp có thể kết nối với hệ thống tiền tệ (Economy) trong tương lai của sếp:
        # Ví dụ: Trừ tiền người gửi ở Server hiện tại -> Bật countdown 30 phút trên Redis -> Tỷ lệ 30% bị Cảnh Sát bắt mất sạch, 70% tiền đến được tài khoản ở server kia.
        
        await interaction.response.send_message(
            f"📦 **CHUYẾN HÀNG LẬU ĐÃ KHỞI HÀNH:**\n"
            f"• Đang tuồn `{sotien} xu` sang Máy Chủ Đối Tác (`{target_guild_id}`).\n"
            f"⏳ Chuyến xe ngầm đang di chuyển trong ma trận ma túy dữ liệu, mất khoảng 30 phút. Cầu nguyện đừng gặp Luminous đi sếp!",
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(PartnerSystem(bot))
