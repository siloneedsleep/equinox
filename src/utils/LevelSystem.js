const dataManager = require('./DataManager');
const { EmbedBuilder } = require('discord.js');

class LevelSystem {
    constructor() {
        // Bộ nhớ đệm (RAM) để lưu danh sách các user đang trong thời gian hồi (Cooldown)
        // Ngăn chặn việc spam chat để cày cấp nhanh
        this.cooldowns = new Set();
    }

    /**
     * Xử lý cộng XP mỗi khi người dùng nhắn tin
     * @param {Object} message - Object tin nhắn từ Discord
     */
    async processXp(message) {
        // Bỏ qua tin nhắn của bot hoặc tin nhắn riêng (DM)
        if (message.author.bot || !message.guild) return;

        const userId = message.author.id;
        const guildId = message.guild.id;
        const cooldownKey = `${guildId}-${userId}`;

        // 1. KIỂM TRA COOLDOWN (Chống gian lận)
        // Nếu user vừa được cộng XP trong vòng 60 giây qua -> Bỏ qua không cộng tiếp
        if (this.cooldowns.has(cooldownKey)) return;

        // Random ngẫu nhiên nhận từ 15 đến 25 XP cho mỗi lần chat
        const xpToAdd = Math.floor(Math.random() * 11) + 15;

        // 2. KÉO DỮ LIỆU TỪ DATABASE
        const userPath = `levels.${guildId}.${userId}`;
        let userData = await dataManager.get(userPath, { xp: 0, level: 1 });

        const oldLevel = userData.level;
        userData.xp += xpToAdd;

        // 3. CÔNG THỨC TÍNH CẤP ĐỘ (RPG Style)
        // Công thức: Level = 0.1 * căn bậc 2 của XP (Ví dụ: XP = 100 -> Level 1, XP = 400 -> Level 2)
        const newLevel = Math.floor(0.1 * Math.sqrt(userData.xp)) + 1;
        userData.level = newLevel;

        // Lưu dữ liệu mới về tệp lưu trữ
        await dataManager.set(userPath, userData);

        // 4. KÍCH HOẠT COOLDOWN
        this.cooldowns.add(cooldownKey);
        setTimeout(() => this.cooldowns.delete(cooldownKey), 60000); // Mở khóa sau 60 giây

        // 5. HIỆU ỨNG CHÚC MỪNG THĂNG CẤP
        if (newLevel > oldLevel) {
            const levelUpEmbed = new EmbedBuilder()
                .setColor('#f1c40f') // Vàng rực rỡ
                .setTitle('🎉 CHÚC MỪNG THĂNG CẤP! 🎉')
                .setDescription(`Đỉnh quá ${message.author} ơi! Bạn đã trò chuyện rất nhiệt tình và thăng cấp lên **Level ${newLevel}**! 🚀`)
                .setThumbnail(message.author.displayAvatarURL())
                .setFooter({ text: 'Luminous V15 - Rank System' });
            
            await message.channel.send({ content: `${message.author}`, embeds: [levelUpEmbed] }).catch(() => {});
        }
    }
}

// Xuất ra 1 instance duy nhất để cắm vào cổng sự kiện
module.exports = new LevelSystem();
