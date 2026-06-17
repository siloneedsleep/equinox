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

    # Hàm bổ trợ xác định Cấp độ dựa trên điểm số trên Redis
    def _get_tier_info(self, points: int) -> dict:
        if points < 1000:
            return {"tier": "TIER 1", "title": "Liên Minh Sơ Khai 🥉", "color": 0xCD7F32, "smuggle_bonus": 0}
        elif points < 5000:
            return {"tier": "TIER 2", "title": "Đối Tác Chiến Lược 🥈", "color": 0xC0C0C0, "smuggle_bonus": 10}
        else:
            return {"tier": "TIER 3", "title": "Chủ Quyền Ma Trận 🥇", "color": 0xFFD700, "smuggle_bonus": 25}

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
        
        # 2. Tạo cấu hình chi tiết cho Server đó (Mặc định bắt đầu với 0 điểm)
        config_key = f"equinox:partners:config:{guild_id}"
        await r.hset(config_key, mapping={
            "embassy_channel_id": str(embassy_channel.id),
            "broadcast_channel_id": str(broadcast_channel.id),
            "points": "0", # Khởi tạo điểm liên minh
            "status": "ACTIVE"
        })

        # 3. Tạo mạch ánh xạ chéo cho Sảnh Chat Đại Sứ Quán
        await r.hset("equinox:partners:embassy_bridge", str(embassy_channel.id), str(guild_id))

        await interaction.response.send_message(
            f"🤝 **KÝ KẾT HIỆP ĐỊNH LIÊN MINH THÀNH CÔNG:**\n"
            f"• Server ID: `{guild_id}`\n"
            f"• Cấp bậc khởi đầu: `TIER 1 - Liên Minh Sơ Khai` 🥉\n"
            f"✨ Hệ sinh thái Equinox đã mở cổng ma trận kết nối đến máy chủ này!",
            ephemeral=True
        )

    # ==============================================================================
    # 📊 LỆNH SLASH: KIỂM TRA THÔNG TIN TIER / ĐIỂM SỐ CỦA SERVER
    # ==============================================================================
    @app_commands.command(name="partner-info", description="Xem trạng thái cấp độ và điểm tích lũy liên minh của Server")
    async def partner_info(self, interaction: discord.Interaction):
        r = await get_redis_connection()
        guild_id = str(interaction.guild.id)

        # Kiểm tra xem server hiện tại có phải là partner không
        is_partner = await r.sismember("equinox:partners:list", guild_id)
        if not is_partner:
            await interaction.response.send_message("❌ Máy chủ này chưa tham gia vào liên minh ma trận của Equinox Network.", ephemeral=True)
            return

        config_key = f"equinox:partners:config:{guild_id}"
        points_bytes = await r.hget(config_key, "points")
        points = int(points_bytes.decode('utf-8') if points_bytes else 0)

        tier_info = self._get_tier_info(points)

        embed = discord.Embed(
            title=f"🤝 HỒ SƠ LIÊN MINH: {interaction.guild.name}",
            color=tier_info["color"]
        )
        embed.add_field(name="🎖️ Danh hiệu Đối Tác", value=f"**{tier_info['title']}**", inline=True)
        embed.add_field(name="✨ Điểm Tích Lũy", value=f"`{points}` điểm", inline=True)
        
        # Hiển thị đặc quyền dựa theo Tier
        privileges = f"• Sảnh Đại Sứ Quán: `MỞ` ✅\n• Cộng thêm tỷ lệ buôn lậu: `+{tier_info['smuggle_bonus']}%` 📦"
        if tier_info["tier"] == "TIER 3":
            privileges += "\n• Thuế Chợ Đen: `Giảm 50%` 💰\n• Định danh tối cao: `Có` 👑"
            
        embed.add_field(name="🛡️ Đặc Quyền Hiện Có", value=privileges, inline=False)
        await interaction.response.send_message(embed=embed)

    # ==============================================================================
    # 🎭 SỰ KIỆN: SẢNH CHAT ĐẠI SỨ QUÁN + TỰ ĐỘNG CỘNG ĐIỂM TIER ĐỂ LÊN CẤP
    # ==============================================================================
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        r = await get_redis_connection()
        
        # Kiểm tra xem kênh nhắn có phải sảnh đại sứ quán không
        guild_id_bytes = await r.hget("equinox:partners:embassy_bridge", str(message.channel.id))
        if not guild_id_bytes:
            return

        guild_id = guild_id_bytes.decode('utf-8') if isinstance(guild_id_bytes, bytes) else str(guild_id_bytes)

        # 🔥 TỰ ĐỘNG CỘNG ĐIỂM LIÊN MINH (Mỗi tin nhắn chat chéo được cộng 1 điểm thưởng)
        config_key = f"equinox:partners:config:{guild_id}"
        await r.hincrby(config_key, "points", 1)

        # Đọc dữ liệu ca trực
        cycle_bytes = await r.hget("equinox:system:config", "current_cycle")
        cycle = cycle_bytes.decode('utf-8') if isinstance(cycle_bytes, bytes) else "DAY"

        display_name = message.author.display_name
        avatar_url = message.author.display_avatar.url

        # Ca đêm (Tenebris): Chế độ ẩn danh
        if cycle == "NIGHT":
            random.seed(int(message.author.id))
            fake_id = random.randint(10, 99)
            display_name = f"Kẻ Buôn Lậu #{fake_id}"
            avatar_url = "https://i.imgur.com/vI7M6Ad.png"

        all_bridges = await r.hgetall("equinox:partners:embassy_bridge")
        for channel_id_str, g_id_str in all_bridges.items():
            target_channel_id = int(channel_id_str.decode('utf-8') if isinstance(channel_id_str, bytes) else channel_id_str)
            if target_channel_id == message.channel.id:
                continue

            target_channel = self.bot.get_channel(target_channel_id)
            if target_channel:
                try:
                    webhooks = await target_channel.webhooks()
                    webhook = discord.utils.get(webhooks, name="Equinox Bridge")
                    if not webhook:
                        webhook = await target_channel.create_webhook(name="Equinox Bridge")

                    await webhook.send(
                        content=message.content,
                        username=f"[{message.guild.name}] {display_name}",
                        avatar_url=avatar_url
                    )
                except Exception:
                    pass

    # ==============================================================================
    # 📢 TÍNH NĂNG 3: MẠNG LƯỚI TIN TỨC (ẢNH HƯỞNG BỞI TIER ĐỂ ĐỔI MÀU BẢN TIN)
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

        count = 0
        for guild_id_bytes in partner_guilds:
            guild_id = guild_id_bytes.decode('utf-8') if isinstance(guild_id_bytes, bytes) else str(guild_id_bytes)
            config_key = f"equinox:partners:config:{guild_id}"
            
            # Lấy điểm số của Server đối tác đích để hiển thị màu sắc bản tin tương ứng với đẳng cấp của họ
            points_bytes = await r.hget(config_key, "points")
            points = int(points_bytes.decode('utf-8') if points_bytes else 0)
            tier_info = self._get_tier_info(points)

            broad_id = await r.hget(config_key, "broadcast_channel_id")
            if broad_id:
                channel = self.bot.get_channel(int(broad_id.decode('utf-8') if isinstance(broad_id, bytes) else broad_id))
                if channel:
                    # Đổi màu sắc Embed dựa theo ca trực và cấp độ đối tác nhận tin
                    embed_color = tier_info["color"] if cycle == "DAY" else 0x4B0082
                    title_text = f"☀️ BẢO TIN ÁNH SÁNG: {tier_info['tier']}" if cycle == "DAY" else f"🔮 TIN TẶC TENEBRIS ĐÊM: {tier_info['tier']}"

                    embed = discord.Embed(title=title_text, description=noidung, color=embed_color)
                    embed.set_footer(text=f"Phát tin tới hệ sinh thái cấp {tier_info['title']}")
                    
                    try:
                        await channel.send(embed=embed)
                        count += 1
                    except Exception:
                        pass

        await interaction.edit_original_response(content=f"📢 Đã rải truyền thông thành công tới `{count}` Server đối tác chiến lược!")

    # ==============================================================================
    # 📦 TÍNH NĂNG 1: CHỢ ĐEN VẬN LẬU (HƯỞNG BÓNUS TỶ LỆ THEO TIER CỦA SERVER)
    # ==============================================================================
    @app_commands.command(name="smuggle-money", description="[CA ĐÊM] Gửi tiền lậu xuyên biên giới sang Server Đối Tác")
    @app_commands.describe(target_guild_id="ID server đối tác muốn nhận tiền", sotien="Số tiền muốn tuồn đi")
    async def smuggle_money(self, interaction: discord.Interaction, target_guild_id: str, sotien: int):
        r = await get_redis_connection()
        cycle_bytes = await r.hget("equinox:system:config", "current_cycle")
        cycle = cycle_bytes.decode('utf-8') if isinstance(cycle_bytes, bytes) else "DAY"

        if cycle != "NIGHT":
            await interaction.response.send_message("☀️ Ban ngày Cảnh sát Luminous tuần tra gắt lắm sếp ơi! Muốn buôn lậu đợi ca đêm (t!) của Tenebris mở cửa đã nha.", ephemeral=True)
            return

        # Check xem server đích có phải đối tác liên minh không
        is_target_partner = await r.sismember("equinox:partners:list", target_guild_id)
        if not is_target_partner:
            await interaction.response.send_message("❌ Server đích không nằm trong ma trận liên minh, không thể tuồn tiền lậu qua!", ephemeral=True)
            return

        # Bốc dữ liệu điểm của server hiện tại để tính toán tỷ lệ thành công tăng thêm
        current_guild_id = str(interaction.guild.id)
        points_bytes = await r.hget(f"equinox:partners:config:{current_guild_id}", "points")
        points = int(points_bytes.decode('utf-8') if points_bytes else 0)
        tier_info = self._get_tier_info(points)

        # Tỷ lệ thành công mặc định là 60%, cộng thêm % bonus từ Cấp bậc Tier
        success_rate = 60 + tier_info["smuggle_bonus"]

        await interaction.response.send_message(
            f"📦 **CHUYẾN HÀNG LẬU ĐÃ KHỞI HÀNH:**\n"
            f"• Đang tuồn `{sotien} xu` sang Máy Chủ Đối Tác (`{target_guild_id}`).\n"
            f"📈 Tỷ lệ vận chuyển thành công của Server cấp {tier_info['title']}: `{success_rate}%` (Đã cộng `{tier_info['smuggle_bonus']}%` ẩn từ Tier).\n"
            f"⏳ Xe hàng ngầm đang lăn bánh...",
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(PartnerSystem(bot))
