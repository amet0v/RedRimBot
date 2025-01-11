import os.path

from aiogram import Bot, types
from aiogram import F, Router
from aiogram.types import FSInputFile
from aiogram.utils.media_group import MediaGroupBuilder

#with open("token.txt", "r") as t:
#    token = t.read()
token = "6907506430:AAH0f1oBIs8YCUqu8Z1GehNjrFPE9LPCL5k"
bot = Bot(token=token)

router = Router()

navigate_buttons = [
    [types.InlineKeyboardButton(
            text="⬅️ Назад", callback_data="nav_back"),
        types.InlineKeyboardButton(
            text="➡️ Вперед", callback_data="nav_next")]
]

start_buttons = [
    [types.InlineKeyboardButton(
            text="➡️ Вперед", callback_data="nav_next")]
]

end_buttons = [
    [types.InlineKeyboardButton(
            text="⬅️ Назад", callback_data="nav_back")]
]


@router.callback_query(F.data == "marketplace")
async def cb_marketplace(callback: types.CallbackQuery, slide=0):
    path = "images/marketplace/"
    array = os.listdir(path)
    array.sort()
    category = "Маркетплейсы"
    mg_array = get_pics(array, path)
    await send_pics(category, mg_array, slide, callback)


@router.callback_query(F.data == "banners")
async def cb_banners(callback: types.CallbackQuery, slide=0):
    path = "images/banners/"
    array = os.listdir(path)
    category = "Баннеры"
    mg_array = get_pics(array, path)
    await send_pics(category, mg_array, slide, callback)


def get_pics(array, path):
    mg_array = []
    media_group = MediaGroupBuilder()
    step = 6
    for i in range(0, len(array), step):
        for j in range(i, i + step, 1):
            if j < len(array):
                media_group.add(type="photo", media=FSInputFile(path + array[j]))
        mg_array.append(media_group.build())
        media_group = MediaGroupBuilder()
    return mg_array


async def send_pics(category, mg_array, slide, callback: types.CallbackQuery):
    if slide == 0:
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=start_buttons)
    elif slide == len(mg_array) - 1:
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=end_buttons)
    else:
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=navigate_buttons)
    if slide < len(mg_array):
        await callback.message.answer_media_group(mg_array[slide])
        await callback.message.answer(f"{category} {str(slide + 1)}", reply_markup=keyboard)


@router.callback_query(F.data == "nav_next")
async def cb_nav_next(callback: types.CallbackQuery):
    text = callback.message.text.split()
    step = 6
    for i in range(step + 1):
        await bot.delete_message(callback.message.chat.id, callback.message.message_id - i)
    if text[0] == "Маркетплейсы":
        await cb_marketplace(callback, int(text[1]))
    if text[0] == "Баннеры":
        await cb_banners(callback, int(text[1]))


@router.callback_query(F.data == "nav_back")
async def cb_nav_back(callback: types.CallbackQuery):
    text = callback.message.text.split()
    step = 6
    for i in range(step + 1):
        try:
            await bot.delete_message(callback.message.chat.id, callback.message.message_id - i)
        except:
            pass
    if text[0] == "Маркетплейсы":
        await cb_marketplace(callback, int(text[1]) - 2)
    if text[0] == "Баннеры":
        await cb_banners(callback, int(text[1]) - 2)
