import discord
from discord import app_commands
from discord.ext import commands
from database.redis_client import get_redis_connection
from config.settings import LUMINOUS_ID, TENEBRIS_ID

class CoupleInteract(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ==============================================================================
    # 🧠 HÀM XỬ LÝ LOGIC TÌNH TRƯỜNG CHUNG CHO TẤT CẢ LỆNH
    # ==============================================================================
    async def process_interaction(self, interaction: discord.Interaction, target: discord.Member, action_name: str, emoji: str):
        if target.id == interaction.user.id:
            await interaction.response.send_message(f"❌ Tự luyến à sếp? Ai lại tự {action_name} chính mình!", ephemeral=True)
            return

        r = await get_redis_connection()

        # 👑 EASTER EGG: DÁM ĐỤNG VÀO BOT CỐT TRUYỆN
        if target.id in [LUMINOUS_ID, TENEBRIS_ID]:
            if target.id == LUMINOUS_ID:
                await interaction.response.send_message(f"🔪 <@{TENEBRIS_ID}>: Thằng ranh con! Dám đụng vào vợ tao à? Tao đang ngủ cũng phải bật dậy xiên mày!")
            else:
                await interaction.response.send_message(f"🔪 <@{LUMINOUS_ID}>: Tránh xa ông xã Tenebris của bà ra cái đồ Tuesday này!")
            return

        # 💍 CHECK TÌNH TRẠNG HÔN NHÂN CỦA CẢ 2 BÊN
        actor_spouse_bytes = await r.get(f"equinox:marry:{interaction.user.id}")
        target_spouse_bytes = await r.get(f"equinox:marry:{target.id}")

        actor_spouse = actor_spouse_bytes.decode('utf-8') if actor_spouse_bytes else None
        target_spouse = target_spouse_bytes.decode('utf-8') if target_spouse_bytes else None

        # 💖 Trường hợp 1: Hai vợ chồng tương tác hợp pháp
        if actor_spouse == str(target.id):
            embed = discord.Embed(
                description=f"💖 Tình củm ghê! <@{interaction.user.id}> đã {action_name} vợ/chồng yêu <@{target.id}> {emoji}. Phát cẩu lương ngập Server!",
                color=0xFF69B4
            )
            await interaction.response.send_message(embed=embed)
            return

        # 🚨 Trường hợp 2: Kẻ chủ động ĐÃ CÓ VỢ/CHỒNG nhưng đi ngoại tình
        if actor_spouse and actor_spouse != str(target.id):
            embed = discord.Embed(
                title="🚨 BẮT QUẢ TANG NGOẠI TÌNH! 🚨",
                description=f"<@{interaction.user.id}> đã có gia đình mà còn dám ra ngoài {action_name} <@{target.id}>!\n\n<@{actor_spouse}> ra xem vợ/chồng mình đi léng phéng cắm sừng mình này!",
                color=0xFF0000
            )
            await interaction.response.send_message(embed=embed)
            return

        # 🚨 Trường hợp 3: Nạn nhân ĐÃ CÓ VỢ/CHỒNG, kẻ chủ động đập chậu cướp hoa
        if target_spouse and target_spouse != str(interaction.user.id):
            embed = discord.Embed(
                title="🚨 PHÁT HIỆN TRÀ XANH ĐẬP CHẬU CƯỚP HOA! 🚨",
                description=f"<@{interaction.user.id}> đang giở trò đồi bại, dám {action_name} người đã có gia đình là <@{target.id}>!\n\nCảnh sát tình trường gọi tên <@{target_spouse}> mau ra bế vợ/chồng mình về và tẩn cho thằng kia một trận!",
                color=0xFF0000
            )
            await interaction.response.send_message(embed=embed)
            return

        # 🍻 Trường hợp 4: Cả hai đều độc thân vui tính
        msg_dict = {
            "hôn má": f"😘 <@{interaction.user.id}> đã trao nụ hôn ngọt ngào cho <@{target.id}>. Này là đang tán tỉnh nhau đúng không?",
            "ôm chầm lấy": f"🤗 <@{interaction.user.id}> đã dang tay ôm <@{target.id}> vào lòng cực kỳ ấm áp!",
            "âu yếm": f"🥰 <@{interaction.user.id}> đang rúc vào âu yếm <@{target.id}>. Quá trời mờ ám rồi nha!",
            "cắn yêu": f"🧛 <@{interaction.user.id}> vừa cắn yêu một cái rõ đau vào người <@{target.id}>. Bạo lực thế!",
            "xoa đầu": f"🥺 <@{interaction.user.id}> dịu dàng xoa đầu <@{target.id}>. Cưng chiều hết nấc!"
        }
        await interaction.response.send_message(msg_dict.get(action_name, f"<@{interaction.user.id}> đã {action_name} <@{target.id}> {emoji}"))


    # ==============================================================================
    # 🎭 ĐĂNG KÝ CÁC LỆNH SLASH
    # ==============================================================================
    @app_commands.command(name="kiss", description="Trao nụ hôn cho một ai đó trong Server")
    async def kiss(self, interaction: discord.Interaction, target: discord.Member):
        await self.process_interaction(interaction, target, "hôn má", "😘")

    @app_commands.command(name="hug", description="Ôm chặt một ai đó vào lòng")
    async def hug(self, interaction: discord.Interaction, target: discord.Member):
        await self.process_interaction(interaction, target, "ôm chầm lấy", "🤗")

    @app_commands.command(name="cuddle", description="Âu yếm cọ quậy với một ai đó")
    async def cuddle(self, interaction: discord.Interaction, target: discord.Member):
        await self.process_interaction(interaction, target, "âu yếm", "🥰")

    @app_commands.command(name="bite", description="Cắn yêu ai đó một cái")
    async def bite(self, interaction: discord.Interaction, target: discord.Member):
        await self.process_interaction(interaction, target, "cắn yêu", "🧛")

    @app_commands.command(name="pat", description="Xoa đầu vỗ về ai đó")
    async def pat(self, interaction: discord.Interaction, target: discord.Member):
        await self.process_interaction(interaction, target, "xoa đầu", "🥺")

async def setup(bot):
    await bot.add_cog(CoupleInteract(bot))
