const { SlashCommandBuilder } = require('discord.js');
const LuminousEmbed = require('../../utils/EmbedBuilder');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('ping')
        .setDescription('Kiểm tra độ trễ của hệ thống Luminous'),
    async execute(ctx, args) {
        await ctx.deferReply();

        const ping = ctx.client.ws.ping;
        
        const embed = LuminousEmbed.info(
            '🏓 Pong!',
            `Độ trễ Gateway: **${ping}ms**`
        );

        await ctx.reply({ embeds: [embed] });
    }
};
