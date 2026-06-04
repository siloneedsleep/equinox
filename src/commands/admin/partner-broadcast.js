const { SlashCommandBuilder, EmbedBuilder, PermissionFlagsBits, WebhookClient } = require('discord.js');
const dataManager = require('../../utils/DataManager');

module.exports = {
    // 1. DỮ LIỆU ĐẨY LÊN DISCORD API
    data: new SlashCommandBuilder()
        .setName('partner-broadcast')
        .setDescription('Phát sóng tin nhắn đến toàn bộ server đối tác (Chỉ Admin)')
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator) // Khóa chặt, chỉ Admin được xài
        .addStringOption(option => 
            option.setName('message')
                .setDescription('Nội dung thông báo cần phát sóng')
                .setRequired(true))
        .addAttachmentOption(option =>
            option.setName('image')
                .setDescription('Hình ảnh đính kèm (Tùy chọn)')
                .setRequired(false)),

    // 2. LÕI XỬ LÝ PHÁT SÓNG
    async execute(interaction) {
        // Cho ephemeral: false để cả server chiêm ngưỡng uy lực phát sóng của sếp
        await interaction.deferReply({ ephemeral: false });

        const messageContent = interaction.options.getString('message');
        const attachment = interaction.options.getAttachment('image');
        
        // Kéo toàn bộ danh sách đối tác từ database
        const partners = await dataManager.get('partners.verified_guilds', {});
        const guildIds = Object.keys(partners);

        // Check xem có đối tác nào không
        if (guildIds.length === 0) {
            const emptyEmbed = new EmbedBuilder()
                .setColor('#ff3333')
                .setDescription('❌ Hiện tại chưa có server đối tác nào được thiết lập Webhook. Hãy dùng lệnh `/partner-webhook` trước.');
            return interaction.followUp({ embeds: [emptyEmbed] });
        }

        let successCount = 0;
        let failCount = 0;

        // Bọc nội dung sếp gửi thành Embed rực rỡ
        const broadcastEmbed = new EmbedBuilder()
            .setColor('#f1c40f') // Vàng rực hoàng gia
            .setTitle('📢 THÔNG BÁO TỪ LUMINOUS ĐẦU NÃO')
            .setDescription(messageContent)
            .setFooter({ text: `Phát sóng bởi ${interaction.user.tag}`, iconURL: interaction.user.displayAvatarURL() })
            .setTimestamp();

        if (attachment) {
            broadcastEmbed.setImage(attachment.url); // Nối ảnh nếu sếp có up ảnh
        }

        // Bắt đầu cỗ máy lặp qua từng server và rải bom tin nhắn
        for (const guildId of guildIds) {
            const partnerData = partners[guildId];
            if (!partnerData || !partnerData.webhook_url) continue;

            try {
                // Kết nối tới đường ống Webhook của server đó
                const webhookClient = new WebhookClient({ url: partnerData.webhook_url });
                
                // Gửi tin nhắn ẩn danh dưới tên và avatar đã lưu trong storage.json
                await webhookClient.send({
                    username: partnerData.custom_name || 'Luminous Partner',
                    avatarURL: partnerData.custom_avatar || interaction.client.user.displayAvatarURL(),
                    embeds: [broadcastEmbed]
                });
                
                successCount++;
            } catch (error) {
                console.error(`[Broadcast] Lỗi khi gửi tới server ${guildId}:`, error.message);
                failCount++;
                
                // LÕI AUTO-CLEAN: Dọn rác nếu Webhook bên kia đã bị xóa (Mã lỗi 10015 - Unknown Webhook)
                if (error.code === 10015 || error.message.includes('Unknown Webhook')) {
                    await dataManager.delete(`partners.verified_guilds.${guildId}`);
                    console.log(`[Auto-Clean] Đã dọn dẹp Webhook chết của server ${guildId} khỏi storage.json`);
                }
            }
        }

        // Báo cáo nghiệm thu về cho sếp
        const resultEmbed = new EmbedBuilder()
            .setColor(failCount === 0 ? '#00ff00' : '#ffa500') // Xanh lá nếu mượt hết, Cam nếu có lỗi rớt mạng
            .setTitle('✅ Hoàn Tất Phát Sóng Chéo (Cross-Server)')
            .setDescription(`Hệ thống đã rải tin nhắn tới toàn bộ mạng lưới đối tác.`)
            .addFields(
                { name: 'Thành công', value: `🟢 ${successCount} server`, inline: true },
                { name: 'Thất bại (Webhook chết/Lỗi)', value: `🔴 ${failCount} server`, inline: true }
            )
            .setFooter({ text: 'Luminous V15 - Broadcast Engine' })
            .setTimestamp();

        await interaction.followUp({ embeds: [resultEmbed] });
    }
};
