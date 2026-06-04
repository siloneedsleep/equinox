const { SlashCommandBuilder, EmbedBuilder } = require('discord.js');

module.exports = {
    // 1. DỮ LIỆU ĐẨY LÊN DISCORD API
    data: new SlashCommandBuilder()
        .setName('help')
        .setDescription('Mở sổ tay hướng dẫn toàn tập các lệnh của Luminous'),

    // 2. LÕI XỬ LÝ LỆNH
    async execute(interaction) {
        await interaction.deferReply({ ephemeral: false });

        // Gom toàn bộ lệnh đang có trong bộ nhớ bot
        const commands = interaction.client.commands;

        // Trích xuất tên lệnh và mô tả để làm thành một danh sách
        const commandList = commands.map(cmd => `**\`/${cmd.data.name}\`** - ${cmd.data.description}`).join('\n\n');

        // Bọc vào Embed cực kỳ sang trọng
        const helpEmbed = new EmbedBuilder()
            .setColor('#2b2d31') // Màu xám tàng hình tệp với nền Discord
            .setAuthor({ 
                name: '📚 BẢNG CHỈ DẪN LỆNH LUMINOUS', 
                iconURL: interaction.client.user.displayAvatarURL() 
            })
            .setDescription(`Xin chào ${interaction.user}! Dưới đây là toàn bộ lệnh hiện tại của hệ thống. Bạn có thể gõ trực tiếp tên lệnh vào khung chat để sử dụng.\n\n${commandList}`)
            .setFooter({ text: 'Luminous V15 - Help Menu' })
            .setTimestamp();

        // Bắn menu ra kênh chat
        await interaction.followUp({ embeds: [helpEmbed] });
    }
};
