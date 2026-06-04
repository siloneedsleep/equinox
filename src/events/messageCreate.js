const { EmbedBuilder } = require('discord.js');
const autoMod = require('../utils/AutoMod');

module.exports = {
    name: 'messageCreate',
    once: false,
    async execute(message) {
        const client = message.client;

        // 1. Bỏ qua tin nhắn từ bot hoặc hệ thống để tránh vòng lặp (Loop)
        if (message.author.bot || !message.guild) return;

        // 2. TRẠM KIỂM SOÁT AUTOMOD
        // Đưa tin nhắn qua lõi quét. Nếu có vi phạm (true), cắt luồng ngay lập tức!
        const isViolated = await autoMod.processMessage(message);
        if (isViolated) return; 

        // 3. TÍNH NĂNG NHẬN DIỆN PING (Bọc Embed theo lệnh sếp)
        // Nếu user chỉ gõ đúng tag của bot (VD: @Luminous)
        if (message.content === `<@${client.user.id}>`) {
            const pingEmbed = new EmbedBuilder()
                .setColor('#2b2d31') // Màu nền tàng hình cực xịn của Discord
                .setAuthor({ 
                    name: 'Luminous V15 - Core System', 
                    iconURL: client.user.displayAvatarURL() 
                })
                .setDescription(`Xin chào ${message.author}! Tui là Luminous, hệ thống đầu não đang hoạt động ở trạng thái hoàn hảo.\n\n⚡ Vui lòng sử dụng **Slash Commands** (\`/\`) để thao tác các lệnh quản trị và hệ thống.`)
                .setFooter({ text: 'Developed by Silo' })
                .setTimestamp();

            return message.reply({ embeds: [pingEmbed] }).catch(err => console.error(err));
        }

        // 4. KHU VỰC DỰ TRỮ (Dành cho AI Chat hoặc các text commands ẩn sau này)
        // ...
    }
};
