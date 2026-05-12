const { SlashCommandBuilder } = require('discord.js');
const db = require('../../database/db');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('balance')
        .setDescription('Kiểm tra số dư tài khoản của bạn hoặc người khác')
        .addUserOption(opt => opt.setName('user').setDescription('Người bạn muốn xem ví')),

    async execute(ctx, client) {
        // Lấy User từ Slash Option hoặc từ Tag (Prefix)
        const target = ctx.options.getUser(0) || ctx.user;
        
        // Lấy tiền từ DB, nếu chưa từng đào mỏ thì mặc định là 0
        const money = await db.get(`money_${target.id}`) || 0;
        const bank = await db.get(`bank_${target.id}`) || 0;

        // Phản hồi bọc Embed
        await ctx.reply(
            `🏦 **Ngân hàng Luminous**\n\n` +
            `👤 Chủ sở hữu: **${target.username}**\n` +
            `💵 Tiền mặt: \`${money.toLocaleString()}$\` \n` +
            `💳 Gửi ngân hàng: \`${bank.toLocaleString()}$\` \n\n` +
            `✨ Tổng tài sản: \`${(money + bank).toLocaleString()}$\``,
            'info'
        );
    }
};
