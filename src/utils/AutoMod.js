const { EmbedBuilder } = require('discord.js');
const dataManager = require('./DataManager');

class AutoMod {
    constructor() {
        // In-Memory Cache lưu lịch sử chat: { "guildId-userId": [timestamp1, timestamp2, ...] }
        this.messageCache = new Map();
        
        // Ngưỡng cấu hình hệ thống (Cứng)
        this.SPAM_LIMIT = 5;         // Tối đa 5 tin nhắn
        this.SPAM_TIME_FRAME = 3000; // Trong vòng 3 giây (3000ms)
    }

    /**
     * Hàm chính: Quét tin nhắn đi qua hệ thống AutoMod
     * @param {Object} message - Object message từ Discord.js
     * @returns {boolean} - Trả về true nếu có vi phạm (đã xử lý phạt), false nếu an toàn
     */
    async processMessage(message) {
        // Bỏ qua bot và tin nhắn trong DM (tin nhắn riêng)
        if (message.author.bot || !message.guild) return false;
        
        // Không trảm Admin hoặc người có quyền quản lý server
        if (message.member.permissions.has('Administrator') || message.member.permissions.has('ManageGuild')) {
            return false;
        }

        const guildId = message.guild.id;
        
        // 1. Kéo cấu hình AutoMod của server hiện tại từ storage.json
        const settings = await dataManager.get(`automod.guild_settings.${guildId}`, {
            anti_spam: true,
            anti_invite: true,
            anti_mention: 4,  // Mặc định cấm ping quá 4 người
            banned_words: []
        });

        let isViolated = false;
        let reason = '';

        // 2. LÕI CHỐNG BOM PING (Anti-Mass Mention)
        if (settings.anti_mention > 0 && message.mentions.users.size > settings.anti_mention) {
            isViolated = true;
            reason = `Mass Mention (Ping quá ${settings.anti_mention} người)`;
        }

        // 3. LÕI CHỐNG KÉO MEM BẰNG LINK INVITE (Anti-Invite)
        const inviteRegex = /(https?:\/\/)?(www\.)?(discord\.(gg|io|me|li)|discordapp\.com\/invite|discord\.com\/invite)\/[a-zA-Z0-9]+/gi;
        if (!isViolated && settings.anti_invite && inviteRegex.test(message.content)) {
            isViolated = true;
            reason = 'Gửi link mời server Discord khác (Anti-Invite)';
        }

        // 4. LÕI KIỂM TRA TỪ CẤM ĐỘNG (Banned Words)
        if (!isViolated && settings.banned_words && settings.banned_words.length > 0) {
            const containsBannedWord = settings.banned_words.some(word => {
                // Dùng Regex \b để tìm đúng từ khóa, không bị dính chữ (vd: cấm "đồ", chữ "đồng" không bị tính)
                const regex = new RegExp(`\\b${word}\\b`, 'gi'); 
                return regex.test(message.content);
            });

            if (containsBannedWord) {
                isViolated = true;
                reason = 'Sử dụng từ ngữ vi phạm bị cấm tại server này';
            }
        }

        // 5. LÕI CHỐNG SPAM (In-Memory Tốc Độ Cao)
        if (!isViolated && settings.anti_spam) {
            const cacheKey = `${guildId}-${message.author.id}`;
            const now = Date.now();
            
            if (!this.messageCache.has(cacheKey)) {
                this.messageCache.set(cacheKey, []);
            }
            
            const userTimestamps = this.messageCache.get(cacheKey);
            userTimestamps.push(now);
            
            // Lọc và chỉ giữ lại những tin nhắn trong 3 giây gần nhất
            const recentMessages = userTimestamps.filter(timestamp => now - timestamp < this.SPAM_TIME_FRAME);
            this.messageCache.set(cacheKey, recentMessages);

            if (recentMessages.length > this.SPAM_LIMIT) {
                isViolated = true;
                reason = 'Spam tin nhắn quá nhanh';
                this.messageCache.delete(cacheKey); // Clear cache để reset bộ đếm cho thanh niên này
            }
        }

        // --- BỘ THỰC THI ÁN PHẠT (EXECUTIONER) ---
        if (isViolated) {
            try {
                // Xóa tang chứng vi phạm
                await message.delete().catch(() => {});
                
                // Úp sọt bằng Embed đỏ chót theo lệnh sếp
                const warnEmbed = new EmbedBuilder()
                    .setColor('#ff3333') // Đỏ báo động
                    .setTitle('🚨 HỆ THỐNG AUTOMOD 🚨')
                    .setDescription(`**Vi phạm:** ${reason}\n**Đối tượng:** ${message.author}`)
                    .setFooter({ text: 'Hành vi của bạn đã bị ghi nhận.' })
                    .setTimestamp();

                const warningMsg = await message.channel.send({ 
                    content: `${message.author}`, // Ping nhẹ bên ngoài để user chú ý
                    embeds: [warnEmbed] 
                });
                
                // Tự hủy thông báo sau 5 giây để tránh rác khung chat
                setTimeout(() => warningMsg.delete().catch(() => {}), 5000);

                // Úp mặt vào tường (Timeout) 1 phút
                await message.member.timeout(60 * 1000, `Luminous AutoMod: ${reason}`).catch(() => {});
                
                return true; // Trả về true để file nhận sự kiện biết đường cắt luồng, không chạy lệnh khác nữa
            } catch (error) {
                console.error(`[AutoMod] Bot thiếu quyền để phạt user ${message.author.tag}:`, error);
            }
        }

        return false; // Dân lương thiện, cho đi qua
    }
}

// Xuất ra 1 thực thể Singleton duy nhất
module.exports = new AutoMod();
