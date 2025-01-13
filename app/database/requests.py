from app.database.models import async_session
from app.database.models import User, Channel, Post, Role
from sqlalchemy import select, update, delete, or_
from kutter import generateRandomString as gen_rnd

async def set_user(tg_id):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        #print (f"Пользователь [{user.id}] с ID {user[0].tg_id} уже в БД")
        if not user:
            session.add(User(tg_id=tg_id))
            await session.commit()

async def set_channel(tg_id, name):
    async with async_session() as session:
        channel = await session.scalar(select(Channel).where(Channel.tg_id == tg_id))
        #print (f"Группа [{channel.id}] с ID {channel.tg_id} // {channel.name} уже в БД")
        if not channel:
            session.add(Channel(tg_id=tg_id, name=name))
            await session.commit()

async def set_role(user_id, channel_id, role):
    async with async_session() as session:
        roles = await session.scalar(select(Role).where(Role.user_id == user_id, Role.channel_id == channel_id,
                                                        Role.role == role))
        #print(f"Для пользователя [{role.user_id}] в группе [{role.channel_id}] установлена роль {role.role} и ключ [{role.key}]")
        if not roles:
            session.add(Role(user_id = user_id, channel_id=channel_id, role=role, key=gen_rnd(32)))
            await session.commit()

async def set_post(channel_id, image_id, caption):
    async with async_session() as session:
        posts = await session.scalar(select(Post).where(Post.channel_id == channel_id, Post.image_id == image_id, Post.caption == caption)
                                                        )
        #print(f"Для пользователя [{role.user_id}] в группе [{role.channel_id}] установлена роль {role.role} и ключ [{role.key}]")
        if not posts:
            session.add(Post(channel_id = channel_id, caption=caption, image_id=image_id))
            await session.commit()

async def get_user(tg_id):
    async with async_session() as session:
        user = await session.scalars(select(User).where(User.tg_id == tg_id))
        if user:
            for u in user:
                return u
        if not user:
            print(f"Пользователя с {tg_id} нет в БД")

async def get_channel(tg_id):
    async with async_session() as session:
        channel = await session.scalars(select(Channel).where(Channel.tg_id == tg_id))
        if channel:
            for c in channel:
                return c
        if not channel:
            print(f"Канала с {tg_id} нет в БД")

async def get_post(image_id):
    async with async_session() as session:
        post = await session.scalars(select(Post).where(Post.image_id == image_id))
        if post:
            for c in post:
                return c
        if not post:
            print(f"Поста {id} нет в БД")

async def get_channel_by_db_id(db_id):
    async with async_session() as session:
        channels = await session.scalars(select(Channel).where(Channel.id==db_id))
        if channels:
            for c in channels:
                return c
        if not channels:
            print(f"Канала с {db_id} нет в БД")

async def get_user_by_db_id(db_id):
    async with async_session() as session:
        users = await session.scalars(select(User).where(User.id==db_id))
        if users:
            for u in users:
                return u

async def get_post_by_db_id(db_id):
    async with async_session() as session:
        post = await session.scalars(select(Post).where(Post.id==db_id))
        if post:
            for c in post:
                return c
        if not post:
            print(f"Поста с {db_id} нет в БД")

async def get_all_roles():
    async with async_session() as session:
        roles = await session.scalars(
            select(Role).where(Role.user_id != ""))
        if roles :
            return roles
        if not roles:
            print(f"Нет ролей в БД")

async def get_roles_by_user(user_tg_id, role):
    user = await get_user(user_tg_id)
    db_id = user.id
    print("User ID", db_id)
    async with async_session() as session:
        roles = await session.scalars(select(Role).where(Role.user_id == db_id, or_(Role.role == role, Role.role == 'creator')))
        if roles == None:
            print(f"{user.id} не является {role} какого-либо канала")
        else:
            for r in roles:
                return r

async def get_channels_by_user(user_tg_id, role):
    user = await get_user(user_tg_id)
    db_id = user.id
    print("User ID", db_id)
    async with async_session() as session:
        roles = await session.scalars(select(Role).where(Role.user_id == db_id, or_(Role.role == role, Role.role == 'creator')))
        if roles == None:
            print(f"{user.id} не является {role} какого-либо канала")
        else:
            channels_= []
            for r in roles:
                printt = await session.scalars(select(Channel).where(r.channel_id==Channel.id))
                print("role")
                for p in printt:
                    channels_.append(p)
                    print(p.id, p.tg_id, p.name)
            return channels_

