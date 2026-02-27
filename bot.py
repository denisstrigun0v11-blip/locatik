# bot.py
# Telegram бот для изучения Web Technologies и Python

import telebot
from telebot import types
import random
from config import BOT_TOKEN, ADMIN_IDS, QUESTIONS_PER_SESSION
from database import (
    init_database, add_concept, get_random_concept, get_all_concepts,
    get_concepts_by_category, get_concepts_by_categories, get_all_categories,
    delete_concept, update_concept, search_concepts, get_concept_count,
    save_user_progress, get_user_stats, save_quiz_result, get_user_quiz_history,
    get_concept_by_id
)

# Инициализация бота
bot = telebot.TeleBot(BOT_TOKEN)

# Хранилище состояний пользователей
user_states = {}

# Текущая сессия викторины
user_sessions = {}

# =============================================================================
# КЛАВИАТУРЫ
# =============================================================================

def get_main_keyboard():
    """Основная клавиатура бота"""
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        types.KeyboardButton("📚 Изучить понятие"),
        types.KeyboardButton("🐍 Python понятия"),
        types.KeyboardButton("🌐 Веб понятия"),
        types.KeyboardButton("🎯 Викторина"),
        types.KeyboardButton("📊 Моя статистика"),
        types.KeyboardButton("🔍 Поиск"),
        types.KeyboardButton("📂 Категории"),
        types.KeyboardButton("ℹ️ О боте")
    ]
    keyboard.add(*buttons)
    return keyboard

def get_admin_keyboard():
    """Клавиатура администратора"""
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        types.KeyboardButton("➕ Добавить понятие"),
        types.KeyboardButton("📝 Редактировать"),
        types.KeyboardButton("🗑️ Удалить понятие"),
        types.KeyboardButton("📋 Все понятия"),
        types.KeyboardButton("🔙 Главное меню")
    ]
    keyboard.add(*buttons)
    return keyboard

def get_continue_keyboard():
    """Клавиатура продолжения"""
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("➡️ Следующее понятие", callback_data="next_concept"),
        types.InlineKeyboardButton("🔙 В меню", callback_data="main_menu")
    )
    return keyboard

def get_category_keyboard(categories):
    """Клавиатура выбора категории"""
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    for cat in categories:
        buttons.append(types.InlineKeyboardButton(cat, callback_data=f"cat_{cat}"))
    keyboard.add(*buttons)
    keyboard.add(types.InlineKeyboardButton("🔙 Назад", callback_data="main_menu"))
    return keyboard

def get_quiz_category_keyboard():
    """Клавиатура выбора категории викторины"""
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("🌐 Веб-технологии", callback_data="quiz_web"),
        types.InlineKeyboardButton("🐍 Python", callback_data="quiz_python"),
        types.InlineKeyboardButton("🎲 Все категории", callback_data="quiz_all")
    )
    keyboard.add(types.InlineKeyboardButton("🔙 Отмена", callback_data="main_menu"))
    return keyboard

# =============================================================================
# ОБРАБОТЧИКИ КОМАНД
# =============================================================================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Обработка команды /start"""
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    total_concepts = get_concept_count()
    
    welcome_text = f"""
👋 Привет, {user_name}!

Я **WebTechHelperBot** — твой помощник в изучении веб-технологий и Python!

📚 **Что я умею:**
• Показывать рандомные понятия с определениями
• Проводить викторины для проверки знаний
• Искать понятия по ключевым словам
• Вести статистику твоего прогресса
• Фильтровать по категориям (Веб / Python)

📊 **В базе уже {total_concepts} понятий!**

🎯 **Доступные команды:**
/start — Запустить бота
/help — Помощь
/stats — Моя статистика
/search — Поиск понятия
/quiz — Начать викторину

Выбери действие в меню ниже! 👇
    """
    
    bot.send_message(
        message.chat.id, 
        welcome_text, 
        reply_markup=get_main_keyboard(),
    )

