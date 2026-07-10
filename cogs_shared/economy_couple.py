import discord
from discord.ext import commands
from discord import app_commands
from backend.economy_engine import EconomyEngine

class CoupleGiveawayModal(discord.ui.Modal, title="Tổ Chức Giveaway Đôi"):
    prize_input = discord.ui.TextInput(
        label="Phần Thưởng",
        style=discord.TextStyle.short,
        placeholder="Ví dụ: 100M Aequor, Nhẫn Kim Cương..."
    )
    desc_input = discord.ui.TextInput(
        label="Lời nhắn / Thể lệ",
        style=discord.TextStyle.long,
        placeholder="Nhập lời nhắn gửi đến server..."
    )

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🎉 GIVEAWAY ĐÃ BẮT ĐẦU! 🎉", color=discord.Color.gold())
        embed.description = f"**Host:** {interaction.user.mention}\n**Phần thưởng:** {self.prize_input.value}\n\n**Lời nhắn:**\n{self.desc_input.value}"
        embed.set_footer(text="React 🎉 để tham gia!")
        
        await interaction.response.send_message(content="@everyone", embed=embed)
        msg = await interaction.original_response()
        await msg.add_reaction("🎉")

class EconomyCouple(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.engine = EconomyEngine()

    @app_commands.command(name="marry", description="Cầu hôn và thiết lập Quỹ Gia Đình")
    async def marry(self, interaction: discord.Interaction, partner: discord.User):
        if partner.bot or partner == interaction.user:
            return await interaction.response.send_message("🚫 Đối tượng không hợp lệ.", ephemeral=True)
            
        # Kiểm tra nếu 1 trong 2 đã có gia đình
        existing_partner = await self.engine.db.get_couple_data(str(interaction.user.id))
        if existing_partner:
            return await interaction.response.send_message("🚫 Bạn đã có gia đình rồi!", ephemeral=True)

        embed = discord.Embed(title="💍 Lời Cầu Hôn Lãng Mạn", color=discord.Color.fuchsia())
        embed.description = f"{interaction.user.mention} đã quỳ gối và trao nhẫn cho {partner.mention}!\nBạn có đồng ý không?"
        await interaction.response.send_message(content=partner.mention, embed=embed)

    @app_commands.command(name="divorce", description="Ly hôn và chia đôi tài sản")
    async def divorce(self, interaction: discord.Interaction):
        # Logic gọi từ Engine để chia 50/50 tài sản Quỹ Gia Đình
        await interaction.response.send_message("💔 Đã nộp đơn ly hôn lên Tòa Án Equinox.", ephemeral=True)

    @app_commands.command(name="couple-profile", description="Hiển thị hồ sơ tình yêu")
    async def couple_profile(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🕊️ Hồ Sơ Tình Yêu Thượng Lưu", color=discord.Color.purple())
        embed.add_field(name="Spouse A", value=interaction.user.mention, inline=True)
        embed.add_field(name="💞 Điểm Thân Mật", value="999 Points", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="giveaway-create", description="Tổ chức sự kiện phát quà bằng Modal")
    async def giveaway_create(self, interaction: discord.Interaction):
        await interaction.response.send_modal(CoupleGiveawayModal())

async def setup(bot):
    await bot.add_cog(EconomyCouple(bot))
