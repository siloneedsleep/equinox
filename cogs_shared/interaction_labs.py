import discord
from discord.ext import commands
from discord import app_commands
import os
from backend.database import EquinoxDatabase
from backend.economy_engine import EconomyEngine

class InteractionLabs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = EquinoxDatabase(bot.redis)
        self.engine = EconomyEngine(self.db)

    @app_commands.command(name="set_will", description="Lập di chúc ngầm cho người phối ngẫu")
    async def set_will(self, interaction: discord.Interaction, spouse: discord.Member):
        if spouse.id == interaction.user.id or spouse.bot:
            return await interaction.response.send_message("❌ Không thể lập di chúc cho chính mình hoặc Bot.", ephemeral=True)

        await self.db.set_will(interaction.user.id, spouse.id)
        embed = discord.Embed(title="📜 DI CHÚC NGẦM ĐÃ ĐƯỢC LẬP", color=0x2B2D31)
        embed.description = f"Trong trường hợp bạn bị sát hại, 70% tài sản còn lại sẽ thuộc về {spouse.mention}.\n*Bản di chúc này được lưu giữ bí mật bởi Tenebris.*"
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="assassinate", description="[Tenebris] Ám sát một mục tiêu để cướp 30% tài sản sạch")
    async def assassinate(self, interaction: discord.Interaction, victim: discord.Member):
        if self.bot.persona != "Tenebris":
            return await interaction.response.send_message("❌ Chỉ có thể thực hiện ám sát trong ca trực của Tenebris (Ca Đêm).", ephemeral=True)
        
        if victim.id == interaction.user.id or victim.bot:
            return await interaction.response.send_message("❌ Mục tiêu không hợp lệ.", ephemeral=True)

        # Xử lý logic ám sát qua Engine
        result = await self.engine.process_assassination(interaction.user.id, victim.id)

        embed = discord.Embed(title="🩸 HỢP ĐỒNG SÁT THỦ HOÀN TẤT", color=0xFF0000)
        if result["stolen"] > 0:
            embed.description = f"{interaction.user.mention} đã ám sát thành công {victim.mention}!\n💰 Cướp được: **{result['stolen']:,}** Aequor (đã đổi sang Aequis)."
            if result["will_triggered"]:
                embed.add_field(name="📜 Di chúc kích hoạt", value=f"70% tài sản còn lại của nạn nhân đã được chuyển cho người phối ngẫu (<@{result['spouse_id']}>).")
            else:
                embed.add_field(name="❄️ Tài sản đóng băng", value="Nạn nhân không có di chúc, toàn bộ tiền còn lại đã bị hệ thống thu hồi.")

            embed.set_footer(text=f"⚠️ Một lệnh Truy Nã (Bounty) trị giá {result['bounty_posted']:,} đã được treo lên đầu sát thủ!")
        else:
            embed.description = f"{interaction.user.mention} đã ra tay nhưng nạn nhân {victim.mention} quá nghèo để cướp."

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="chat", description="[Owner Only] Gửi tin nhắn dưới danh nghĩa Bot hoặc Webhook")
    @app_commands.choices(mode=[
        app_commands.Choice(name="Bot Mode", value="bot"),
        app_commands.Choice(name="Webhook Mode (Giả danh)", value="webhook")
    ])
    async def owner_chat(self, interaction: discord.Interaction, mode: app_commands.Choice[str], message: str,
                         channel: discord.TextChannel = None, reply_to: str = None,
                         fake_name: str = None, fake_avatar: str = None):

        if interaction.user.id != int(os.getenv("OWNER_ID", 0)):
            return await interaction.response.send_message("❌ Lệnh này chỉ dành cho Đấng Tạo Hóa.", ephemeral=True)
            
        target_channel = channel or interaction.channel

        if mode.value == "bot":
            # Chế độ Bot
            if reply_to:
                try:
                    ref_msg = await target_channel.fetch_message(int(reply_to))
                    await ref_msg.reply(content=message)
                except:
                    await target_channel.send(content=message)
            else:
                await target_channel.send(content=message)
            await interaction.response.send_message("✅ Đã gửi tin nhắn (Bot Mode).", ephemeral=True)
            
        else:
            # Chế độ Webhook
            webhook = await target_channel.create_webhook(name=fake_name or "Equinox System")
            await webhook.send(
                content=message,
                username=fake_name or "Equinox System",
                avatar_url=fake_avatar or self.bot.user.avatar.url
            )
            await webhook.delete() # Xóa dấu vết
            await interaction.response.send_message("✅ Đã gửi tin nhắn (Webhook Mode - Tuyệt mật).", ephemeral=True)

async def setup(bot):
    await bot.add_cog(InteractionLabs(bot))
