const { SlashCommandBuilder, ActionRowBuilder, ButtonBuilder, ButtonStyle, EmbedBuilder } = require('discord.js');
const db = require('../../database/db');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('marry')
        .setDescription('Cầu hôn người thương với một đám cưới hoành tráng')
        .addUserOption(opt => opt.setName('user').setRequired(true).setDescription('Người bạn muốn trao nhẫn')),

    async execute(ctx, client) {
        const { user: author, guild, channel } = ctx;
        const target = ctx.options.getUser(0);

        // --- Kiểm tra điều kiện ---
        if (target.id === author.id) return ctx.reply('⚠️ Định tự cưới chính mình à? Tỉnh táo lại đi!', 'error');
        if (target.bot) return ctx.reply('⚠️ Bot không biết yêu đâu, đừng cố quá!', 'error');

        const authorPartner = await db.get(`partner_${author.id}`);
        const targetPartner = await db.get(`partner_${target.id}`);

        if (authorPartner) return ctx.reply('⚠️ Bạn đang trong một mối quan hệ, hãy ly hôn trước khi bắt đầu cái mới!', 'error');
        if (targetPartner) return ctx.reply(`⚠️ **${target.username}** đã thuộc về người khác rồi.`, 'error');

        // --- Gửi lời cầu hôn ---
        const proposalEmbed = new EmbedBuilder()
            .setTitle('💖 LỜI CẦU HÔN LÃNG MẠN 💖')
            .setDescription(`**${author.username}** đang quỳ xuống và trao nhẫn cho **${target.username}**!\n\n*"Bạn có đồng ý cùng mình đi đến cuối con đường không?"*`)
            .setColor(0xff69b4)
            .setThumbnail(target.displayAvatarURL())
            .setFooter({ text: 'Bạn có 60 giây để trả lời' });

        const row = new ActionRowBuilder().addComponents(
            new ButtonBuilder().setCustomId('accept').setLabel('Em đồng ý! 💍').setStyle(ButtonStyle.Success),
            new ButtonBuilder().setCustomId('deny').setLabel('Chúng ta chỉ là bạn...').setStyle(ButtonStyle.Danger)
        );

        const msg = await channel.send({ content: `${target}`, embeds: [proposalEmbed], components: [row] });

        // --- Xử lý phản hồi ---
        const filter = i => i.user.id === target.id;
        const collector = msg.createMessageComponentCollector({ filter, time: 60000 });

        collector.on('collect', async i => {
            if (i.customId === 'accept') {
                const date = Math.floor(Date.now() / 1000);
                // Lưu dữ liệu hôn nhân
                await db.set(`partner_${author.id}`, target.id);
                await db.set(`partner_${target.id}`, author.id);
                await db.set(`marry_date_${author.id}`, date);
                await db.set(`marry_date_${target.id}`, date);
                await db.add(`family_exp_${author.id}`, 100); // Tặng 100 điểm Family đầu tiên

                const successEmbed = new EmbedBuilder()
                    .setTitle('🎊 ĐÁM CƯỚI THẾ KỶ 🎊')
                    .setDescription(`Chúc mừng **${author}** và **${target}** đã chính thức kết hôn!\n\n🗓️ **Ngày kỷ niệm:** <t:${date}:D>`)
                    .setImage('https://i.imgur.com/6Ywv9Zp.gif') // Tìm link gif đám cưới anime/cute
                    .setColor(0xffd700);

                await i.update({ embeds: [successEmbed], components: [] });
            } else {
                await i.update({ content: `💔 **${author}**, rất tiếc... lời cầu hôn đã bị từ chối.`, embeds: [], components: [] });
            }
        });
    }
};
