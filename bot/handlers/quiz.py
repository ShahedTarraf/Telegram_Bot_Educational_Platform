"""
Quiz Handler - Auto-graded quizzes
معالج الاختبارات التلقائية
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from loguru import logger
from datetime import datetime
import random

from database.models.quiz import Quiz
from database.models.user import User


async def show_quizzes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show available quizzes for a course"""
    query = update.callback_query
    await query.answer()
    
    course_id = query.data.replace("quizzes_", "")
    
    # Verify user has access
    user = await User.find_one(User.telegram_id == update.effective_user.id)
    if not user or not user.has_approved_course(course_id):
        await query.message.reply_text("❌ ليس لديك صلاحية الوصول لهذا المحتوى")
        return
    
    # Get quizzes for this course
    quizzes = await Quiz.find(
        Quiz.related_to == "courses",
        Quiz.related_id == course_id,
        Quiz.is_active == True
    ).to_list()
    
    if quizzes:
        text = f"📝 **الاختبارات المتاحة** ({len(quizzes)} اختبار)\n\n"
        
        keyboard = []
        for i, quiz in enumerate(quizzes, 1):
            # Get user's attempts
            attempts_count = quiz.get_attempts_count(str(update.effective_user.id))
            best_attempt = quiz.get_best_attempt(str(update.effective_user.id))
            
            status = ""
            if best_attempt:
                if best_attempt.passed:
                    status = f" ✅ ({best_attempt.score}/{best_attempt.max_score})"
                else:
                    status = f" ❌ ({best_attempt.score}/{best_attempt.max_score})"
            
            text += f"{i}. **{quiz.title}**{status}\n"
            text += f"   ❓ {len(quiz.questions)} سؤال"
            
            if quiz.time_limit_minutes:
                text += f" | ⏱️ {quiz.time_limit_minutes} د"
            
            text += f" | 🔄 {attempts_count}/{quiz.max_attempts}\n\n"
            
            # Add button
            keyboard.append([InlineKeyboardButton(
                f"📝 {quiz.title}",
                callback_data=f"quiz_view_{quiz.id}"
            )])
        
        keyboard.append([InlineKeyboardButton("« رجوع", callback_data=f"course_{course_id}")])
        
        await query.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    else:
        text = """
📝 **الاختبارات**

لا توجد اختبارات متاحة حالياً...

📝 سيتم إضافة اختبارات قريباً من قبل المدرس.
        """
        
        keyboard = [[InlineKeyboardButton("« رجوع", callback_data=f"course_{course_id}")]]
        
        await query.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def view_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View quiz details"""
    query = update.callback_query
    await query.answer()
    
    quiz_id = query.data.replace("quiz_view_", "")
    quiz = await Quiz.find_one(Quiz.id == quiz_id)
    
    if not quiz:
        await query.message.edit_text("❌ الاختبار غير موجود")
        return
    
    user_id = str(update.effective_user.id)
    
    # Get user's attempts
    attempts = quiz.get_user_attempts(user_id)
    attempts_count = len(attempts)
    best_attempt = quiz.get_best_attempt(user_id)
    
    text = quiz.get_info_text()
    
    text += f"\n📊 **محاولاتك:** {attempts_count}/{quiz.max_attempts}\n"
    
    if best_attempt:
        text += f"\n🏆 **أفضل نتيجة:** {best_attempt.score}/{best_attempt.max_score} "
        text += f"({int(best_attempt.score/best_attempt.max_score*100)}%)\n"
        
        if best_attempt.passed:
            text += "✅ **ناجح**\n"
        else:
            text += "❌ **راسب**\n"
    
    keyboard = []
    
    # Check if user can attempt
    if quiz.can_attempt(user_id):
        keyboard.append([InlineKeyboardButton(
            "🚀 بدء الاختبار",
            callback_data=f"quiz_start_{quiz.id}"
        )])
    else:
        if attempts_count >= quiz.max_attempts:
            text += "\n⚠️ **لقد استنفدت جميع محاولاتك!**\n"
    
    # Show previous attempts
    if attempts:
        keyboard.append([InlineKeyboardButton(
            "📊 عرض المحاولات السابقة",
            callback_data=f"quiz_attempts_{quiz.id}"
        )])
    
    keyboard.append([InlineKeyboardButton("« رجوع", callback_data=f"quizzes_{quiz.related_id}")])
    
    await query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start quiz attempt"""
    query = update.callback_query
    await query.answer()
    
    quiz_id = query.data.replace("quiz_start_", "")
    quiz = await Quiz.find_one(Quiz.id == quiz_id)
    
    if not quiz:
        await query.message.edit_text("❌ الاختبار غير موجود")
        return
    
    user_id = str(update.effective_user.id)
    
    # Start attempt
    attempt = await quiz.start_attempt(user_id)
    
    if not attempt:
        await query.message.edit_text(
            "❌ لا يمكنك بدء الاختبار الآن.\n"
            "ربما استنفدت جميع محاولاتك أو الاختبار غير متاح."
        )
        return
    
    # Store quiz session in context
    context.user_data['active_quiz'] = {
        'quiz_id': str(quiz.id),
        'question_index': 0,
        'answers': [],
        'start_time': datetime.utcnow()
    }
    
    # Show first question
    await show_quiz_question(update, context, quiz, 0)


