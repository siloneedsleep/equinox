import discord
from discord.ext import commands
from discord import app_commands
from backend.database import EquinoxDatabase
from config.settings import DEFAULT_MAIN_SERVER_LINK, OWNER_ID
from cogs_shared.embed_util import create_premium_embed
import re
import json

class AuthRequiredView(discord.ui.View):
    def __init__(self, luminous_id: str, tenebris_id: str, redirect_uri: str, main_server_link: str):
        super().__init__(timeout=None)
        scopes = "identify%20activities.write"
        l_link = f"https://discord.com/oauth2/authorize?client_id={luminous_id}&redirect_uri={redirect_uri}&response_type=code&scope={scopes}&state=luminous"
        t_link = f"https://discord.com/oauth2/authorize?client_id={tenebris_id}&redirect_uri={redirect_uri}&response_type=code&scope={scopes}&state=tenebris"
        self.add_item(discord.ui.Button(label="Ủy quyền Luminous", url=l_link, style=discord.ButtonStyle.link, emoji="☀️"))
        self.add_item(discord.ui.Button(label="Ủy quyền Tenebris", url=t_link, style=discord.ButtonStyle.link, emoji="🌙"))
        self.add_item(discord.ui.Button(label="Server Nhà Chính", url=main_server_link, style=discord.ButtonStyle.link, emoji="🎪"))

