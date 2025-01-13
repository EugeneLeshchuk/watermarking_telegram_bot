from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

class AddImage(StatesGroup):
    channel_id = State()