async def show_quiz_question(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    quiz: Quiz,
    question_index: int
):
    """Show quiz question"""
    if question_index >= len(quiz.questions):
        # Quiz completed
        await complete_quiz(update, context)
        return
    
    question = quiz.questions[question_index]
    
    text = f"❓ **السؤال {question_index + 1}/{len(quiz.questions)}**\n\n"
    text += f"{question.question}\n\n"
    text += f"💰 **النقاط:** {question.points}\n"
    
    # Show time remaining if there's a limit
    if quiz.time_limit_minutes:
        elapsed = (datetime.utcnow() - context.user_data['active_quiz']['start_time']).seconds
        remaining = quiz.time_limit_minutes * 60 - elapsed
        
        if remaining <= 0:
            # Time's up!
            await complete_quiz(update, context)
            return
        
        text += f"⏱️ **الوقت المتبقي:** {remaining // 60}:{remaining % 60:02d}\n"
    
    # Show options
    keyboard = []
    for i, option in enumerate(question.options):
        keyboard.append([InlineKeyboardButton(
            f"{chr(65 + i)}. {option.text}",
            callback_data=f"quiz_answer_{question_index}_{i}"
        )])
    
    # Add navigation
    nav_buttons = []
    if question_index > 0:
        nav_buttons.append(InlineKeyboardButton(
            "« السابق",
            callback_data=f"quiz_prev_{question_index}"
        ))
    
    nav_buttons.append(InlineKeyboardButton(
        "🏁 إنهاء الاختبار",
        callback_data="quiz_finish"
    ))
    
    keyboard.append(nav_buttons)
    
    query = update.callback_query
    await query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def answer_quiz_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Record answer and show next question"""
    query = update.callback_query
    await query.answer()
    
    # Parse callback data: quiz_answer_{question_index}_{option_index}
    parts = query.data.split('_')
    question_index = int(parts[2])
    option_index = int(parts[3])
    
    # Get active quiz
    active_quiz = context.user_data.get('active_quiz')
    if not active_quiz:
        await query.message.edit_text("❌ الجلسة انتهت. يرجى بدء الاختبار من جديد.")
        return
    
    quiz = await Quiz.find_one(Quiz.id == active_quiz['quiz_id'])
    if not quiz:
        await query.message.edit_text("❌ الاختبار غير موجود")
        return
    
    # Record answer
    answers = active_quiz['answers']
    
    # Ensure answers list is long enough
    while len(answers) <= question_index:
        answers.append(-1)
    
    answers[question_index] = option_index
    active_quiz['answers'] = answers
    active_quiz['question_index'] = question_index + 1
    
    # Show next question
    await show_quiz_question(update, context, quiz, question_index + 1)


async def complete_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Complete and grade quiz"""
    query = update.callback_query
    if query:
        await query.answer()
    
    active_quiz = context.user_data.get('active_quiz')
    if not active_quiz:
        return
    
    quiz = await Quiz.find_one(Quiz.id == active_quiz['quiz_id'])
    if not quiz:
        return
    
    user_id = str(update.effective_user.id)
    answers = active_quiz['answers']
    
    # Submit and grade
    attempt = await quiz.submit_attempt(user_id, answers)
    
    if not attempt:
        await query.message.edit_text("❌ حدث خطأ في تسليم الاختبار")
        return
    
    # Show results
    percentage = int(attempt.score / attempt.max_score * 100) if attempt.max_score > 0 else 0
    
    text = f"""
🎉 **اكتمل الاختبار!**

📝 **الاختبار:** {quiz.title}
📊 **النتيجة:** {attempt.score}/{attempt.max_score} نقطة
📈 **النسبة:** {percentage}%
⏱️ **الوقت المستغرق:** {attempt.time_taken_seconds // 60}:{attempt.time_taken_seconds % 60:02d}

{'✅ **مبروك! أنت ناجح!** 🎉' if attempt.passed else '❌ **للأسف لم تنجح. حاول مرة أخرى!**'}

💪 **لديك {quiz.max_attempts - quiz.get_attempts_count(user_id)} محاولة متبقية**
    """
    
    keyboard = [
        [InlineKeyboardButton("📊 عرض الأجوبة", callback_data=f"quiz_review_{quiz.id}_{len(quiz.get_user_attempts(user_id))-1}")],
        [InlineKeyboardButton("« العودة", callback_data=f"quiz_view_{quiz.id}")]
    ]
    
    await query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    
    # Clear active quiz
    context.user_data.pop('active_quiz', None)
    
    logger.info(f"Quiz completed by user {user_id}: {attempt.score}/{attempt.max_score}")


