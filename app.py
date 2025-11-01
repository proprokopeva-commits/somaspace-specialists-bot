from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    FSInputFile, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from pathlib import Path
import asyncio
import os
import csv
import logging
import sys

# === Логирование ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("somaspace-specialists-bot")

# === Токен ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set. Add it in Railway → Settings → Variables.")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# === Главное меню ===
def get_main_menu():
    buttons = [
        [KeyboardButton(text="🌱 Что такое SõmaSpace")],
        [KeyboardButton(text="📋 Условия участия")],
        [KeyboardButton(text="🧭 Пройти анкету")],
        [KeyboardButton(text="💬 Канал для специалистов")],
        [KeyboardButton(text="❓ Задать вопрос")],
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

WELCOME_CAPTION = (
    "Привет 🌿\n\n"
    "<b>SõmaSpace</b> — пространство для специалистов, "
    "которые работают с людьми бережно, профессионально и живо.\n\n"
    "Мы соединяем психологов, коучей и юристов с компаниями, "
    "где забота о людях становится культурой.\n\n"
    "Хотите узнать, как присоединиться?"
)

# === Состояния анкеты ===
class SpecialistForm(StatesGroup):
    name = State()
    approach = State()
    experience = State()
    contact = State()

def save_specialist(user_id, name, approach, experience, contact):
    os.makedirs("data", exist_ok=True)
    file_path = "data/specialists.csv"
    file_exists = os.path.isfile(file_path)
    with open(file_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["user_id", "name", "approach", "experience", "contact"])
        writer.writerow([user_id, name, approach, experience, contact])
    logger.info("Saved specialist: %s | %s | %s", name, approach, contact)

# === /start ===
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    base_path = Path(__file__).parent
    image_path = base_path / "files" / "start_image.jpg"  # добавь картинку сюда

    if image_path.exists():
        photo = FSInputFile(image_path)
        await bot.send_photo(
            chat_id=message.chat.id,
            photo=photo,
            caption=WELCOME_CAPTION,
            parse_mode="HTML",
            reply_markup=get_main_menu(),
        )
    else:
        await message.answer(WELCOME_CAPTION, parse_mode="HTML", reply_markup=get_main_menu())

# === /menu ===
@dp.message(Command("menu"))
async def menu_cmd(message: types.Message):
    await message.answer("Главное меню 👇", reply_markup=get_main_menu())

# === Что такое SõmaSpace ===
@dp.message(F.text == "🌱 Что такое SõmaSpace")
async def what_is_soma(message: types.Message):
    text = (
        "<b>SõmaSpace</b> — это не просто платформа, а живое пространство, "
        "где специалист остаётся в контакте с собой и другими.\n\n"
        "🌀 Мы объединяем профессионалов, которые помогают людям и командам "
        "расти без потери человечности.\n\n"
        "Здесь важны не KPI, а <b>живые метрики</b>: присутствие, связь и устойчивость."
    )
    await message.answer(text, parse_mode="HTML")

# === Условия участия ===
@dp.message(F.text == "📋 Условия участия")
async def conditions(message: types.Message):
    text = (
        "💫 Для участия важно:\n"
        "• профильное образование или обучение в признанном подходе,\n"
        "• личная терапия и супервизия,\n"
        "• готовность к сотрудничеству и обмену опытом.\n\n"
        "Мы предлагаем партнёрскую модель: поток клиентов, поддержка, развитие и живая среда."
    )
    await message.answer(text, parse_mode="HTML")

# === Пройти анкету ===
@dp.message(F.text == "🧭 Пройти анкету")
async def start_form(message: types.Message, state: FSMContext):
    await message.answer("Начнём 🌿 Как вас зовут?", parse_mode="HTML")
    await state.set_state(SpecialistForm.name)

@dp.message(SpecialistForm.name)
async def form_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("В каком подходе вы работаете? (например, гештальт, коучинг, телесная терапия)", parse_mode="HTML")
    await state.set_state(SpecialistForm.approach)

@dp.message(SpecialistForm.approach)
async def form_approach(message: types.Message, state: FSMContext):
    await state.update_data(approach=message.text)
    await message.answer("Сколько часов практики у вас за плечами?", parse_mode="HTML")
    await state.set_state(SpecialistForm.experience)

@dp.message(SpecialistForm.experience)
async def form_experience(message: types.Message, state: FSMContext):
    await state.update_data(experience=message.text)
    await message.answer("Как с вами можно связаться? (email, телефон, Telegram)", parse_mode="HTML")
    await state.set_state(SpecialistForm.contact)

@dp.message(SpecialistForm.contact)
async def form_contact(message: types.Message, state: FSMContext):
    data = await state.get_data()
    name = data.get("name")
    approach = data.get("approach")
    experience = data.get("experience")
    contact = message.text
    save_specialist(message.from_user.id, name, approach, experience, contact)
    await message.answer(
        "Спасибо 🌱\n\n"
        "Мы получили вашу анкету. Если формат подойдёт — свяжемся с вами лично.\n\n"
        "А пока можно присоединиться к каналу для специалистов 👇",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Канал SõmaSpace • Специалисты", url="https://t.me/somaspace_pro")]
            ]
        ),
    )
    await state.clear()

# === Канал для специалистов ===
@dp.message(F.text == "💬 Канал для специалистов")
async def channel_link(message: types.Message):
    text = (
        "В канале — тексты, кейсы и практики о профессии и живом присутствии в работе.\n\n"
        "Присоединяйтесь, чтобы быть в потоке <b>SõmaSpace</b> 🌿"
    )
    link_button = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Открыть канал", url="https://t.me/somaspace_pro")]]
    )
    await message.answer(text, parse_mode="HTML", reply_markup=link_button)

# === Задать вопрос ===
@dp.message(F.text == "❓ Задать вопрос")
async def ask_question(message: types.Message):
    await message.answer(
        "Напишите свой вопрос — мы ответим лично или направим к нужному человеку 💫",
        parse_mode="HTML",
    )

# === Запуск ===
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_my_commands([
        BotCommand(command="start", description="Начать"),
        BotCommand(command="menu", description="Главное меню"),
    ])
    logger.info("SõmaSpace Specialists Bot started ✅")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
