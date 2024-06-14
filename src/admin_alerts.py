import os

from helpers import get_user_details


async def alert_admin(message, context, update):
    user_details = await get_user_details(update)

    # alert admin
    await context.bot.send_message(
        chat_id=os.environ['ADMIN_CHAT_ID'],
        text=f'{user_details}\n\n{message}'
    )