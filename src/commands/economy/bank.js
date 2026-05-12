const { SlashCommandBuilder } = require('discord.js');
const db = require('../../database/db');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('bank')
        .setDescription('Quản lý tiền trong ngân hàng')
        .addStringOption(opt => opt.setName('action').setRequired(true).addChoices(
            { name: 'Gửi tiền (dep)', value: 'dep' },
            { name: 'Rút tiền (with)', value: 'with' }
        ))
        .addIntegerOption(opt => opt.setName('amount').setRequired(true).setDescription('Số tiền (nhập -1 để chọn tất cả)')),

    async execute(ctx) {
        const action = ctx.options.getString(0);
        let amount = ctx.options.getInteger(1);
        
        const cash = await db.get(`money_${ctx.user.id}`) || 0;
        const bank = await db.get(`bank_${ctx.user.id}`) || 0;

        if (action === 'dep') {
            if (amount === -1) amount = cash;
            if (amount <= 0 || cash < amount) return ctx.reply('❌ Số tiền gửi không hợp lệ!', 'error');

            await db.sub(`money_${ctx.user.id}`, amount);
            await db.add(`bank_${ctx.user.id}`, amount);
            await ctx.reply(`🏦 Đã gửi \`${amount.toLocaleString()}$\` vào ngân hàng!`, 'success');
        } else {
            if (amount === -1) amount = bank;
            if (amount <= 0 || bank < amount) return ctx.reply('❌ Số tiền rút không hợp lệ!', 'error');

            await db.sub(`bank_${ctx.user.id}`, amount);
            await db.add(`money_${ctx.user.id}`, amount);
            await ctx.reply(`🏦 Đã rút \`${amount.toLocaleString()}$\` về ví!`, 'success');
        }
    }
};
