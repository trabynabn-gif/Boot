const TelegramBot = require('node-telegram-bot-api');
const { WebcastPushConnection } = require('tiktok-live-connector');

const token = process.env.TELEGRAM_BOT_TOKEN;
if (!token) {
    console.error("Error: TELEGRAM_BOT_TOKEN is missing!");
    process.exit(1);
}

const bot = new TelegramBot(token, { polling: true });
console.log("Telegram Bot is running...");

bot.onText(/\/start/, (msg) => {
    bot.sendMessage(msg.chat.id, "أهلاً بك! أرسل رابط اللايف أو اسم المستخدم لبدء التكبيس.");
});

bot.on('message', async (msg) => {
    const chatId = msg.chat.id;
    const text = msg.text;
    if (!text || text.startsWith('/')) return;

    let username = text.trim();
    if (username.includes('tiktok.com/@')) {
        const parts = username.split('@')[1];
        username = parts.split('/')[0].split('?')[0];
    }

    bot.sendMessage(chatId, `جاري الاتصال بـ @${username} وبدء التكبيس...`);

    try {
        const tiktokLiveConnection = new WebcastPushConnection(username);
        await tiktokLiveConnection.connect();
        bot.sendMessage(chatId, `تم الاتصال بنجاح بـ @${username}! جارٍ إرسال التفاعلات...`);

        let tapInterval = setInterval(async () => {
            try {
                await tiktokLiveConnection.like?.();
            } catch (err) {}
        }, 1000);

        tiktokLiveConnection.on('disconnected', () => {
            clearInterval(tapInterval);
            bot.sendMessage(chatId, `انتهى بث @${username}.`);
        });

    } catch (err) {
        bot.sendMessage(chatId, `فشل الاتصال: تأكد أن المستخدم فاتح بث حالياً.`);
    }
});
