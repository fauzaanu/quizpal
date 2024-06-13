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
