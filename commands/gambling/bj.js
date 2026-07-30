// Blackjack Ánh Sáng - Giao diện Embed 2.0 [cite: 76, 77, 212, 221]
const { SlashCommandBuilder, ActionRowBuilder, ButtonBuilder, ButtonStyle, EmbedBuilder, ComponentType } = require('discord.js');

module.exports = {
    name: 'bj',
    description: 'Blackjack Ánh Sáng (21 Điểm)',
    slashData: new SlashCommandBuilder()
        .setName('bj')
        .setDescription('Blackjack Ánh Sáng (21 Điểm)')
        .addIntegerOption(opt => opt.setName('bet').setDescription('Số tiền cược').setRequired(true)),
        
    async execute(context, args, isSlash) {
        const author = isSlash ? context.user : context.author;
        const db = context.client.readDB();
        
        let bet = isSlash ? context.options.getInteger('bet') : parseInt(args[0]);
        if (isNaN(bet) || bet <= 0) return isSlash ? context.reply({ content: '⚠️ Cú pháp: `l!bj <số tiền>`', flags: 64 }) : context.reply('⚠️ Cú pháp: `l!bj <số tiền>`');
        
        if (!db.users[author.id]) db.users[author.id] = { balance: 0, xp: 0, level: 1, cooldowns: {} };
        if (db.users[author.id].balance < bet) return isSlash ? context.reply({ content: '❌ Bạn không đủ Lux!', flags: 64 }) : context.reply('❌ Bạn không đủ Lux!');

        db.users[author.id].balance -= bet;
        context.client.writeDB(db);

        const deck = [];
        const suits = ['♠️', '♥️', '♣️', '♦️'];
        const values = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A'];
        
        for (let suit of suits) {
            for (let value of values) deck.push({ value, suit });
        }
        deck.sort(() => Math.random() - 0.5);

        const drawCard = () => deck.pop();
        const calculateScore = (hand) => {
            let score = 0, aces = 0;
            for (let card of hand) {
                if (['J', 'Q', 'K'].includes(card.value)) score += 10;
                else if (card.value === 'A') { score += 11; aces += 1; }
                else score += parseInt(card.value);
            }
            while (score > 21 && aces > 0) { score -= 10; aces -= 1; }
            return score;
        };

        const formatHand = (hand) => hand.map(c => `**${c.value}**${c.suit}`).join(' | ');

        let playerHand = [drawCard(), drawCard()];
        let dealerHand = [drawCard(), drawCard()];
        let isGameOver = false;

        const generateEmbed = (hideDealer = true) => {
            const pScore = calculateScore(playerHand);
            const dScore = hideDealer ? calculateScore([dealerHand[0]]) : calculateScore(dealerHand);
            const dDisplay = hideDealer ? `${formatHand([dealerHand[0]])} | ❓` : formatHand(dealerHand);
            
            return new EmbedBuilder()
                .setColor('#000000')
                .setTitle('🃏 Blackjack Ánh Sáng')
                .addFields(
                    { name: `Bot Luminous (${hideDealer ? '?' : dScore})`, value: dDisplay },
                    { name: `Người chơi (${pScore})`, value: formatHand(playerHand) },
                    { name: 'Tiền cược', value: `**${bet.toLocaleString()} Lux**` }
                );
        };

        const generateComponents = (disableAll = false, allowDouble = false) => {
            return new ActionRowBuilder().addComponents(
                new ButtonBuilder().setCustomId('bj_hit').setLabel('Rút bài (Hit)').setStyle(ButtonStyle.Success).setDisabled(disableAll),
                new ButtonBuilder().setCustomId('bj_stand').setLabel('Dừng (Stand)').setStyle(ButtonStyle.Danger).setDisabled(disableAll),
                new ButtonBuilder().setCustomId('bj_double').setLabel('Nhân đôi (Double)').setStyle(ButtonStyle.Primary).setDisabled(disableAll || !allowDouble)
            );
        };

        const pScoreInit = calculateScore(playerHand);
        if (pScoreInit === 21) {
            const winAmount = Math.floor(bet * 2.5);
            db.users[author.id].balance += winAmount;
            context.client.writeDB(db);
            const embed = generateEmbed(false).setColor('#FFD700').setDescription(`🎉 **BLACKJACK!** Bạn thắng **${winAmount.toLocaleString()} Lux**!`);
            return isSlash ? context.reply({ embeds: [embed] }) : context.reply({ embeds: [embed] });
        }

        const payload = { embeds: [generateEmbed(true)], components: [generateComponents(false, db.users[author.id].balance >= bet)] };
        const response = await (isSlash ? context.reply({ ...payload, fetchReply: true }) : context.reply(payload));
        const collector = response.createMessageComponentCollector({ componentType: ComponentType.Button, time: 60000 });

        collector.on('collect', async i => {
            if (i.user.id !== author.id) return i.reply({ content: '❌ Không phải ván của bạn!', ephemeral: true });

            if (i.customId === 'bj_double') {
                db.users[author.id].balance -= bet;
                bet *= 2;
                playerHand.push(drawCard());
                i.customId = 'bj_stand'; // Force stand after double down
            } else if (i.customId === 'bj_hit') {
                playerHand.push(drawCard());
            }

            const pScore = calculateScore(playerHand);
            
            if (pScore > 21 || i.customId === 'bj_stand') {
                isGameOver = true;
                collector.stop();
                
                let finalDesc = '';
                let color = '#FF0000';
                
                if (pScore > 21) {
                    finalDesc = `💥 **QUẮC (Bust)!** Bạn mất **${bet.toLocaleString()} Lux**.`;
                    db.jackpot = (db.jackpot || 0) + Math.floor(bet * 0.05);
                } else {
                    let dScore = calculateScore(dealerHand);
                    while (dScore < 17) { dealerHand.push(drawCard()); dScore = calculateScore(dealerHand); }
                    
                    if (dScore > 21 || pScore > dScore) {
                        const winAmount = bet * 2;
                        db.users[author.id].balance += winAmount;
                        color = '#00FF00';
                        finalDesc = `🎉 **THẮNG!** Bạn nhận **${winAmount.toLocaleString()} Lux**.`;
                    } else if (pScore === dScore) {
                        db.users[author.id].balance += bet;
                        color = '#FFFF00';
                        finalDesc = `🤝 **HÒA!** Bạn được hoàn lại **${bet.toLocaleString()} Lux**.`;
                    } else {
                        finalDesc = `❌ **THUA!** Luminous có điểm cao hơn. Mất **${bet.toLocaleString()} Lux**.`;
                        db.jackpot = (db.jackpot || 0) + Math.floor(bet * 0.05);
                    }
                }
                
                context.client.writeDB(db);
                const finalEmbed = generateEmbed(false).setColor(color).setDescription(finalDesc);
                await i.update({ embeds: [finalEmbed], components: [generateComponents(true, false)] });
            } else {
                await i.update({ embeds: [generateEmbed(true)], components: [generateComponents(false, false)] });
            }
        });
    }
};
