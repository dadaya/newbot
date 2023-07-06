import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

# Set up logging
logging.basicConfig(level=logging.INFO)

# Replace YOUR_TOKEN with your actual bot token
bot = Bot(token='5968554956:TOKEN')
dp = Dispatcher(bot)

# Handler for incoming messages
@dp.message_handler()
async def echo_message(message: types.Message):
    # Extract user information
    user = message.from_user
    username = user.username or user.first_name
    text = message.text

    # Log user's message and username
    logging.info(f"{username} sent message: {text}")

    # Send reply message
    reply_text = "Sorry, this bot is no longer active. You can continue to use ChatGPT on the OpenAI website. \n\nИзвините, этот бот больше не работает, но вы можете продолжить пользоваться ChatGPT на сайте https://chat.openai.com/"
    await bot.send_message(chat_id=message.chat.id, text=reply_text)

# Start the bot
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
