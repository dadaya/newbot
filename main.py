import logging
import time
from aiogram import Bot, Dispatcher, executor, types
import openai
import psycopg2

# Set up the bot and OpenAI API credentials
bot_token = '5968554956:AAGNPB8pXT8jMQ15udAHiTCNavLnFWVvhiY'
api_key = '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'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=bot_token)
dp = Dispatcher(bot)

openai.api_key = api_key

MAX_ATTEMPTS = 2
DELAY_SECONDS = 3

messages = {}


@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    # Connect to PostgreSQL database
    conn = psycopg2.connect(dbname="neondb", user="renkin60", password="A6GoiNjLw2nJ", host="ep-sweet-breeze-413056.eu-central-1.aws.neon.tech", options="project=ep-sweet-breeze-413056")
    # Create a cursor
    cursor = conn.cursor()
    try:
        user = message.from_user
        user_id = user.id
        username = user.username
        first_name = user.first_name
        last_name = user.last_name

        # Check if the user is already in the database
        cursor.execute("SELECT * FROM bot_users WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        if result:
            # User is already in the database, do nothing
            pass
        else:
            # User is not in the database, insert the user into the bot_users table
            cursor.execute("INSERT INTO bot_users (user_id, username, first_name, last_name) VALUES (%s, %s, %s, %s)", (user_id, username, first_name, last_name))

        # Commit the transaction
        conn.commit()
        # Close the cursor and connection
        cursor.close()
        conn.close()

        # Send greeting message
        await message.answer("Привет! Я ChatGPT. Отправьте мне сообщение, и я постараюсь ответить!")

    except Exception as e:
        logging.error(f'Error in start_cmd: {e}')


# Command handler for /newtopic
@dp.message_handler(commands=['newtopic'])
async def new_topic_cmd(message: types.Message):
    try:
        if message.from_user.username is None:
            username = message.from_user.first_name
        else:
            username = message.from_user.username
        messages[username] = []
        await message.reply('Starting a new topic! * * * \n\nНачинаем новую тему! * * *', parse_mode='Markdown')
    except Exception as e:
        logging.error(f'Error in new_topic_cmd: {e}')


# Message handler for all other messages
@dp.message_handler()
async def echo_msg(message: types.Message):
    try:
        user_message = message.text
        username = message.from_user.username
        first_name = message.from_user.first_name

        # Use the user's first name if their username is None
        if username is None:
            username = first_name

        # Add the user's message to their message history
        if username not in messages:
            messages[username] = []
        messages[username].append({"role": "user", "content": user_message})
        messages[username].append({"role": "user",
                                   "content": f"chat: {message.chat} Сейчас {time.strftime('%d/%m/%Y %H:%M:%S')} user: {username} message: {user_message}"})
        logging.info(f'{username}: {user_message}')

        # Check if the message is a reply to the bot's message or a new message
        should_respond = not message.reply_to_message or message.reply_to_message.from_user.id == bot.id

        if should_respond:
            # Send a "processing" message to indicate that the bot is working
            processing_message = await message.reply(
                'Your request is being processed, please wait * * * \n\nВаш запрос обрабатывается, пожалуйста подождите * * *',
                parse_mode='Markdown')

            # Send a "typing" action to indicate that the bot is typing a response
            await bot.send_chat_action(chat_id=message.chat.id, action="typing")

            # Generate a response using OpenAI's Chat API
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages[username],
                max_tokens=1200,
                temperature=0.7,
                frequency_penalty=0,
                presence_penalty=0,
                user=username
            )
            chatgpt_response = completion.choices[0]['message']

            # Add the bot's response to the user's message history
            messages[username].append({"role": "assistant", "content": chatgpt_response['content']})
            logging.info(f'ChatGPT response: {chatgpt_response["content"]}')

            # Send the bot's response to the user
            await message.reply(chatgpt_response['content'])

            # Delete the "processing" message
            await bot.delete_message(chat_id=processing_message.chat.id, message_id=processing_message.message_id)

    except Exception as ex:
        # retry logic
        attempt_count = 0
        while attempt_count < MAX_ATTEMPTS:
            attempt_count += 1
            time.sleep(DELAY_SECONDS)

            try:
                await message.reply(
                    'The bot encountered an error, re-creating the dialogue and retrying * * * \n\nБот столкнулся с ошибкой, пересоздаю диалог и пытаюсь еще раз * * *',
                    parse_mode='Markdown')
                await new_topic_cmd(message)
                await echo_msg(message)
                break
            except:
                continue

        if attempt_count == MAX_ATTEMPTS:
            await message.reply(
                'The bot encountered an error and was unable to process your request. Please try again later.',
                parse_mode='Markdown')


if __name__ == '__main__':
    executor.start_polling(dp)
