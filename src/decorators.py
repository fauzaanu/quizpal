import random
from functools import wraps

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext

from constants import CHANNEL
from helpers import balance_updater


def has_joined_channel(func):
    @wraps(func)
    async def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        """Decorator to check if the user has joined the channel"""

        # only check if the user joined the channel 50% of the time
        if random.randint(0, 1) == 0:
            return await func(update, context, *args, **kwargs)

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

        await balance_updater(update, context)
        return await func(update, context, *args, **kwargs)

    return wrapper
