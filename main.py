from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters
)
import json
import random
import os

TOKEN = "7887015261:AAH_EWWhvLqQwL8Wghlsieg2XAtt7YjyeKU"
OWNER_ID = 7196600990

QUESTIONS_FILE = "questions.json"
SCORES_FILE = "scores.json"
SETTINGS_FILE = "settings.json"

def load_json(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != OWNER_ID:
        try:
            await context.bot.send_message(
                chat_id=OWNER_ID,
                text=f"👤 مستخدم جديد دخل البوت:\nالاسم: {user.full_name}\nالمعرف: {user.id}"
            )
        except: pass

    settings = load_json(SETTINGS_FILE)
    keyboard = [[InlineKeyboardButton("ابدأ المسابقة ▶️", callback_data="start_quiz")]]
    await update.message.reply_text(
        f"<b>📚 أهلاً بك في بوت المسابقات الدينية</b>\n"
        f"يعتمد على فقه السيد السيستاني وسيرة الأئمة (ع)\n\n"
        f"🧠 كل سؤال يحتوي على ٤ اختيارات\n"
        f"🏅 ستحصل على نقطة عن كل إجابة صحيحة\n\n"
        f"🤖 هذا البوت من تصميم: <a href='https://t.me/{settings['designer'].lstrip('@')}'>{settings['designer']}</a>\n"
        f"📢 تابع قناتنا: <a href='{settings['channel']}'>اضغط هنا</a>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    questions = load_json(QUESTIONS_FILE)
    question = random.choice(questions)
    q_text = f"<b>❓ السؤال:</b>\n{question['question']}"
    keyboard = []
    for i, opt in enumerate(question['options']):
        keyboard.append([InlineKeyboardButton(f"{i+1}️⃣ {opt}", callback_data=f"answer_{question['question']}_{i}")])
    context.user_data["current"] = question
    await update.callback_query.message.edit_text(
        q_text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("_")
    chosen = int(data[-1])
    question_text = "_".join(data[1:-1])

    current = context.user_data.get("current")
    if not current or current["question"] != question_text:
        await query.message.edit_text("❌ هذا السؤال لم يعد نشطًا. أرسل /start للبدء من جديد.")
        return

    is_correct = (chosen == current["answer"])
    user_id = query.from_user.id
    scores = load_json(SCORES_FILE)

    if str(user_id) not in scores:
        scores[str(user_id)] = 0
    if is_correct:
        scores[str(user_id)] += 1
        reply = f"✅ <b>إجابة صحيحة!</b>\n🏅 نقاطك: {scores[str(user_id)]}"
    else:
        correct_text = current['options'][current['answer']]
        reply = f"❌ <b>إجابة خاطئة!</b>\n✔️ الجواب الصحيح: {correct_text}\n🏅 نقاطك: {scores[str(user_id)]}"

    save_json(SCORES_FILE, scores)
    await query.message.edit_text(reply, parse_mode="HTML")

async def score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    scores = load_json(SCORES_FILE)
    user_id = str(update.effective_user.id)
    pts = scores.get(user_id, 0)
    await update.message.reply_text(f"📊 نقاطك الحالية: {pts}")

async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    scores = load_json(SCORES_FILE)
    if not scores:
        await update.message.reply_text("لا يوجد متصدرين بعد.")
        return
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:10]
    text = "<b>🏆 قائمة المتصدرين:</b>\n\n"
    for i, (uid, pts) in enumerate(sorted_scores, 1):
        text += f"{i}. <code>{uid}</code> — {pts} نقطة\n"
    await update.message.reply_text(text, parse_mode="HTML")

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("score", score))
    app.add_handler(CommandHandler("top", top))
    app.add_handler(CallbackQueryHandler(show_question, pattern="^start_quiz$"))
    app.add_handler(CallbackQueryHandler(handle_answer, pattern=r"^answer_"))

    print("✅ البوت يعمل الآن...")
    app.run_polling()

if __name__ == "__main__":
    import nest_asyncio, asyncio
    nest_asyncio.apply()
    asyncio.run(main())
