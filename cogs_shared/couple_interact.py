import discord
from discord import app_commands
from discord.ext import commands
from database.redis_client import get_redis_connection
# Import file Sổ Sinh Tử AI để nạp log ngầm
from cogs_shared.celestial_karma import CelestialKarma 

class CoupleInteract(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Hàm lõi (Helper Function) xử lý tương tác chéo và check "trà xanh" gốc của sếp
    async def process_interaction(self, interaction: discord.Interaction, target: discord.Member, action_name: str, action_icon: str, action_past: str):
        if target.id == interaction.user.id:
            await interaction.response.send_message(f"❌ Sếp định tự {action_name} chính mình à? Đáng thương vcl... Kiếm người yêu đi sếp!", ephemeral=True)
            return

        # Đoạn check nhắm vào 2 con Bot để lôi Lore ông xã/sát thủ ra hăm dọa
        if target.id == self.bot.user.id:
            from config.settings import LUMINOUS_ID, TENEBRIS_ID
            if target.id == LUMINOUS_ID:
                await interaction.response.send_message("🚨 **CẢNH BÁO HẠCH TÂM:** Gan to bằng trời! Dám đụng vào Luminous hả? Tenebris mà biết gã sẽ xua sát thủ Chợ Đen đến bế sếp đi đấy!", ephemeral=True)
            else:
                await interaction.response.send_message("🔮 **TENEBRIS PHẢN HỒI:** Tránh xa ta ra cái tên phàm trần kia, ta không rảnh làm trò cẩu lương này với ngươi!", ephemeral=True)
            return

        r = await get_redis_connection()
        
        # 1. MẠCH CHECK CA TRỰC ĐỂ NẠP LOG KARMA CHUẨN LORE
        cycle_bytes = await r.hget("equinox:system:config", "current_cycle")
        cycle = cycle_bytes.decode('utf-8') if cycle_bytes else "DAY"
        
        # Ép chuỗi trạng thái ghi log gửi cho Karma AI
        time_text = "ca ngày" if cycle == "DAY" else "ca đêm"
        karma_log = f"Đã dùng lệnh /{action_name} để {action_name} @{target.display_name} vào {time_text}"
        
        # Nạp dữ liệu chạy ngầm lên RAM Redis cho con AI đọc vị sau này
        await CelestialKarma.log_karma_action(interaction.user.id, karma_log)

        # 2. XỬ LÝ BIỂU THỊ EMBED TƯƠNG TÁC RA KHUNG CHAT MƯỢT MÀ
        embed = discord.Embed(
            description=f"{action_icon} **{interaction.user.mention}** đã {action_past} **{target.mention}** một cái thật gắt!",
            color=0x00FFFF if cycle == "DAY" else "0x4B0082"
        )
        await interaction.response.send_message(embed=embed)

    # ==============================================================================
    # BỘ LỆNH SLASH TƯƠNG TÁC ĐỒNG BỘ (BẬT LÊN LÀM VỐN CHO KARMA AI)
    # ==============================================================================
    @app_commands.command(name="kiss", description="Trao cho đối phương một nụ hôn nồng cháy (Tự động nạp log Karma)")
    async def couple_kiss(self, interaction: discord.Interaction, target: discord.Member):
        await self.process_interaction(interaction, target, "kiss", "💋", "hôn")

    @app_commands.command(name="hug", description="Ôm chầm lấy đối phương thật ấm áp (Tự động nạp log Karma)")
    async def couple_hug(self, interaction: discord.Interaction, target: discord.Member):
        await self.process_interaction(interaction, target, "hug", "🫂", "ôm")

    @app_commands.command(name="cuddle", description="Âu yếm, nũng nịu với đối phương")
    async def couple_cuddle(self, interaction: discord.Interaction, target: discord.Member):
        await self.process_interaction(interaction, target, "cuddle", "❤️", "âu yếm")

async def setup(bot):
    await bot.add_cog(CoupleInteract(bot))