async def review_quiz_answers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Review quiz answers"""
    query = update.callback_query
    await query.answer()
    
    # Parse: quiz_review_{quiz_id}_{attempt_index}
    parts = query.data.split('_')
    quiz_id = parts[2]
    attempt_index = int(parts[3])
    
    quiz = await Quiz.find_one(Quiz.id == quiz_id)
    if not quiz:
        await query.message.edit_text("❌ الاختبار غير موجود")
        return
    
    user_id = str(update.effective_user.id)
    attempts = quiz.get_user_attempts(user_id)
    
    if attempt_index >= len(attempts):
        await query.message.edit_text("❌ المحاولة غير موجودة")
        return
    
    attempt = attempts[attempt_index]
    
    text = f"📊 **مراجعة الأجوبة - المحاولة {attempt_index + 1}**\n\n"
    
    for i, question in enumerate(quiz.questions):
        text += f"❓ **س{i+1}:** {question.question}\n"
        
        if i < len(attempt.answers):
            selected = attempt.answers[i]
            result = quiz.get_question_result(i, selected)
            
            if selected >= 0 and selected < len(question.options):
                text += f"📝 **إجابتك:** {question.options[selected].text}\n"
            else:
                text += f"📝 **إجابتك:** لم تجب\n"
            
            if result['is_correct']:
                text += "✅ **صحيحة!**\n"
            else:
                text += "❌ **خاطئة!**\n"
                if quiz.show_correct_answers and result['correct_answer_text']:
                    text += f"✔️ **الإجابة الصحيحة:** {result['correct_answer_text']}\n"
            
            if result['explanation']:
                text += f"💡 **الشرح:** {result['explanation']}\n"
        
        text += "\n"
    
    keyboard = [[InlineKeyboardButton("« رجوع", callback_data=f"quiz_view_{quiz.id}")]]
    
    await query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
