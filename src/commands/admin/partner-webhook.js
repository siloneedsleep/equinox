const { SlashCommandBuilder, EmbedBuilder, PermissionFlagsBits, ChannelType } = require('discord.js');
const dataManager = require('../../utils/DataManager');

module.exports = {
    // 1. DỮ LIỆU ĐẨY LÊN DISCORD API
    data: new SlashCommandBuilder()
        .setName('partner-webhook')
        .setDescription('Thiết lập Webhook phát sóng cho server đối tác (Chỉ Admin)')
        // Cấp quyền cứng: Chỉ Admin server mới thấy và dùng được lệnh này
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator) 
        .addChannelOption(option =>
            option.setName('channel')
                .setDescription('Kênh nhận tin phát sóng chéo')
                .addChannelTypes(ChannelType.GuildText) // Chỉ cho phép chọn kênh Text
                .setRequired(true))
        .addStringOption(option =>
            option.setName('custom_name')
                .setDescription('Tên hiển thị tùy chỉnh cho Webhook (Tùy chọn)')
                .setRequired(false))
        .addStringOption(option =>
            option.setName('custom_avatar')
                .setDescription('Link ảnh đại diện (Avatar URL) cho Webhook (Tùy chọn)')
                .setRequired(false)),

    // 2. LÕI XỬ LÝ LỆNH
    async execute(interaction) {
        // Cú lừa "bot đang suy nghĩ" để kéo dài thời gian xử lý quá 3 giây, tránh lỗi sập lệnh
        await interaction.deferReply({ ephemeral: true });

        // Lấy dữ liệu sếp nhập vào
        const channel = interaction.options.getChannel('channel');
        const customName = interaction.options.getString('custom_name') || 'Luminous | Partner';
        const customAvatar = interaction.options.getString('custom_avatar') || interaction.client.user.displayAvatarURL();
        const guildId = interaction.guild.id;

        try {
            // Chọc vào API Discord để tạo Webhook
            const webhook = await channel.createWebhook({
                name: customName,
                avatar: customAvatar,
                reason: `Được thiết lập bởi ${interaction.user.tag} cho Luminous Partner System`
            });

            // Ghi dữ liệu trực tiếp vào storage.json qua DataManager
            await dataManager.set(`partners.verified_guilds.${guildId}`, {
                webhook_url: webhook.url,
                custom_name: customName,
                custom_avatar: customAvatar,
                added_at: new Date().toISOString(),
                added_by: interaction.user.id
            });

            // Bọc Embed báo thành công rực rỡ theo đúng lệnh sếp
            const successEmbed = new EmbedBuilder()
                .setColor('#00ff00') // Xanh lá cây thành công
                .setTitle('✅ Thiết lập Webhook Thành Công!')
                .setDescription(`Đã kết nối thành công hệ thống phát sóng với kênh ${channel}.\nDữ liệu đã được đồng bộ hóa an toàn vào \`storage.json\`.`)
                .addFields(
                    { name: 'Tên hiển thị', value: customName, inline: true },
                    { name: 'Được thiết lập bởi', value: `<@${interaction.user.id}>`, inline: true }
                )
                .setThumbnail(customAvatar) // Hiện cái ảnh avatar sếp vừa set lên cho trực quan
                .setFooter({ text: 'Luminous V15 - Core System' })
                .setTimestamp();

            await interaction.followUp({ embeds: [successEmbed] });

        } catch (error) {
            console.error('[Webhook Setup Error]', error);
            
            // Bọc Embed báo lỗi nếu bot không có quyền quản lý webhook
            const errorEmbed = new EmbedBuilder()
                .setColor('#ff3333')
                .setTitle('❌ Thiết lập Thất Bại')
                .setDescription(`Luminous bị từ chối quyền tạo Webhook tại kênh ${channel}.\n\n**Khắc phục:** Sếp vui lòng cấp cho bot quyền \`Manage Webhooks\` (Quản lý Webhook) tại kênh này hoặc định dạng URL ảnh không hợp lệ.`)
                .setFooter({ text: 'Luminous System Log' });

            await interaction.followUp({ embeds: [errorEmbed] });
        }
    }
};
