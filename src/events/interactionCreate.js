const { EmbedBuilder } = require('discord.js');

module.exports = {
    name: 'interactionCreate',
    once: false,
    async execute(interaction) {
        // Trạm này hiện tại chỉ tập trung xử lý Slash Commands
        if (!interaction.isChatInputCommand()) return;

        // Lôi lệnh tương ứng từ bộ nhớ của Client ra
        const command = interaction.client.commands.get(interaction.commandName);

        if (!command) {
            const notFoundEmbed = new EmbedBuilder()
                .setColor('#ff3333') // Đỏ báo lỗi
                .setDescription('❌ Lệnh này không tồn tại hoặc đã bị sếp Silo gỡ bỏ khỏi hệ thống.')
                .setTimestamp();
            return interaction.reply({ embeds: [notFoundEmbed], ephemeral: true });
        }

        try {
            // Nổ máy thực thi lệnh
            await command.execute(interaction);
        } catch (error) {
            console.error(`[System Error] Lỗi khi chạy lệnh /${interaction.commandName}:`, error);
            
            // Bọc Embed báo lỗi xịn xò nếu code của lệnh bị crash
            const crashEmbed = new EmbedBuilder()
                .setColor('#ff3333')
                .setTitle('⚠️ Cảnh báo Hệ thống (Core Crash)')
                .setDescription('Đã xảy ra lỗi nghiêm trọng trong lõi khi thực thi lệnh này.\nLỗi này đã được ghi nhận. Vui lòng đợi Dev Silo fix bug!')
                .setFooter({ text: 'Luminous V15 - Error Handler' })
                .setTimestamp();

            // Check xem bot đã phản hồi (reply) hoặc đang suy nghĩ (defer) chưa để chống lỗi "Unknown interaction"
            if (interaction.replied || interaction.deferred) {
                await interaction.followUp({ embeds: [crashEmbed], ephemeral: true });
            } else {
                await interaction.reply({ embeds: [crashEmbed], ephemeral: true });
            }
        }
    }
};
