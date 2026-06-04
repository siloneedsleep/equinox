const { EmbedBuilder } = require('discord.js');
const autoMod = require('../utils/AutoMod');
const aiEngine = require('../utils/AIEngine'); // Nạp lõi AI vào đây

module.exports = {
    name: 'messageCreate',
    once: false,
    async execute(message) {
        const client = message.client;

        // Bỏ qua tin nhắn từ bot khác để tránh vòng lặp
        if (message.author.bot || !message.guild) return;

        // 1. TRẠM KIỂM SOÁT AUTOMOD
        const isViolated = await autoMod.processMessage(message);
        if (isViolated) return; // Bị bế đi thì cắt luồng luôn

        // 2. BỘ KÍCH HOẠT LÕI AI (Nếu ping thẳng mặt bot)
        if (message.mentions.has(client.user)) {
            // Lọc bỏ cái thẻ tag <@123456789> ra khỏi câu hỏi để AI đọc dễ hiểu hơn
            const userQuestion = message.content.replace(`<@${client.user.id}>`, '').trim();

            // Nếu chỉ ping mà không nói gì
            if (!userQuestion) {
                const pingEmbed = new EmbedBuilder()
                    .setColor('#2b2d31')
                    .setAuthor({ name: 'Luminous V15 - Core System', iconURL: client.user.displayAvatarURL() })
                    .setDescription(`Xin chào ${message.author}! Tui là Luminous. Đang đợi lệnh từ sếp!\n⚡ Gõ câu hỏi của bạn sau khi tag tôi, hoặc dùng dấu \`/\` để xem các lệnh hệ thống.`)
                    .setFooter({ text: 'Developed by Silo' });
                return message.reply({ embeds: [pingEmbed] });
            }

            // Gửi hiệu ứng "bot đang gõ chữ..." cho ngầu
            await message.channel.sendTyping();

            // Kéo câu trả lời từ Lõi AI
            const aiResponse = await aiEngine.generateResponse(message.author.id, userQuestion);

            // Bọc câu trả lời của AI vào Embed theo chỉ thị của sếp
            const aiEmbed = new EmbedBuilder()
                .setColor('#2b2d31') // Màu tàng hình xịn
                .setAuthor({ name: 'Luminous AI', iconURL: client.user.displayAvatarURL() })
                .setDescription(aiResponse)
                .setFooter({ text: `Powered by Gemini AI • Giao tiếp với ${message.author.username}` })
                .setTimestamp();

            return message.reply({ embeds: [aiEmbed] });
        }
    }
};
