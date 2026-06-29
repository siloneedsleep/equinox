import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from backend.database import EquinoxDatabase

class HelpSelect(discord.ui.Select):
    def __init__(self, bot):
        self.bot = bot
        options = [
            discord.SelectOption(label="Người dùng (Member)", description="Lệnh cơ bản cho mọi thành viên", emoji="👥"),
            discord.SelectOption(label="Đặc quyền VIP", description="Lệnh cho Voice Premium & Admin", emoji="💎"),
            discord.SelectOption(label="Kinh tế & Drama", description="Hệ thống tiền tệ, sát thủ, di chúc", emoji="💰"),
            discord.SelectOption(label="Quản trị (Admin/Staff)", description="Lệnh điều hành và xử phạt", emoji="🛡️"),
            discord.SelectOption(label="Chủ sở hữu (Owner)", description="Lệnh vĩ mô điều khiển hệ thống", emoji="👑"),
        ]
        super().__init__(placeholder="Chọn danh mục lệnh cần xem...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selection = self.values[0]
        embed = discord.Embed(color=self.bot.theme_color)

        if "Member" in selection:
            embed.title = "👥 DANH MỤC LỆNH NGƯỜI DÙNG"
            embed.description = (
                "**/help**: Hiển thị bảng hướng dẫn này.\n"
                "**/redeem [key]**: Kích hoạt mã Premium Key.\n"
                "**/bag**: Xem túi đồ và tài sản hiện có."
            )
        elif "VIP" in selection:
            embed.title = "💎 DANH MỤC ĐẶC QUYỀN VIP"
            embed.description = (
                "**/status_add**: Tùy chỉnh Profile thật (Rich Presence).\n"
                "**/livestatus [on/off]**: Treo profile 24/7 qua Proxy."
            )
        elif "Kinh tế" in selection:
            embed.title = "💰 HỆ THỐNG KINH TẾ & DRAMA"
            embed.description = (
                "**/open [id]**: Mở túi Star Pouch nhận tiền theo ca.\n"
                "**/launder [amount]**: Rửa tiền bẩn (phí 15-25%).\n"
                "**/trade [user]**: Giao dịch an toàn vật phẩm và tiền.\n"
                "**/set_will [user]**: Lập di chúc cho người phối ngẫu.\n"
                "**/assassinate [user]**: [Ca Đêm] Ám sát cướp 30% tài sản."
            )
        elif "Quản trị" in selection:
            embed.title = "🛡️ HỆ THỐNG QUẢN TRỊ"
            embed.description = (
                "**/warn [user] [reason]**: Phạt gậy thành viên (Luật bảo vệ cấp trên).\n"
                "**/set-role [level] [role]**: Ánh xạ Role sang Level hệ thống."
            )
        elif "Chủ sở hữu" in selection:
            embed.title = "👑 LỆNH TỐI THƯỢNG (OWNER ONLY)"
            embed.description = (
                "**/system api add**: Nạp API Key (Ecosytem/Jules).\n"
                "**/system key add**: Tạo mã Premium Key mới.\n"
                "**/system force_shift**: Cưỡng chế đổi ca trực.\n"
                "**/chat [mode] [message]**: Giả danh Webhook/Bot để giao tiếp.\n"
                "**/jules [prompt]**: Triệu hồi AI Kiến trúc sư can thiệp mã nguồn."
            )

        embed.set_footer(text=f"Yêu cầu bởi {interaction.user.name}", icon_url=interaction.user.display_avatar.url)
        await interaction.response.edit_message(embed=embed, view=HelpView(self.bot))

class HelpView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=120)
        self.add_item(HelpSelect(bot))

class SystemCore(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = EquinoxDatabase(bot.redis)

    @app_commands.command(name="help", description="Trung tâm điều khiển và hướng dẫn Equinox Network V2")
    async def help_cmd(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🪐 EQUINOX NETWORK V2 - COMMAND CENTER",
            description=(
                "Chào mừng bạn đến với hệ sinh thái đa thực thể.\n"
                "Vui lòng chọn danh mục phía dưới để xem chi tiết các lệnh.\n\n"
                "**Trạng thái hiện tại:**\n"
                f"🎭 Thực thể đang trực: **{self.bot.persona}**\n"
                f"⏰ Thời gian hệ thống: {discord.utils.format_dt(discord.utils.utcnow(), 'T')}"
            ),
            color=self.bot.theme_color
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text="Owner: Silo | Developed by Jules")

        await interaction.response.send_message(embed=embed, view=HelpView(self.bot))

    system_group = app_commands.Group(name="system", description="Lệnh quản trị hệ thống (Độc quyền Owner)")
    api_group = app_commands.Group(parent=system_group, name="api", description="Quản trị xoay tua API Key")
    key_group = app_commands.Group(parent=system_group, name="key", description="Quản trị Premium Key")

    async def check_owner(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != int(os.getenv("OWNER_ID", 0)):
            embed = discord.Embed(description="❌ **Từ chối truy cập.** Chỉ Owner mới có quyền này.", color=0xFF0000)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return False
        return True

    @key_group.command(name="add", description="Tạo mã Premium Key mới")
    async def sys_add_key(self, interaction: discord.Interaction, duration_days: int):
        if not await self.check_owner(interaction): return
        token = await self.db.create_premium_key(duration_days)
        embed = discord.Embed(title="🔑 TẠO KEY THÀNH CÔNG", color=0x00FF00)
        embed.add_field(name="Mã Key", value=f"`{token}`", inline=False)
        embed.add_field(name="Thời hạn", value=f"{duration_days} ngày", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @api_group.command(name="add", description="Nạp API Key vào bể xoay tua")
    @app_commands.choices(target=[
        app_commands.Choice(name="Gemini Ecosytem (Luminous/Tenebris)", value="ecosystem"),
        app_commands.Choice(name="Jules Core API (Developer Only)", value="jules")
    ])
    async def api_add(self, interaction: discord.Interaction, target: app_commands.Choice[str], token_id: str, key_content: str):
        if not await self.check_owner(interaction): return
        redis_key = "api_keys" if target.value == "ecosystem" else "jules_api_keys"
        payload = {"key_content": key_content, "status": "active", "fail_count": 0, "cooldown_until": 0}
        await self.bot.redis.hset(redis_key, token_id, json.dumps(payload))

        embed = discord.Embed(description=f"✅ Đã nạp API Key `{token_id}` vào mục **{target.name}**", color=0x00FF00)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @system_group.command(name="force_shift", description="Cưỡng chế đổi ca lập tức")
    async def force_shift(self, interaction: discord.Interaction, persona: str):
        if not await self.check_owner(interaction): return
        payload = {"action": "shift_change", "active_persona": persona}
        await self.bot.redis.publish("equinox_system", json.dumps(payload))
        embed = discord.Embed(description=f"🚀 Đã phát lệnh đổi ca khẩn cấp sang: **{persona}**", color=0xFCE883)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="redeem", description="Kích hoạt Premium Key")
    async def redeem(self, interaction: discord.Interaction, token: str):
        success = await self.db.redeem_premium_key(interaction.user.id, token)
        if success:
            embed = discord.Embed(title="🎉 KÍCH HOẠT THÀNH CÔNG", description="Bạn đã có đặc quyền VIP.", color=0x00FF00)
        else:
            embed = discord.Embed(title="❌ KÍCH HOẠT THẤT BẠI", description="Key không hợp lệ hoặc đã sử dụng.", color=0xFF0000)
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(SystemCore(bot))
