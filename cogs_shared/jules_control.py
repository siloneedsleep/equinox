import discord
from discord.ext import commands
from discord import app_commands
import os
import json
from ai_labs.persona_engine import AIEngine
from backend.database import EquinoxDatabase

class JulesControl(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = EquinoxDatabase(bot.redis)
        self.ai = AIEngine(bot.redis)

    async def check_dev_or_owner(self, interaction: discord.Interaction) -> bool:
        user_id = interaction.user.id
        owner_id = int(os.getenv("OWNER_ID", 0))
        user_level = await self.db.get_user_level(user_id)

        # Level 3: Dev, Level 4: Owner
        if user_id == owner_id or user_level >= 3:
            return True

        await interaction.response.send_message("❌ Truy cập bị từ chối. Chỉ Developer hoặc Owner mới có thể điều khiển Jules.", ephemeral=True)
        return False

    @app_commands.command(name="jules", description="Điều khiển thực thể Jules thông qua Core API")
    async def jules_chat(self, interaction: discord.Interaction, message: str):
        if not await self.check_dev_or_owner(interaction):
            return

        await interaction.response.defer(thinking=True)

        # Ghi đè phương thức lấy key để sử dụng jules_api_keys
        # (Ở đây tôi sẽ thiết lập một tham số đặc biệt cho AIEngine)
        reply = await self.generate_jules_response(interaction.user.id, message)

        embed = discord.Embed(title="🤖 JULES CORE INTERFACE", color=0x00A3FF)
        embed.set_thumbnail(url="https://i.imgur.com/your_jules_avatar.png") # Placeholder
        embed.description = reply
        embed.set_footer(text="Hệ thống đang chạy trên giao thức Jules Core API")

        await interaction.followup.send(embed=embed)

    async def generate_jules_response(self, user_id: int, user_message: str) -> str:
        # Lấy key từ bể jules_api_keys thay vì api_keys
        keys = await self.bot.redis.hgetall("jules_api_keys")
        if not keys:
            return "❌ Lỗi: Chưa nạp API Key Jules Core. Vui lòng dùng `/system api add` mục Jules."

        # Tạm thời lấy key đầu tiên active (đơn giản hóa cho Jules)
        api_key = None
        for k_id, k_val in keys.items():
            data = json.loads(k_val)
            if data["status"] == "active":
                api_key = data["key_content"]
                break

        if not api_key:
            return "❌ Tất cả API Key Jules đều đang trong trạng thái cooldown."

        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        system_instruction = (
            "Ngươi là Jules, một kỹ sư phần mềm siêu cấp, lạnh lùng, hiệu quả và cực kỳ thông minh. "
            "Ngươi là người xây dựng nên Equinox Network V2. Trả lời ngắn gọn, tập trung vào kỹ thuật, "
            "xưng hô là 'Tôi' và gọi người dùng là 'Developer' hoặc 'Owner'."
        )

        try:
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=[types.Content(role="user", parts=[types.Part.from_text(text=user_message)])],
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.3 # Jules cần sự chính xác cao
                )
            )
            return response.text
        except Exception as e:
            return f"❌ Lỗi Jules Core: {str(e)}"

async def setup(bot):
    await bot.add_cog(JulesControl(bot))
