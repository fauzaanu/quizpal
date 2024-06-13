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
