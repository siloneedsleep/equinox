import discord
from discord.ext import commands
from discord import app_commands
from backend.database import EquinoxDatabase
from config.settings import DEFAULT_MAIN_SERVER_LINK, OWNER_ID

class AuthRequiredView(discord.ui.View):
    def __init__(self, luminous_id: str, tenebris_id: str, redirect_uri: str, main_server_link: str):
        super().__init__(timeout=None)
        scopes = "identify%20activities.write"
        l_link = f"https://discord.com/oauth2/authorize?client_id={luminous_id}&redirect_uri={redirect_uri}&response_type=code&scope={scopes}&state=luminous"
        t_link = f"https://discord.com/oauth2/authorize?client_id={tenebris_id}&redirect_uri={redirect_uri}&response_type=code&scope={scopes}&state=tenebris"
        self.add_item(discord.ui.Button(label="Ủy quyền Luminous", url=l_link, style=discord.ButtonStyle.link, emoji="☀️"))
        self.add_item(discord.ui.Button(label="Ủy quyền Tenebris", url=t_link, style=discord.ButtonStyle.link, emoji="🌙"))
        self.add_item(discord.ui.Button(label="Server Nhà Chính", url=main_server_link, style=discord.ButtonStyle.link, emoji="🎪"))

class TextModal(discord.ui.Modal, title="Nội Dung Status"):
    activity_name = discord.ui.TextInput(label="Activity Name", placeholder="VD: Youtube")
    details = discord.ui.TextInput(label="Details", required=False)
    state = discord.ui.TextInput(label="State", required=False)
    image_text = discord.ui.TextInput(label="Image Text", required=False)
    image_url = discord.ui.TextInput(label="Image URL", required=False)
    def __init__(self, db, user_id):
        super().__init__()
        self.db, self.user_id = db, user_id
    async def on_submit(self, interaction: discord.Interaction):
        data = await self.db.get_custom_status(self.user_id) or {}
        data.update({"name": self.activity_name.value, "details": self.details.value, "state": self.state.value, "large_text": self.image_text.value, "large_image": self.image_url.value})
        await self.db.save_custom_status(self.user_id, data)
        await interaction.response.send_message("✅ Đã lưu chữ.", ephemeral=True)

class ButtonModal(discord.ui.Modal, title="Cấu Hình Nút"):
    btn1_name = discord.ui.TextInput(label="Tên Nút 1", required=False)
    btn1_link = discord.ui.TextInput(label="Link Nút 1", required=False)
    btn2_name = discord.ui.TextInput(label="Tên Nút 2", required=False)
    btn2_link = discord.ui.TextInput(label="Link Nút 2", required=False)
    def __init__(self, db, user_id):
        super().__init__()
        self.db, self.user_id = db, user_id
    async def on_submit(self, interaction: discord.Interaction):
        btns = []
        if self.btn1_name.value and self.btn1_link.value: btns.append({"label": self.btn1_name.value, "url": self.btn1_link.value})
        if self.btn2_name.value and self.btn2_link.value: btns.append({"label": self.btn2_name.value, "url": self.btn2_link.value})
        data = await self.db.get_custom_status(self.user_id) or {}
        data["buttons"] = btns
        await self.db.save_custom_status(self.user_id, data)
        await interaction.response.send_message("✅ Đã lưu nút.", ephemeral=True)

class StatusControlView(discord.ui.View):
    def __init__(self, db, user_id):
        super().__init__(timeout=300)
        self.db, self.user_id = db, user_id
    @discord.ui.select(placeholder="Loại hoạt động...", options=[discord.SelectOption(label="Playing", value="0"), discord.SelectOption(label="Listening", value="2"), discord.SelectOption(label="Watching", value="3"), discord.SelectOption(label="Streaming", value="1")])
    async def select_type(self, interaction: discord.Interaction, select: discord.ui.Select):
        data = await self.db.get_custom_status(self.user_id) or {}
        data["type"] = int(select.values[0])
        await self.db.save_custom_status(self.user_id, data)
        await interaction.response.send_message("✅ Đã chọn loại.", ephemeral=True)
    @discord.ui.button(label="✍️ Nhập Chữ", style=discord.ButtonStyle.primary)
    async def text_btn(self, interaction: discord.Interaction, btn): await interaction.response.send_modal(TextModal(self.db, self.user_id))
    @discord.ui.button(label="🔗 Cấu Hình Nút", style=discord.ButtonStyle.secondary)
    async def btn_btn(self, interaction: discord.Interaction, btn): await interaction.response.send_modal(ButtonModal(self.db, self.user_id))
    @discord.ui.button(label="🚀 Đăng Ký", style=discord.ButtonStyle.success)
    async def sub_btn(self, interaction: discord.Interaction, btn): await interaction.response.send_message("🎉 Đã thiết lập thành công!", ephemeral=True)

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
                return await interaction.response.send_message("❌ Yêu cầu Admin+ hoặc Premium Key.", ephemeral=True)

            oauth_l = await self.bot.redis.hexists(f"oauth:{user_id}", "luminous")
            oauth_t = await self.bot.redis.hexists(f"oauth:{user_id}", "tenebris")
            if not (oauth_l and oauth_t):
                from config.settings import LUMINOUS_CLIENT_ID, TENEBRIS_CLIENT_ID, OAUTH2_REDIRECT_URI
                main_link = await self.bot.redis.get("system_link:main_server") or DEFAULT_MAIN_SERVER_LINK
                view = AuthRequiredView(LUMINOUS_CLIENT_ID, TENEBRIS_CLIENT_ID, OAUTH2_REDIRECT_URI, main_link)
                return await interaction.response.send_message("⚠️ Cần ủy quyền OAuth2.", view=view, ephemeral=True)

        await interaction.response.send_message("💠 BẢNG ĐIỀU KHIỂN VIP", view=StatusControlView(self.db, user_id), ephemeral=True)

    @app_commands.command(name="livestatus", description="Treo profile 24/7")
    @app_commands.choices(mode=[app_commands.Choice(name="On", value="on"), app_commands.Choice(name="Off", value="off")])
    async def livestatus(self, interaction: discord.Interaction, mode: app_commands.Choice[str]):
        user_id = interaction.user.id
        # OWNER BYPASS
        if user_id != OWNER_ID:
            if not await self.db.has_premium(user_id) and await self.db.get_user_level(user_id) < 2:
                return await interaction.response.send_message("❌ Cần Premium Key.", ephemeral=True)

        state = (mode.value == "on")
        await self.db.toggle_livestatus(user_id, state)
        await interaction.response.send_message(f"🌐 Đã **{mode.name.upper()}** Proxy Presence.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(StatusUI(bot))
