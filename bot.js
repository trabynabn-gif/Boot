const { WebcastPushConnection } = require('tiktok-live-connector');
const fs = require('fs');
const readline = require('readline');

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

function loadAccounts() {
    return fs.readFileSync('../accounts.txt', 'utf8').split('\n').map(l => l.trim()).filter(Boolean);
}

if (loadAccounts().length === 0) {
    console.log('⚠️ لا توجد حسابات مسجلة في accounts.txt');
    process.exit(1);
}

rl.question('🎯 أخل يوزر صاحب البث (بدون @): ', (username) => {
    username = username.trim().replace('@', '');
    rl.close();

    console.log('🚀 جاري الاتصال المباشر ببث الحساب: @' + username + ' ...');
    new WebcastPushConnection(username).connect().then(state => {
        console.log('✅ تم الاتصال بنجاح بغرفة البث! رقم الغرفة:', state.roomId);
        let count = 0;
        let t = setInterval(() => {
            count++;
            console.log('❤️ تم إرسال نبضة تكبيس رقم ' + count);
            if (count >= 5) { clearInterval(t); process.exit(0); }
        }, 1000);
    }).catch(e => console.log('❌ فشل الاتصال: تأكد أن الحساب طالع بث.'));
});
