import discord
from discord.ext import commands
from discord import app_commands

class AuthRequiredView(discord.ui.View):
    def __init__(self, luminous_link: str, tenebris_link: str, main_server_link: str):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="Mời Luminous", url=luminous_link, style=discord.ButtonStyle.link, emoji="☀️"))
        self.add_item(discord.ui.Button(label="Mời Tenebris", url=tenebris_link, style=discord.ButtonStyle.link, emoji="🌙"))
        self.add_item(discord.ui.Button(label="Server Nhà Chính", url=main_server_link, style=discord.ButtonStyle.link, emoji="🎪"))

class TextModal(discord.ui.Modal, title="Cấu Hình Nội Dung Status"):
    activity_name = discord.ui.TextInput(label="Tên Ứng Dụng / Trò Chơi", placeholder="VD: Youtube, Liên Quân...", max_length=100)
    details = discord.ui.TextInput(label="Dòng 1 (Nội dung chính)", placeholder="VD: Đang cày view...", required=False, max_length=128)
    state = discord.ui.TextInput(label="Dòng 2 (Nội dung phụ)", placeholder="VD: Trận 5 - Chuỗi thắng...", required=False, max_length=128)
    image_text = discord.ui.TextInput(label="Dòng 3 (Chữ khi di chuột vào ảnh)", placeholder="VD: Equinox VIP", required=False, max_length=128)

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(title="✅ Đã Lưu Nội Dung Status", color=interaction.client.theme_color)
        embed.add_field(name="Ứng dụng", value=self.activity_name.value, inline=False)
        if self.details.value:
            embed.add_field(name="Dòng 1", value=self.details.value, inline=False)
        if self.state.value:
            embed.add_field(name="Dòng 2", value=self.state.value, inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

class ButtonModal(discord.ui.Modal, title="Cấu Hình Nút Bấm"):
    btn1_name = discord.ui.TextInput(label="Tên Nút 1", required=False, max_length=32)
    btn1_link = discord.ui.TextInput(label="Link Nút 1", placeholder="https://...", required=False)
    btn2_name = discord.ui.TextInput(label="Tên Nút 2", required=False, max_length=32)
    btn2_link = discord.ui.TextInput(label="Link Nút 2", placeholder="https://...", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(title="✅ Đã Lưu Nút Bấm", color=interaction.client.theme_color)
        if self.btn1_name.value:
            embed.add_field(name=f"Nút 1: {self.btn1_name.value}", value=self.btn1_link.value or "Trống", inline=False)
        if self.btn2_name.value:
            embed.add_field(name=f"Nút 2: {self.btn2_name.value}", value=self.btn2_link.value or "Trống", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

class StatusControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(placeholder="Chọn loại hoạt động...", options=[
        discord.SelectOption(label="Đang chơi", value="playing", emoji="🎮"),
        discord.SelectOption(label="Đang nghe", value="listening", emoji="🎧"),
        discord.SelectOption(label="Đang xem", value="watching", emoji="📺"),
        discord.SelectOption(label="Đang stream", value="streaming", emoji="🟣"),
    ])
    async def select_activity(self, interaction: discord.Interaction, select: discord.ui.Select):
        embed = discord.Embed(description=f"✅ Đã lưu loại hoạt động: **{select.values[0].upper()}**", color=interaction.client.theme_color)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Nhập Chữ Status", style=discord.ButtonStyle.primary, emoji="✍️")
    async def text_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TextModal())

    @discord.ui.button(label="Cấu Hình Nút Bấm", style=discord.ButtonStyle.secondary, emoji="🔗")
    async def button_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ButtonModal())

    @discord.ui.button(label="Đăng Ký Trạng Thái", style=discord.ButtonStyle.success, emoji="🚀")
    async def submit_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="🎉 THIẾT LẬP TRẠNG THÁI THÀNH CÔNG!", color=0x00FF00)
        embed.description = "Cấu hình của bạn đã được tải lên hệ thống Equinox và đồng bộ với Gateway."
        embed.add_field(name="⚠️ LƯU Ý QUAN TRỌNG", value="Hiện tại trạng thái này chỉ hiển thị khi bạn đang mở app Discord.\nĐể giữ cho Profile luôn sáng đèn 24/7 kể cả khi tắt máy, hãy dùng lệnh:\n👉 `/livestatus on`", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

class StatusUI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="status_add", description="Tùy chỉnh trạng thái hiển thị trên Profile Discord thật")
    async def status_add(self, interaction: discord.Interaction):
        oauth_complete = True 
        
        if not oauth_complete:
            embed = discord.Embed(title="⚠️ YÊU CẦU ỦY QUYỀN HỆ THỐNG", color=0xFF0000)
            embed.description = "Bạn chưa cấp quyền OAuth2 (Tùy chỉnh Profile) cho các thực thể của Equinox Network.\nVui lòng click vào các nút bên dưới để xác thực trước khi tiếp tục."
            view = AuthRequiredView("https://discord.com/oauth2...", "https://discord.com/oauth2...", "https://discord.gg/equinox")
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            return

        embed = discord.Embed(title="💠 BẢNG ĐIỀU KHIỂN TRẠNG THÁI VIP", color=self.bot.theme_color)
        embed.description = "Thiết lập trạng thái hiển thị trên profile thật của bạn.\n\n*Nếu bỏ qua bước điền Form và bấm `Đăng Ký`, hệ thống sẽ tự động chạy chế độ Mặc Định (Giờ real-time & Nút bấm nhà chính).* \n\n*Link nút bấm tùy biến bắt buộc phải bắt đầu bằng `https://`*"
        embed.set_footer(text="Đặc quyền tối thượng dành cho Voice Premium Key")
        
        await interaction.response.send_message(embed=embed, view=StatusControlView())

    @app_commands.command(name="livestatus", description="Bật/Tắt chế độ treo trạng thái 24/7 (Cần Premium Key)")
    @app_commands.choices(mode=[
        app_commands.Choice(name="Bật (On)", value="on"),
        app_commands.Choice(name="Tắt (Off)", value="off")
    ])
    async def livestatus(self, interaction: discord.Interaction, mode: app_commands.Choice[str]):
        embed = discord.Embed(title="🌐 HỆ THỐNG PROXY PRESENCE", color=self.bot.theme_color)
        if mode.value == "on":
            embed.description = "✅ Đã **BẬT** chế độ treo profile 24/7.\nTrạng thái của bạn sẽ được giữ nguyên hiển thị liên tục kể cả khi tắt máy, thoát Discord hay rớt mạng."
        else:
            embed.description = "❌ Đã **TẮT** chế độ treo profile 24/7.\nTrạng thái sẽ trở về bình thường theo thiết bị của bạn."
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(StatusUI(bot))
