from aiogram import executor
import handlers  
from config import dp

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)