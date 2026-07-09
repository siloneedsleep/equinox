import discord
from discord.ext import commands
from cogs_shared.embed_util import create_premium_embed

class HelpSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Core System", description="Quản lý hệ thống, Ping, Status", emoji="🪐"),
            discord.SelectOption(label="Economy", description="Hệ thống kinh tế, túi mù, rửa tiền", emoji="💰"),
            discord.SelectOption(label="Identity/Status", description="Quản lý Profile và Presence", emoji="🎭"),
            discord.SelectOption(label="Giveaways", description="Quản lý Giveaways", emoji="🎉"),
            discord.SelectOption(label="Pick Roles", description="Lấy Role tự động", emoji="🏷️")
        ]
        super().__init__(placeholder="Chọn một chuyên mục để xem chi tiết...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        # Prevent default empty response error
        await interaction.response.defer()

        category = self.values[0]
        embed = create_premium_embed(title=f"{category} Commands", description=f"Danh sách các lệnh cho mục **{category}**.")

        if category == "Core System":
            embed.add_field(name="/ping", value="Kiểm tra độ trễ của Bot.\n*Quyền: Mọi người (Level 0)*", inline=False)
            embed.add_field(name="/jules", value="Truy cập Jules Core.\n*Quyền: Silo/Dev (Level 3-4)*", inline=False)
        elif category == "Economy":
            embed.add_field(name="/wallet", value="Xem số dư Aequor/Aequis.\n*Quyền: Mọi người (Level 0)*", inline=False)
            embed.add_field(name="/starpouch", value="Mở túi mù ngẫu nhiên.\n*Quyền: Mọi người (Level 0)*", inline=False)
            embed.add_field(name="/laundering", value="Rửa tiền (Aequis -> Aequor).\n*Quyền: Mọi người (Level 0)*", inline=False)
            embed.add_field(name="/assassinate", value="Ám sát người chơi khác.\n*Quyền: Mọi người (Level 0)*", inline=False)
        elif category == "Identity/Status":
            embed.add_field(name="/status add", value="Thiết lập Rich Presence (Profile).\n*Quyền: Admin/Premium (Level 2+)*", inline=False)
            embed.add_field(name="/livestatus", value="Kích hoạt Proxy duy trì Profile 24/7.\n*Quyền: Admin/Premium (Level 2+)*", inline=False)
        elif category == "Giveaways":
            embed.add_field(name="/giveaway create", value="Tạo Giveaway mới (với Modal).\n*Quyền: Admin (Level 2+)*", inline=False)
        elif category == "Pick Roles":
            embed.add_field(name="/role-setup", value="Thiết lập bảng chọn Role bằng Emoji.\n*Quyền: Admin (Level 2+)*", inline=False)

        await interaction.edit_original_response(embed=embed)

class HelpView(discord.ui.View):
    def __init__(self, timeout=60):
        super().__init__(timeout=timeout)
        self.add_item(HelpSelect())

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        # It's tricky to edit the message on timeout without storing it,
        # so typically we just let the components visually freeze client-side,
        # or we store the message object when sending.

class GeneralUI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="help", description="Hiển thị menu trợ giúp toàn diện của Equinox")
    async def help_cmd(self, interaction: discord.Interaction):
        embed = create_premium_embed(
            title="🪐 Equinox Network - Trung tâm Trợ Giúp",
            description="Chào mừng bạn đến với Equinox! Vui lòng chọn một chuyên mục từ menu thả xuống bên dưới để khám phá các tính năng của hệ sinh thái.",
            color=self.bot.theme_color
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        view = HelpView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(GeneralUI(bot))
