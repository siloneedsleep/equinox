const { SlashCommandBuilder, EmbedBuilder, ActionRowBuilder, StringSelectMenuBuilder } = require('discord.js');

module.exports = {
    name: 'help',
    description: 'Hiển thị danh mục hệ thống Luminous',
    slashData: new SlashCommandBuilder()
        .setName('help')
        .setDescription('Hiển thị danh mục hệ thống Luminous'),
    
    async execute(context, args, isSlash) {
        const embed = new EmbedBuilder()
            .setColor('#FFD700')
            .setTitle('🌟 Luminous Bot - Bảng Điều Khiển')
            .setDescription('Vui lòng chọn một danh mục từ lăng kính bên dưới để xem chi tiết các lệnh.');

        const row = new ActionRowBuilder()
            .addComponents(
                new StringSelectMenuBuilder()
                    .setCustomId('help_menu')
                    .setPlaceholder('Chọn danh mục lệnh Luminous...')
                    .addOptions([
                        { label: '🌾 Cày Tiền (Income)', description: 'Các lệnh thu thập Lux', value: 'income' },
                        { label: '🎲 Cờ Bạc (Gambling)', description: 'Các lệnh giải trí, cá cược', value: 'gambling' },
                        { label: '👤 Hệ Thống (System)', description: 'Thông tin hồ sơ, giao dịch', value: 'system' },
                        { label: '👑 Admin (Owner Only)', description: 'Lệnh quản trị hệ thống', value: 'admin' }
                    ]),
            );

        const payload = { embeds: [embed], components: [row] };
        return isSlash ? context.reply(payload) : context.reply(payload);
    }
};
