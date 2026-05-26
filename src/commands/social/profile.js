const { SlashCommandBuilder, EmbedBuilder } = require('discord.js');
const db = require('../../database/db');
const { sendEmbed } = require('../../utils/embedWrapper');
const { rings } = require('../../utils/items');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('profile')
        .setDescription('Xem ví tiền, ngân hàng và tình trạng hôn nhân')
        .addUserOption(option =>
            option
                .setName('user')
                .setDescription('Xem profile người khác (cần Premium)')
                .setRequired(false)
        ),

    async execute(ctx) {
        try {
            // Optimize: Defer reply để tránh timeout khi query DB
            if (!ctx.deferred) {
                await ctx.deferReply({ ephemeral: false });
            }

            const target = ctx.options.getUser('user') || ctx.user;
            
            // Check Premium khi soi người khác
            if (target.id !== ctx.user.id) {
                const isPre = await Promise.race([
                    db.get(`premium_${ctx.user.id}`),
                    new Promise((_, reject) => setTimeout(() => reject(new Error('DB timeout')), 5000))
                ]).catch(() => false);

                const isOwner = ctx.user.id === process.env.OWNER_ID || ctx.user.id === '914831312295165982';
                
                if (!isPre && !isOwner) {
                    return await sendEmbed(ctx, '⚠️ Soi ví người khác cần có **Premium**!', 'error');
                }
            }

            // --- Lấy toàn bộ dữ liệu tài chính với timeout ---
            const [cash, bank, partnerId, ringId, isPremium] = await Promise.all([
                Promise.race([db.get(`money_${target.id}`), new Promise((_, r) => setTimeout(() => r(0), 3000))]).catch(() => 0),
                Promise.race([db.get(`bank_${target.id}`), new Promise((_, r) => setTimeout(() => r(0), 3000))]).catch(() => 0),
                Promise.race([db.get(`partner_${target.id}`), new Promise((_, r) => setTimeout(() => r(null), 3000))]).catch(() => null),
                Promise.race([db.get(`couple_ring_${target.id}`), new Promise((_, r) => setTimeout(() => r(null), 3000))]).catch(() => null),
                Promise.race([db.get(`premium_${target.id}`), new Promise((_, r) => setTimeout(() => r(false), 3000))]).catch(() => false)
            ]);

            const total = (cash || 0) + (bank || 0);
            const ringInfo = rings.find(r => r.id === ringId);

            const embed = new EmbedBuilder()
                .setTitle(`🌟 HỒ SƠ: ${target.username.toUpperCase()} 🌟`)
                .setThumbnail(target.displayAvatarURL({ dynamic: true }))
                .setColor(ringInfo ? ringInfo.color : 0x2b2d31)
                .addFields(
                    { 
                        name: '💰 TÀI CHÍNH', 
                        value: `💵 Ví: \`${(cash || 0).toLocaleString()}$\`\n🏦 Ngân hàng: \`${(bank || 0).toLocaleString()}$\`\n📊 Tổng: \`${total.toLocaleString()}$\``, 
                        inline: false 
                    },
                    { 
                        name: '💍 HÔN NHÂN', 
                        value: partnerId ? `👤 Bạn đời: <@${partnerId}>\n✨ Nhẫn: ${ringInfo ? `${ringInfo.emoji} ${ringInfo.name}` : 'Không có'}` : '🔓 Chủ nghĩa độc thân', 
                        inline: true 
                    }
                )
                .setFooter({ text: `Luminous Economy • 2026` })
                .setTimestamp();

            // Icon đặc biệt cho Owner hoặc Premium
            const isOwner = target.id === process.env.OWNER_ID || target.id === '914831312295165982';
            if (isOwner) {
                embed.setAuthor({ name: '👑 Silo - Owner', iconURL: target.displayAvatarURL() });
            } else if (isPremium) {
                embed.setAuthor({ name: '💎 Hội Viên Premium', iconURL: target.displayAvatarURL() });
            }

            await ctx.editReply({ embeds: [embed] });

        } catch (error) {
            console.error('❌ Lỗi trong lệnh profile:', error);
            await sendEmbed(ctx, '❌ Không thể lấy thông tin profile. Vui lòng thử lại sau.', 'error').catch(() => null);
        }
    }
};
