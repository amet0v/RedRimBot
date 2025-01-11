import os.path
import pickle

from aiogram import Bot, types, Router, F
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import FSInputFile

from filters.chat_type import ChatTypeFilter
from config import texts

#with open("token.txt", "r") as t:
#    token = t.read()
#token = "907506430:AAH0f1oBIs8YCUqu8Z1GehNjrFPE9LPCL5k"
token = "6907506430:AAH0f1oBIs8YCUqu8Z1GehNjrFPE9LPCL5k"
bot = Bot(token=token)

router = Router()
sg = -1002145835504
pinned_chats = [119, 116, 86, 102, None]


class Order:
    def __init__(self, customer, topic):
        self.customer = customer
        self.topic = topic

    def __str__(self):
        return f"customer id: {self.customer}\ntopic id: {self.topic}"


class OrderManagement(StatesGroup):
    approve_closing = State()
    set_price = State()
    change_topic_name = State()


o_buttons = [
        [types.InlineKeyboardButton(
            text="⬅️ Назад", callback_data="back_to_menu")],
        [types.InlineKeyboardButton(
            text="🖼 Наши работы", callback_data="portfolio")],
        [types.InlineKeyboardButton(
            text="📞 Контакты", callback_data="contacts")]
    ]


@router.callback_query(F.data == "change_topic_name")
async def cb_close_order(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Подпишите заказ или введите \"`Отмена`\"",
                                  parse_mode=ParseMode.MARKDOWN_V2)
    await state.set_state(OrderManagement.change_topic_name)


@router.callback_query(F.data == "close_order")
async def cb_close_order(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите \"`Закрыть заказ`\"",
                                  parse_mode=ParseMode.MARKDOWN_V2)
    await state.set_state(OrderManagement.approve_closing)


@router.callback_query(F.data == "send_price")
async def cb_send_price(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Укажите цену или введите \"`Отмена`\"",
                                  parse_mode=ParseMode.MARKDOWN_V2)
    await state.set_state(OrderManagement.set_price)


@router.callback_query(F.data == "create_order")
async def cb_create_order(callback: types.CallbackQuery):
    #проверка на бан
    blacklist = []
    with open("config/blacklist.txt", "r") as f:
        for line in f:
            if line != "":
                blacklist.append(int(line))
    if callback.from_user.id in blacklist:
        await callback.message.answer("Вас заблокировали")
        return
    #если все ок
    file_name = "orders/order-" + str(callback.from_user.id) + ".pickle"
    if os.path.exists(file_name):
        await callback.message.answer("У вас уже открыт заказ")
    else:
        with open("config/order_id.txt", "r") as f:
            order_id = f.read()
        new_topic = await bot.create_forum_topic(sg, name="Заказ №" + order_id + " - " + str(callback.from_user.full_name),
                                                 icon_custom_emoji_id="5350452584119279096")
        order_id = int(order_id) + 1
        with open("config/order_id.txt", "w") as f:
            f.write(str(order_id))
        new_order = Order(callback.from_user.id, new_topic.message_thread_id)
        with open(file_name, 'wb') as f:
            pickle.dump(new_order, f)
        # knopka
        buttons = [
            [
                types.InlineKeyboardButton(
                    text="Подписать заказ", callback_data="change_topic_name")
            ],
            [
                types.InlineKeyboardButton(
                    text="Указать цену", callback_data="send_price"),
                types.InlineKeyboardButton(
                    text="Закрыть заказ", callback_data="close_order")
            ]
        ]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
        await bot.send_message(sg, f"Управление заказом\n" + "username: @" + str(callback.from_user.username) + "\n" + str(new_order),
                               new_order.topic, reply_markup=keyboard)
        # ne knopka
    o_keyboard = types.InlineKeyboardMarkup(inline_keyboard=o_buttons)
    await bot.edit_message_media(types.InputMediaPhoto(media=FSInputFile("images/order.png")),
                                 callback.message.chat.id, callback.message.message_id)
    await bot.edit_message_caption(callback.message.chat.id, callback.message.message_id, caption=texts.o_text,
                                   parse_mode=ParseMode.MARKDOWN_V2)
    await bot.edit_message_reply_markup(callback.message.chat.id, callback.message.message_id,
                                        reply_markup=o_keyboard)
        #await callback.message.answer("Вы открыли заказ")


