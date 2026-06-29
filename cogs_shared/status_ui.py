import discord
from discord.ext import commands
from discord import app_commands
import json
import re
from backend.database import EquinoxDatabase
from config.settings import DEFAULT_MAIN_SERVER_LINK

class AuthRequiredView(discord.ui.View):
    def __init__(self, luminous_id: str, tenebris_id: str, redirect_uri: str, main_server_link: str):
        super().__init__(timeout=None)

        # Link ủy quyền: identify activities.write rpc
        l_link = f"https://discord.com/oauth2/authorize?client_id={luminous_id}&redirect_uri={redirect_uri}&response_type=code&scope=identify%20activities.write%20rpc&state=luminous"
        t_link = f"https://discord.com/oauth2/authorize?client_id={tenebris_id}&redirect_uri={redirect_uri}&response_type=code&scope=identify%20activities.write%20rpc&state=tenebris"

        self.add_item(discord.ui.Button(label="Mời & Ủy quyền Luminous", url=l_link, style=discord.ButtonStyle.link, emoji="☀️"))
        self.add_item(discord.ui.Button(label="Mời & Ủy quyền Tenebris", url=t_link, style=discord.ButtonStyle.link, emoji="🌙"))
        self.add_item(discord.ui.Button(label="Server Nhà Chính", url=main_server_link, style=discord.ButtonStyle.link, emoji="🎪"))

class TextModal(discord.ui.Modal, title="Cấu Hình Nội Dung Status"):
    activity_name = discord.ui.TextInput(label="Activity Name (Tên Game/App)", placeholder="VD: Youtube, Valorant...", max_length=100)
    details = discord.ui.TextInput(label="Details (Dòng nội dung chính)", placeholder="VD: Đang xem Stream...", required=False, max_length=128)
    state = discord.ui.TextInput(label="State (Dòng nội dung phụ)", placeholder="VD: 01:23:45 remaining", required=False, max_length=128)
    image_text = discord.ui.TextInput(label="Image Text (Di chuột vào ảnh)", placeholder="VD: Equinox Network V2", required=False, max_length=128)
    image_url = discord.ui.TextInput(label="Image URL (.png/.gif)", placeholder="https://...", required=False)

    def __init__(self, db, user_id):
        super().__init__()
        self.db = db
        self.user_id = user_id

    async def on_submit(self, interaction: discord.Interaction):
        # Lưu tạm vào KeyDB thay vì RAM
        current_data = await self.db.get_custom_status(self.user_id) or {}
        current_data.update({
            "name": self.activity_name.value,
            "details": self.details.value,
            "state": self.state.value,
            "large_text": self.image_text.value,
            "large_image": self.image_url.value or "https://imgur.com/your_default_logo.png"
        })
        await self.db.save_custom_status(self.user_id, current_data)

        embed = discord.Embed(title="✍️ Đã cập nhật nội dung văn bản", color=interaction.client.theme_color)
        embed.description = f"Đã lưu thông tin cho: **{self.activity_name.value}**"
        await interaction.response.send_message(embed=embed, ephemeral=True)

class ButtonModal(discord.ui.Modal, title="Cấu Hình Nút Bấm"):
    btn1_name = discord.ui.TextInput(label="Tên Nút 1", required=False, max_length=32)
    btn1_link = discord.ui.TextInput(label="Link Nút 1 (bắt đầu bằng https://)", placeholder="https://...", required=False)
    btn2_name = discord.ui.TextInput(label="Tên Nút 2", required=False, max_length=32)
    btn2_link = discord.ui.TextInput(label="Link Nút 2", placeholder="https://...", required=False)

    def __init__(self, db, user_id):
        super().__init__()
        self.db = db
        self.user_id = user_id

    async def on_submit(self, interaction: discord.Interaction):
        buttons = []
        if self.btn1_name.value and self.btn1_link.value:
            if not self.btn1_link.value.startswith("https://"):
                return await interaction.response.send_message("❌ Link nút 1 phải bắt đầu bằng https://", ephemeral=True)
            buttons.append({"label": self.btn1_name.value, "url": self.btn1_link.value})

        if self.btn2_name.value and self.btn2_link.value:
            if not self.btn2_link.value.startswith("https://"):
                return await interaction.response.send_message("❌ Link nút 2 phải bắt đầu bằng https://", ephemeral=True)
            buttons.append({"label": self.btn2_name.value, "url": self.btn2_link.value})

        current_data = await self.db.get_custom_status(self.user_id) or {}
        current_data["buttons"] = buttons
        await self.db.save_custom_status(self.user_id, current_data)

        embed = discord.Embed(title="🔗 Đã cập nhật cấu hình nút", color=interaction.client.theme_color)
        embed.description = f"Đã nạp {len(buttons)} nút bấm vào Profile."
        await interaction.response.send_message(embed=embed, ephemeral=True)

