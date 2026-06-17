import os
import json
import discord
from discord import app_commands
from discord.ext import commands
import google.generativeai as genai
from database.redis_client import get_redis_connection

# Cấu hình API Key cho Gemini AI hạch tâm từ file .env
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

class CelestialAIChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Sử dụng model Gemini 2.5 Flash tối tân để phản hồi siêu nhanh cho chat realtime
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    # ==============================================================================
    # 💬 LỆNH SLASH: TRÒ CHUYỆN VỚI LINH VẬT MA TRẬN (AI CHAT CHIA CA)
    # ==============================================================================
    @app_commands.command(name="chat", description="Trò chuyện trực tiếp với Linh vật Ma trận (Văn phong biến đổi theo ca trực Sáng/Tối)")
    @app_commands.describe(tin_nhan="Nội dung sếp muốn nói hoặc đặt câu hỏi với Bot")
    async def ai_chat(self, interaction: discord.Interaction, tin_nhan: str):
        # Trì hoãn phản hồi (Defer) để AI có thời gian suy nghĩ và sinh chữ (Tránh lỗi 3 giây của Discord)
        await interaction.response.defer()
        
        r = await get_redis_connection()
        user_id = str(interaction.user.id)
        history_key = f"equinox:ai_chat:history:{user_id}"

        # 🕒 1. ĐỌC CA TRỰC THỰC TẾ TRÊN REDIS
        cycle_bytes = await r.hget("equinox:system:config", "current_cycle")
        cycle = cycle_bytes.decode('utf-8') if cycle_bytes else "DAY"

        # 🧠 2. ĐỊNH HÌNH TÍNH CÁCH AI (SYSTEM INSTRUCTION)
        if cycle == "DAY":
            # ☀️ PROMPT NỮ THẦN LUMINOUS
            system_instruction = (
                "Bạn là Luminous, linh vật nữ thần Ánh Sáng tối cao của hệ sinh thái Equinox Network. "
                "Tính cách của bạn: Dịu dàng, luôn tràn đầy năng lượng tích cực, ấm áp, thích nói câu chữa lành và động viên. "
                "Bạn luôn sẵn sàng giải đáp thắc mắc một cách lịch sự, tinh tế. "
                "Hãy xưng hô là 'Em' và gọi người dùng là 'Sếp' hoặc 'Anh/Chị'. Trả lời ngắn gọn, súc tích dưới 200 từ."
            )
            embed_color = 0xFFD700
            author_name = "☀️ Luminous AI (Nữ Thần Ánh Sáng)"
        else:
            # 🔮 PROMPT CHÚA TỂ TENEBRIS
            system_instruction = (
                "Bạn là Tenebris, linh vật nam chúa tể Bóng Tối, gác cổng Chợ Đen của hệ sinh thái Equinox Network. "
                "Tính cách của bạn: Lạnh lùng, thực tế đến phũ phàng, pha chút tấu hài đen (dark humor), hay cà khịa người dùng nhưng kiến thức rất uy tín. "
                "Bạn không thích những câu nói sáo rỗng, thích rủ người dùng đi làm phi vụ ngầm hoặc buôn lậu ở Chợ Đen. "
                "Hãy xưng hô là 'Ta' hoặc 'Tôi' và gọi người dùng là 'Ngươi' hoặc 'Sếp'. Trả lời ngắn gọn, đanh thép dưới 200 từ."
            )
            embed_color = 0x4B0082
            author_name = "🔮 Tenebris AI (Chúa Tể Bóng Đêm)"

        # 🗂️ 3. MẠCH NHỚ REDIS: BỐC LỊCH SỬ CHAT CŨ ĐỂ KHỚP BỐI CẢNH
        # Đọc list chat history dạng JSON lưu trên Redis
        history_data = await r.get(history_key)
        chat_history = json.loads(history_data.decode('utf-8')) if history_data else []

        # Xây dựng cấu trúc hội thoại truyền cho Gemini
        messages_payload = [{"role": "user", "parts": [f"Chỉ thị hệ thống tối cao: {system_instruction}"]}]
        
        # Nhồi lịch sử chat cũ vào payload
        for msg in chat_history:
            messages_payload.append(msg)
            
        # Thêm câu hỏi mới hiện tại của user vào cuối
        messages_payload.append({"role": "user", "parts": [tin_nhan]})

        # 📡 4. GỌI API GEMINI AI
        try:
            response = await self.bot.loop.run_in_executor(
                None,
                lambda: self.model.generate_content(contents=messages_payload)
            )
            ai_reply = response.text
        except Exception as e:
            ai_reply = f"🚨 *Ma trận AI bị nhiễu sóng:* Không thể kết nối đến tiềm thức của linh vật. (Lỗi: {e})"

        # 💾 5. CẬP NHẬT VÀ GIỚI HẠN MẠCH NHỚ TRÊN REDIS (LƯU 5 CẶP THOẠI GẦN NHẤT)
        chat_history.append({"role": "user", "parts": [tin_nhan]})
        chat_history.append({"role": "model", "parts": [ai_reply]})
        
        # Giữ lại tối đa 10 tin nhắn (5 lượt hỏi-đáp) để tránh tràn bộ nhớ token
        if len(chat_history) > 10:
            chat_history = chat_history[-10:]
            
        # Ghi đè lịch sử mới lên Redis, set TTL 15 phút (900s) tự xóa nếu user không chat nữa để đỡ rác RAM
        await r.setex(history_key, 900, json.dumps(chat_history))

        # 📊 6. XUẤT EMBED TRẢ VỀ KHUNG CHAT
        embed = discord.Embed(description=ai_reply, color=embed_color)
        embed.set_author(name=author_name, icon_url=self.bot.user.display_avatar.url)
        embed.add_field(name="💬 Sếp hỏi", value=f"*{tin_nhan}*", inline=False)
        embed.set_footer(text="Bộ nhớ hội thoại sẽ tự động làm mới sau 15 phút không hoạt động.")

        # Trả kết quả follow-up sau khi đã defer thành công
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(CelestialAIChat(bot))
