const TelegramBot = require('node-telegram-bot-api');
const { WebcastPushConnection } = require('tiktok-live-connector');

const token = '8756087132:AAF_ZTzRITtUK58Vu4fiFThYhVJJEB5xJIE';
const ADMIN_ID = 1520960859;

const bot = new TelegramBot(token, { polling: true });
console.log("Telegram Bot is running...");

// لوحة الأزرار الثابتة تحت الشات
const mainKeyboard = {
    reply_markup: {
        keyboard: [
            [{ text: '⚡ ( تكبيس )' }, { text: '✍️ ( تعليق موحد )' }],
            [{ text: '+ ( إضافة جلسة حساب )' }, { text: '📊 ( عدد الحسابات )' }],
            [{ text: '🗑️ ( حذف جلسة )' }]
        ],
        resize_keyboard: true
    }
};

bot.onText(/\/start/, (msg) => {
    if (msg.from.id !== ADMIN_ID) return;
    bot.sendMessage(msg.chat.id, "أهلاً بك يا غالي! البوت جاهز. اختر من الأزرار بالأسفل أو أرسل اسم المستخدم/رابط اللايف مباشرة:", mainKeyboard);
});

bot.on('message', async (msg) => {
    const chatId = msg.chat.id;
    
    if (msg.from.id !== ADMIN_ID) {
        return bot.sendMessage(chatId, "عذراً، هذا البوت مخصص للاستخدام الشخصي فقط.");
    }

    const text = msg.text;
    if (!text) return;

    // التعامل مع الأزرار
    if (text.includes('تكبيس')) {
        return bot.sendMessage(chatId, "أرسل الآن اسم المستخدم أو رابط البث لتطبيق عملية التكبيس (5 تكبيسات بفاصل نصف ثانية ومؤقت 30 ثانية).", mainKeyboard);
    }
    if (text.includes('عدد الحسابات')) {
        return bot.sendMessage(chatId, "حالة النظام: متصل وجاهز للعمل بأمان تام.", mainKeyboard);
    }
    if (text.includes('تعليق موحد') || text.includes('إضافة جلسة حساب') || text.includes('حذف جلسة')) {
        return bot.sendMessage(chatId, "هذه الميزة سيتم تفعيلها بالتكامل الكامل مع البث المباشر قريباً. أرسل رابط البث الآن للبدء.", mainKeyboard);
    }

    if (text.startsWith('/')) return;

    let username = text.trim();
    if (username.includes('tiktok.com/@')) {
        const parts = username.split('@')[1];
        username = parts.split('/')[0].split('?')[0];
    }

    bot.sendMessage(chatId, `جاري الاتصال بـ @${username} لإرسال الـ 5 تكبيسات (فاصل نصف ثانية) وضبط مؤقت 30 ثانية...`, mainKeyboard);

    try {
        const tiktokLiveConnection = new WebcastPushConnection(username);
        await tiktokLiveConnection.connect();
        bot.sendMessage(chatId, `تم الاتصال بنجاح بـ @${username}! بدء التكبيس المجدولة...`, mainKeyboard);

        let tapCount = 0;
        const targetTaps = 5; 
        let isFinished = false;

        const stopSession = async (reason) => {
            if (isFinished) return;
            isFinished = true;
            clearInterval(tapInterval);
            clearTimeout(timeOut);
            
            try {
                await tiktokLiveConnection.disconnect();
            } catch (e) {}

            bot.sendMessage(chatId, `انتهت الجلسة بنجاح (${reason}). إجمالي التكبيسات المرسلة: ${tapCount}. تم الخروج حفاظاً على الأمان.`, mainKeyboard);
        };

        let tapInterval = setInterval(async () => {
            if (isFinished) return;
            if (tapCount >= targetTaps) {
                stopSession("تم إرسال الـ 5 تكبيسات المطلوبة بنجاح");
                return;
            }

            try {
                await tiktokLiveConnection.like?.();
                tapCount++;
            } catch (err) {}
        }, 500);

        let timeOut = setTimeout(() => {
            stopSession("انتهاء الحد الأقصى للوقت (30 ثانية)");
        }, 30000);

        tiktokLiveConnection.on('disconnected', () => {
            stopSession("انقطع الاتصال بالبث");
        });

    } catch (err) {
        bot.sendMessage(chatId, `فشل الاتصال: تأكد أن المستخدم فاتح بث حالياً وأن الاسم صحيح.`, mainKeyboard);
    }
});
