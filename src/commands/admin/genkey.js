const { SlashCommandBuilder } = require('discord.js');
const db = require('../../database/db');
const crypto = require('crypto'); // Thư viện có sẵn trong Node.js

module.exports = {
    data: new SlashCommandBuilder()
        .setName('genkey')
        .setDescription('Tạo Key Premium (Chỉ Owner)')
        .addIntegerOption(opt => opt.setName('days').setRequired(true).setDescription('Số ngày Premium'))
        .addIntegerOption(opt => opt.setName('uses').setRequired(true).setDescription('Số lần Key có thể được sử dụng')),

    async execute(ctx, client) {
        if (ctx.user.id !== '914831312295165982') return ctx.reply('⛔ Quyền hạn của bạn không đủ!', 'error');

        const days = ctx.options.getString(0);
        const uses = ctx.options.getString(1);

        if (!days || !uses) return ctx.reply('⚠️ Cú pháp: `l!genkey <ngày> <số_lần>`', 'error');

        // Tạo chuỗi Key ngẫu nhiên (Ví dụ: LUMI-XXXX-XXXX)
        const rawKey = crypto.randomBytes(4).toString('hex').toUpperCase();
        const key = `LUMI-${rawKey}-${days}D`;

        // Lưu thông tin Key vào Database
        await db.set(`key_${key}`, {
            days: parseInt(days),
            maxUses: parseInt(uses),
            currentUses: 0,
            users: [] // Danh sách ID đã dùng key này để tránh 1 người dùng 1 key nhiều lần
        });

        await ctx.reply(
            `✅ **ĐÃ TẠO KEY PREMIUM**\n\n` +
            `🔑 Key: \`${key}\` \n` +
            `📅 Thời hạn: \`${days} ngày\` \n` +
            `👥 Lượt dùng: \`${uses} lần\``, 
            'success'
        );
    }
};