@bot.message_handler(commands=['help'])
def send_help(message):
    """Обработка команды /help"""
    help_text = """
📖 **Помощь по боту WebTechHelperBot**

**Основные функции:**

📚 **Изучение понятий**
• Получай случайные понятия из базы
• Читай определения и примеры
• Фильтруй по категориям (Веб/Python)

🎯 **Викторина**
• Проверь свои знания
• Вопросы с вариантами ответов
• Выбор категории (Веб/Python/Все)

🔍 **Поиск**
• Ищи понятия по названию
• Ищи по тексту определения

📊 **Статистика**
• Смотри свой прогресс
• Количество изученных понятий
• Результаты викторин

**Команды:**
/start — Главное меню
/help — Эта справка
/stats — Твоя статистика
/quiz — Начать викторину
/search — Поиск понятия

**Для администраторов:**
➕ Добавить понятие
📝 Редактировать понятие
🗑️ Удалить понятие
    """
    bot.send_message(message.chat.id, text, parse_mode='HTML')

@bot.message_handler(commands=['stats'])
def send_stats(message):
    """Обработка команды /stats"""
    user_id = message.from_user.id
    stats = get_user_stats(user_id)
    total_concepts = get_concept_count()
    
    success_rate = stats['total_correct'] * 100 // max(stats['total_shown'], 1)
    progress = stats['learned_count'] * 100 // max(total_concepts, 1)
    
    stats_text = f"""
📊 **Твоя статистика**

📚 Всего понятий в базе: {total_concepts}
👀 Показано понятий: {stats['total_shown']}
✅ Правильных ответов: {stats['total_correct']}
🎓 Изучено понятий: {stats['learned_count']}

📈 Прогресс обучения: {progress}%
🎯 Успешность: {success_rate}%
    """
    bot.send_message(message.chat.id, text, parse_mode='HTML')

@bot.message_handler(commands=['quiz'])
def start_quiz_command(message):
    """Обработка команды /quiz"""
    quiz_category_choice(message)

@bot.message_handler(commands=['search'])
def search_command(message):
    """Обработка команды /search"""
    msg = bot.send_message(
        message.chat.id,
        "🔍 Введите поисковый запрос:",
        reply_markup=types.ReplyKeyboardRemove()
    )
    bot.register_next_step_handler(msg, process_search)

# =============================================================================
# ОБРАБОТЧИКИ ТЕКСТОВЫХ СООБЩЕНИЙ
# =============================================================================

@bot.message_handler(func=lambda message: message.text == "📚 Изучить понятие")
def show_random_concept(message):
    """Показ случайного понятия (все категории)"""
    concept = get_random_concept()
    
    if concept:
        show_concept_message(message.chat.id, concept)
        save_user_progress(message.from_user.id, concept['id'], True)
    else:
        bot.send_message(message.chat.id, "❌ В базе пока нет понятий.")

@bot.message_handler(func=lambda message: message.text == "🐍 Python понятия")
def show_python_concepts(message):
    """Показ случайного понятия из Python категорий"""
    python_categories = ["Python Basics", "Python Libraries"]
    concept = get_random_concept(categories=python_categories)
    
    if concept:
        show_concept_message(message.chat.id, concept)
        save_user_progress(message.from_user.id, concept['id'], True)
    else:
        bot.send_message(message.chat.id, "❌ Python понятия пока не добавлены.")

@bot.message_handler(func=lambda message: message.text == "🌐 Веб понятия")
def show_web_concepts(message):
    """Показ случайного понятия из Веб категорий"""
    web_categories = ["Frontend", "Backend", "General", "Tools"]
    concept = get_random_concept(categories=web_categories)
    
    if concept:
        show_concept_message(message.chat.id, concept)
        save_user_progress(message.from_user.id, concept['id'], True)
    else:
        bot.send_message(message.chat.id, "❌ Веб понятия пока не добавлены.")

def show_concept_message(chat_id, concept):
    """Форматирование и отправка сообщения с понятием"""
    concept_text = f"""
📖 **{concept['term']}**

📝 **Определение:**
{concept['definition']}

🏷️ **Категория:** {concept['category']}

💡 **Пример:**
{concept['example'] if concept['example'] else 'Нет примера'}

─────────────────
📅 Добавлено: {concept['created_at']}
    """
    
    bot.send_message(
        chat_id,
        concept_text,
        reply_markup=get_continue_keyboard(),
        parse_mode='HTML'
    )

