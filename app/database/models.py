from sqlalchemy import BigInteger, String, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
import aiosqlite

engine = create_async_engine(url='sqlite+aiosqlite:///db.sqlite3')

async_session = async_sessionmaker(engine)

class Base(AsyncAttrs, DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int]=mapped_column(primary_key=True)
    tg_id = mapped_column(BigInteger)

class Channel(Base):
    __tablename__ = 'channels'
    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id = mapped_column(BigInteger)
    name: Mapped[str] = mapped_column(String(32))


class Post(Base):
    __tablename__ = 'posts'
    id: Mapped[int] = mapped_column(primary_key=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey('channels.id'))
    image_id = mapped_column(BigInteger)
    caption: Mapped[str] = mapped_column(String(256))

class Role(Base):
    __tablename__ = 'roles'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id = mapped_column(ForeignKey('users.id'))
    channel_id = mapped_column(ForeignKey('channels.id'))
    role: Mapped[str] = mapped_column(String(32))
    key: Mapped[str] = mapped_column(String(32))


async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)