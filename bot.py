import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

API_TOKEN = '8265138326:AAEtF4s1AvSkYuTcuebI91jorUezTsGjBzk'
bot = telebot.TeleBot(API_TOKEN)

# قائمة الأسئلة
questions = [
    {
        "question": "ما هي عاصمة العراق؟",
        "options": ["بغداد", "أربيل", "البصرة"],
        "correct": "بغداد"
    },
    {
        "question": "كم عدد ألوان علم العراق؟",
        "options": ["3", "4", "5"],
        "correct": "4"
    },
    {
        "question": "ما هو أكبر كوكب في المجموعة الشمسية؟",
        "options": ["الأرض", "المشتري", "المريخ"],
        "correct": "المشتري"
    }
]

# لتخزين حالة اللعبة لكل كروب
# شكل البيانات: {chat_id: {"score": {user_id: points}, "current_q": 0, "active": True}}
group_games = {}

# أمر بدء المسابقة في الكروب
@bot.message_handler(commands=['startgame', 'مسباق'])
def start_group_game(message):
    chat_id = message.chat.id
    
    # التأكد أن الأمر يُستخدم في مجموعة (Group أو Supergroup)
    if message.chat.type not in ['group', 'supergroup']:
        bot.reply_to(message, "هذا الأمر مخصص للعمل داخل المجموعات فقط! أضفني إلى جروب وابدأ اللعب هناك. 🎮")
        return

    group_games[chat_id] = {
        "score": {},
        "current_q": 0,
        "active": True
    }
    
    bot.send_message(chat_id, "🎮 **بدأت مسابقة التحدي في الجروب!**\nاستعدوا، سيتم إرسال السؤال الأول الآن... شعالين يا شباب!")
    send_group_question(chat_id)

# دالة إرسال السؤال للكروب
def send_group_question(chat_id):
    game = group_games.get(chat_id)
    if not game or not game["active"]:
        return

    q_index = game["current_q"]
    
    if q_index < len(questions):
        q_data = questions[q_index]
        markup = InlineKeyboardMarkup()
        
        for option in q_data["options"]:
            markup.add(InlineKeyboardButton(option, callback_data=f"gans_{option}"))
            
        bot.send_message(chat_id, f"❓ **السؤال ({q_index + 1}):**\n{q_data['question']}", reply_markup=markup)
    else:
        # انتهت الأسئلة، إعلان الفائزين
        scores = game["score"]
        if scores:
            # ترتيب اللاعبين حسب النقاط
            sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            result_text = "🏆 **انتهت المسابقة! نتائج المتصدرين في الجروب:**\n\n"
            for idx, (uid, pts) in enumerate(sorted_scores, 1):
                try:
                    user_info = bot.get_chat_member(chat_id, uid).user
                    name = user_info.first_name
                except:
                    name = f"مستخدم {uid}"
                result_text += f"{idx}. {name} ⟵ النقاط: {pts}\n"
        else:
            result_text = "🏆 انتهت المسابقة ولم يجب أحد إجابة صحيحة!"

        bot.send_message(chat_id, result_text)
        group_games[chat_id]["active"] = False

# استقبال الإجابات من الأزرار في الكروب
@bot.callback_query_handler(func=lambda call: call.data.startswith('gans_'))
def handle_group_answer(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    user_name = call.from_user.first_name

    if chat_id not in group_games or not group_games[chat_id]["active"]:
        bot.answer_callback_query(call.id, "لا توجد مسابقة نشطة حالياً في هذا الجروب. اطلب من أحد بدء لعبة بـ /startgame", show_alert=True)
        return

    game = group_games[chat_id]
    q_index = game["current_q"]
    correct_ans = questions[q_index]["correct"]
    selected_ans = call.data.split('gans_')[1]

    if selected_ans == correct_ans:
        # احتساب النقاط للمستخدم
        if user_id not in game["score"]:
            game["score"][user_id] = 0
        game["score"][user_id] += 1

        bot.answer_callback_query(call.id, "إجابة صحيحة! كسبت نقطة 🎯")
        bot.send_message(chat_id, f"✅ كفو **{user_name}** جاوب صح وسجل نقطة! الإجابة كانت: {correct_ans}")

        # الانتقال للسؤال التالي تلقائياً
        game["current_q"] += 1
        
        # حذف أرسال السؤال القديم أو تعديله لمنع الضغط عليه مرة أخرى (اختياري)
        try:
            bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
        except:
            pass

        # إرسال السؤال التالي بعد ثانية
        send_group_question(chat_id)
    else:
        bot.answer_callback_query(call.id, "إجابة خاطئة! ❌ حاول في السؤال القادم", show_alert=False)

bot.infinity_polling()