def validate_url(url: str) -> bool:
    regex = re.compile(
        r'^https://' # Chỉ cho phép https
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url is not None and regex.search(url)

class TextModal(discord.ui.Modal, title="Nội Dung Status (Tối đa 128 ký tự)"):
    activity_name = discord.ui.TextInput(label="Tên Ứng Dụng", placeholder="VD: Youtube", max_length=128)
    details = discord.ui.TextInput(label="Dòng 1 (Details)", required=False, max_length=128)
    state = discord.ui.TextInput(label="Dòng 2 (State)", required=False, max_length=128)
    image_text = discord.ui.TextInput(label="Chữ khi trỏ chuột vào ảnh", required=False, max_length=128)
    image_url = discord.ui.TextInput(label="Link ảnh (Bắt buộc mp4/png/gif/jpg)", required=False, placeholder="Bỏ qua nếu không có")

    def __init__(self, bot, db, user_id):
        super().__init__()
        self.bot, self.db, self.user_id = bot, db, user_id

    async def on_submit(self, interaction: discord.Interaction):
        data = await self.db.get_custom_status(self.user_id) or {}
        data.update({
            "name": self.activity_name.value[:128],
            "details": self.details.value[:128],
            "state": self.state.value[:128],
            "large_text": self.image_text.value[:128],
            "large_image": self.image_url.value
        })
        await self.db.save_custom_status(self.user_id, data)
        await interaction.response.send_message("✅ Đã lưu văn bản Status. Hãy nhấn **Đăng Ký** để kích hoạt.", ephemeral=True)

class ButtonModal(discord.ui.Modal, title="Cấu Hình Nút Bấm"):
    btn1_name = discord.ui.TextInput(label="Tên Nút 1", required=False, max_length=32)
    btn1_link = discord.ui.TextInput(label="Link Nút 1 (Phải bắt đầu bằng https://)", required=False)
    btn2_name = discord.ui.TextInput(label="Tên Nút 2", required=False, max_length=32)
    btn2_link = discord.ui.TextInput(label="Link Nút 2 (Phải bắt đầu bằng https://)", required=False)

    def __init__(self, bot, db, user_id):
        super().__init__()
        self.bot, self.db, self.user_id = bot, db, user_id

    async def on_submit(self, interaction: discord.Interaction):
        btns = []
        if self.btn1_name.value and self.btn1_link.value:
            if not validate_url(self.btn1_link.value):
                return await interaction.response.send_message("❌ Link nút 1 không hợp lệ! Phải là `https://`", ephemeral=True)
            btns.append({"label": self.btn1_name.value[:32], "url": self.btn1_link.value})

        if self.btn2_name.value and self.btn2_link.value:
             if not validate_url(self.btn2_link.value):
                return await interaction.response.send_message("❌ Link nút 2 không hợp lệ! Phải là `https://`", ephemeral=True)
             btns.append({"label": self.btn2_name.value[:32], "url": self.btn2_link.value})

        data = await self.db.get_custom_status(self.user_id) or {}
        data["buttons"] = btns
        await self.db.save_custom_status(self.user_id, data)
        await interaction.response.send_message("✅ Đã lưu thiết lập Nút bấm. Hãy nhấn **Đăng Ký** để kích hoạt.", ephemeral=True)

class StatusControlView(discord.ui.View):
    def __init__(self, bot, db, user_id):
        super().__init__(timeout=300)
        self.bot, self.db, self.user_id = bot, db, user_id

    @discord.ui.select(placeholder="Loại hoạt động...", options=[discord.SelectOption(label="Playing", value="0"), discord.SelectOption(label="Listening", value="2"), discord.SelectOption(label="Watching", value="3"), discord.SelectOption(label="Streaming", value="1")])
    async def select_type(self, interaction: discord.Interaction, select: discord.ui.Select):
        data = await self.db.get_custom_status(self.user_id) or {}
        data["type"] = int(select.values[0])
        await self.db.save_custom_status(self.user_id, data)
        await interaction.response.send_message("✅ Đã chọn loại hoạt động.", ephemeral=True)

    @discord.ui.button(label="✍️ Nhập Chữ", style=discord.ButtonStyle.primary)
    async def text_btn(self, interaction: discord.Interaction, btn):
        await interaction.response.send_modal(TextModal(self.bot, self.db, self.user_id))

    @discord.ui.button(label="🔗 Cấu Hình Nút", style=discord.ButtonStyle.secondary)
    async def btn_btn(self, interaction: discord.Interaction, btn):
        await interaction.response.send_modal(ButtonModal(self.bot, self.db, self.user_id))

    @discord.ui.button(label="🚀 Xem Preview & Đăng Ký", style=discord.ButtonStyle.success)
    async def sub_btn(self, interaction: discord.Interaction, btn):
        data = await self.db.get_custom_status(self.user_id)
        if not data or "name" not in data or not data["name"]:
            return await interaction.response.send_message("❌ Bạn chưa nhập Tên Ứng Dụng! Hãy dùng nút 'Nhập Chữ' trước.", ephemeral=True)

        desc = f"**{data.get('name', 'N/A')}**\n"
        desc += f"{data.get('details', '')}\n"
        desc += f"{data.get('state', '')}\n"

        embed = create_premium_embed(
            title="🔍 PREVIEW RICH PRESENCE",
            description=desc,
            color=0x3498db
        )
        if data.get("large_image"):
            embed.set_thumbnail(url=data.get("large_image"))

        if "buttons" in data and data["buttons"]:
            btn_txt = "\n".join([f"🔘 [{b['label']}]({b['url']})" for b in data["buttons"]])
            embed.add_field(name="Nút Bấm", value=btn_txt, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

        # Bắn tín hiệu Pub/Sub để Proxy Gateway update ngay lập tức
        await self.bot.redis.publish("equinox_presence_update", json.dumps({"user_id": self.user_id}))

class StatusUI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = EquinoxDatabase(bot.redis)

    status_group = app_commands.Group(name="status", description="[VIP] Tùy chỉnh Profile")

    @status_group.command(name="add", description="Thiết lập trạng thái")
    async def status_add(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        is_owner = (user_id == OWNER_ID)
        
        # OWNER BYPASS
        if not is_owner:
            user_level = await self.db.get_user_level(user_id)
            has_key = await self.db.has_premium(user_id)
            if user_level < 2 and not has_key:
                err_embed = create_premium_embed("TỪ CHỐI TRUY CẬP", "❌ Yêu cầu cấp độ Admin (Level 2+) hoặc thẻ Premium Key để sử dụng tính năng này.", color=0xe74c3c)
                return await interaction.response.send_message(embed=err_embed, ephemeral=True)

            oauth_l = await self.bot.redis.hexists(f"oauth:{user_id}", "luminous")
            oauth_t = await self.bot.redis.hexists(f"oauth:{user_id}", "tenebris")
            if not (oauth_l and oauth_t):
                from config.settings import LUMINOUS_CLIENT_ID, TENEBRIS_CLIENT_ID, OAUTH2_REDIRECT_URI
                main_link = await self.bot.redis.get("system_link:main_server") or DEFAULT_MAIN_SERVER_LINK
                view = AuthRequiredView(LUMINOUS_CLIENT_ID, TENEBRIS_CLIENT_ID, OAUTH2_REDIRECT_URI, main_link)
                auth_embed = create_premium_embed("YÊU CẦU ỦY QUYỀN", "⚠️ Vui lòng ủy quyền cho cả 2 bot Luminous và Tenebris để hệ thống có thể thay đổi Profile của bạn 24/7.", color=0xf1c40f)
                return await interaction.response.send_message(embed=auth_embed, view=view, ephemeral=True)

        embed = create_premium_embed("BẢNG ĐIỀU KHIỂN RICH PRESENCE", "Sử dụng các nút bên dưới để cấu hình Profile ảo của bạn.", color=0x3498db)
        await interaction.response.send_message(embed=embed, view=StatusControlView(self.bot, self.db, user_id), ephemeral=True)

    @app_commands.command(name="livestatus", description="Treo profile 24/7")
    @app_commands.choices(mode=[app_commands.Choice(name="On", value="on"), app_commands.Choice(name="Off", value="off")])
    async def livestatus(self, interaction: discord.Interaction, mode: app_commands.Choice[str]):
        user_id = interaction.user.id
        # OWNER BYPASS
        if user_id != OWNER_ID:
            if not await self.db.has_premium(user_id) and await self.db.get_user_level(user_id) < 2:
                err_embed = create_premium_embed("TỪ CHỐI", "❌ Cần Premium Key.", color=0xe74c3c)
                return await interaction.response.send_message(embed=err_embed, ephemeral=True)

        state = (mode.value == "on")
        await self.db.toggle_livestatus(user_id, state)

        status_embed = create_premium_embed("PROXY PRESENCE", f"🌐 Proxy Presence đã được chuyển sang chế độ **{mode.name.upper()}**.", color=0x2ecc71 if state else 0x95a5a6)
        await interaction.response.send_message(embed=status_embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(StatusUI(bot))