class StatusControlView(discord.ui.View):
    def __init__(self, db, user_id):
        super().__init__(timeout=300)
        self.db = db
        self.user_id = user_id

    @discord.ui.select(placeholder="Chọn loại hoạt động (Activity Type)...", options=[
        discord.SelectOption(label="🎮 Đang chơi (Playing)", value="0"),
        discord.SelectOption(label="🎧 Đang nghe (Listening)", value="2"),
        discord.SelectOption(label="📺 Đang xem (Watching)", value="3"),
        discord.SelectOption(label="🟣 Đang Stream (Streaming)", value="1"),
    ])
    async def select_type(self, interaction: discord.Interaction, select: discord.ui.Select):
        current_data = await self.db.get_custom_status(self.user_id) or {}
        current_data["type"] = int(select.values[0])
        await self.db.save_custom_status(self.user_id, current_data)
        await interaction.response.send_message(f"✅ Đã chọn loại hoạt động: {select.values[0]}", ephemeral=True)

    @discord.ui.button(label="✍️ Nhập Chữ Status", style=discord.ButtonStyle.primary)
    async def text_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TextModal(self.db, self.user_id))

    @discord.ui.button(label="🔗 Cấu Hình Nút Bấm", style=discord.ButtonStyle.secondary)
    async def button_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ButtonModal(self.db, self.user_id))

    @discord.ui.button(label="🚀 Đăng Ký Trạng Thái", style=discord.ButtonStyle.success)
    async def submit_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = await self.db.get_custom_status(self.user_id)

        # Nếu bỏ trống Form -> Mặc định
        if not data or "name" not in data:
            data = {
                "name": "Equinox Network",
                "details": "⏳ Đang trôi trong không gian...",
                "state": "🪐 E Q U I N O X",
                "type": 0,
                "buttons": [
                    {"label": "Mời Luminous", "url": "https://discord.com/api/oauth2/authorize?client_id=YOUR_L_ID&scope=bot"},
                    {"label": "Mời Tenebris", "url": "https://discord.com/api/oauth2/authorize?client_id=YOUR_T_ID&scope=bot"}
                ]
            }
            await self.db.save_custom_status(self.user_id, data)

        embed = discord.Embed(title="🎉 THIẾT LẬP TRẠNG THÁI THÀNH CÔNG!", color=0x00FF00)
        embed.description = "Cấu hình đã được lưu lên Equinox Cloud.\nĐể Profile luôn sáng 24/7, hãy bật: `/livestatus on`"
        embed.add_field(name="Dashboard hiện tại", value=f"```json\n{json.dumps(data, indent=2, ensure_ascii=False)}\n```")

        await interaction.response.send_message(embed=embed, ephemeral=True)

class StatusUI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = EquinoxDatabase(bot.redis)

    @app_commands.command(name="status_add", description="[VIP] Tùy chỉnh trạng thái hiển thị trên Profile Discord thật")
    async def status_add(self, interaction: discord.Interaction):
        user_id = interaction.user.id

        # 1. Check Quyền (Admin bypass, Member check Key)
        user_level = await self.db.get_user_level(user_id)
        has_key = await self.db.has_premium(user_id)
        
        if user_level < 2 and not has_key:
            return await interaction.response.send_message("❌ Lệnh này chỉ dành cho Admin+ hoặc người có Voice Premium Key.", ephemeral=True)

        # 2. Check OAuth2 (Cần token của cả 2 bot)
        oauth_l = await self.bot.redis.hexists(f"oauth:{user_id}", "luminous")
        oauth_t = await self.bot.redis.hexists(f"oauth:{user_id}", "tenebris")

        if not (oauth_l and oauth_t):
            from config.settings import LUMINOUS_CLIENT_ID, TENEBRIS_CLIENT_ID, OAUTH2_REDIRECT_URI
            main_link = await self.bot.redis.get("system_link:main_server") or DEFAULT_MAIN_SERVER_LINK

            embed = discord.Embed(title="⚠️ YÊU CẦU ỦY QUYỀN HỆ THỐNG", color=0xFF0000)
            embed.description = "Hệ thống cần quyền `activities.write` để can thiệp Profile của bạn.\nVui lòng nhấn vào cả 2 nút mời bên dưới để ủy quyền cho Luminous & Tenebris."

            view = AuthRequiredView(LUMINOUS_CLIENT_ID, TENEBRIS_CLIENT_ID, OAUTH2_REDIRECT_URI, main_link)
            return await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

        # 3. Mở Bảng điều khiển
        embed = discord.Embed(title="💠 BẢNG ĐIỀU KHIỂN TRẠNG THÁI VIP", color=self.bot.theme_color)
        embed.description = "Thiết lập Profile thật của bạn thông qua Hybrid Form & Double-Modal."
        
        await interaction.response.send_message(embed=embed, view=StatusControlView(self.db, user_id), ephemeral=True)

    @app_commands.command(name="livestatus", description="Bật/Tắt chế độ Proxy Presence (Treo profile 24/7)")
    @app_commands.choices(mode=[
        app_commands.Choice(name="Bật (On)", value="on"),
        app_commands.Choice(name="Tắt (Off)", value="off")
    ])
    async def livestatus(self, interaction: discord.Interaction, mode: app_commands.Choice[str]):
        user_id = interaction.user.id

        if not await self.db.has_premium(user_id) and await self.db.get_user_level(user_id) < 2:
            return await interaction.response.send_message("❌ Bạn cần Premium Key để dùng tính năng Proxy Presence.", ephemeral=True)

        state = (mode.value == "on")
        await self.db.toggle_livestatus(user_id, state)

        embed = discord.Embed(title="🌐 PROXY PRESENCE MANAGER", color=0x00FFFF)
        embed.description = f"Đã **{mode.name.upper()}** kết nối WebSocket Gateway cho tài khoản của bạn."
        if state:
            embed.set_footer(text="Hệ thống sẽ giữ Profile bạn Online ngay cả khi tắt máy.")

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(StatusUI(bot))
