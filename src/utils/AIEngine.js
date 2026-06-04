const { GoogleGenerativeAI } = require('@google/generative-ai');
const dataManager = require('./DataManager');

class AIEngine {
    constructor() {
        // Bộ nhớ đệm (RAM) lưu ngữ cảnh chat để AI nhớ bạn đang nói chuyện gì (Tối đa lưu theo ID user)
        this.chatHistory = new Map(); 
    }

    /**
     * Xử lý câu hỏi và trả về câu trả lời từ AI
     * @param {string} userId - ID của người đang chat
     * @param {string} userMessage - Nội dung tin nhắn
     * @returns {Promise<string>}
     */
    async generateResponse(userId, userMessage) {
        // 1. Chọc vào storage.json để lấy Key hệ thống (Sếp đã nạp qua lệnh /system-keys)
        const geminiKey = await dataManager.get('system.global_keys.gemini');
        
        if (!geminiKey) {
            return "⚠️ Hệ thống Trí Tuệ Nhân Tạo đang tạm ngưng do sếp Silo chưa nạp API Key.\nSếp hãy dùng lệnh `/system-keys` nạp key Google (Gemini) vào nhé!";
        }

        try {
            // Khởi động lõi AI
            const genAI = new GoogleGenerativeAI(geminiKey);
            const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });

            // 2. Mồi thông tin nhân vật (System Prompt) cho phiên chat mới
            if (!this.chatHistory.has(userId)) {
                this.chatHistory.set(userId, [
                    {
                        role: "user",
                        parts: [{ text: "Từ bây giờ, bạn là Luminous, một hệ thống AI đầu não, lạnh lùng, chuyên nghiệp nhưng trung thành. Bạn được tạo ra bởi sếp Silo. Hãy trả lời ngắn gọn, súc tích." }]
                    },
                    {
                        role: "model",
                        parts: [{ text: "Rõ! Tôi là Luminous, hệ thống đầu não tối cao do sếp Silo chế tạo. Tôi đã sẵn sàng nhận lệnh." }]
                    }
                ]);
            }

            const history = this.chatHistory.get(userId);
            
            // 3. Khởi tạo đoạn chat với lịch sử cũ
            const chat = model.startChat({ history: history });

            // Bắn tin nhắn mới lên Google API
            const result = await chat.sendMessage(userMessage);
            const responseText = result.response.text();

            // 4. Lưu lại lịch sử để nói chuyện tiếp
            history.push({ role: "user", parts: [{ text: userMessage }] });
            history.push({ role: "model", parts: [{ text: responseText }] });
            
            // Lõi Auto-Clean Memory: Giữ cho não không bị quá tải (Chỉ nhớ 15 lượt gần nhất)
            if (history.length > 30) {
                history.splice(2, 2); // Bỏ đi bộ nhớ cũ nhất (trừ đoạn mồi nhân vật ở đầu)
            }
            
            return responseText;
        } catch (error) {
            console.error('[AIEngine Error]', error);
            return "❌ Lõi AI đang bị nghẽn mạch hoặc API Key bị từ chối/hết hạn. Sếp vui lòng kiểm tra lại log hệ thống!";
        }
    }
}

module.exports = new AIEngine();
