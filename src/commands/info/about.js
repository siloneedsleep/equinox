const { SlashCommandBuilder } = require('discord.js');
const LuminousEmbed = require('../../utils/EmbedBuilder');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('about')
        .setDescription('Xem thông tin chi tiết về hệ thống bot'),
    async execute(ctx, args) {
        await ctx.deferReply();

        const ping = ctx.client.ws.ping;
        const serverCount = ctx.client.guilds.cache.size;

        const embed = LuminousEmbed.info(
            '🤖 Thông Tin Hệ Thống Luminous',
            'Luminous Engine v15 là một hệ thống bot Discord đa năng, tích hợp kinh tế, giải trí và AI.'
        )
        .addFields(
            { name: '👑 Trưởng dự án (Project Lead)', value: 'Silo (`<@914831312295165982>`)', inline: false },
            { name: '✨ Nền tảng', value: 'JavaScript (discord.js v14)', inline: true },
            { name: '🏓 Độ trễ', value: `**${ping}ms**`, inline: true },
            { name: '🌍 Phủ sóng', value: `**${serverCount}** máy chủ`, inline: true }
        );

        await ctx.reply({ embeds: [embed] });
    }
};