@bot.message_handler(func=lambda message: message.text == "🎯 Викторина")
def quiz_category_choice(message):
    """Выбор категории для викторины"""
    keyboard = get_quiz_category_keyboard()
    
    bot.send_message(
        message.chat.id,
        "🎯 **Выберите категорию для викторины:**\n\n"
        "🌐 Веб-технологии — HTML, CSS, JavaScript, API\n"
        "🐍 Python — основы и библиотеки\n"
        "🎲 Все категории — случайные вопросы",
        reply_markup=keyboard,
        parse_mode='HTML'
    )

def start_quiz(message, category_type):
    """Запуск викторины с выбранной категорией"""
    user_id = message.from_user.id
    
    # Определяем категории для викторины
    if category_type == 'web':
        categories = ["Frontend", "Backend", "General", "Tools"]
    elif category_type == 'python':
        categories = ["Python Basics", "Python Libraries"]
    else:
        categories = None
    
    # Получаем понятия для викторины
    if categories:
        all_concepts = get_concepts_by_categories(categories)
    else:
        all_concepts = get_all_concepts()
    
    if len(all_concepts) < 4:
        bot.send_message(
            message.chat.id,
            "❌ Недостаточно понятий для викторины (нужно минимум 4)"
        )
        return
    
    # Выбираем 5 случайных вопросов
    questions = random.sample(all_concepts, min(5, len(all_concepts)))
    
    # Сохраняем сессию викторины
    user_sessions[user_id] = {
        'questions': questions,
        'current_question': 0,
        'score': 0,
        'category': category_type
    }
    
    send_quiz_question(message, user_id)

def send_quiz_question(message, user_id):
    """Отправка вопроса викторины"""
    session = user_sessions.get(user_id)
    
    if not session or session['current_question'] >= len(session['questions']):
        finish_quiz(message, user_id)
        return
    
    question = session['questions'][session['current_question']]
    
    # Создаем варианты ответов (1 правильный + 3 неправильных)
    all_concepts = get_all_concepts()
    wrong_answers = random.sample(
        [c for c in all_concepts if c['id'] != question['id']],
        min(3, len(all_concepts) - 1)
    )
    
    answers = [question] + wrong_answers
    random.shuffle(answers)
    
    # Создаем клавиатуру с вариантами
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for answer in answers:
        btn = types.InlineKeyboardButton(
            answer['term'],
            callback_data=f"quiz_{question['id']}_{answer['id']}"
        )
        keyboard.add(btn)
    
    quiz_text = f"""
🎯 **Викторина** | Вопрос {session['current_question'] + 1}/{len(session['questions'])}

❓ **Определение:**
{question['definition']}

Выберите правильный термин: 👇
    """
    
    bot.send_message(
        message.chat.id,
        quiz_text,
        reply_markup=keyboard,
        parse_mode='HTML'
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('quiz_'))
def handle_quiz_answer(call):
    """Обработка ответа викторины"""
    user_id = call.from_user.id
    session = user_sessions.get(user_id)
    
    if not session:
        return
    
    # Парсим данные из callback
    parts = call.data.split('_')
    correct_id = int(parts[1])
    selected_id = int(parts[2])
    
    # Проверяем ответ
    is_correct = correct_id == selected_id
    
    if is_correct:
        session['score'] += 1
        bot.answer_callback_query(call.id, "✅ Правильно!", show_alert=False)
    else:
        correct_concept = get_concept_by_id(correct_id)
        if correct_concept:
            bot.answer_callback_query(
                call.id,
                f"❌ Неверно! Правильный ответ: {correct_concept['term']}",
                show_alert=True
            )
    
    # Сохраняем прогресс
    save_user_progress(user_id, correct_id, is_correct)
    
    # Переходим к следующему вопросу
    session['current_question'] += 1
    send_quiz_question(call.message, user_id)

