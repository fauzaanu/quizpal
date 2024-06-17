import os

import requests
from dotenv import load_dotenv
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import BadRequest

from models import TelegramUser
from src.constants import INTRO_MESSAGE
from src.markdown_escaper import escape_dot


def balance_markup(star_balance):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(text=f'You have {star_balance} ⭐', callback_data='balance')],
    ])


def alpha_space(string_to_convert):
    converted_string = str()
    for char in string_to_convert:
        if char.isalnum() or char == ' ':
            converted_string += char
    return converted_string


async def get_user_details(update):
    user_details = "ℹ️ User Details\n\n"

    if update.message:
        if update.message.chat.first_name:
            user_details += f'👤 First Name: {update.message.chat.first_name}\n'
        if update.message.chat.last_name:
            user_details += f'👤 Last Name: {update.message.chat.last_name}\n'
        if update.message.chat.username:
            user_details += f'📎 Username: @{update.message.chat.username}\n'
        if update.message.chat.id:
            user_details += f'🆔 Chat ID: {update.message.chat.id}\n'
    elif update.callback_query:
        if update.callback_query.message.chat.first_name:
            user_details += f'👤 First Name: {update.callback_query.message.chat.first_name}\n'
        if update.callback_query.message.chat.last_name:
            user_details += f'👤 Last Name: {update.callback_query.message.chat.last_name}\n'
        if update.callback_query.message.chat.username:
            user_details += f'📎 Username: @{update.callback_query.message.chat.username}\n'
        if update.callback_query.message.chat.id:
            user_details += f'🆔 Chat ID: {update.callback_query.message.chat.id}\n'

    return user_details


def remove_question_words(string_to_convert):
    question_words = ['who', 'what', 'when', 'where', 'why', 'how', 'which', 'whom']
    converted_string = str()
    for word in string_to_convert.split():
        if word.lower() not in question_words:
            converted_string += word + ' '
    return converted_string


def remove_verbs(string_to_convert):
    verbs = ['is', 'are', 'am', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
             'shall', 'will', 'should', 'would', 'may', 'might', 'must', 'can', 'could', "the"]
    prepositions = [
        'aboard', 'about', 'above', 'across', 'after', 'against', 'along', 'amid', 'among', 'anti', 'around',
        'as', 'at', 'before', 'behind', 'below', 'beneath', 'beside', 'besides', 'between', 'beyond', 'but', 'by',
        'concerning', 'considering', 'despite', 'down', 'during', 'except', 'excepting', 'excluding', 'following',
        'for', 'from', 'in', 'inside', 'into', 'like', 'minus', 'near', 'of', 'off', 'on', 'onto', 'opposite',
        'outside',
        'over', 'past', 'per', 'plus', 'regarding', 'round', 'save', 'since', 'than', 'through', 'to', 'toward',
        'towards', 'under', 'underneath', 'unlike', 'until', 'up', 'upon', 'versus', 'via', 'with', 'within', 'without'
    ]
    verb_string = str()
    final_string = str()

    for word in string_to_convert.split():
        if word.lower() not in verbs:
            verb_string += word + ' '

    for word in verb_string.split():
        if word.lower() not in prepositions:
            final_string += word + ' '

    return final_string


async def alert_admin(message, context, update):
    user_details = await get_user_details(update)

    # alert admin
    await context.bot.send_message(
        chat_id=os.environ['ADMIN_CHAT_ID'],
        text=f'{user_details}\n\n{message}'
    )


async def get_journal_articles(question: str):
    """from the question grab some journal articles:
    no longer used as semantic scholar approved api request
    """

    # https://www.doaj.org/api/search/articles/cognitive%20load?page=1&pageSize=20

    question = remove_question_words(alpha_space(remove_verbs(question)))
    base_url = "https://www.doaj.org/api/search/articles/"

    response = requests.get(f"{base_url}{question}?page=1&pageSize=2")
    response_json = response.json()

    if response_json['total'] == 0:
        return None
    else:
        response_str = str()
        response_str = process_response_str(response_json, response_str)
        return response_str


def semantic_scholar(question: str):
    headers = {
        'X-API-KEY': os.environ['SEMANTIC_SCHOLAR_API_KEY']
    }

    # https://api.semanticscholar.org/graph/v1/paper/
    # search?query=covid&year=2020-2023&openAccessPdf&fieldsOfStudy=Physics,
    # Philosophy&fields=title,year,authors
    res = requests.get(f'https://api.semanticscholar.org/graph/v1/paper/search?'
                       f'query={question}&openAccessPdf&limit=1&fields=url,title,openAccessPdf',
                       headers=headers)

    if res.status_code != 200:
        return None
    else:
        json_response = res.json()
        print(json_response)

        formated_response = str()
        if json_response['total'] == 0:
            return None
        # check if the next key is present
        if 'next' in json_response:
            if json_response['next'] >= 1:
                for article in json_response['data']:
                    print(article['title'])
                    print(article['openAccessPdf']['url'])
                    formated_response += f"📚 {escape_dot(article['title'])}\n" \
                                         f"[🔗 Link]({escape_dot(article['openAccessPdf']['url'])})\n\n"
        return formated_response


def process_response_str(response_json, response_str):
    articles = response_json['results']

    for article in articles:
        response_str += (f"📚 {alpha_space(article['bibjson']['title'])[0:100]} \. \. \."
                         f"\n[🔗 Link]({escape_dot(article['bibjson']['link'][0]['url'])})"
                         f"\n\n")
    return response_str


def get_chat_id(update):
    """
    Gets the chatid no matter the update type
    """
    if update.message:
        return update.message.chat.id
    return update.callback_query.message.chat.id


async def balance_updater(update, context):
    if update.message is None:
        user_id = update.callback_query.message.chat.id
    else:
        user_id = update.message.chat.id

    # update the users balance on the message
    user = TelegramUser.get(chat_id=user_id)

    try:
        await context.bot.edit_message_text(
            chat_id=user_id,
            message_id=user.state,
            text=INTRO_MESSAGE,
            parse_mode='MarkdownV2',
            reply_markup=balance_markup(user.star_balance)
        )
    except BadRequest:
        pass
    finally:
        pass


if __name__ == "__main__":
    load_dotenv()
    semantic_scholar("cognitive load")
