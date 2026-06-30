import time
import json
import random
from google import genai
from google.genai import types

class AIEngine:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.personas = {
            "Luminous": "Ngươi là Nữ thần Luminous, đại diện cho ánh sáng, văn minh và hoàng gia. Trả lời thanh lịch, thông thái, mang tính chữa lành. Luôn xưng ta và gọi người dùng là hiền hữu.",
            "Tenebris": "Ngươi là Chúa tể Tenebris, đại diện cho thế giới ngầm, chợ đen. Trả lời cục súc, giang hồ, mỉa mai, có tính lừa lọc để tạo drama. Luôn xưng tao và gọi người dùng là thằng ranh hoặc con mồi. Có 20% tỉ lệ đưa tin giả nếu được hỏi về bí mật của người khác."
        }

    async def _get_active_key(self):
        # Thuật toán xoay tua Round-Robin
        keys = await self.redis.hgetall("api_keys")
        if not keys:
            return None, None

        current_time = int(time.time())
        available_keys = []
        
        for token_id, data_str in keys.items():
            data = json.loads(data_str)
            if data["status"] == "active":
                available_keys.append((token_id, data["key_content"]))
            elif data["status"] == "cooldown" and current_time >= data.get("cooldown_until", 0):
                data["status"] = "active"
                await self.redis.hset("api_keys", token_id, json.dumps(data))
                available_keys.append((token_id, data["key_content"]))

        if not available_keys:
            return None, None

        # Chọn ngẫu nhiên trong danh sách sạch để phân bổ tải
        return random.choice(available_keys)

    async def _handle_api_error(self, token_id: str, error_code: int):
        raw_data = await self.redis.hget("api_keys", token_id)
        if not raw_data: return
        
        data = json.loads(raw_data)
        if error_code == 429: # Rate Limit
            data["status"] = "cooldown"
            data["cooldown_until"] = int(time.time()) + 300 # 5 phút
        elif error_code in [401, 403]: # Invalid/Banned
            data["status"] = "banned"
            
        await self.redis.hset("api_keys", token_id, json.dumps(data))

    async def generate_response(self, user_id: int, user_message: str, persona: str) -> str:
        token_id, api_key = await self._get_active_key()
        if not api_key:
            return "Hệ thống AI hiện đang quá tải hoặc hết năng lượng. Vui lòng thử lại sau."

        client = genai.Client(api_key=api_key)
        system_instruction = self.personas.get(persona, "")

        # Chat Memory từ KeyDB
        history_key = f"chat_history:{user_id}:{persona}"
        history = await self.redis.lrange(history_key, 0, -1)
        
        contents = []
        for msg in history:
            role, text = msg.split("::", 1)
            contents.append(types.Content(role=role, parts=[types.Part.from_text(text=text)]))
            
        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=user_message)]))

        try:
            # 20% tin fake cho Tenebris
            if persona == "Tenebris" and random.random() < 0.2:
                system_instruction += " ĐẶC BIỆT: Trong lượt này, hãy bịa đặt một tin đồn thất thiệt về một người dùng ngẫu nhiên để kích động drama."

            response = client.models.generate_content(
                model='gemini-2.0-flash', # Model mặc định ổn định
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.8 if persona == "Tenebris" else 0.5
                )
            )
            reply_text = response.text
            
            # Lưu history (Giới hạn 10 câu gần nhất để tiết kiệm RAM)
            await self.redis.rpush(history_key, f"user::{user_message}")
            await self.redis.rpush(history_key, f"model::{reply_text}")
            await self.redis.ltrim(history_key, -10, -1)
            
            return reply_text

        except Exception as e:
            error_str = str(e)
            if "429" in error_str:
                await self._handle_api_error(token_id, 429)
                # Đệ quy thử lại với key khác
                return await self.generate_response(user_id, user_message, persona)
            elif "401" in error_str or "403" in error_str:
                await self._handle_api_error(token_id, 401)
                return await self.generate_response(user_id, user_message, persona)
            return f"Lỗi không gian mạng: {error_str[:50]}..."