def finish_quiz(message, user_id):
    """Завершение викторины"""
    session = user_sessions.pop(user_id, None)
    
    if not session:
        return
    
    score = session['score']
    total = len(session['questions'])
    percentage = score * 100 // total
    
    # Сохраняем результат
    save_quiz_result(user_id, score, total)
    
    # Определяем сообщение по результату
    if percentage == 100:
        emoji = "🏆"
        text = "Отлично! Идеальный результат!"
    elif percentage >= 80:
        emoji = "🎉"
        text = "Превосходно!"
    elif percentage >= 60:
        emoji = "👍"
        text = "Хороший результат!"
    elif percentage >= 40:
        emoji = "📚"
        text = "Нужно ещё позаниматься!"
    else:
        emoji = "💪"
        text = "Не сдавайся! Попробуй ещё раз!"
    
    result_text = f"""
{emoji} **Викторина завершена!**

✅ Правильных ответов: {score}/{total}
📊 Результат: {percentage}%

{text}
    """
    
    bot.send_message(message.chat.id, result_text,parse_mode='HTML')
    
    # Показываем кнопку возврата в меню
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("🔙 В главное меню", callback_data="main_menu"))
    bot.send_message(message.chat.id, "Продолжить?", reply_markup=keyboard)

@bot.message_handler(func=lambda message: message.text == "📊 Моя статистика")
def show_user_stats(message):
    """Показ статистики пользователя"""
    user_id = message.from_user.id
    stats = get_user_stats(user_id)
    total_concepts = get_concept_count()
    history = get_user_quiz_history(user_id)
    
    success_rate = stats['total_correct'] * 100 // max(stats['total_shown'], 1)
    progress = stats['learned_count'] * 100 // max(total_concepts, 1)
    
    stats_text = f"""
📊 **Твоя статистика обучения**

📚 **Общая информация:**
• Всего понятий в базе: {total_concepts}
• Показано понятий: {stats['total_shown']}
• Изучено понятий: {stats['learned_count']}

🎯 **Прогресс:**
• Правильных ответов: {stats['total_correct']}
• Успешность: {success_rate}%
• Прогресс: {progress}%
    """
    
    if history:
        stats_text += "\n\n📈 **Последние викторины:**\n"
        for i, quiz in enumerate(history[:3], 1):
            percentage = quiz['score'] * 100 // quiz['total_questions']
            stats_text += f"{i}. {quiz['score']}/{quiz['total_questions']} ({percentage}%)\n"
    
    bot.send_message(message.chat.id, stats_text, parse_mode='HTML')

@bot.message_handler(func=lambda message: message.text == "🔍 Поиск")
def search_prompt(message):
    """Запрос поискового запроса"""
    msg = bot.send_message(
        message.chat.id,
        "🔍 Введите слово или фразу для поиска:",
        reply_markup=types.ReplyKeyboardRemove()
    )
    bot.register_next_step_handler(msg, process_search)

def process_search(message):
    """Обработка поискового запроса"""
    query = message.text.strip()
    
    if len(query) < 2:
        bot.send_message(message.chat.id, "❌ Запрос слишком короткий (минимум 2 символа)")
        return
    
    results = search_concepts(query)
    
    if not results:
        bot.send_message(message.chat.id, f"❌ По запросу '{query}' ничего не найдено")
        return
    
    # Показываем первые 5 результатов
    for concept in results[:5]:
        concept_text = f"""
📖 **{concept['term']}**

📝 {concept['definition'][:200]}{'...' if len(concept['definition']) > 200 else ''}

🏷️ Категория: {concept['category']}
        """
        bot.send_message(message.chat.id, concept_text, parse_mode='HTML')
    
    if len(results) > 5:
        bot.send_message(message.chat.id, f"... и ещё {len(results) - 5} результатов")
    
    # Возвращаем клавиатуру
    bot.send_message(message.chat.id, "🔙 Меню", reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda message: message.text == "📂 Категории")
