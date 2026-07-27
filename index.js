const { Client, GatewayIntentBits, Collection } = require('discord.js');
const fs = require('fs');
const config = require('./config.json');

const client = new Client({
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent
    ]
});

client.commands = new Collection();
client.prefix = config.prefix;

// Utility đọc/ghi Database JSON
client.dbPath = './database.json';
client.readDB = () => JSON.parse(fs.readFileSync(client.dbPath, 'utf8'));
client.writeDB = (data) => fs.writeFileSync(client.dbPath, JSON.stringify(data, null, 2));

client.once('ready', () => {
    console.log(`Bot ${client.user.tag} đã hoạt động!`);
});

// Xử lý Prefix Commands
client.on('messageCreate', async message => {
    if (message.author.bot || !message.content.startsWith(client.prefix)) return;

    const args = message.content.slice(client.prefix.length).trim().split(/ +/);
    const commandName = args.shift().toLowerCase();

    const command = client.commands.get(commandName);
    if (!command) return;

    try {
        await command.execute(message, args, false);
    } catch (error) {
        console.error(error);
    }
});

// Xử lý Slash Commands (Embed 2.0 / Components)
client.on('interactionCreate', async interaction => {
    if (!interaction.isChatInputCommand()) return;

    const command = client.commands.get(interaction.commandName);
    if (!command) return;

    try {
        await command.execute(interaction, [], true);
    } catch (error) {
        console.error(error);
    }
});

client.login(config.token);
