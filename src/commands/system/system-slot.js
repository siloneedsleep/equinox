const { SlashCommandBuilder, EmbedBuilder, PermissionFlagsBits } = require('discord.js');
const dataManager = require('../../utils/DataManager');

module.exports = {
    // 1. DỮ LIỆU ĐẨY LÊN DISCORD API
    data: new SlashCommandBuilder()
        .setName('system-slot')
        .setDescription('Sắc phong ngầm các đặc quyền hệ thống (Chỉ Dev/Owner)')
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator) // Chặn cửa ngoài
        .addStringOption(option =>
            option.setName('action')
                .setDescription('Hành động bạn muốn thực hiện')
                .setRequired(true)
                .addChoices(
                    { name: 'Cấp quyền (Add)', value: 'add' },
                    { name: 'Tước quyền (Remove)', value: 'remove' }
                ))
        .addStringOption(option =>
            option.setName('slot')
                .setDescription('Vị trí đặc quyền trong Luminous')
                .setRequired(true)
                .addChoices(
                    { name: '💻 Nhà phát triển (Dev)', value: 'dev' },
                    { name: '🛡️ Quản trị viên (Admin)', value: 'admin' },
                    { name: '🤝 Khách mời/Nhân viên (Staff)', value: 'staff' }
                ))
        .addUserOption(option =>
            option.setName('target')
                .setDescription('Người được chọn')
                .setRequired(true)),

    // 2. LÕI XỬ LÝ SẮC PHONG
    async execute(interaction) {
        // Lệnh ngầm nên phải ẩn thông báo (chỉ người gõ mới thấy)
        await interaction.deferReply({ ephemeral: true });

        const action = interaction.options.getString('action');
        const slot = interaction.options.getString('slot');
        const targetUser = interaction.options.getUser('target');
        const executorId = interaction.user.id;

        // Kéo danh sách Slot từ storage.json ra
        let slots = await dataManager.get('system.staff_slots', {
            dev: [],
            admin: [],
            staff: []
        });

        // 🔒 LÕI BẢO MẬT KÉP: Chỉ Owner của Server hoặc Dev tối cao mới được cấp quyền DEV
        if (slot === 'dev' && !slots.dev.includes(executorId) && interaction.guild.ownerId !== executorId && executorId !== process.env.OWNER_ID) {
            const denyEmbed = new EmbedBuilder()
                .setColor('#ff3333')
                .setTitle('⛔ TỪ CHỐI TRUY CẬP')
                .setDescription('Bạn không đủ thẩm quyền tối cao để sắc phong chức vụ **Dev** cho người khác!');
            return interaction.followUp({ embeds: [denyEmbed] });
        }

        let success = false;
        let message = '';

        // Xử lý thêm/xóa ID vào mảng
        if (action === 'add') {
            if (!slots[slot].includes(targetUser.id)) {
                slots[slot].push(targetUser.id);
                success = true;
                message = `Đã sắc phong đặc quyền **${slot.toUpperCase()}** cho ${targetUser}.`;
            } else {
                message = `Đối tượng ${targetUser} đã có sẵn quyền **${slot.toUpperCase()}** rồi, không thể cấp thêm.`;
            }
        } else {
            if (slots[slot].includes(targetUser.id)) {
                slots[slot] = slots[slot].filter(id => id !== targetUser.id);
                success = true;
                message = `Đã tước đặc quyền **${slot.toUpperCase()}** của ${targetUser}.`;
            } else {
                message = `Đối tượng ${targetUser} không nắm giữ quyền **${slot.toUpperCase()}** để tước.`;
            }
        }

        // Lưu lại dữ liệu vào tệp nếu có sự thay đổi
        if (success) {
            await dataManager.set('system.staff_slots', slots);
        }

        // Báo cáo kết quả
        const resultEmbed = new EmbedBuilder()
            .setColor(success ? '#f1c40f' : '#808080') // Vàng quyền lực nếu thành công, xám nếu lỗi
            .setTitle('👑 HỆ THỐNG PHÂN QUYỀN NGẦM')
            .setDescription(message)
            .setFooter({ text: `Thực thi bởi ${interaction.user.tag}` })
            .setTimestamp();

        await interaction.followUp({ embeds: [resultEmbed] });
    }
};