def show_categories(message):
    """Показ категорий понятий"""
    categories = get_all_categories()
    
    if not categories:
        bot.send_message(message.chat.id, "❌ Категории пока не созданы")
        return
    
    keyboard = get_category_keyboard(categories)
    
    categories_text = "📂 **Доступные категории:**\n\n"
    for cat in categories:
        count = get_concept_count(cat)
        categories_text += f"• {cat} ({count} понятий)\n"
    
    bot.send_message(message.chat.id, categories_text, reply_markup=keyboard, parse_mode='HTML')

@bot.message_handler(func=lambda message: message.text == "ℹ️ О боте")
def about_bot(message):
    """Информация о боте"""
    total_concepts = get_concept_count()
    
    # Подсчёт по категориям
    web_count = get_concept_count("Frontend") + get_concept_count("Backend") + get_concept_count("General") + get_concept_count("Tools")
    python_count = get_concept_count("Python Basics") + get_concept_count("Python Libraries")
    
    about_text = f"""
🤖 **WebTechHelperBot**

**Версия:** 2.0.0
**Предмет:** Веб-технологии + Python

**Описание:**
Бот создан для помощи в изучении основных понятий и определений веб-технологий и программирования на Python.

📊 **Статистика базы:**
• Всего понятий: {total_concepts}
• Веб-технологии: {web_count}
• Python: {python_count}

**Категории:**
🌐 **Веб-технологии:**
• Frontend (HTML, CSS, JavaScript)
• Backend (API, SQL, Server)
• General (URL, Client, Framework)
• Tools (Git, Deployment)

🐍 **Python:**
• Python Basics (переменные, функции, классы)
• Python Libraries (NumPy, Pandas, Flask)

**Функции:**
• Случайные понятия с определениями
• Викторины с выбором категории
• Поиск по базе понятий
• Статистика прогресса
• Фильтр по категориям

**Разработано:** 2026
**Для:** Изучения веб-технологий и Python

🎯 Удачи в обучении!
    """
    bot.send_message(message.chat.id, about_text, parse_mode='HTML')

# =============================================================================
# АДМИН-ФУНКЦИИ
# =============================================================================

@bot.message_handler(func=lambda message: message.text == "➕ Добавить понятие")
def add_concept_prompt(message):
    """Запрос на добавление понятия"""
    if message.from_user.id not in ADMIN_IDS:
        bot.send_message(message.chat.id, "❌ У вас нет прав администратора")
        return
    
    msg = bot.send_message(
        message.chat.id,
        "➕ **Добавление нового понятия**\n\nВведите термин:",
        parse_mode='HTML',
        reply_markup=types.ReplyKeyboardRemove()
    )
    bot.register_next_step_handler(msg, process_add_term)

def process_add_term(message):
    """Обработка ввода термина"""
    user_states[message.from_user.id] = {
        'state': 'add_concept',
        'term': message.text.strip().upper()
    }
    
    msg = bot.send_message(
        message.chat.id,
        f"Термин: {message.text.strip().upper()}\n\nВведите определение:",
        reply_markup=types.ReplyKeyboardRemove()
    )
    bot.register_next_step_handler(msg, process_add_definition)

def process_add_definition(message):
    """Обработка ввода определения"""
    user_states[message.from_user.id]['definition'] = message.text.strip()
    
    msg = bot.send_message(
        message.chat.id,
        "Введите категорию (или нажмите 'Пропустить' для General):",
        reply_markup=types.ReplyKeyboardRemove()
    )
    bot.register_next_step_handler(msg, process_add_category)

def process_add_category(message):
    """Обработка ввода категории"""
    category = message.text.strip() if message.text.strip() else "General"
    user_states[message.from_user.id]['category'] = category
    
    msg = bot.send_message(
        message.chat.id,
        "Введите пример использования (или напишите 'Пропустить'):",
        reply_markup=types.ReplyKeyboardRemove()
    )
    bot.register_next_step_handler(msg, process_add_example)

