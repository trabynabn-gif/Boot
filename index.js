const TelegramBot = require('node-telegram-bot-api');
const { WebcastPushConnection } = require('tiktok-live-connector');

const token = '8756087132:AAF_ZTzRITtUK58Vu4fiFThYhVJJEB5xJIE';
const ADMIN_ID = 1520960859;

const bot = new TelegramBot(token, { polling: true });
console.log("Telegram Bot is running with full features and active buttons...");

// قاعدة بيانات محلية لإدارة الجلسات والحسابات والتعليق الموحد
let activeSessions = [];
let customCommentText = "منور البث 🌹";
let botMode = "idle"; // idle, waiting_for_session, waiting_for_comment

// الواجهة الرئيسية بالأزرار الثابتة التي طلبتها
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
    bot.sendMessage(msg.chat.id, "أهلاً بك يا غالي في لوحة التحكم الذكية لإدارة بوت التيك توك. اختر من الأزرار بالأسفل:", mainKeyboard);
});

bot.on('message', async (msg) => {
    const chatId = msg.chat.id;
    
    if (msg.from.id !== ADMIN_ID) {
        return bot.sendMessage(chatId, "عذراً، هذا البوت مخصص للاستخدام الشخصي فقط.");
    }

    const text = msg.text;
    if (!text) return;

    // معالجة الأزرار الرئيسية
    if (text.includes('إضافة جلسة حساب')) {
        botMode = "waiting_for_session";
        return bot.sendMessage(chatId, "➕ أرسل الآن اسم المستخدم أو رابط البث المباشر (اليوزر) لإضافته كجلسة جديدة:", mainKeyboard);
    }
    
    if (text.includes('عدد الحسابات')) {
        let sessionList = activeSessions.length > 0 ? activeSessions.map(s => `- @${s}`).join('\n') : "لا توجد جلسات مسجلة حالياً.";
        return bot.sendMessage(chatId, `📊 إحصائيات الجلسات:\n- عدد الحسابات المسجلة: ${activeSessions.length}\n\nقائمة الحسابات:\n${sessionList}`, mainKeyboard);
    }

    if (text.includes('حذف جلسة')) {
        activeSessions = [];
        return bot.sendMessage(chatId, "🗑️ تم مسح وحذف جميع الجلسات النشطة بنجاح.", mainKeyboard);
    }

    if (text.includes('تعليق موحد')) {
        botMode = "waiting_for_comment";
        return bot.sendMessage(chatId, `✍️ أرسل النص الجديد للتعليق الموحد.\n(النص الحالي: "${customCommentText}")`, mainKeyboard);
    }

    if (text.includes('تكبيس')) {
        if (activeSessions.length === 0) {
            return bot.sendMessage(chatId, "⚠️ لا توجد أي جلسة حساب مسجلة! اضغط على (+ إضافة جلسة حساب) أولاً أو أرسل اسم البث مباشرة.", mainKeyboard);
        }
        
        bot.sendMessage(chatId, `⚡ جاري بدء عملية التكبيس لجميع الجلسات المسجلة (${activeSessions.length} حساب) بحد أقصى 5 تكبيسات وبفاصل نصف ثانية ومؤقت 30 ثانية...`, mainKeyboard);
        
        // تشغيل التكبيس لكل الحسابات المسجلة
        for (let username of activeSessions) {
            runTappingSession(chatId, username);
        }
        return;
    }

    if (text.startsWith('/')) return;

    // الحالات الخاصة حسب الأزرار المحددة مسبقاً
    if (botMode === "waiting_for_comment") {
        customCommentText = text.trim();
        botMode = "idle";
        return bot.sendMessage(chatId, `✅ تم حفظ التعليق الموحد بنجاح: "${customCommentText}"`, mainKeyboard);
    }

    if (botMode === "waiting_for_session" || !text.includes('(')) {
        let username = text.trim();
        if (username.includes('tiktok.com/@')) {
            const parts = username.split('@')[1];
            username = parts.split('/')[0].split('?')[0];
        }

        if (!activeSessions.includes(username)) {
            activeSessions.push(username);
        }
        botMode = "idle";
        
        bot.sendMessage(chatId, `🚀 تم إضافة وتسجيل الجلسة لـ @${username} بنجاح! جاري تنفيذ التكبيس الآمن...`, mainKeyboard);
        runTappingSession(chatId, username);
    }
});

// دالة تشغيل التكبيس الآمن للجلسة
async function runTappingSession(chatId, username) {
    try {
        const tiktokLiveConnection = new WebcastPushConnection(username);
        await tiktokLiveConnection.connect();
        
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

            bot.sendMessage(chatId, `🏁 انتهت جلسة @${username} (${reason}). إجمالي التكبيسات: ${tapCount}.`, mainKeyboard);
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
        bot.sendMessage(chatId, `❌ فشل الاتصال بـ @${username}: تأكد أنه فاتح بث حالياً وأن الاسم صحيح.`, mainKeyboard);
    }
}
