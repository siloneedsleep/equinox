const { SlashCommandBuilder, EmbedBuilder, PermissionFlagsBits } = require('discord.js');
const dataManager = require('../../utils/DataManager');

module.exports = {
    // 1. DỮ LIỆU ĐẨY LÊN DISCORD API
    data: new SlashCommandBuilder()
        .setName('system-keys')
        .setDescription('Quản lý và nạp API Key cho hệ thống AI (Chỉ Dev/Owner)')
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator) // Khóa vòng ngoài
        .addStringOption(option =>
            option.setName('platform')
                .setDescription('Chọn nền tảng AI bạn muốn nạp Key')
                .setRequired(true)
                .addChoices(
                    { name: '🟢 OpenAI (ChatGPT)', value: 'openai' },
                    { name: '🔵 Google (Gemini)', value: 'gemini' },
                    { name: '🟣 Anthropic (Claude)', value: 'anthropic' }
                ))
        .addStringOption(option =>
            option.setName('key')
                .setDescription('Dán API Key vào đây (Bảo mật tuyệt đối, không ai thấy)')
                .setRequired(true)),

    // 2. LÕI XỬ LÝ LỆNH
    async execute(interaction) {
        // LỚP BẢO MẬT 1: Ẩn 100% nội dung phản hồi, chỉ người gõ mới thấy
        await interaction.deferReply({ ephemeral: true });

        const platform = interaction.options.getString('platform');
        const apiKey = interaction.options.getString('key').trim();
        const executorId = interaction.user.id;

        // Kéo danh sách Slot Dev ra để kiểm duyệt
        const devSlots = await dataManager.get('system.staff_slots.dev', []);

        // LỚP BẢO MẬT 2: Chặn đứng những kẻ mạo danh Admin nhưng không phải Dev/Owner thực sự
        if (!devSlots.includes(executorId) && interaction.guild.ownerId !== executorId && executorId !== process.env.OWNER_ID) {
            const denyEmbed = new EmbedBuilder()
                .setColor('#ff3333')
                .setTitle('⛔ TỪ CHỐI TRUY CẬP')
                .setDescription('Bạn có thể là Admin server này, nhưng bạn **không phải là Dev** của Luminous.\nLệnh này can thiệp vào tài sản lõi (API Key). Vui lòng dừng lại!');
            return interaction.followUp({ embeds: [denyEmbed] });
        }

        // Vượt qua kiểm duyệt -> Ghi Key thẳng vào database storage.json
        await dataManager.set(`system.global_keys.${platform}`, apiKey);

        // LỚP BẢO MẬT 3: Làm mờ (Masking) đoạn giữa của API Key để che mắt rò rỉ
        // Ví dụ: sk-proj-1234567890 -> sk-proj...7890
        const maskedKey = apiKey.length > 15 
            ? `${apiKey.substring(0, 7)}...${apiKey.slice(-5)}` 
            : '********';

        // Báo cáo nạp thành công
        const successEmbed = new EmbedBuilder()
            .setColor('#00ff00')
            .setTitle('🔐 NẠP API KEY THÀNH CÔNG')
            .setDescription(`Hệ thống đã mã hóa và đồng bộ Key cho nền tảng **${platform.toUpperCase()}** vào \`storage.json\`.`)
            .addFields(
                { name: 'Nền tảng', value: platform, inline: true },
                { name: 'Mã Key', value: `\`${maskedKey}\``, inline: true }
            )
            .setFooter({ text: 'Luminous V15 - Core Vault' })
            .setTimestamp();

        await interaction.followUp({ embeds: [successEmbed] });
    }
};