def process_add_example(message):
    """Обработка ввода примера и сохранение"""
    example = message.text.strip() if message.text.strip().lower() != "пропустить" else ""
    state = user_states[message.from_user.id]
    
    success = add_concept(
        state['term'],
        state['definition'],
        state['category'],
        example
    )
    
    if success:
        bot.send_message(
            message.chat.id,
            f"✅ Понятие '{state['term']}' успешно добавлено!",
            reply_markup=get_admin_keyboard()
        )
    else:
        bot.send_message(
            message.chat.id,
            f"❌ Понятие '{state['term']}' уже существует!",
            reply_markup=get_admin_keyboard()
        )
    
    # Очищаем состояние
    if message.from_user.id in user_states:
        del user_states[message.from_user.id]

@bot.message_handler(func=lambda message: message.text == "📋 Все понятия")
def show_all_concepts(message):
    """Показ всех понятий"""
    if message.from_user.id not in ADMIN_IDS:
        bot.send_message(message.chat.id, "❌ У вас нет прав администратора")
        return
    
    concepts = get_all_concepts()
    
    if not concepts:
        bot.send_message(message.chat.id, "❌ В базе нет понятий")
        return
    
    text = f"📋 **Все понятия ({len(concepts)}):**\n\n"
    for i, concept in enumerate(concepts[:20], 1):
        text += f"{i}. **{concept['term']}** - {concept['category']}\n"
    
    if len(concepts) > 20:
        text += f"\n... и ещё {len(concepts) - 20} понятий"
    
    bot.send_message(message.chat.id, text, parse_mode='HTML'), reply_markup=get_admin_keyboard())

@bot.message_handler(func=lambda message: message.text == "🔙 Главное меню" or message.text == "🔙 В меню")
def show_main_menu(message):
    """Возврат в главное меню"""
    bot.send_message(
        message.chat.id,
        "🔙 Возврат в главное меню",
        reply_markup=get_main_keyboard()
    )

# =============================================================================
# ОБРАБОТКА CALLBACK
# =============================================================================

@bot.callback_query_handler(func=lambda call: call.data == "next_concept")
def handle_next_concept(call):
    """Обработка кнопки следующего понятия"""
    concept = get_random_concept()
    if concept:
        show_concept_message(call.message.chat.id, concept)
        save_user_progress(call.from_user.id, concept['id'], True)

@bot.callback_query_handler(func=lambda call: call.data == "main_menu")
def handle_main_menu(call):
    """Обработка кнопки главного меню"""
    bot.send_message(
        call.message.chat.id,
        "🔙 Главное меню",
        reply_markup=get_main_keyboard()
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('cat_'))
def handle_category_select(call):
    """Обработка выбора категории"""
    category = call.data.replace('cat_', '')
    concepts = get_concepts_by_category(category)
    
    if not concepts:
        bot.answer_callback_query(call.id, "❌ В этой категории нет понятий")
        return
    
    concept = random.choice(concepts)
    show_concept_message(call.message.chat.id, concept)
    save_user_progress(call.from_user.id, concept['id'], True)

@bot.callback_query_handler(func=lambda call: call.data.startswith('quiz_'))
def handle_quiz_category(call):
    """Обработка выбора категории викторины"""
    category = call.data.replace('quiz_', '')
    user_id = call.from_user.id
    
    # Определяем категории для викторины
    if category == 'web':
        categories = ["Frontend", "Backend", "General", "Tools"]
    elif category == 'python':
        categories = ["Python Basics", "Python Libraries"]
    else:
        categories = None
    
    # Получаем понятия для викторины
    if categories:
        all_concepts = get_concepts_by_categories(categories)
    else:
        all_concepts = get_all_concepts()
    
    if len(all_concepts) < 4:
        bot.answer_callback_query(call.id, "❌ Недостаточно понятий для викторины")
        return
    
    questions = random.sample(all_concepts, min(5, len(all_concepts)))
    
    user_sessions[user_id] = {
        'questions': questions,
        'current_question': 0,
        'score': 0,
        'category': category
    }
    
    bot.answer_callback_query(call.id)
    send_quiz_question(call.message, user_id)

# =============================================================================
# ЗАПУСК БОТА
# =============================================================================

