import io
import types
import aiohttp
from aiogram.client.session.aiohttp import AiohttpSession
import cv2
import numpy as np
from PIL import Image
from aiogram import F, Bot as bot, Router, Bot
from aiogram.enums import ParseMode
from aiogram.methods import get_chat
from aiogram.filters import CommandStart, Command, ChatMemberUpdatedFilter, JOIN_TRANSITION, IS_NOT_MEMBER, IS_MEMBER, StateFilter
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, FSInputFile, CallbackQuery, ChatJoinRequest, ChatMemberUpdated, BufferedInputFile, \
    InputFile
from kutter import encode, decode, secret_to_bits
from io import BytesIO

from config import TOKEN
import app.keyboards as kb
import app.states as st
import app.database.requests as rq

router = Router()

#session = AiohttpSession(proxy='http://proxy.server:3128')
bot = Bot(token=TOKEN)

class Post(StatesGroup):
    channel = State()
    file = State()
    search = State()

@router.callback_query(F.data.startswith('administration'))
async def choose_channel(callback: CallbackQuery, state:FSMContext):
    await state.set_state(Post.channel)
    print(await state.get_state())
    await callback.answer('')
    await callback.message.answer('Выберите канал', reply_markup=await kb.channels(callback.from_user.id))

@router.callback_query(F.data.startswith('find_post'))
async def choose_channel(callback: CallbackQuery, state:FSMContext):
    await state.set_state(Post.search)
    print(await state.get_state())
    await callback.answer('')
    await callback.message.answer('Введите ID поста:')

@router.message(Post.search)
async def show_post(message: Message, state:FSMContext):
    print(await state.get_state())
    print(f'Запрошен пост {int(message.text)}')
    post = await rq.get_post_by_db_id(int(message.text))
    await message.answer(f'Запрошен пост с ID {int(message.text)}')
    if not post:
        await message.answer("Поста с таким ID не существует.")
    if post:
        channel = await rq.get_channel_by_db_id(post.channel_id)
        channels = await rq.get_channels_by_user(message.from_user.id, 'member')
        if not channels:
            await message.answer("Вы не являетесь подписчиком какого-либо канала.")
        subscribed_channel = None
        for c in channels:
            if c.id == channel.id:
                subscribed_channel = c
                #(dir1 + "/" + i, dir2 + "/" + j, j, ".jpg", .2, 100)
                file_in_io = io.BytesIO()
                file_in_io_2 = io.BytesIO()
                photo = await bot.get_file(post.image_id)
                ph = await bot.download_file(photo.file_path, file_in_io)
                print(type(ph))
                result = ph.read()
                print(type(result))
                #img = cv2.imdecode(np.fromstring(file_in_io.getvalue()))
                #cv2.imshow('image',img)

                key = await rq.get_roles_by_user(message.from_user.id, 'member')

                print("This is key", key.key)
                #print(secret_to_bits(key.key))

                container = encode(result, "", key.key, ".png", .2, 100)
                #container.show()
                container.save(file_in_io_2,"png")
                b = file_in_io_2.getvalue()
                container.close()
                #print(container.read())
                #img: bytes = await bot.get
                await message.answer_document(document=(BufferedInputFile(b, filename='result.png')), caption=post.caption)
                break
        if not subscribed_channel:
            await message.answer("У вас нет доступа к этому каналу.")

    await state.set_state(None)

#@router.message()
#async def encode(reply: types:)


@router.callback_query(Post.channel)
async def choose_image(callback: CallbackQuery, state:FSMContext):
    print(await state.get_state())
    await state.update_data(channel=callback.data.split("_")[1])
    await state.set_state(Post.file)
    print(callback.data.split("_")[1])

    await callback.answer('')
    await callback.message.answer('Выберите изображение и напишите к нему текст:')

@router.message(Post.file)
async def make_post(message: Message, state:FSMContext):
    if not message.document:
        print ("ERROR-01: No document in user's message")
        await state.set_state(Post.file)
        await message.answer("Пожалуйста, прикрепите изображение как файл.")
    if message.caption == None:
        print ("ERROR-02: No caption in user's message")
        await state.set_state(Post.file)
        await message.answer("Изображение не может быть без текста.")
    else:
        await state.update_data(file=message)
        data = await state.get_data()
        await state.set_state(None)
        channel_bd_id = await rq.get_channel(data["channel"])
        print(channel_bd_id.id, data["file"].document.file_id,  data["file"].caption)
        await rq.set_post(channel_bd_id.id, data["file"].document.file_id, data["file"].caption)
        post = await rq.get_post(data["file"].document.file_id)
        await message.answer_document(text = f"[{post.id}] / {post.image_id} / \n {post.caption}", document=post.image_id, reply_markup= await kb.menu())
        channel = await rq.get_channel_by_db_id(post.channel_id)
        await bot.send_message(channel.tg_id, text=
        f"<a href='https://t.me/content_board_bot'> Вышел новый пост с ID [{post.id}]</a>",
                               parse_mode=ParseMode.HTML)


