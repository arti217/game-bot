"""
🎮 ЖИЗНЬ-СИМУЛЯТОР для групп
Версия с кнопками и меню команд
"""

import logging
import json
import os
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
import random

# ============ НАСТРОЙКИ ============
BOT_TOKEN = "8413409428:AAFPmD5PXvHtmg9AwjLCR9h16Bo0ho0cdr0"
DATA_FILE = "game_data.json"
# ===================================

# Логирование
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ============ ДАННЫЕ ИГРЫ ============

JOBS = {
    "Курьер": {"salary": 500, "level": 1},
    "Официант": {"salary": 800, "level": 2},
    "Продавец": {"salary": 1200, "level": 3},
    "Таксист": {"salary": 2000, "level": 5},
    "Охранник": {"salary": 2500, "level": 6},
    "Менеджер": {"salary": 4000, "level": 8},
    "Программист": {"salary": 8000, "level": 12},
    "Юрист": {"salary": 12000, "level": 15},
    "Врач": {"salary": 15000, "level": 18},
    "Бизнесмен": {"salary": 25000, "level": 22},
    "Директор": {"salary": 50000, "level": 28},
}

CARS = {
    "Велосипед": 5000,
    "Скутер": 30000,
    "Лада Гранта": 150000,
    "Hyundai Solaris": 350000,
    "Kia Rio": 400000,
    "Volkswagen Polo": 500000,
    "Toyota Camry": 1200000,
    "BMW 3": 2500000,
    "Mercedes E-class": 4000000,
    "Porsche Cayenne": 8000000,
    "Bentley": 15000000,
    "Lamborghini": 25000000,
    "Ferrari": 35000000,
    "Bugatti": 100000000,
}

PHONES = {
    "Nokia 3310": 2000,
    "Samsung A10": 15000,
    "Xiaomi Redmi": 25000,
    "iPhone SE": 50000,
    "Samsung S21": 80000,
    "iPhone 13": 100000,
    "iPhone 14 Pro": 150000,
    "Samsung Fold": 200000,
}

HOUSES = {
    "Комната": 500000,
    "Студия": 2000000,
    "Однушка": 4000000,
    "Двушка": 6000000,
    "Трёшка": 9000000,
    "Пентхаус": 25000000,
    "Коттедж": 40000000,
    "Особняк": 80000000,
    "Вилла": 150000000,
}

BUSINESSES = {
    "Ларёк": {"price": 100000, "income": 5000},
    "Кофейня": {"price": 500000, "income": 10000},
    "Магазин": {"price": 2000000, "income": 20000},
    "Ресторан": {"price": 5000000, "income": 40000},
    "Отель": {"price": 20000000, "income": 80000},
    "ТЦ": {"price": 100000000, "income": 160000},
}

# ============ БАЗА ДАННЫХ ============

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_user(user_id):
    data = load_data()
    uid = str(user_id)
    if uid not in data:
        data[uid] = {
            "name": "",
            "balance": 50000,
            "bank": 0,
            "level": 1,
            "exp": 0,
            "job": None,
            "cars": [],
            "phones": [],
            "houses": [],
            "businesses": [],
            "last_work": None,
            "last_bonus": None,
            "last_crime": None,
            "last_collect": None,
            "used_promos": [],
        }
        save_data(data)
    # Добавляем last_collect если его нет (для старых игроков)
    if "last_collect" not in data[uid]:
        data[uid]["last_collect"] = None
        save_data(data)
    return data[uid]

def update_user(user_id, user_data):
    data = load_data()
    data[str(user_id)] = user_data
    save_data(data)

def add_exp(user_id, amount):
    user = get_user(user_id)
    user["exp"] += amount
    exp_needed = user["level"] * 100
    lvl_up = False
    while user["exp"] >= exp_needed:
        user["exp"] -= exp_needed
        user["level"] += 1
        exp_needed = user["level"] * 100
        lvl_up = True
    update_user(user_id, user)
    return user["level"], lvl_up

