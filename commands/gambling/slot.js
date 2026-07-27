const { SlashCommandBuilder } = require('discord.js');

module.exports = {
    name: 'slot',
    description: 'Prism Slots - Quay lăng kính',
    slashData: new SlashCommandBuilder()
        .setName('slot')
        .setDescription('Prism Slots - Quay lăng kính')
        .addIntegerOption(opt => opt.setName('bet').setDescription('Số tiền cược').setRequired(true)),
        
    async execute(context, args, isSlash) {
        const author = isSlash ? context.user : context.author;
        const db = context.client.readDB();
        
        let bet = isSlash ? context.options.getInteger('bet') : parseInt(args[0]);
        
        if (isNaN(bet) || bet <= 0) {
            const msg = '⚠️ Cú pháp: `l!slot <số tiền>` (Tiền cược > 0)';
            return isSlash ? context.reply({ content: msg, flags: 64 }) : context.reply(msg);
        }

        if (!db.users[author.id]) db.users[author.id] = { balance: 0, xp: 0, level: 1, cooldowns: {} };
        
        if (db.users[author.id].balance < bet) {
            const msg = '❌ Bạn không đủ Lux để quay!';
            return isSlash ? context.reply({ content: msg, flags: 64 }) : context.reply(msg);
        }

        const symbols = ['💎', '☀️', '🌟', '🔮', '🕊️'];
        const slot1 = symbols[Math.floor(Math.random() * symbols.length)];
        const slot2 = symbols[Math.floor(Math.random() * symbols.length)];
        const slot3 = symbols[Math.floor(Math.random() * symbols.length)];
        
        let winAmount = 0;
        let resultMsg = '';

        if (slot1 === '☀️' && slot2 === '☀️' && slot3 === '☀️') {
            winAmount = (db.jackpot || 0) + bet;
            db.jackpot = 0;
            resultMsg = `🎉 **NỔ HŨ HÀO QUANG (JACKPOT)!** 🎉\nBạn đã trúng toàn bộ hũ Server: **${winAmount.toLocaleString()} Lux**!`;
        } else if (slot1 === slot2 && slot2 === slot3) {
            winAmount = bet * 5;
            resultMsg = `✨ **TRÚNG LỚN!** Ba biểu tượng trùng nhau.\nBạn thắng **${winAmount.toLocaleString()} Lux ($LX$)**!`;
        } else if (slot1 === slot2 || slot2 === slot3 || slot1 === slot3) {
            winAmount = Math.floor(bet * 1.5);
            resultMsg = `✅ **TRÚNG NHỎ!** Hai biểu tượng trùng nhau.\nBạn thắng **${winAmount.toLocaleString()} Lux ($LX$)**!`;
        } else {
            db.jackpot = (db.jackpot || 0) + Math.floor(bet * 0.05);
            winAmount = -bet;
            resultMsg = `❌ **TRƯỢT RỒI!**\nBạn đã mất **${bet.toLocaleString()} Lux ($LX$)**.`;
        }

        db.users[author.id].balance += winAmount;
        context.client.writeDB(db);

        const msg = `🎰 **PRISM SLOTS** 🎰\n[ ${slot1} | ${slot2} | ${slot3} ]\n${resultMsg}\n💰 Số dư: **${db.users[author.id].balance.toLocaleString()} Lux**`;
        return isSlash ? context.reply(msg) : context.reply(msg);
    }
};
