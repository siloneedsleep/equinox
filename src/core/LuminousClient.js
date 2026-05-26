const { Client, GatewayIntentBits, Collection, Partials } = require('discord.js');

class LuminousClient extends Client {
    constructor() {
        super({
            // Khai báo các quyền (Intents) cần thiết để bot hoạt động hết công suất
            intents: [
                GatewayIntentBits.Guilds,
                GatewayIntentBits.GuildMessages,
                GatewayIntentBits.MessageContent, // Bắt buộc phải có để đọc được prefix l!
                GatewayIntentBits.GuildMembers,
                GatewayIntentBits.GuildVoiceStates // Dành cho tính năng Stay VC sau này
            ],
            // Khai báo Partials để bot xử lý được cả các tin nhắn cũ trước khi bot online
            partials: [
                Partials.Message, 
                Partials.Channel, 
                Partials.User
            ],
        });

        // Khởi tạo các kho chứa dữ liệu trên RAM
        this.commands = new Collection();
        this.prefix = process.env.PREFIX || 'l!';
        this.db = null; // Sẽ được nạp ở tầng Database sau
    }

    async start(token) {
        // Tạm thời log ra để sếp biết luồng đang chạy tới đâu
        console.log('⏳ Đang khởi tạo các mô-đun cốt lõi...');

        // Nạp bộ xử lý tự động (Loader) - File này mình sẽ viết tiếp theo
        const Loader = require('./Loader');
        const loader = new Loader(this);
        
        await loader.loadEvents();
        await loader.loadCommands();

        // Kích hoạt kết nối với Discord API
        await this.login(token);
    }
}

module.exports = LuminousClient;