@router.chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))
async def on_user_join(event: ChatMemberUpdated):
    print("Hello_World")
    await event.bot.send_message(event.new_chat_member.user.id,f"Привет, {event.new_chat_member.user.first_name}! "
                                                               f"На странице этого бота ты сможешь просматривать эксклюзивные авторские посты.\n"
                                                               f"Оповещения о новых постах будут приходить в канале автора.")
    await rq.set_user(event.new_chat_member.user.id)
    user = await rq.get_user(event.new_chat_member.user.id)
    channel = await rq.get_channel(event.chat.id)
    if user and channel:
        await rq.set_role(user.id, channel.id, 'member')
        print(f"{user.id}/{user.tg_id} теперь участник группы {channel.id}/{channel.tg_id}")


@router.channel_post(F.text =='@content_board_bot')
async def is_owner_command(message: Message):
    if message.chat.type == "channel":
        print("1")
        is_owner = await is_group_owner(message)

        if is_owner[0]:
            await rq.set_user(is_owner[0])
            await rq.set_channel(is_owner[1], is_owner[2])
            user = await rq.get_user(is_owner[0])
            channel = await rq.get_channel(is_owner[1])
            if user and channel:
                await rq.set_role(user.id, channel.id, 'creator')
                print(f"{user.id}/{user.tg_id} теперь владелец группы {channel.id}/{channel.tg_id}")
                await bot.send_message(user.tg_id, f"Привет, группа {channel.name} добавлена в БД", reply_markup=await kb.menu())
                await bot.send_message(channel.tg_id, text=
                "<a href='https://t.me/content_board_bot'> Для подписки на контент креатора нажмите сюда</a>", parse_mode=ParseMode.HTML)

            else:
                print("Администратор не найден")

async def is_group_owner(message: Message):
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        chat_title = message.chat.title
        print(user_id, chat_id, chat_title)
        member = await bot.get_chat_member(chat_id, user_id)
        if member.status == 'creator':
            return user_id, chat_id, chat_title
        else:
            return False

    except Exception as e:
        await message.answer(f"Error checking group owner: {e}")
        return False

@router.message(StateFilter(None))
async def help_(message: Message, state:FSMContext):
    if message.forward_origin == None:
        await message.answer('Чтобы выложить новый пост:\n1. Добавьте бота в администраторы канала.'
                             '\n2. Позовите его в канале с помощью команды @content_board_bot.'
                             '\n3. В чате с ботом выберите "Управление каналом."'
                             '\n4. В списке доступных каналов выберите канал, куда хотите опубликовать пост.'
                             '\n5. Отправьте боту изображение как ФАЙЛ с подписью. Готово!', reply_markup=await kb.menu())
    else:
        if message.photo == None:
            await message.answer("Пересланное сообщение не содержит изображения.", reply_markup=await kb.menu())
        else:
            await message.answer("Тут есть фото.", reply_markup=await kb.menu())
            file_in_io = io.BytesIO()
            photo = await bot.get_file(message.photo[-1].file_id)
            ph = await bot.download_file(photo.file_path, file_in_io)
            print(type(ph))
            result = ph.read()
            print(type(result))
            # img = cv2.imdecode(np.fromstring(file_in_io.getvalue()))
            # cv2.imshow('image',img)
            text = decode(result)
            print(f"Decoded\n{text}")
            similarity = 0
            most_similar_string=""
            channel_id = -1
            leaked_user_id = -1
            roles = await rq.get_all_roles()
            for r in roles:
                current_similarity=0
                current_string = secret_to_bits(r.key)
                #print(r.key)
                #print(current_string)
                for current_bit in range(len(text)):
                    if current_string[current_bit]==text[current_bit]:
                        current_similarity+=1
                if current_similarity >= similarity:
                    similarity = current_similarity
                    most_similar_string = current_string
                    leaked_user_id = r.user_id
                    channel_id = r.channel_id
                print(current_similarity)
                print(f"{current_string}\n"
                      f"{current_similarity / len(text)}\n")

            print("Most similar string:")
            print(most_similar_string,"\n")
            member_id = await rq.get_user_by_db_id(leaked_user_id)
            member_chat_id = await rq.get_channel_by_db_id(channel_id)
            print(member_id.tg_id)
            print(member_chat_id.tg_id)
            member = await bot.get_chat_member(member_chat_id.tg_id, member_id.tg_id)
            if member:
                #await message.answer(f"С вероятностью {similarity/ len(text)} пост был отправлен пользователем {member.user.first_name}.")
                await message.answer(
                    f"Вероятнее всего, пост был отправлен пользователем {member.user.first_name}.")
            else:
                await message.answer(f"С вероятностью {similarity / len(most_similar_string)} пост был отправлен пользователем с ID {member_chat_id}. "
                                     f"\nВ данный момент он не является участником чата.")

@router.message(F.data.startswith('/post'))
async def get_photo(message: Message):
    await message.answer_document(document='BQACAgIAAxkBAAMSZ1lFIOkbLaAmt8OV0tVPPT77yjsAArZXAAI5m9FKj8a1PS_loFs2BA')


#@router.message(F.document)
#async def how_are_you(message: Message):
#    await message.answer(f'ID фото: {message.document.file_id}')

#@router.message(Command('get_file'))
#async def get_photo(message: Message):
#    await message.answer_document(document='BQACAgIAAxkBAAMSZ1lFIOkbLaAmt8OV0tVPPT77yjsAArZXAAI5m9FKj8a1PS_loFs2BA')