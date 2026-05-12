const { Events } = require('discord.js');
const db = require('../database/db');
const { sendEmbed } = require('../utils/embedWrapper');

module.exports = {
    name: Events.MessageCreate,
    async execute(message, client) {
        // Chỉ xử lý tin nhắn từ người dùng, không xử lý bot hoặc tin nhắn ngoài server
        if (message.author.bot || !message.guild) return;

        // Lấy prefix từ Quick.db, nếu không có dùng mặc định trong .env hoặc 'k!'
        const customPrefix = await db.get(`prefix_${message.guild.id}`) || process.env.PREFIX || 'k!';

        // Kiểm tra xem tin nhắn có bắt đầu bằng prefix không
        if (!message.content.startsWith(customPrefix)) return;

        const args = message.content.slice(customPrefix.length).trim().split(/ +/);
        const commandName = args.shift().toLowerCase();

        const command = client.commands.get(commandName);
        if (!command) return;

        // Giả lập một "context" giống Interaction để dùng chung cho hàm Hybrid
        const context = {
            message: message,
            channel: message.channel,
            guild: message.guild,
            user: message.author,
            member: message.member,
            // Hàm reply giả lập luôn bọc Embed
            reply: async (content, type) => await sendEmbed(message, content, type),
            // Giả lập lấy tham số
            options: {
                getString: (index) => args[index] || null,
                getUser: (index) => message.mentions.users.first() || null
            }
        };

        try {
            await command.execute(context, client);
        } catch (error) {
            console.error(error);
            await sendEmbed(message, '❌ Đã xảy ra lỗi khi thực thi lệnh này!', 'error');
        }
    },
};
