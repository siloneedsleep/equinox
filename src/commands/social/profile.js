const { SlashCommandBuilder, EmbedBuilder } = require('discord.js');
const db = require('../../database/db');
const { rings } = require('../../utils/items');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('profile')
        .setDescription('Xem hồ sơ chi tiết (Soi người khác yêu cầu Premium)'),

    async execute(ctx) {
        const target = ctx.options.getUser(0) || ctx.user;
        
        // Logic check Premium khi soi người khác
        if (target.id !== ctx.user.id) {
            const isPre = await db.get(`premium_${ctx.user.id}`);
            if (!isPre && ctx.user.id !== '914831312295165982') return ctx.reply('⚠️ Soi người khác cần **Premium**!', 'error');
        }

        const money = await db.get(`money_${target.id}`) || 0;
        const partnerId = await db.get(`partner_${target.id}`);
        const ringId = await db.get(`couple_ring_${target.id}`);
        const ringInfo = rings.find(r => r.id === ringId);

        const embed = new EmbedBuilder()
            .setTitle(`🌟 HỒ SƠ: ${target.username} 🌟`)
            .setThumbnail(target.displayAvatarURL())
            .setColor(ringInfo ? ringInfo.color : 0x2b2d31)
            .addFields(
                { name: '💰 Tài sản', value: `💵 \`${money.toLocaleString()}$\``, inline: true },
                { name: '💍 Hôn nhân', value: partnerId ? `<@${partnerId}>` : 'Độc thân', inline: true },
                { name: '✨ Nhẫn cưới', value: ringInfo ? `${ringInfo.emoji} ${ringInfo.name}` : 'Chưa có', inline: true }
            );

        if (target.id === '914831312295165982') embed.setAuthor({ name: '👑 Vua Vibe Coding' });
        await ctx.reply({ embeds: [embed] });
    }
};
