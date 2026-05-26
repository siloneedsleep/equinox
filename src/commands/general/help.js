const { SlashCommandBuilder } = require('discord.js');
const LuminousEmbed = require('../../utils/EmbedBuilder');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('help')
        .setDescription('Xem danh sách các lệnh hiện có của bot'),
    async execute(ctx, args) {
        await ctx.deferReply();

        const commands = ctx.client.commands;
        
        const embed = LuminousEmbed.info(
            '📚 Bảng hướng dẫn',
            'Dưới đây là danh sách các lệnh bạn có thể sử dụng trong hệ thống:'
        );

        let commandList = '';
        commands.forEach(cmd => {
            commandList += `**/${cmd.data.name}**: ${cmd.data.description}\n`;
        });

        embed.setDescription(commandList || 'Hiện tại chưa có lệnh nào trong hệ thống.');

        await ctx.reply({ embeds: [embed] });
    }
};
