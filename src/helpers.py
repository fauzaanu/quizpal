import os

from telegram import InlineKeyboardMarkup, InlineKeyboardButton


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
             'shall', 'will', 'should', 'would', 'may', 'might', 'must', 'can', 'could']
    prepositions = [
        'aboard', 'about', 'above', 'across', 'after', 'against', 'along', 'amid', 'among', 'anti', 'around',
        'as', 'at', 'before', 'behind', 'below', 'beneath', 'beside', 'besides', 'between', 'beyond', 'but', 'by',
        'concerning', 'considering', 'despite', 'down', 'during', 'except', 'excepting', 'excluding', 'following',
        'for', 'from', 'in', 'inside', 'into', 'like', 'minus', 'near', 'of', 'off', 'on', 'onto', 'opposite', 'outside',
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