def format_money(amount):
    return f"{amount:,}₽".replace(",", " ")

# ============ ПРОМОКОДЫ ============

PROMOCODES = {
    "START2024": {"money": 50000, "description": "Стартовый бонус"},
    "BONUS": {"money": 25000, "description": "Бонусный код"},
    "VIP": {"money": 100000, "description": "VIP бонус"},
    "RICH": {"money": 500000, "description": "Мега бонус"},
}

def get_used_promos(user_id):
    user = get_user(user_id)
    return user.get("used_promos", [])

def add_used_promo(user_id, promo):
    data = load_data()
    uid = str(user_id)
    if uid in data:
        if "used_promos" not in data[uid]:
            data[uid]["used_promos"] = []
        data[uid]["used_promos"].append(promo)
        save_data(data)

# ============ КОМАНДЫ ============

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Регистрация и помощь"""
    user = get_user(update.effective_user.id)
    user["name"] = update.effective_user.first_name
    update_user(update.effective_user.id, user)
    
    keyboard = [
        [InlineKeyboardButton("💼 Работа", callback_data="menu_jobs"),
         InlineKeyboardButton("🏪 Магазины", callback_data="menu_shop")],
        [InlineKeyboardButton("🎰 Казино", callback_data="menu_casino"),
         InlineKeyboardButton("🏦 Банк", callback_data="menu_bank")],
        [InlineKeyboardButton("👤 Профиль", callback_data="menu_profile"),
         InlineKeyboardButton("❓ Помощь", callback_data="menu_help")],
    ]
    
    text = f"""
🎮 <b>ЖИЗНЬ-СИМУЛЯТОР</b>

Привет, {update.effective_user.first_name}!
Твой стартовый капитал: {format_money(50000)}

Выбери действие или используй команды:
/help — помощь
/work — работать
/jobs — список профессий
"""
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Помощь и FAQ"""
    text = """
❓ <b>ПОМОЩЬ И FAQ</b>

<b>🎮 Как начать играть?</b>
1. Напиши /start для регистрации
2. Устройся на работу: /jobs → выбери профессию
3. Работай: /work (каждую минуту)
4. Копи деньги и покупай имущество!

<b>💼 Как заработать?</b>
• /work — работать (раз в 1 мин)
• /bonus — бонус раз в сутки
• /crime — рискнуть (можно потерять деньги)
• /collect — доход с бизнесов

<b>🏪 Что покупать?</b>
• /cars — машины (статус)
• /phones — телефоны (статус)
• /houses — жильё (статус)
• /business — бизнесы (пассивный доход!)

<b>🎰 Казино</b>
• /casino [сумма] — испытать удачу
• /dice [сумма] — игра в кости

<b>🏦 Банк</b>
• /deposit [сумма] — положить в банк
• /withdraw [сумма] — снять с банка

<b>💡 Советы:</b>
• Начни с работы курьером
• Копи на бизнес — это пассивный доход!
• Не рискуй всем в казино

<b>🎁 Промокоды</b>
Используй /promo КОД для активации

━━━━━━━━━━━━━━━
❓ Не нашёл ответ на свой вопрос?
📩 Пиши: @OHA_CATAHA
━━━━━━━━━━━━━━━
"""
    await update.message.reply_text(text, parse_mode="HTML")


async def cmd_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Баланс игрока"""
    user = get_user(update.effective_user.id)
    text = f"""
💰 <b>Баланс {update.effective_user.first_name}</b>

