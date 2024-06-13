from functools import wraps

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import BadRequest
from telegram.ext import CallbackContext

from constants import CHANNEL, INTRO_MESSAGE
from helpers import balance_markup
from models import TelegramUser


def has_joined_channel(func):
    @wraps(func)
    async def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        """Decorator to check if the user has joined the channel"""

        if update.message is None:
            user_id = update.callback_query.message.chat.id
        else:
            user_id = update.message.chat.id

        # Check if the user is a member of the channel
        member = await context.bot.get_chat_member(
            chat_id=CHANNEL,
            user_id=user_id
        )
        if member.status in ['member', 'administrator', 'creator']:
            # User is a member of the channel
            return await func(update, context, *args, **kwargs)
        else:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"You should be a subscriber of {CHANNEL} channel to use this bot. "
                     f"Please join the channel and send /start again.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(text='Join Channel', url=f'https://t.me/{CHANNEL[1:]}')]
                ])
            )

    return wrapper


def balance_update(func):
    @wraps(func)
    async def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        """Decorator to check if the user has joined the channel"""

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
            # User is a member of the channel
            return await func(update, context, *args, **kwargs)

    return wrapper
