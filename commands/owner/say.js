const { SlashCommandBuilder } = require('discord.js');
const config = require('../../config.json');

module.exports = {
    name: 'say',
    description: 'Điều khiển bot phát ngôn (Chỉ Owner)',
    slashData: new SlashCommandBuilder()
        .setName('say')
        .setDescription('Điều khiển bot phát ngôn (Chỉ Owner)')
        .addChannelOption(opt => opt.setName('channel').setDescription('Kênh mục tiêu').setRequired(true))
        .addStringOption(opt => opt.setName('message').setDescription('Nội dung truyền tải').setRequired(true)),
    
    async execute(context, args, isSlash) {
        const authorId = isSlash ? context.user.id : context.author.id;
        
        if (!config.ownerIds.includes(authorId)) {
            const errMsg = '❌ Lệnh này chỉ dành cho Bot Owner!';
            return isSlash ? context.reply({ content: errMsg, flags: 64 }) : context.reply(errMsg);
        }

        let targetChannel, messageContent;

        if (isSlash) {
            targetChannel = context.options.getChannel('channel');
            messageContent = context.options.getString('message');
            
            await targetChannel.send(messageContent);
            return context.reply({ content: '✅ Đã truyền tải thông điệp thành công!', flags: 64 });
        } else {
            const channelMention = args[0];
            if (!channelMention || !channelMention.startsWith('<#') || !channelMention.endsWith('>')) {
                return context.reply('⚠️ Cú pháp: `l!say <#channel> <nội dung>`');
            }
            
            const channelId = channelMention.slice(2, -1);
            targetChannel = context.client.channels.cache.get(channelId);
            messageContent = args.slice(1).join(' ');
            
            if (!targetChannel) return context.reply('❌ Không tìm thấy Thánh địa (Kênh) này!');
            if (!messageContent) return context.reply('⚠️ Lăng kính trống! Vui lòng nhập nội dung.');

            await targetChannel.send(messageContent);
            return context.message.delete().catch(() => {});
        }
    }
};
