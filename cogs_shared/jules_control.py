import discord
from discord.ext import commands
from discord import app_commands
import os
import json
import subprocess
from backend.database import EquinoxDatabase

class JulesControl(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = EquinoxDatabase(bot.redis)

    async def check_dev_or_owner(self, interaction: discord.Interaction) -> bool:
        user_id = interaction.user.id
        owner_id = int(os.getenv("OWNER_ID", 0))
        user_level = await self.db.get_user_level(user_id)
        if user_id == owner_id or user_level >= 3:
            return True
        embed = discord.Embed(description="❌ Hệ thống từ chối. Chỉ Kiến trúc sư mới có quyền triệu hồi Jules.", color=0xFF0000)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return False

    @app_commands.command(name="jules", description="Triệu hồi Jules - Kiến trúc sư tối thượng của Equinox Network")
    async def jules_execute(self, interaction: discord.Interaction, prompt: str):
        if not await self.check_dev_or_owner(interaction):
            return

        embed_loading = discord.Embed(
            title="⚙️ JULES CORE IS PROCESSING...",
            description="Đang khởi tạo môi trường sandbox và phân tích mã nguồn...",
            color=0x00A3FF
        )
        await interaction.response.send_message(embed=embed_loading)

        response_text, log_details = await self.jules_brain_process(prompt)

        embed_result = discord.Embed(
            title="✅ JULES EXECUTION COMPLETE",
            description=response_text,
            color=0x2ECC71
        )
        if log_details:
            # Rút ngắn log nếu quá dài
            clean_logs = log_details[:1000] + ("..." if len(log_details) > 1000 else "")
            embed_result.add_field(name="🛠️ Logs", value=f"```bash\n{clean_logs}```", inline=False)

        await interaction.edit_original_response(embed=embed_result)

    async def jules_brain_process(self, prompt: str):
        from config.settings import JULES_TOKEN
        api_key = JULES_TOKEN

        if not api_key:
            return "❌ Không tìm thấy biến môi trường JULES_TOKEN. Vui lòng nạp API Key của Jules.", None

        from google import genai
        from google.genai import types

        try:
            client = genai.Client(api_key=api_key)
            system_instruction = (
                "Ngươi là Jules, AI Kiến trúc sư. Phản hồi JSON: "
                "{'thought': '...', 'action': ['lệnh bash'], 'reply': '...'}"
            )

            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=[types.Content(role="user", parts=[types.Part.from_text(text=prompt)])],
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    temperature=0.2
                )
            )

            data = json.loads(response.text)
            actions = data.get("action", [])
            thought = data.get("thought", "")
            reply = data.get("reply", "Đã thực thi.")

            logs = []
            for cmd in actions:
                try:
                    process = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
                    logs.append(f"$ {cmd}\n{process.stdout}{process.stderr}")
                except subprocess.TimeoutExpired:
                    logs.append(f"$ {cmd}\n[Timeout after 10s]")

            return f"**Tư duy:** {thought}\n\n**Kết quả:** {reply}", "\n".join(logs)
        except Exception as e:
            return f"❌ Lỗi Jules Brain: {str(e)}", None

async def setup(bot):
    await bot.add_cog(JulesControl(bot))
