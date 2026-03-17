import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

TOKEN = "8029553969:AAEXO5qiduKijjBpMJrCiDOPMUxJfC-XD_Q"

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Bienvenue 👋 Ton bot fonctionne !")

@dp.message()
async def echo(message: types.Message):
    await message.answer(f"Tu as dit : {message.text}")

async def main():
    await dp.start_polling(bot)
