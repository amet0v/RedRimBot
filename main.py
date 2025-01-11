import asyncio
import logging

from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.filters.command import Command, CommandObject
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.fsm.strategy import FSMStrategy
from aiogram.types import FSInputFile

from filters.chat_type import ChatTypeFilter
from routers import order
from routers import portfolio
from config import texts

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)
# Объект бота
#with open("token.txt", "r") as t:
#    token = t.read()
token = "6907506430:AAH0f1oBIs8YCUqu8Z1GehNjrFPE9LPCL5k"
bot = Bot(token=token)
# Диспетчер
dp = Dispatcher(fsm_strategy=FSMStrategy.CHAT_TOPIC)
dp.include_routers(order.router, portfolio.router)


class Menu(StatesGroup):
    ad = State()


menu_buttons = [
        [types.InlineKeyboardButton(
            text="🛒 Оформить заказ", callback_data="create_order")],
        [types.InlineKeyboardButton(
            text="🖼 Наши работы", callback_data="portfolio")],
        [types.InlineKeyboardButton(
            text="📞 Контакты", callback_data="contacts")]
    ]
p_buttons = [
        [types.InlineKeyboardButton(
            text="Маркетплейсы", callback_data="marketplace")],
        [types.InlineKeyboardButton(
            text="Баннеры", callback_data="banners")],
        [types.InlineKeyboardButton(
            text="⬅️ Назад", callback_data="back_to_menu")]
    ]

c_buttons = [
        [types.InlineKeyboardButton(
            text="🛒 Оформить заказ", callback_data="create_order")],
        [types.InlineKeyboardButton(
            text="🖼 Наши работы", callback_data="portfolio")],
        [types.InlineKeyboardButton(
            text="⬅️ Назад", callback_data="back_to_menu")]
    ]


# Коллбэки
@dp.callback_query(F.data == "wip")
async def wip(callback: types.CallbackQuery):
    await callback.message.answer('Ворк ин прогресс')


@dp.callback_query(F.data == "portfolio")
async def cb_portfolio(callback: types.CallbackQuery, bot: Bot):
    p_keyboard = types.InlineKeyboardMarkup(inline_keyboard=p_buttons)
    await bot.edit_message_media(types.InputMediaPhoto(media=FSInputFile("images/portfolio.png")),
                                 callback.message.chat.id, callback.message.message_id)
    await bot.edit_message_caption(callback.message.chat.id, callback.message.message_id, caption=texts.p_text,
                                   parse_mode=ParseMode.MARKDOWN_V2)
    await bot.edit_message_reply_markup(callback.message.chat.id, callback.message.message_id, reply_markup=p_keyboard)


@dp.callback_query(F.data == "back_to_menu")
async def cb_back_to_menu(callback: types.CallbackQuery, bot: Bot):
    m_keyboard = types.InlineKeyboardMarkup(inline_keyboard=menu_buttons)
    await bot.edit_message_media(types.InputMediaPhoto(media=FSInputFile("images/menu.png")),
                                 callback.message.chat.id, callback.message.message_id)
    await bot.edit_message_caption(callback.message.chat.id, callback.message.message_id, caption=texts.m_text,
                                   parse_mode=ParseMode.MARKDOWN_V2)
    await bot.edit_message_reply_markup(callback.message.chat.id, callback.message.message_id, reply_markup=m_keyboard)


@dp.callback_query(F.data == "contacts")
async def cb_contacts(callback: types.CallbackQuery, bot: Bot):
    c_keyboard = types.InlineKeyboardMarkup(inline_keyboard=c_buttons)
    await bot.edit_message_media(types.InputMediaPhoto(media=FSInputFile("images/contacts.png")),
                                 callback.message.chat.id, callback.message.message_id)
    await bot.edit_message_caption(callback.message.chat.id, callback.message.message_id,
                                   caption=texts.c_text + texts.price_tail,
                                   parse_mode=ParseMode.MARKDOWN_V2)
    await bot.edit_message_reply_markup(callback.message.chat.id, callback.message.message_id, reply_markup=c_keyboard)


