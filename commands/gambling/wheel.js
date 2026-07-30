// Wheel of Light [cite: 78, 79, 80]
const { SlashCommandBuilder } = require('discord.js');

module.exports = {
    name: 'wheel',
    description: 'Wheel of Light - Vòng quay ánh sáng',
    slashData: new SlashCommandBuilder()
        .setName('wheel')
        .setDescription('Wheel of Light - Vòng quay ánh sáng')
        .addStringOption(opt => opt.setName('color')
            .setDescription('Chọn màu cược')
            .setRequired(true)
            .addChoices(
                { name: 'Trắng (White) - x2', value: 'white' },
                { name: 'Xanh (Blue) - x3', value: 'blue' },
                { name: 'Vàng (Gold) - x5', value: 'gold' },
                { name: 'Tím (Purple) - x15', value: 'purple' },
                { name: 'Kim Cương (Diamond) - x100', value: 'diamond' }
            ))
        .addIntegerOption(opt => opt.setName('bet').setDescription('Số tiền cược').setRequired(true)),
        
    async execute(context, args, isSlash) {
        const author = isSlash ? context.user : context.author;
        const db = context.client.readDB();
        
        let color, bet;

        if (isSlash) {
            color = context.options.getString('color');
            bet = context.options.getInteger('bet');
        } else {
            color = args[0]?.toLowerCase();
            bet = parseInt(args[1]);
            
            if (!['white', 'blue', 'gold', 'purple', 'diamond'].includes(color) || isNaN(bet)) {
                return context.reply('⚠️ Cú pháp: `l!wheel <white/blue/gold/purple/diamond> <số tiền>`');
            }
        }

        if (bet <= 0) return isSlash ? context.reply({ content: '⚠️ Tiền cược > 0!', flags: 64 }) : context.reply('⚠️ Tiền cược > 0!');
        if (!db.users[author.id]) db.users[author.id] = { balance: 0, xp: 0, level: 1, cooldowns: {} };
        if (db.users[author.id].balance < bet) return isSlash ? context.reply({ content: '❌ Bạn không đủ Lux!', flags: 64 }) : context.reply('❌ Bạn không đủ Lux!');

        db.users[author.id].balance -= bet;

        const rand = Math.random();
        let resultColor = '';
        let multiplier = 0;
        let emoji = '';

        if (rand < 0.001) { resultColor = 'diamond'; multiplier = 100; emoji = '💎'; }       // 0.1% [cite: 79]
        else if (rand < 0.05) { resultColor = 'purple'; multiplier = 15; emoji = '🟣'; }    // 4.9%
        else if (rand < 0.20) { resultColor = 'gold'; multiplier = 5; emoji = '🟡'; }       // 15%
        else if (rand < 0.50) { resultColor = 'blue'; multiplier = 3; emoji = '🔵'; }       // 30%
        else { resultColor = 'white'; multiplier = 2; emoji = '⚪'; }                       // 50%

        let resultMsg = `Vòng quay dừng lại ở ô **${emoji} ${resultColor.toUpperCase()}**!\n\n`;

        if (color === resultColor) {
            const winAmount = bet * multiplier;
            db.users[author.id].balance += winAmount;
            resultMsg += `✅ **THẮNG LỚN!** Bạn nhận được **${winAmount.toLocaleString()} Lux** (x${multiplier})!`;
        } else {
            db.jackpot = (db.jackpot || 0) + Math.floor(bet * 0.05);
            resultMsg += `❌ **TRƯỢT RỒI!** Bạn đã mất **${bet.toLocaleString()} Lux**.`;
        }

        context.client.writeDB(db);

        const msg = `☸️ **WHEEL OF LIGHT** ☸️\n${resultMsg}\n💰 Số dư: **${db.users[author.id].balance.toLocaleString()} Lux**`;
        return isSlash ? context.reply(msg) : context.reply(msg);
    }
};
