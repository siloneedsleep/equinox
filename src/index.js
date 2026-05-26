require('dotenv').config();
const { Client, GatewayIntentBits, Collection, ChannelType } = require('discord.js');
const fs = require('fs');
const path = require('path');
const db = require('./database/db');
const { joinVoiceChannel } = require('@discordjs/voice');

const client = new Client({
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent,
        GatewayIntentBits.GuildMembers,
        GatewayIntentBits.GuildVoiceStates
    ]
});

// Khởi tạo các Collection
client.commands = new Collection();
client.prefixCommands = new Map();
client.ownerId = process.env.OWNER_ID || '914831312295165982';
const PREFIX = process.env.PREFIX || '!';

// --- Handler nạp lệnh ---
const foldersPath = path.join(__dirname, 'commands');
if (fs.existsSync(foldersPath)) {
    const commandFolders = fs.readdirSync(foldersPath);
    for (const folder of commandFolders) {
        const commandsPath = path.join(foldersPath, folder);
        if (!fs.existsSync(commandsPath)) continue;
        
        const commandFiles = fs.readdirSync(commandsPath).filter(file => file.endsWith('.js'));
        for (const file of commandFiles) {
            try {
                const filePath = path.join(commandsPath, file);
                const command = require(filePath);
                
                if ('data' in command && 'execute' in command) {
                    const commandName = command.data.name;
                    client.commands.set(commandName, command);
                    // Register for prefix commands
                    client.prefixCommands.set(commandName, command);
                }
            } catch (error) {
                console.error(`❌ Lỗi khi nạp lệnh ${file}:`, error);
            }
        }
    }
}

console.log(`✅ Đã nạp ${client.commands.size} lệnh`);

// --- Handler nạp Event ---
const eventsPath = path.join(__dirname, 'events');
if (fs.existsSync(eventsPath)) {
    const eventFiles = fs.readdirSync(eventsPath).filter(file => file.endsWith('.js'));
    for (const file of eventFiles) {
        try {
            const filePath = path.join(eventsPath, file);
            const event = require(filePath);
            
            if (event.name && event.execute) {
                if (event.once) {
                    client.once(event.name, (...args) => event.execute(...args, client));
                } else {
                    client.on(event.name, (...args) => event.execute(...args, client));
                }
            }
        } catch (error) {
            console.error(`❌ Lỗi khi nạp event ${file}:`, error);
        }
    }
}

console.log(`✅ Đã nạp events`);

// --- Handler cho Prefix Commands ---
client.on('messageCreate', async (message) => {
    try {
        // Ignore bot messages
        if (message.author.bot) return;

        // Check for prefix
        if (!message.content.startsWith(PREFIX)) return;

        // Extract command name
        const args = message.content.slice(PREFIX.length).split(/\s+/);
        const commandName = args[0]?.toLowerCase();

        if (!commandName) return;

        // Get command
        const command = client.prefixCommands.get(commandName);
        if (!command) return;

        try {
            // Execute hybrid command with message context
            await command.execute(message, client);
        } catch (error) {
            console.error(`❌ Lỗi thực thi lệnh ${commandName}:`, error);
            await message.reply({
                content: '❌ Có lỗi xảy ra khi thực thi lệnh.',
                allowedMentions: { repliedUser: false }
            }).catch(() => null);
        }
    } catch (error) {
        console.error('❌ Lỗi xử lý messageCreate:', error);
    }
});

// --- Logic Tự Động Reconnect Voice 24/7 khi Bot Restart ---
client.once('ready', async () => {
    console.log(`✅ ${client.user.tag} đã sẵn sàng!`);
    console.log(`📊 Kết nối ${client.guilds.cache.size} server`);
    console.log(`🔧 Prefix: ${PREFIX}`);
    
    // Quét tất cả server để xem room nào cần treo 24/7 (với timeout)
    const reconnectPromises = client.guilds.cache.map(async (guild) => {
        try {
            // Timeout cho DB query
            const stayChannelId = await Promise.race([
                db.get(`stay_vc_${guild.id}`),
                new Promise((_, reject) => setTimeout(() => reject(new Error('DB timeout')), 5000))
            ]).catch(() => null);

            if (!stayChannelId) return;

            const channel = guild.channels.cache.get(stayChannelId);
            if (!channel || channel.type !== ChannelType.GuildVoice) {
                console.warn(`⚠️ Channel ${stayChannelId} không tồn tại hoặc không phải voice channel`);
                return;
            }

            try {
                joinVoiceChannel({
                    channelId: channel.id,
                    guildId: guild.id,
                    adapterCreator: guild.voiceAdapterCreator,
                    selfDeaf: true,
                    selfMute: true
                });
                console.log(`🎙️ Đã kết nối lại Voice 24/7 tại server: ${guild.name}`);
            } catch (voiceError) {
                console.error(`❌ Lỗi reconnect voice tại ${guild.name}:`, voiceError.message);
            }
        } catch (error) {
            console.error(`❌ Lỗi xử lý reconnect voice cho guild ${guild.id}:`, error);
        }
    });

    await Promise.all(reconnectPromises).catch(err => {
        console.error('❌ Lỗi trong quá trình reconnect voice:', err);
    });
});

// --- Global Error Handler ---
process.on('unhandledRejection', (reason, promise) => {
    console.error('❌ Unhandled Rejection at:', promise, 'reason:', reason);
});

process.on('uncaughtException', (error) => {
    console.error('❌ Uncaught Exception:', error);
});

// --- Safe Login ---
client.login(process.env.TOKEN).catch(error => {
    console.error('❌ Không thể login:', error);
    process.exit(1);
});

module.exports = client;