if __name__ == "__main__":
    # Инициализация базы данных
    init_database()
    
    # Добавление начальных понятий (если база пустая)
    if get_concept_count() == 0:
        initial_concepts = [
            # ========== ВЕБ-ТЕХНОЛОГИИ ==========
            ("HTML", "Язык гипертекстовой разметки для создания структуры веб-страниц", "Frontend", "<h1>Заголовок</h1>"),
            ("CSS", "Каскадные таблицы стилей для оформления веб-страниц", "Frontend", "color: red;"),
            ("JavaScript", "Язык программирования для интерактивности на веб-страницах", "Frontend", "console.log('Hello');"),
            ("HTTP", "Протокол передачи гипертекста для обмена данными в вебе", "Backend", "GET /index.html"),
            ("URL", "Универсальный локатор ресурса - адрес веб-страницы", "General", "https://example.com"),
            ("DOM", "Объектная модель документа - представление HTML в виде дерева", "Frontend", "document.getElementById()"),
            ("API", "Интерфейс программирования приложений для взаимодействия сервисов", "Backend", "REST API"),
            ("JSON", "Текстовый формат обмена данными на основе JavaScript", "Backend", '{"name": "John"}'),
            ("SQL", "Язык структурированных запросов для работы с базами данных", "Backend", "SELECT * FROM users"),
            ("Git", "Система контроля версий для отслеживания изменений в коде", "Tools", "git commit -m 'msg'"),
            ("Responsive Design", "Адаптивный дизайн для разных размеров экранов", "Frontend", "@media (max-width: 768px)"),
            ("Bootstrap", "Популярный CSS-фреймворк для быстрой разработки", "Frontend", "class='container'"),
            ("React", "JavaScript-библиотека для создания пользовательских интерфейсов", "Frontend", "<Component />"),
            ("Node.js", "Среда выполнения JavaScript на стороне сервера", "Backend", "require('express')"),
            ("Database", "Организованная коллекция структурированной информации", "Backend", "MySQL, PostgreSQL"),
            ("Server", "Компьютер или программа, предоставляющая услуги клиентам", "Backend", "Web Server"),
            ("Client", "Программа или устройство, запрашивающее услуги у сервера", "General", "Web Browser"),
            ("Framework", "Каркас для разработки приложений с готовыми компонентами", "General", "Django, Laravel"),
            ("Library", "Библиотека готового кода для повторного использования", "General", "jQuery, Lodash"),
            ("Deployment", "Процесс размещения приложения на сервере для доступа пользователей", "Tools", "CI/CD"),
            
            # ========== PYTHON BASICS ==========
            ("Python", "Высокоуровневый язык программирования общего назначения с простым синтаксисом", "Python Basics", "print('Hello, World!')"),
            ("Переменная", "Именованная область памяти для хранения данных в программе", "Python Basics", "x = 10"),
            ("Список (List)", "Упорядоченная изменяемая коллекция элементов в Python", "Python Basics", "my_list = [1, 2, 3]"),
            ("Кортеж (Tuple)", "Упорядоченная неизменяемая коллекция элементов в Python", "Python Basics", "my_tuple = (1, 2, 3)"),
            ("Словарь (Dict)", "Коллекция пар ключ-значение для хранения данных", "Python Basics", "my_dict = {'name': 'John'}"),
            ("Множество (Set)", "Неупорядоченная коллекция уникальных элементов", "Python Basics", "my_set = {1, 2, 3}"),
            ("Функция", "Именованный блок кода, который можно вызывать многократно", "Python Basics", "def func(): pass"),
            ("Класс", "Шаблон для создания объектов с атрибутами и методами", "Python Basics", "class MyClass:"),
            ("Модуль", "Файл с кодом Python, который можно импортировать в другие программы", "Python Basics", "import math"),
            ("Пакет (Package)", "Каталог с модулями Python и файлом __init__.py", "Python Basics", "import package.module"),
            ("Исключение", "Объект, представляющий ошибку во время выполнения программы", "Python Basics", "try: ... except:"),
            ("Декоратор", "Функция, которая модифицирует поведение другой функции", "Python Basics", "@decorator"),
            ("Генератор", "Функция, которая возвращает итератор с помощью yield", "Python Basics", "yield value"),
            ("Лямбда-функция", "Анонимная функция, определённая в одном выражении", "Python Basics", "lambda x: x + 1"),
            ("Метод", "Функция, определённая внутри класса и связанная с объектом", "Python Basics", "obj.method()"),
            ("Атрибут", "Переменная, принадлежащая объекту или классу", "Python Basics", "obj.attribute"),
            ("Итератор", "Объект, который позволяет перебирать элементы коллекции", "Python Basics", "iter(), next()"),
            ("Контекстный менеджер", "Объект для управления ресурсами с помощью with", "Python Basics", "with open('file') as f:"),
            ("PEP 8", "Соглашение о стиле кода для Python программ", "Python Basics", "import this"),
            ("Virtual Environment", "Изолированная среда для установки пакетов Python", "Python Basics", "python -m venv env"),
            
            # ========== PYTHON LIBRARIES ==========
            ("NumPy", "Библиотека для научных вычислений и работы с многомерными массивами", "Python Libraries", "import numpy as np"),
            ("Pandas", "Библиотека для анализа и обработки табличных данных", "Python Libraries", "import pandas as pd"),
            ("Matplotlib", "Библиотека для построения графиков и визуализации данных", "Python Libraries", "import matplotlib.pyplot as plt"),
            ("Requests", "Библиотека для отправки HTTP-запросов к API и веб-сервисам", "Python Libraries", "import requests"),
            ("BeautifulSoup", "Библиотека для парсинга HTML и XML документов", "Python Libraries", "from bs4 import BeautifulSoup"),
            ("Flask", "Лёгкий веб-фреймворк для создания веб-приложений на Python", "Python Libraries", "from flask import Flask"),
            ("Django", "Полнофункциональный веб-фреймворк для разработки на Python", "Python Libraries", "django-admin startproject"),
            ("TensorFlow", "Библиотека машинного обучения от Google для нейросетей", "Python Libraries", "import tensorflow as tf"),
            ("PyTorch", "Библиотека глубокого обучения с динамическими графами", "Python Libraries", "import torch"),
            ("Scikit-learn", "Библиотека машинного обучения для классических алгоритмов", "Python Libraries", "from sklearn import model"),
            ("OpenCV", "Библиотека компьютерного зрения для обработки изображений", "Python Libraries", "import cv2"),
            ("Pillow", "Библиотека для работы с изображениями в Python", "Python Libraries", "from PIL import Image"),
            ("SQLAlchemy", "Библиотека для работы с базами данных и ORM", "Python Libraries", "from sqlalchemy import create_engine"),
            ("PyTest", "Фреймворк для написания и запуска тестов в Python", "Python Libraries", "pytest test_file.py"),
            ("Logging", "Встроенный модуль для ведения логов в приложениях", "Python Libraries", "import logging"),
            ("Datetime", "Встроенный модуль для работы с датой и временем", "Python Libraries", "from datetime import datetime"),
            ("OS", "Встроенный модуль для взаимодействия с операционной системой", "Python Libraries", "import os"),
            ("Re (Regex)", "Встроенный модуль для работы с регулярными выражениями", "Python Libraries", "import re"),
            ("Random", "Встроенный модуль для генерации случайных чисел", "Python Libraries", "import random"),
        ]
        
        for term, definition, category, example in initial_concepts:
            add_concept(term, definition, category, example)
        
        print(f"✓ Добавлено {len(initial_concepts)} начальных понятий")
    
    print("🤖 WebTechHelperBot 2.0 запущен...")
    print(f"📚 Всего понятий в базе: {get_concept_count()}")
  # Добавляем Flask для Render
    from flask import Flask
    import os
    
    app = Flask(__name__)
    
    @app.route('/')
    def home():
        return "WebTechHelperBot is running! 🤖"
    
    @app.route('/health')
    def health():
        return "OK", 200
    
    # Запускаем бота в отдельном потоке
    import threading
    
    def run_bot():
        bot.infinity_polling()
    
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Запускаем Flask сервер
   # Render задаёт PORT через переменную окружения
port = int(os.environ.get('PORT', 5000))
print(f"🌐 Flask server running on port {port}")
app.run(host='0.0.0.0', port=port, debug=False)


