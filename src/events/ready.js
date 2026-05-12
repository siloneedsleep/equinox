const { Events } = require('discord.js');

module.exports = {
    name: Events.ClientReady,
    once: true,
    execute(client) {
        console.log(`✅ Luminous Bot đã sẵn sàng! Đăng nhập dưới tên: ${client.user.tag}`);
    },
};