💵 Наличные: {format_money(user['balance'])}
🏦 В банке: {format_money(user['bank'])}
💎 Всего: {format_money(user['balance'] + user['bank'])}
"""
    await update.message.reply_text(text, parse_mode="HTML")


async def cmd_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Профиль игрока"""
    user = get_user(update.effective_user.id)
    exp_needed = user["level"] * 100
    
    job_text = user["job"] if user["job"] else "Безработный"
    
    biz_income = sum(BUSINESSES[b]["income"] for b in user["businesses"])
    
    text = f"""
👤 <b>Профиль {update.effective_user.first_name}</b>

📊 Уровень: {user['level']}
⭐ Опыт: {user['exp']}/{exp_needed}
💼 Работа: {job_text}

💵 Наличные: {format_money(user['balance'])}
🏦 В банке: {format_money(user['bank'])}

🚗 Машин: {len(user['cars'])}
📱 Телефонов: {len(user['phones'])}
🏠 Недвижимости: {len(user['houses'])}
🏢 Бизнесов: {len(user['businesses'])}
💰 Доход от бизнеса: {format_money(biz_income)}/мин
"""
    await update.message.reply_text(text, parse_mode="HTML")


async def cmd_work(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Работать"""
    user = get_user(update.effective_user.id)
    
    if not user["job"]:
        await update.message.reply_text("❌ Ты безработный! Устройся на работу: /jobs")
        return
    
    # Проверка кулдауна (1 минута)
    if user["last_work"]:
        last = datetime.fromisoformat(user["last_work"])
        diff = datetime.now() - last
        if diff < timedelta(minutes=1):
            remaining = timedelta(minutes=1) - diff
            secs = int(remaining.total_seconds())
            await update.message.reply_text(f"⏳ Ты устал! Отдохни ещё {secs} сек")
            return
    
    salary = JOBS[user["job"]]["salary"]
    user["balance"] += salary
    user["last_work"] = datetime.now().isoformat()
    update_user(update.effective_user.id, user)
    
    new_level, lvl_up = add_exp(update.effective_user.id, 10)
    
    text = f"💼 Ты поработал {user['job']}ом и заработал {format_money(salary)}!"
    if lvl_up:
        text += f"\n\n🎉 Поздравляем! Новый уровень: {new_level}!"
    
    await update.message.reply_text(text)


async def cmd_bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ежедневный бонус"""
    user = get_user(update.effective_user.id)
    
    if user["last_bonus"]:
        last = datetime.fromisoformat(user["last_bonus"])
        if datetime.now() - last < timedelta(hours=24):
            diff = timedelta(hours=24) - (datetime.now() - last)
            hours = int(diff.total_seconds() // 3600)
            mins = int((diff.total_seconds() % 3600) // 60)
            await update.message.reply_text(f"⏳ Бонус уже получен! Следующий через {hours}ч {mins}м")
            return
    
    bonus = random.randint(5000, 25000) * user["level"]
    user["balance"] += bonus
    user["last_bonus"] = datetime.now().isoformat()
    update_user(update.effective_user.id, user)
    
    await update.message.reply_text(f"🎁 Ты получил ежедневный бонус: {format_money(bonus)}!")


async def cmd_crime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пойти на дело"""
    user = get_user(update.effective_user.id)
    
    if user.get("last_crime"):
        last = datetime.fromisoformat(user["last_crime"])
        if datetime.now() - last < timedelta(minutes=30):
            diff = timedelta(minutes=30) - (datetime.now() - last)
            mins = int(diff.total_seconds() // 60)
            await update.message.reply_text(f"⏳ Ты прячешься от полиции! Подожди {mins} мин")
            return
    
    user["last_crime"] = datetime.now().isoformat()
    
    if random.random() < 0.4:
        money = random.randint(10000, 100000)
        user["balance"] += money
        update_user(update.effective_user.id, user)
        await update.message.reply_text(f"😎 Дело выгорело! Ты украл {format_money(money)}")
    else:
        fine = min(user["balance"], random.randint(5000, 30000))
        user["balance"] -= fine
        update_user(update.effective_user.id, user)
        await update.message.reply_text(f"🚔 Тебя поймали! Штраф: {format_money(fine)}")


async def cmd_jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Список профессий с кнопками"""
    user = get_user(update.effective_user.id)
    
    keyboard = []
    row = []
    for job, info in JOBS.items():
        if user["level"] >= info["level"]:
            status = "✅"
            callback = f"job_{job}"
        else:
            status = "🔒"
            callback = f"job_locked_{info['level']}"
        
        btn_text = f"{status} {job}"
        row.append(InlineKeyboardButton(btn_text, callback_data=callback))
        
        if len(row) == 2:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    current_job = user["job"] if user["job"] else "Безработный"
    
    text = f"""
💼 <b>Биржа труда</b>

Твоя работа: {current_job}
Твой уровень: {user['level']}

✅ — доступно
🔒 — нужен уровень

Выбери профессию:
"""
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


async def cmd_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Магазины"""
    keyboard = [
        [InlineKeyboardButton("🚗 Автосалон", callback_data="shop_cars"),
         InlineKeyboardButton("📱 Техника", callback_data="shop_phones")],
        [InlineKeyboardButton("🏠 Недвижимость", callback_data="shop_houses"),
         InlineKeyboardButton("🏢 Бизнесы", callback_data="shop_business")],
    ]
    
    text = """
🏪 <b>Магазины</b>

Выбери категорию:
"""
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


async def cmd_cars(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Автосалон"""
    user = get_user(update.effective_user.id)
    
    keyboard = []
    for car, price in CARS.items():
        if car in user["cars"]:
            status = "✅"
            callback = "car_owned"
        else:
            status = f"{format_money(price)}"
            callback = f"buycar_{car}"
        
        keyboard.append([InlineKeyboardButton(f"{car} — {status}", callback_data=callback)])
    
    text = f"""
🚗 <b>Автосалон</b>

Твой баланс: {format_money(user['balance'])}
✅ — уже куплено

Выбери машину:
"""
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


async def cmd_phones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Магазин телефонов"""
    user = get_user(update.effective_user.id)
    
    keyboard = []
    for phone, price in PHONES.items():
        if phone in user["phones"]:
            status = "✅"
            callback = "phone_owned"
        else:
            status = f"{format_money(price)}"
            callback = f"buyphone_{phone}"
        
        keyboard.append([InlineKeyboardButton(f"{phone} — {status}", callback_data=callback)])
    
    text = f"""
📱 <b>Магазин техники</b>

Твой баланс: {format_money(user['balance'])}
✅ — уже куплено

Выбери телефон:
"""
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


async def cmd_houses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Недвижимость"""
    user = get_user(update.effective_user.id)
    
    keyboard = []
    for house, price in HOUSES.items():
        if house in user["houses"]:
            status = "✅"
            callback = "house_owned"
        else:
            status = f"{format_money(price)}"
            callback = f"buyhouse_{house}"
        
        keyboard.append([InlineKeyboardButton(f"{house} — {status}", callback_data=callback)])
    
    text = f"""
🏠 <b>Недвижимость</b>

Твой баланс: {format_money(user['balance'])}
✅ — уже куплено

Выбери жильё:
"""
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


async def cmd_business(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Бизнесы"""
    user = get_user(update.effective_user.id)
    
    keyboard = []
    for biz, info in BUSINESSES.items():
        if biz in user["businesses"]:
            status = f"✅ +{format_money(info['income'])}/мин"
            callback = "biz_owned"
        else:
            status = f"{format_money(info['price'])}"
            callback = f"buybiz_{biz}"
        
        keyboard.append([InlineKeyboardButton(f"{biz} — {status}", callback_data=callback)])
    
    text = f"""
🏢 <b>Бизнесы</b>

Твой баланс: {format_money(user['balance'])}
✅ — уже куплено

Бизнес копит деньги пока ты offline!
Собирай командой /collect
Максимум копится 24 часа.

Выбери бизнес:
"""
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


async def cmd_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Положить в банк"""
    user = get_user(update.effective_user.id)
    
    if not context.args:
        await update.message.reply_text("❌ Укажи сумму: /deposit 10000")
        return
    
    try:
        amount = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Укажи число!")
        return
    
    if amount <= 0:
        await update.message.reply_text("❌ Сумма должна быть положительной!")
        return
    
    if amount > user["balance"]:
        await update.message.reply_text("❌ У тебя нет столько наличных!")
        return
    
    user["balance"] -= amount
    user["bank"] += amount
    update_user(update.effective_user.id, user)
    
    await update.message.reply_text(f"✅ Положил в банк: {format_money(amount)}\n🏦 В банке: {format_money(user['bank'])}")


async def cmd_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Снять с банка"""
    user = get_user(update.effective_user.id)
    
    if not context.args:
        await update.message.reply_text("❌ Укажи сумму: /withdraw 10000")
        return
    
    try:
        amount = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Укажи число!")
        return
    
    if amount <= 0:
        await update.message.reply_text("❌ Сумма должна быть положительной!")
        return
    
    if amount > user["bank"]:
        await update.message.reply_text("❌ В банке нет столько денег!")
        return
    
    user["bank"] -= amount
    user["balance"] += amount
    update_user(update.effective_user.id, user)
    
    await update.message.reply_text(f"✅ Снял с банка: {format_money(amount)}\n💵 Наличные: {format_money(user['balance'])}")


async def cmd_casino(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Казино"""
    user = get_user(update.effective_user.id)
    
    if not context.args:
        await update.message.reply_text("❌ Укажи ставку: /casino 1000")
        return
    
    try:
        bet = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Укажи число!")
        return
    
    if bet <= 0:
        await update.message.reply_text("❌ Ставка должна быть положительной!")
        return
    
    if bet > user["balance"]:
        await update.message.reply_text("❌ У тебя нет столько денег!")
        return
    
    if random.random() < 0.45:
        win = bet * 2
        user["balance"] += bet
        update_user(update.effective_user.id, user)
        await update.message.reply_text(f"🎰 ДЖЕКПОТ! 🎉\nТы выиграл {format_money(win)}!")
    else:
        user["balance"] -= bet
        update_user(update.effective_user.id, user)
        await update.message.reply_text(f"🎰 Не повезло... Ты проиграл {format_money(bet)}")


async def cmd_dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Кости"""
    user = get_user(update.effective_user.id)
    
    if not context.args:
        await update.message.reply_text("❌ Укажи ставку: /dice 1000")
        return
    
    try:
        bet = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Укажи число!")
        return
    
    if bet <= 0:
        await update.message.reply_text("❌ Ставка должна быть положительной!")
        return
    
    if bet > user["balance"]:
        await update.message.reply_text("❌ У тебя нет столько денег!")
        return
    
    your_dice = random.randint(1, 6) + random.randint(1, 6)
    bot_dice = random.randint(1, 6) + random.randint(1, 6)
    
    text = f"🎲 Твои кости: {your_dice}\n🎲 Кости бота: {bot_dice}\n\n"
    
    if your_dice > bot_dice:
        win = bet * 2
        user["balance"] += bet
        update_user(update.effective_user.id, user)
        text += f"🎉 Ты выиграл {format_money(win)}!"
    elif your_dice < bot_dice:
        user["balance"] -= bet
        update_user(update.effective_user.id, user)
        text += f"😢 Ты проиграл {format_money(bet)}"
    else:
        text += "🤝 Ничья! Деньги остаются при тебе."
    
    await update.message.reply_text(text)


async def cmd_inventory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Имущество"""
    user = get_user(update.effective_user.id)
    
    text = f"📦 <b>Имущество {update.effective_user.first_name}</b>\n\n"
    
    if user["cars"]:
        text += "🚗 <b>Машины:</b>\n"
        for car in user["cars"]:
            text += f"  • {car}\n"
    else:
        text += "🚗 Машин нет\n"
    
    if user["phones"]:
        text += "\n📱 <b>Телефоны:</b>\n"
        for phone in user["phones"]:
            text += f"  • {phone}\n"
    else:
        text += "\n📱 Телефонов нет\n"
    
    if user["houses"]:
        text += "\n🏠 <b>Недвижимость:</b>\n"
        for house in user["houses"]:
            text += f"  • {house}\n"
    else:
        text += "\n🏠 Недвижимости нет\n"
    
    if user["businesses"]:
        text += "\n🏢 <b>Бизнесы:</b>\n"
        for biz in user["businesses"]:
            income = BUSINESSES[biz]["income"]
            text += f"  • {biz} (+{format_money(income)}/час)\n"
    else:
        text += "\n🏢 Бизнесов нет\n"
    
    await update.message.reply_text(text, parse_mode="HTML")


async def cmd_top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Топ игроков"""
    data = load_data()
    
    if not data:
        await update.message.reply_text("😢 Пока нет игроков!")
        return
    
    players = []
    for uid, user in data.items():
        total = user["balance"] + user["bank"]
        name = user.get("name", f"Игрок {uid}")
        players.append((name, total, user["level"]))
    
    players.sort(key=lambda x: x[1], reverse=True)
    
    text = "🏆 <b>Топ богачей:</b>\n\n"
    medals = ["🥇", "🥈", "🥉"]
    
    for i, (name, total, level) in enumerate(players[:10]):
        medal = medals[i] if i < 3 else f"{i+1}."
        text += f"{medal} {name} — {format_money(total)} (ур. {level})\n"
    
    await update.message.reply_text(text, parse_mode="HTML")


async def cmd_collect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Собрать накопленный доход с бизнесов"""
    user = get_user(update.effective_user.id)
    
    if not user["businesses"]:
        await update.message.reply_text("❌ У тебя нет бизнесов! Смотри /business")
        return
    
    # Считаем доход в минуту
    income_per_minute = sum(BUSINESSES[b]["income"] for b in user["businesses"])
    
    # Считаем сколько минут прошло с последнего сбора
    if user["last_collect"]:
        last = datetime.fromisoformat(user["last_collect"])
        minutes_passed = int((datetime.now() - last).total_seconds() // 60)
    else:
        minutes_passed = 60  # Первый раз даём за час
    
    if minutes_passed < 1:
        await update.message.reply_text("⏳ Доход ещё не накопился! Подожди минутку.")
        return
    
    # Максимум 24 часа накопления (1440 минут)
    minutes_passed = min(minutes_passed, 1440)
    
    total_income = income_per_minute * minutes_passed
    user["balance"] += total_income
    user["last_collect"] = datetime.now().isoformat()
    update_user(update.effective_user.id, user)
    
    hours = minutes_passed // 60
    mins = minutes_passed % 60
    time_text = ""
    if hours > 0:
        time_text += f"{hours}ч "
    if mins > 0:
        time_text += f"{mins}м"
    
    await update.message.reply_text(
        f"💰 Собрал доход с бизнесов!\n\n"
        f"⏱ Накопилось за: {time_text}\n"
        f"📈 Доход/мин: {format_money(income_per_minute)}\n"
        f"💵 Получено: {format_money(total_income)}"
    )


async def cmd_promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Активировать промокод"""
    user = get_user(update.effective_user.id)
    
    if not context.args:
        await update.message.reply_text("❌ Укажи промокод: /promo КОД")
        return
    
    promo = context.args[0].upper()
    
    if promo not in PROMOCODES:
        await update.message.reply_text("❌ Неверный промокод!")
        return
    
    used_promos = get_used_promos(update.effective_user.id)
    if promo in used_promos:
        await update.message.reply_text("❌ Ты уже использовал этот промокод!")
        return
    
    reward = PROMOCODES[promo]["money"]
    desc = PROMOCODES[promo]["description"]
    
    user["balance"] += reward
    update_user(update.effective_user.id, user)
    add_used_promo(update.effective_user.id, promo)
    
    await update.message.reply_text(
        f"✅ Промокод активирован!\n\n"
        f"🎁 {desc}\n"
        f"💰 Получено: {format_money(reward)}"
    )


# ============ ОБРАБОТЧИКИ КНОПОК ============

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий кнопок"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id
    user = get_user(user_id)
    
    # Меню
    if data == "menu_jobs":
        await query.message.reply_text("Используй /jobs для просмотра профессий")
    elif data == "menu_shop":
        await query.message.reply_text("Используй /shop для просмотра магазинов")
    elif data == "menu_casino":
        await query.message.reply_text("Используй /casino [сумма] для игры")
    elif data == "menu_bank":
        await query.message.reply_text("Используй /deposit или /withdraw")
    elif data == "menu_profile":
        await query.message.reply_text("Используй /profile для просмотра профиля")
    elif data == "menu_help":
        await query.message.reply_text("Используй /help для помощи")
    
    # Выбор работы
    elif data.startswith("job_"):
        if data.startswith("job_locked_"):
            level_needed = data.split("_")[2]
            await query.answer(f"🔒 Нужен {level_needed} уровень!", show_alert=True)
        else:
            job_name = data.replace("job_", "")
            if job_name in JOBS:
                user["job"] = job_name
                update_user(user_id, user)
                salary = JOBS[job_name]["salary"]
                await query.message.reply_text(f"✅ Ты устроился на работу: {job_name}!\n💰 Зарплата: {format_money(salary)}/смена\n\nТеперь используй /work")
    
    # Покупка машины
    elif data.startswith("buycar_"):
        car_name = data.replace("buycar_", "")
        if car_name in CARS:
            price = CARS[car_name]
            if car_name in user["cars"]:
                await query.answer("У тебя уже есть эта машина!", show_alert=True)
            elif user["balance"] < price:
                await query.answer(f"Не хватает денег! Нужно: {format_money(price)}", show_alert=True)
            else:
                user["balance"] -= price
                user["cars"].append(car_name)
                update_user(user_id, user)
                await query.message.reply_text(f"✅ Ты купил {car_name} за {format_money(price)}!")
    
    # Покупка телефона
    elif data.startswith("buyphone_"):
        phone_name = data.replace("buyphone_", "")
        if phone_name in PHONES:
            price = PHONES[phone_name]
            if phone_name in user["phones"]:
                await query.answer("У тебя уже есть этот телефон!", show_alert=True)
            elif user["balance"] < price:
                await query.answer(f"Не хватает денег! Нужно: {format_money(price)}", show_alert=True)
            else:
                user["balance"] -= price
                user["phones"].append(phone_name)
                update_user(user_id, user)
                await query.message.reply_text(f"✅ Ты купил {phone_name} за {format_money(price)}!")
    
    # Покупка дома
    elif data.startswith("buyhouse_"):
        house_name = data.replace("buyhouse_", "")
        if house_name in HOUSES:
            price = HOUSES[house_name]
            if house_name in user["houses"]:
                await query.answer("У тебя уже есть это жильё!", show_alert=True)
            elif user["balance"] < price:
                await query.answer(f"Не хватает денег! Нужно: {format_money(price)}", show_alert=True)
            else:
                user["balance"] -= price
                user["houses"].append(house_name)
                update_user(user_id, user)
                await query.message.reply_text(f"✅ Ты купил {house_name} за {format_money(price)}!")
    
    # Покупка бизнеса
    elif data.startswith("buybiz_"):
        biz_name = data.replace("buybiz_", "")
        if biz_name in BUSINESSES:
            price = BUSINESSES[biz_name]["price"]
            income = BUSINESSES[biz_name]["income"]
            if biz_name in user["businesses"]:
                await query.answer("У тебя уже есть этот бизнес!", show_alert=True)
            elif user["balance"] < price:
                await query.answer(f"Не хватает денег! Нужно: {format_money(price)}", show_alert=True)
            else:
                user["balance"] -= price
                user["businesses"].append(biz_name)
                update_user(user_id, user)
                await query.message.reply_text(f"✅ Ты купил {biz_name} за {format_money(price)}!\n💰 Доход: {format_money(income)}/мин\n\nСобирай накопленное: /collect")
    
    # Уже куплено
    elif data in ["car_owned", "phone_owned", "house_owned", "biz_owned"]:
        await query.answer("✅ Уже куплено!", show_alert=True)
    
    # Магазины из кнопок
    elif data == "shop_cars":
        await query.message.reply_text("Используй /cars для просмотра автосалона")
    elif data == "shop_phones":
        await query.message.reply_text("Используй /phones для просмотра телефонов")
    elif data == "shop_houses":
        await query.message.reply_text("Используй /houses для просмотра недвижимости")
    elif data == "shop_business":
        await query.message.reply_text("Используй /business для просмотра бизнесов")


# ============ УСТАНОВКА КОМАНД ============

async def set_commands(app):
    """Установить команды бота для меню"""
    commands = [
        BotCommand("start", "🎮 Начать игру"),
        BotCommand("help", "❓ Помощь"),
        BotCommand("work", "💼 Работать"),
        BotCommand("bonus", "🎁 Ежедневный бонус"),
        BotCommand("jobs", "💼 Список профессий"),
        BotCommand("shop", "🏪 Магазины"),
        BotCommand("cars", "🚗 Автосалон"),
        BotCommand("houses", "🏠 Недвижимость"),
        BotCommand("business", "🏢 Бизнесы"),
        BotCommand("casino", "🎰 Казино"),
        BotCommand("profile", "👤 Профиль"),
        BotCommand("balance", "💰 Баланс"),
        BotCommand("inventory", "📦 Имущество"),
        BotCommand("top", "🏆 Топ игроков"),
        BotCommand("promo", "🎁 Промокод"),
    ]
    await app.bot.set_my_commands(commands)


# ============ ЗАПУСК ============

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Команды
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("balance", cmd_balance))
    app.add_handler(CommandHandler("profile", cmd_profile))
    app.add_handler(CommandHandler("work", cmd_work))
    app.add_handler(CommandHandler("bonus", cmd_bonus))
    app.add_handler(CommandHandler("crime", cmd_crime))
    app.add_handler(CommandHandler("jobs", cmd_jobs))
    app.add_handler(CommandHandler("shop", cmd_shop))
    app.add_handler(CommandHandler("cars", cmd_cars))
    app.add_handler(CommandHandler("phones", cmd_phones))
    app.add_handler(CommandHandler("houses", cmd_houses))
    app.add_handler(CommandHandler("business", cmd_business))
    app.add_handler(CommandHandler("deposit", cmd_deposit))
    app.add_handler(CommandHandler("withdraw", cmd_withdraw))
    app.add_handler(CommandHandler("casino", cmd_casino))
    app.add_handler(CommandHandler("dice", cmd_dice))
    app.add_handler(CommandHandler("inventory", cmd_inventory))
    app.add_handler(CommandHandler("top", cmd_top))
    app.add_handler(CommandHandler("collect", cmd_collect))
    app.add_handler(CommandHandler("promo", cmd_promo))
    
    # Кнопки
    app.add_handler(CallbackQueryHandler(button_callback))
    
    # Установка команд при запуске
    app.post_init = set_commands
    
    print("=" * 50)
    print("🎮 ЖИЗНЬ-СИМУЛЯТОР ЗАПУЩЕН!")
    print("Для остановки нажмите Ctrl+C")
    print("=" * 50)
    
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()