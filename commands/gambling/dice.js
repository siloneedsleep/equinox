const { SlashCommandBuilder } = require('discord.js');

module.exports = {
    name: 'dice',
    description: 'Starlight Dice - Đổ xí ngầu',
    slashData: new SlashCommandBuilder()
        .setName('dice')
        .setDescription('Starlight Dice - Đổ xí ngầu')
        .addStringOption(opt => opt.setName('choice')
            .setDescription('Chọn High, Low hoặc Seven')
            .setRequired(true)
            .addChoices(
                { name: 'High (8-12)', value: 'high' },
                { name: 'Low (2-6)', value: 'low' },
                { name: 'Seven (7)', value: 'seven' }
            ))
        .addIntegerOption(opt => opt.setName('bet').setDescription('Số tiền cược').setRequired(true)),
        
    async execute(context, args, isSlash) {
        const author = isSlash ? context.user : context.author;
        const db = context.client.readDB();
        
        let choice, bet;

        if (isSlash) {
            choice = context.options.getString('choice');
            bet = context.options.getInteger('bet');
        } else {
            choice = args[0]?.toLowerCase();
            bet = parseInt(args[1]);
            
            if (!['high', 'low', 'seven', 'h', 'l', 's'].includes(choice) || isNaN(bet)) {
                return context.reply('⚠️ Cú pháp: `l!dice <high/low/seven> <số tiền>`');
            }
            if (choice === 'h') choice = 'high';
            if (choice === 'l') choice = 'low';
            if (choice === 's') choice = 'seven';
        }

        if (bet <= 0) {
            const msg = '⚠️ Tiền cược > 0!';
            return isSlash ? context.reply({ content: msg, flags: 64 }) : context.reply(msg);
        }
        
        if (!db.users[author.id]) db.users[author.id] = { balance: 0, xp: 0, level: 1, cooldowns: {} };
        
        if (db.users[author.id].balance < bet) {
            const msg = '❌ Bạn không đủ Lux để cược!';
            return isSlash ? context.reply({ content: msg, flags: 64 }) : context.reply(msg);
        }

        const dice1 = Math.floor(Math.random() * 6) + 1;
        const dice2 = Math.floor(Math.random() * 6) + 1;
        const total = dice1 + dice2;
        
        let resultType = total === 7 ? 'seven' : (total > 7 ? 'high' : 'low');
        let winAmount = 0;
        let resultMsg = '';

        if (choice === resultType) {
            winAmount = choice === 'seven' ? bet * 5 : bet;
            db.users[author.id].balance += winAmount;
            resultMsg = `✅ Bạn đoán đúng **${choice.toUpperCase()}**! Thắng **${winAmount.toLocaleString()} Lux ($LX$)**.`;
        } else {
            db.users[author.id].balance -= bet;
            db.jackpot = (db.jackpot || 0) + Math.floor(bet * 0.02);
            resultMsg = `❌ Bạn đoán sai! Mất **${bet.toLocaleString()} Lux ($LX$)**.`;
        }

        context.client.writeDB(db);

        const msg = `🎲 **STARLIGHT DICE** 🎲\nLăng kính đổ ra: **${dice1}** và **${dice2}** (Tổng: **${total}**)\n${resultMsg}\n💰 Số dư: **${db.users[author.id].balance.toLocaleString()} Lux**`;
        return isSlash ? context.reply(msg) : context.reply(msg);
    }
};
