import os
import discord
from discord import app_commands
from discord.ext import commands
import google.generativeai as genai
from database.redis_client import get_redis_connection

# Cấu hình API Key cho Gemini AI hạch tâm từ file .env
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

class CelestialKarma(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    # ==============================================================================
    # 📌 HÀM BỔ TRỢ: GHI NHẬT KÝ HÀNH VI (GỌI HÀM NÀY Ở CÁC COG KHÁC KHI USER HÀNH ĐỘNG)
    # ==============================================================================
    @staticmethod
    async def log_karma_action(user_id: int, action_description: str):
        """
        Hàm tĩnh để sếp dễ dàng import và gọi ở bất kỳ file nào.
        Ví dụ: await CelestialKarma.log_karma_action(interaction.user.id, "Đã ôm @Ai_đó ca ngày")
               await CelestialKarma.log_karma_action(interaction.user.id, "Thuê sát thủ bắt cóc @Ai_đó ca đêm")
        """
        r = await get_redis_connection()
        history_key = f"equinox:karma:history:{user_id}"
        
        # Đẩy hành vi mới vào danh sách (List) trên Redis
        await r.rpush(history_key, action_description)
        # Giới hạn chỉ lưu tối đa 7 hành vi gần nhất để prompt không bị quá dài
        await r.ltrim(history_key, -7, -1)
        # Set TTL 3 ngày cho nhật ký tự hủy nếu member lặn mất tăm
        await r.expire(history_key, 259200)

    # ==============================================================================
    # ⚖️ LỆNH SLASH: NHẬT KÝ NGHIỆP QUẢ - AI PHÁN XÉT CA TRỰC
    # ==============================================================================
    @app_commands.command(name="karma", description="Nhờ Luminous hoặc Tenebris đọc vị nhật ký hành vi và phán xét linh hồn của sếp")
    @app_commands.describe(user="Đối tượng muốn xem sổ sinh tử (Để trống nếu tự check bản thân)")
    async def view_karma(self, interaction: discord.Interaction, user: discord.Member = None):
        await interaction.response.defer()
        
        target = user if user else interaction.user
        target_id = str(target.id)
        
        r = await get_redis_connection()

        # 🕒 1. Đọc ca trực thực tế trên RAM Redis
        cycle_bytes = await r.hget("equinox:system:config", "current_cycle")
        cycle = cycle_bytes.decode('utf-8') if cycle_bytes else "DAY"

        # 🗂️ 2. BỐC NHẬT KÝ HÀNH VI TỪ REDIS
        history_key = f"equinox:karma:history:{target_id}"
        actions_bytes = await r.lrange(history_key, 0, -1)
        
        # Nếu chưa có lịch sử, tạo bối cảnh trống
        if not actions_bytes:
            actions_list = ["Chưa thực hiện hành động nổi bật nào, một linh hồn trống rỗng."]
        else:
            actions_list = [act.decode('utf-8') for act in actions_bytes]
            
        actions_string = "\n- ".join(actions_list)

        # 🧠 3. ĐỊNH HÌNH LORE VÀ PROMPT ÉP VĂN PHÒNG AI
        if cycle == "DAY":
            # ☀️ CA NGÀY: Luminous tuyên dương công trạng, bao dung, hướng thiện
            system_instruction = (
                "Bạn là Luminous, linh vật nữ thần Ánh Sáng tối cao của hệ sinh thái Equinox Network. "
                "Tính cách của bạn: Dịu dàng, ấm áp, luôn nhìn vào mặt tích cực để bao dung, khen ngợi hoặc khuyên nhủ hướng thiện. "
                "Nhiệm vụ: Hãy đọc danh sách các hành vi gần đây của người dùng và viết một bài 'Phân tích Nghiệp Quả' ngắn gọn (dưới 150 từ). "
                "Nếu họ làm việc tốt (ôm, hôn, chúc phúc), hãy khen ngợi hết lời. Nếu họ làm việc xấu (bắt cóc, phá hoại), hãy nhẹ nhàng nhắc nhở, khuyên bảo họ quay đầu. "
                "Hãy xưng là 'Em' và gọi họ là 'Sếp' hoặc tag tên họ. Trả lời bằng văn phong ngọt ngào."
            )
            embed_title = f"⚖️ SỔ SINH TỬ LUMINOUS: PHÁN QUYẾT ÁNH SÁNG"
            embed_color = 0xFFD700
            author_name = "☀️ Luminous Thần Điện"
        else:
            # 🔮 CA ĐÊM: Tenebris vạch trần tội trạng, móc mỉa, dark humor
            system_instruction = (
                "Bạn là Tenebris, linh vật nam chúa tể Bóng Tối, gác cổng Chợ Đen của hệ sinh thái Equinox Network. "
                "Tính cách của bạn: Lạnh lùng, thực tế, độc miệng, thích cà khịa và có văn phong tấu hài đen (dark humor). "
                "Nhiệm vụ: Hãy đọc danh sách các hành vi gần đây của người dùng và viết một bài 'Bóc Trần Tội Trạng' ngắn gọn (dưới 150 từ). "
                "Nếu họ làm việc xấu ban đêm (bắt cóc, gài bẫy, đỏ đen), hãy đắc chí, rủ họ làm phản diện. Nếu họ làm việc tốt ban ngày, hãy mỉa mai họ là kẻ giả tạo thích làm người tốt. "
                "Hãy xưng là 'Ta' hoặc 'Tôi' và gọi họ là 'Ngươi' hoặc 'Sếp'. Trả lời đanh thép, khét lẹt."
            )
            embed_title = f"⚖️ SỔ SINH TỬ TENEBRIS: PHÁN XÉT BÓNG ĐÊM"
            embed_color = 0x4B0082
            author_name = "🔮 Tenebris Chợ Đen"

        # 📡 4. ĐẨY DATA CHO GEMINI XỬ LÝ
        prompt = (
            f"Chỉ chỉ hệ thống: {system_instruction}\n\n"
            f"Danh tính đối tượng: {target.display_name}\n"
            f"Nhật ký hành vi bốc từ hệ thống:\n- {actions_string}\n\n"
            f"Hãy đưa ra lời luận tội hoặc tuyên dương công trạng ngay:"
        )

        try:
            response = await self.bot.loop.run_in_executor(
                None, 
                lambda: self.model.generate_content(prompt)
            )
            ai_reply = response.text
        except Exception as e:
            ai_reply = f"🚨 *Cán cân nghiệp quả bị nhiễu sóng:* (Lỗi kết nối AI: {e})"

        # 📊 5. ĐÓNG GÓI EMBED XUẤT RA DIỆN DIỆN
        embed = discord.Embed(description=ai_reply, color=embed_color)
        embed.set_author(name=author_name, icon_url=self.bot.user.display_avatar.url)
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="📜 Lịch sử lưu vết ngầm gần đây", value=f"```md\n- {actions_string}\n```", inline=False)
        embed.set_footer(text=f"Yêu cầu bởi {interaction.user.display_name}")

        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(CelestialKarma(bot))
