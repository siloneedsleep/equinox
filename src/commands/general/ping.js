const { SlashCommandBuilder, EmbedBuilder } = require('discord.js');

module.exports = {
    // 1. DỮ LIỆU ĐẨY LÊN DISCORD API
    data: new SlashCommandBuilder()
        .setName('ping')
        .setDescription('Kiểm tra độ trễ mạng và trạng thái cốt lõi của Luminous'),

    // 2. LÕI XỬ LÝ LỆNH
    async execute(interaction) {
        // Hoãn phản hồi để bot có thời gian tính toán độ trễ (hiển thị công khai cho mọi người xem)
        const sent = await interaction.deferReply({ fetchReply: true, ephemeral: false });

        // Tính toán độ trễ phản hồi (Roundtrip) và độ trễ đường truyền API (Websocket)
        const roundtripLatency = sent.createdTimestamp - interaction.createdTimestamp;
        const websocketLatency = interaction.client.ws.ping;

        // Phân loại màu sắc Embed theo tốc độ mạng
        let pingColor = '#00ff00'; // Xanh lá: Mạng ngon (< 150ms)
        if (roundtripLatency > 500) pingColor = '#ff3333'; // Đỏ: Mạng lag (> 500ms)
        else if (roundtripLatency > 150) pingColor = '#f1c40f'; // Vàng: Hơi delay (150ms - 500ms)

        // Bọc thông số vào Embed chuẩn form quân đội
        const pingEmbed = new EmbedBuilder()
            .setColor(pingColor)
            .setTitle('🏓 PONG! Báo cáo Trạng thái Hệ thống')
            .setDescription('Đường truyền tín hiệu từ Luminous Core đến Discord API:')
            .addFields(
                { name: '📡 Độ trễ Phản hồi (Roundtrip)', value: `\`${roundtripLatency}ms\``, inline: true },
                { name: '⚡ Độ trễ API (Websocket)', value: `\`${websocketLatency}ms\``, inline: true },
                { name: '🤖 Uptime (Thời gian chạy)', value: `<t:${Math.floor(interaction.client.readyTimestamp / 1000)}:R>`, inline: false }
            )
            .setThumbnail(interaction.client.user.displayAvatarURL())
            .setFooter({ text: 'Luminous V15 - Network Monitor' })
            .setTimestamp();

        // Bắn kết quả lên kênh chat
        await interaction.followUp({ embeds: [pingEmbed] });
    }
};