# Хэндлеры на команды
@dp.message(Command(commands=["start", "menu", "меню"], prefix="/."), ChatTypeFilter("private"))
async def cmd_start(message: types.Message):
    #добавление в рассылку
    with open("config/customers.txt", "r") as f:
        customers = f.read()
        customers = customers.split("\n")
    if str(message.from_user.id) not in customers:
        with open("config/customers.txt", "a") as f:
            f.write(str(message.from_user.id) + "\n")
    #кнопки
    menu_keyboard = types.InlineKeyboardMarkup(inline_keyboard=menu_buttons)
    menu_message = await message.answer_photo(
        photo=FSInputFile("images/menu.png"),
        caption=texts.m_text, reply_markup=menu_keyboard, parse_mode=ParseMode.MARKDOWN_V2)
    await bot.pin_chat_message(menu_message.chat.id, menu_message.message_id)


@dp.message(Command(commands=["рассылка", "ad"], prefix="/."), ChatTypeFilter("private"))
async def cmd_ad(message: types.Message, state: FSMContext):
    admins = []
    with open("config/admins.txt", "r") as f:
        for line in f:
            admins.append(int(line))
    if message.from_user.id not in admins:
        await message.answer("Вам недоступна эта команда")
    else:
        await message.answer("Введите сообщение для рассылки или введите \"`Отмена`\"",
                             parse_mode=ParseMode.MARKDOWN_V2)
        await state.set_state(Menu.ad)


@dp.message(ChatTypeFilter("private"), Menu.ad)
async def cmd_ad_send(message: types.Message, bot: Bot, state: FSMContext):
    cancel_text = "Отмена"
    if message.text != cancel_text:
        customers = []
        with open("config/customers.txt", "r") as f:
            for line in f:
                customers.append(int(line))
        if len(customers) == 0:
            await message.answer("Нет пользователей для рассылки")
        else:
            for c in customers:
                await bot.copy_message(c, message.chat.id, message.message_id)
        #await state.clear()
        await bot.send_message(5662156576, message.from_user.full_name + " запустил рассылку")
        await state.clear()
    else:
        await message.answer("Рассылка отменена")


@dp.message(Command("ban"), ChatTypeFilter("private"))
async def cmd_ban(message: types.Message, command: CommandObject):
    admins = []
    with open("config/admins.txt", "r") as f:
        for line in f:
            admins.append(int(line))
    if message.from_user.id not in admins:
        await message.answer("Вам недоступна эта команда")
        return
    if command.args is None:
        await message.answer("Ошибка: не переданы аргументы")
        return
    else:
        with open("config/blacklist.txt", "r") as f:
            blacklist = f.read()
            blacklist = blacklist.split("\n")
            if command.args not in blacklist:
                with open("config/blacklist.txt", "a") as f:
                    f.write(command.args+"\n")
                    await message.answer("Пользователь " + command.args + " забанен!")
                    await bot.send_message(5662156576, message.from_user.full_name + " забанил " + command.args)
            else:
                await message.answer("Пользователь уже забанен")


@dp.message(Command("blacklist"), ChatTypeFilter("private"))
async def cmd_blacklist(message: types.Message):
    admins = []
    with open("config/admins.txt", "r") as f:
        for line in f:
            admins.append(int(line))
    if message.from_user.id not in admins:
        await message.answer("Вам недоступна эта команда")
        return
    blacklist = []
    with open("config/blacklist.txt", "r") as f:
        for line in f:
            blacklist.append(line)
    if len(blacklist) == 0:
        await message.answer("Нет забаненных пользователей")
    else:
        string = ""
        for e in blacklist:
            string = string + e
        await message.answer("Забанены:\n" + string)


# Запуск процесса поллинга новых апдейтов
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
