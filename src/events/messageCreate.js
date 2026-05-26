const Context = require('../core/Context');
const chalk = require('chalk');

module.exports = {
    name: 'messageCreate',
    once: false,
    async execute(message, client) {
        if (message.author.bot) return;

        const prefix = client.prefix;
        
        if (!message.content.startsWith(prefix)) return;

        // 1. Cắt chuỗi để lấy args trước
        const args = message.content.slice(prefix.length).trim().split(/ +/);
        
        // 2. Khai báo biến commandName bằng "let" để có thể thay đổi giá trị ở dưới
        let commandName = args.shift().toLowerCase();

        // 3. Xử lý tất cả các phím tắt (Alias) tại đây
        if (commandName === 'ld') commandName = 'lockdown';
        if (commandName === 'sp') commandName = 'setpresence';
        if (commandName === 'sl') commandName = 'setlevel';

        // 4. Lấy lệnh từ bộ nạp commands
        const command = client.commands.get(commandName);

        if (!command) return;

        const ctx = new Context(message, client);

        try {
            await command.execute(ctx, args);
        } catch (error) {
            console.error(chalk.red(`[COMMAND ERROR] Lỗi khi thực thi lệnh ${commandName} (Prefix):`), error);
            
            const errorMsg = '❌ Đã xảy ra lỗi hệ thống khi thực thi lệnh này. Sếp vui lòng kiểm tra lại log!';
            await ctx.reply(errorMsg).catch(() => null);
        }
    }
};
