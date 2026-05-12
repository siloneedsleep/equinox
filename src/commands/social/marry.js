const { SlashCommandBuilder, ActionRowBuilder, ButtonBuilder, ButtonStyle, EmbedBuilder } = require('discord.js');
const db = require('../../database/db');
const { rings } = require('../../utils/items');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('marry')
        .setDescription('Cầu hôn người thương (Cần có nhẫn trong túi)'),

    async execute(ctx) {
        const { user: author, channel } = ctx;
        const target = ctx.options.getUser(0);

        if (!target || target.id === author.id || target.bot) return ctx.reply('⚠️ Đối tượng không hợp lệ!', 'error');

        // Check tình trạng hôn nhân
        if (await db.get(`partner_${author.id}`)) return ctx.reply('⚠️ Bạn đã kết hôn rồi!', 'error');
        if (await db.get(`partner_${target.id}`)) return ctx.reply('⚠️ Người ấy đã có chủ!', 'error');

        // Check Nhẫn trong túi
        const userRingId = await db.get(`ring_${author.id}`);
        if (!userRingId) return ctx.reply('⚠️ Bạn chưa mua nhẫn! Hãy dùng `k!shop` và `k!buy`.', 'error');
        const ringInfo = rings.find(r => r.id === userRingId);

        const proposalEmbed = new EmbedBuilder()
            .setTitle('💖 LỜI CẦU HÔN LÃNG MẠN 💖')
            .setDescription(`**${author.username}** đang quỳ xuống, trao chiếc **${ringInfo.emoji} ${ringInfo.name}** cho **${target.username}**!\n\n*"${ringInfo.desc}"*`)
            .setColor(ringInfo.color)
            .setFooter({ text: 'Phản hồi trong 60 giây' });

        const row = new ActionRowBuilder().addComponents(
            new ButtonBuilder().setCustomId('accept').setLabel('Em đồng ý! 💍').setStyle(ButtonStyle.Success),
            new ButtonBuilder().setCustomId('deny').setLabel('Từ chối').setStyle(ButtonStyle.Danger)
        );

        const msg = await channel.send({ content: `${target}`, embeds: [proposalEmbed], components: [row] });
        const collector = msg.createMessageComponentCollector({ filter: i => i.user.id === target.id, time: 60000 });

        collector.on('collect', async i => {
            if (i.customId === 'accept') {
                const date = Math.floor(Date.now() / 1000);
                await db.set(`partner_${author.id}`, target.id);
                await db.set(`partner_${target.id}`, author.id);
                await db.set(`marry_date_${author.id}`, date);
                await db.set(`marry_date_${target.id}`, date);
                await db.set(`couple_ring_${author.id}`, userRingId);
                await db.set(`couple_ring_${target.id}`, userRingId);
                await db.delete(`ring_${author.id}`); // Xóa nhẫn trong túi sau khi dùng

                await i.update({ content: `🎊 **${author}** và **${target}** đã chính thức kết hôn với **${ringInfo.name}**!`, embeds: [], components: [] });
            } else {
                await i.update({ content: '💔 Lời cầu hôn bị từ chối...', embeds: [], components: [] });
            }
        });
    }
};