@router.message(OrderManagement.change_topic_name)
async def cmd_change_topic_name(message: types.Message, bot: Bot, state: FSMContext):
    cancel_text = "Отмена"
    # topic.message_thread_id = message.message_thread_id
    if message.text != cancel_text:
        try:
            await bot.edit_forum_topic(sg, message.message_thread_id, message.text)
            await state.clear()
        except TelegramBadRequest as ex:
            if ex.message == "Bad Request: TOPIC_NOT_MODIFIED":
                await message.answer("Название чата не было изменено\.\nПопробуйте еще раз или введите \"`Отмена`\"",
                                     parse_mode=ParseMode.MARKDOWN_V2)
    else:
        await message.answer("Название чата не было изменено.\nВозврат к чату с клиентом")
        await state.clear()


@router.message(OrderManagement.approve_closing)
async def cmd_close_approved(message: types.Message, bot: Bot, state: FSMContext):
    to_delete = None
    approve_text = "Закрыть заказ"
    if message.text == approve_text:
        await message.answer("✅ Заказ закрыт")  # исполнителю
        for file in os.listdir("orders"):
            with open("orders/" + file, 'rb') as f:
                loop_data = pickle.load(f)
                if loop_data.topic == message.message_thread_id:
                    await bot.send_message(loop_data.customer,
                                           "✅ Дизайнер закрыл ваш заказ.\nСпасибо за то что выбрали нас 🤗")  # заказчику
                    to_delete = "orders/" + file
        await bot.edit_message_reply_markup(sg, message.message_thread_id+1, reply_markup=None)
        await bot.close_forum_topic(sg, message.message_thread_id)
        await state.clear()
        if os.path.exists(to_delete):
            os.remove(to_delete)
    else:
        if not message.from_user.is_bot:
            await message.answer("Заказ не был закрыт.\nВозврат к чату с клиентом")
            await state.clear()


@router.message(OrderManagement.set_price)
async def cmd_price_approved(message: types.Message, bot: Bot, state: FSMContext):
    cancel_text = "Отмена"
    if message.text != cancel_text:
        price_text = "💲Стоимость заказа: " + message.text + texts.price_tail
        await message.answer("Вы отправили заказчику текст:\n\n" + price_text, parse_mode=ParseMode.MARKDOWN_V2)
        for file in os.listdir("orders"):
            with open("orders/" + file, 'rb') as f:
                loop_data = pickle.load(f)
                if loop_data.topic == message.message_thread_id:
                    await bot.send_message(loop_data.customer, price_text, parse_mode=ParseMode.MARKDOWN_V2)
                    break
            f.close()
    else:
        await message.answer("Возврат к чату с клиентом")
    await state.clear()


@router.message(StateFilter(None), ChatTypeFilter(chat_type='private'))
async def receive_customer_message(message: types.Message):
    if not message.from_user.is_bot:
        file_name = "orders/order-" + str(message.from_user.id) + ".pickle"
        if os.path.exists(file_name):
            with open(file_name, 'rb') as f:
                order_data = pickle.load(f)
            await bot.forward_message(sg, message.chat.id, message.message_id, message_thread_id=order_data.topic)
            await message.react([types.ReactionTypeEmoji(emoji="⚡")])
        else:
            await message.answer("У вас не открыт заказ")


@router.message(StateFilter(None), ChatTypeFilter(chat_type='supergroup'))
async def receive_designer_message(message: types.Message):
    if not message.from_user.is_bot:
        for file in os.listdir("orders"):
            with open("orders/" + file, 'rb') as f:
                loop_data = pickle.load(f)
                if loop_data.topic == message.message_thread_id:
                    if message.message_thread_id not in pinned_chats:
                        await bot.copy_message(loop_data.customer, message.chat.id, message.message_id)
                        await message.react([types.ReactionTypeEmoji(emoji="⚡")])
