import telebot
import threading
from time import sleep
import urllib
import sqlite3
import vk_api
# import youtube_dl


COUNT_OS_POSTS = 3

BOT_TOKEN = "TOKEN" # from env var
BOT_INTERVAL = 3
BOT_TIMEOUT = 30

conn = None
chat_id = None
post_ids = []
vk_session = vk_api.VkApi(app_id=6843360, token='TOKEN'); # from env var
vk = vk_session.get_api()

bot = None #Keep the bot object as global variable if needed

def bot_polling():
    global bot #Keep the bot object as global variable if needed
    print("Starting bot polling now")
    while True:
        try:
            print("New bot instance started")
            bot = telebot.TeleBot(BOT_TOKEN) #Generate new bot instance
            # botactions() #If bot is used as a global variable, remove bot as an input param
            # bot.polling(none_stop=True, interval=BOT_INTERVAL, timeout=BOT_TIMEOUT)
        except Exception as ex: #Error in polling
            print("Bot polling failed, restarting in {}sec. Error:\n{}".format(BOT_TIMEOUT, ex))
            # bot.stop_polling()
            sleep(BOT_TIMEOUT)
        else: #Clean exit
            # bot.stop_polling()
            print("Bot polling loop finished")
            break #End loop


def botactions():
    # global bot
    #Set all your bot handlers inside this function
    #If bot is used as a global variable, remove bot as an input param
    @bot.message_handler(commands=["start"])
    def command_start(message):
        bot.reply_to(message, "Hi there!")

def telebot_send_post(post_id, user_id, text, attachments):
    if attachments != []:
        attachments_list = []
        for attachment in attachments:
            if attachment['type'] == 'video':
                bot.send_message(user_id, f'*Видеофрагмент*\n\n{text}')
            elif attachment['type'] == 'audio':
                bot.send_message(user_id, f'*Аудиофрагмент*\n\n{text}')
                add_post_to_db(post_id)
            elif attachment['type'] == 'photo':
                attachments_list.append(telebot.types.InputMediaPhoto(attachment['photo']['sizes'][-1]['url'],
                                        caption=text if len(attachments_list) == 0 else None))
        bot.send_media_group(user_id, attachments_list)
        # text_reply_markup = telebot.types.InlineKeyboardMarkup(telebot.types.InlineKeyboardButton('Like', callback_data=''))
        # bot.send_message(358124668, '', reply_markup=)
    else:
        bot.send_message(user_id, f'{text}')
    add_post_to_db(post_id)

def is_post_id_in_db(post_id):
    cur = conn.cursor()
    result = cur.execute(f'SELECT * FROM `itpedia_youtube` WHERE `post_id` = {post_id}').fetchall()
    if result == []:
        return False
    else:
        return True

def add_post_to_db(post_id):
    cur = conn.cursor()
    result = cur.execute(f'INSERT INTO `itpedia_youtube` (post_id) VALUES({post_id})')
    conn.commit()
    print(f'NEW POST `{post_id}` ADDED TO DATABASE!')

def check_community_posts():
    wall = vk.wall.get(domain='itpedia_youtube', count=COUNT_OS_POSTS)

    for post in wall['items'][::-1]:
        if post['marked_as_ads'] == 1:
            continue
        if not is_post_id_in_db(post['id']):
            attachments = []
            try:
                for attachment in post['attachments']:
                    attachments.append(attachment)
            except KeyError:
                attachments.append('')
#            telebot_send_post(post['id'], CHAT_ID, post['text'], attachments)
        else:
            post_id = post['id']
            print(f'POST `{post_id}` IS ALREADY IN DATABASE')

def create_connection(db_file):
    """ create a database connection to a SQLite database """
    global conn
    try:
        conn = sqlite3.connect(db_file)
    except sqlite3.Error as e:
        print(e)


# polling_thread = threading.Thread(target=bot_polling)
# polling_thread.daemon = True
# polling_thread.start()

bot_polling()

#Keep main program running while bot runs threaded
if __name__ == "__main__":
    # while True:
    try:
        create_connection("database.db")
        check_community_posts()
        # sleep(60)
    except Exception as e:
        print(e)
    finally:
        conn.close()