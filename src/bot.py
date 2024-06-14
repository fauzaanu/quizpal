import json
import logging
import os
from typing import Callable, Coroutine, Any, Union, List, Dict, Optional

from dotenv import load_dotenv
from telegram import LabeledPrice, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram._utils.types import JSONDict
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, PreCheckoutQueryHandler, \
    CallbackQueryHandler, BaseRateLimiter
from telegram.ext._utils.types import RLARGS

from constants import INTRO_MESSAGE
from decorators import balance_update, has_joined_channel
from helpers import balance_markup, alpha_space, get_user_details, remove_question_words, remove_verbs, alert_admin, \
    get_journal_articles
from models import TelegramUser, Topic, StarPayment, QuizQuestion
from prompt_engineering import generate_quiz_question

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


async def start_command(update, context):
    """Welcome message to the user"""

    user, created = TelegramUser.get_or_create(
        chat_id=update.message.chat.id,
    )

    await alert_admin("Someone used start", context, update)

    if user.star_balance == 0:
        user.first_name = update.message.chat.first_name,
        user.last_name = update.message.chat.last_name,
        user.username = update.message.chat.username,
        user.star_balance = 4
        user.save()

    intro_msg = await context.bot.send_message(
        chat_id=update.message.chat.id,
        text=INTRO_MESSAGE,
        parse_mode='MarkdownV2',
        reply_markup=balance_markup(user.star_balance)
    )

    user.state = intro_msg.message_id
    user.save()

    # pin the message
    await context.bot.pin_chat_message(
        chat_id=update.message.chat.id,
        message_id=intro_msg.message_id,
        disable_notification=True
    )

    await context.bot.send_message(
        chat_id=update.message.chat.id,
        text='📝 Send /help to see a video demo of how to use the bot.'
    )


@has_joined_channel
@balance_update
async def save_topic(update, context):
    """
    We will save the topic the user sends to us.
    We will also change the state of the user to TOPIC
    """
    #
    # # print the message that was replied to
    # print(update.message.reply_to_message)
    # return

    topic = update.message.text

    topic = topic.strip()
    topic = alpha_space(topic)
    topic = remove_question_words(topic)
    topic = remove_verbs(topic)

    # if the topic length is more than 100 characters, return an error message
    if len(topic) > 75 or len(topic.split()) > 10:
        await context.bot.send_message(
            chat_id=update.message.chat.id,
            text=('📝 Please describe your topic in 75 characters or fewer and in 10 words or less\n\n'
                  'Your topic has been shortened to:\n\n'
                  f'`{topic}`\n\n'
                  f'ℹ️ Your topic still contains {len(topic)} characters and {len(topic.split())} words\n'
                  ),
            parse_mode='MarkdownV2'
        )
        return

    user = TelegramUser.get(chat_id=update.message.chat.id)

    topic, created = Topic.get_or_create(
        name=topic,
        user=user,
    )

    if user.star_balance == 1:
        # lol, dont ask
        user.star_balance += 50
        user.save()
        return

        await context.bot.send_message(
            chat_id=update.message.chat.id,
            text='You have 1 star left. Please top up to continue generating questions.'
        )
        return await send_invoice(update, context, chat_id=update.message.chat.id)

    await generate_and_send_question(update.message.chat.id, topic, update, user, context, retry=0)


async def generate_and_send_question(chat_id, topic, update, user, context, retry=0):
    if retry > 3:
        return await context.bot.send_message(
            chat_id=chat_id,
            text='We are unable to generate a question at the moment. Please try again later.'
        )

    temp_msg = await context.bot.send_message(
        chat_id=chat_id,
        text='🔄 Generating a question for you. Please wait... ⏳'
    )

    await context.bot.send_sticker(
        chat_id=chat_id,
        sticker='CAACAgUAAxkBAAETL15mavgdEtgBIuC86s8bgHu56aa2pAACMAADqZrmFqVk6HtGfY7iNQQ'
    )
    try:
        previous_questions = [question.question for question in topic.questions]
        quiz_question = await generate_quiz_question(update, context, topic.name, previous_questions)
        print(json.dumps(quiz_question, indent=2))

        options = quiz_question['options']
        correct_option = quiz_question['correct_option']
        correct_option_id = options.index(correct_option)

        question_text = quiz_question['question']
        question = QuizQuestion.get(question=question_text)

        keyboard = [
            [
                InlineKeyboardButton(text='Learn more', callback_data=f'ex?q={question.id}'),
                InlineKeyboardButton(text='♾️ Next Question', callback_data=f'nq?t={topic.id}')
            ],

        ]

        # generate a question
        try:
            await context.bot.send_poll(
                type='quiz',
                chat_id=chat_id,
                question=question_text,
                options=options,
                correct_option_id=correct_option_id,
                is_anonymous=True,
                protect_content=False,

            )

            topic_text = str()
            journal_text = str()
            for topic in quiz_question['related_topics']:
                topic_text += f'🔗 `{topic}`\n'
                j = await get_journal_articles(topic)
                journal_text += j if j else ''

            if journal_text:
                journal_text = (f"*✨ Related Journal Articles*\n\n"
                                + journal_text)

            explanation_text = (
                f"❓ _{alpha_space(question_text)}_ \n\n"
                f"📖 *Answer*\n\n"
                f"||{alpha_space(quiz_question['explanation'])}|| \n\n"
                f"✏️💡\n\n"
                f"**✨ Suggested Topics**\n\n"
                f"{topic_text}\n\n"
                f"{journal_text if journal_text else ''}"
            )

            await context.bot.send_message(
                chat_id=chat_id,
                text=explanation_text,
                parse_mode="MarkdownV2",
                reply_markup=InlineKeyboardMarkup(keyboard),
                disable_web_page_preview=True
            )
            user.star_balance -= 1
            user.save()
        except Exception as e:
            print(e)
            # return await generate_and_send_question(chat_id, topic, update, user, context, retry + 1)
        # except BadRequest:
        # return await generate_and_send_question(chat_id, topic, update, user, context, retry + 1)

        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=user.state,
            text=INTRO_MESSAGE,
            parse_mode='MarkdownV2',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(text=f'You have {user.star_balance} ⭐', callback_data='balance')],
            ])
        )

    except ValueError as e:
        print(e)
    finally:
        await context.bot.delete_message(
            chat_id=temp_msg.chat.id,
            message_id=temp_msg.message_id
        )


@balance_update
@has_joined_channel
async def learn_more(update, context):
    query = update.callback_query
    question_text = query.data.split('=')[1]
    question = QuizQuestion.get(id=question_text)
    question_text = question.question
    topic = question.topic

    learn_more_message = (
        f'🔍 *Learn more*\n\n'
        f'>TikTok link works in desktop view only\n\n'
        f'🔗 Click below to copy the question and search anywhere else\n\n'
        f'`{question_text}`\n\n'
        f'🔍🌐✨'
    )

    keyboard = [
        [
            InlineKeyboardButton(text='Perplexity', url=f'https://perplexity.ai/search?q={question_text}'),
            InlineKeyboardButton(text='Google', url=f'https://goo.gl/search?{question_text}')
        ],
        [
            InlineKeyboardButton(text='Youtube', url=f'https://youtube.com/results?search_query={question_text}'),
            InlineKeyboardButton(text='TikTok Desktop', url=f'https://tiktok.com/search?q={question_text}')
        ],
        [
            InlineKeyboardButton(text='ChatGPT', url=f'https://chatgpt.com/?q={question_text}')
        ],
        [
            InlineKeyboardButton(text='♾️ Next Question', callback_data=f'nq?t={topic.id}')
        ],
    ]

    await context.bot.send_message(
        chat_id=query.message.chat.id,
        text=learn_more_message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='MarkdownV2',
    )


@balance_update
@has_joined_channel
async def next_question_callback(update, context):
    query = update.callback_query
    topic_id = int(query.data.split('=')[1])
    topic = Topic.get(id=topic_id)
    topic_name = topic.name
    user = TelegramUser.get(chat_id=query.message.chat.id)
    topic = Topic.get(name=topic_name, user=user)

    if user.star_balance == 1:
        await context.bot.send_message(
            chat_id=query.message.chat.id,
            text='You have 1 star left. Please top up to continue generating questions.'
        )
        return await send_invoice(update, context, chat_id=query.message.chat.id)

    await generate_and_send_question(query.message.chat.id, topic, update, user, context, retry=0)


@balance_update
@has_joined_channel
async def topics(update, context):
    """
    displays a list of topics to pick from, includes all the topics the user has created
    """
    user = TelegramUser.get(chat_id=update.message.chat.id)
    topics = user.topics

    if not topics:
        await context.bot.send_message(
            chat_id=update.message.chat.id,
            text='You have not created any topics yet. Please create a topic first.'
        )
    else:
        # get the last 3 topics
        topic_names = [topic.name for topic in topics[-3:]]
        message = 'Pick a topic from the list below\n\n'
        await context.bot.send_message(
            chat_id=update.message.chat.id,
            text=message,
            reply_markup=ReplyKeyboardMarkup(
                [
                    [KeyboardButton(text=name)] for name in topic_names
                ],
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )


@balance_update
@has_joined_channel
async def get_balance(update, context):
    """Retrieves the balance of the user"""
    user = TelegramUser.get(chat_id=update.message.chat.id)
    await context.bot.send_message(
        chat_id=update.message.chat.id,
        text=f'You have {user.star_balance} stars left.'
    )


@balance_update
@has_joined_channel
async def send_invoice(update, context, chat_id):
    await context.bot.send_invoice(
        chat_id=chat_id,
        title='Quizpal Topup',
        description='Top up your stars to continue generating questions.'
                    'Each question costs 1 star. With 150 stars, you can generate 150 questions.',
        payload='WPBOT-PYLD',
        currency='XTR',
        prices=[
            LabeledPrice('Basic', 150)
        ],
        provider_token='',
    )


async def precheckout_callback(update, context):
    # F7379681202039436480U996280547B6915733021A150m181920

    # F7379681202039436480U996280547B6915733021A150m181920
    query = update.pre_checkout_query
    if query.invoice_payload != 'WPBOT-PYLD':
        await query.answer(ok=False, error_message="Something went wrong...")
    else:
        await query.answer(ok=True)


async def successful_payment_callback(update, context):
    user = TelegramUser.get(chat_id=update.message.chat.id)

    StarPayment.create(
        user=TelegramUser.get(chat_id=update.message.chat.id),
        amount=update.message.successful_payment.total_amount,
        telegram_charge_id=update.message.successful_payment.telegram_payment_charge_id
    )

    user.star_balance += update.message.successful_payment.total_amount
    user.save()

    await context.bot.edit_message_text(
        chat_id=update.message.chat.id,
        message_id=user.state,
        text=INTRO_MESSAGE,
        parse_mode='MarkdownV2',
        reply_markup=balance_markup(user.star_balance)
    )

    await context.bot.send_message(
        chat_id=update.message.chat.id,
        text=f'Your stars have been topped up successfully. '
             f'Your current balance is {user.star_balance} stars.'
    )


@balance_update
@has_joined_channel
async def withdraw_stars(update, context):
    """withdraws stars from the user's account and refunds the payment to the user's account"""
    user = TelegramUser.get(chat_id=update.message.chat.id)
    if user.star_balance == 0:
        await context.bot.send_message(
            chat_id=update.message.chat.id,
            text='You do not have any stars to withdraw.'
        )
    else:
        # get last payment
        for payment in user.payments:
            if not payment.refunded:
                status = await context.bot.refund_star_payment(
                    user_id=update.message.chat.id,
                    telegram_payment_charge_id=payment.telegram_charge_id
                )
                if status:
                    await context.bot.send_message(
                        chat_id=update.message.chat.id,
                        text=f'Your payment {payment.telegram_charge_id} has been refunded successfully.'
                    )
                    payment.refunded = True
                    payment.save()

                    user.star_balance -= payment.amount
                    user.save()

                    await context.bot.edit_message_text(
                        chat_id=update.message.chat.id,
                        message_id=user.state,
                        text=INTRO_MESSAGE,
                        parse_mode='MarkdownV2',
                        reply_markup=balance_markup(user.star_balance)
                    )
                else:
                    await context.bot.send_message(
                        chat_id=update.message.chat.id,
                        text=f'An error occurred while withdrawing your stars for payment {payment.telegram_charge_id}.'
                    )


@balance_update
@has_joined_channel
async def get_video(update, context):
    """Sends a video to the user"""

    # video_path = os.path.join(os.getcwd(), 'assets', 'qz-demo.mp4')
    await context.bot.send_video(
        chat_id=update.message.chat.id,
        # BAACAgUAAxkBAAIES2ZsZGvRcNn9gNaF5lQOFAMRPZPWAAITDwACnCloV-S5689zfIM-NQQ
        video='BAACAgUAAxkBAAIES2ZsZGvRcNn9gNaF5lQOFAMRPZPWAAITDwACnCloV-S5689zfIM-NQQ',
        caption='📽️ Here is a video demo of how to use the bot.'
    )


# async def file_id_grabber(update, context):
#     """sends file id to admin"""
#     update_str = str(update)
#     start_str = "file_id='"
#     end_str = "'"
#     # grab all the file ids
#     for i in range(update_str.count(start_str)):
#         start = update_str.find(start_str)
#         end = update_str.find(end_str, start + len(start_str))
#         file_id = update_str[start + len(start_str):end]
#
#         file = await context.bot.get_file(file_id)
#         image_ext = ['.jpg', '.jpeg', '.png', '.gif']
#         if file.file_path.endswith('.mp4'):
#             await context.bot.send_video(
#                 chat_id=os.environ['ADMIN_CHAT_ID'],
#                 video=file_id
#             )
#         # image paths
#         elif file.file_path.endswith(tuple(image_ext)):
#             await context.bot.send_photo(
#                 chat_id=os.environ['ADMIN_CHAT_ID'],
#                 photo=file_id
#             )
#
#         else:
#             await context.bot.send_document(
#                 chat_id=os.environ['ADMIN_CHAT_ID'],
#                 document=file_id
#             )
#
#         await context.bot.send_message(
#             chat_id=os.environ['ADMIN_CHAT_ID'],
#             text=f'Recieved File ID: {file_id}'
#         )
#
#         update_str = update_str[end:]


if __name__ == '__main__':
    load_dotenv(override=True)
    token = os.environ['TELEGRAM_BOT_TOKEN']

    application = ApplicationBuilder().token(token).build()

    # Handlers
    commands = CommandHandler('start', start_command)
    topic = CommandHandler('topics', topics)
    withdraw = CommandHandler('withdraw', withdraw_stars)
    balance = CommandHandler('balance', get_balance)
    video = CommandHandler('help', get_video)
    successful_payment = MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback)
    save_topic = MessageHandler(filters.TEXT, save_topic)
    # file_id_grabber = MessageHandler(filters.ALL, file_id_grabber)

    # Command handlers
    application.add_handler(commands)
    application.add_handler(balance)
    application.add_handler(topic)
    application.add_handler(withdraw)
    application.add_handler(video)

    # payments
    application.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    application.add_handler(successful_payment)

    # Next question callback
    application.add_handler(CallbackQueryHandler(next_question_callback, pattern='nq'))

    # Learn more callback
    application.add_handler(CallbackQueryHandler(learn_more, pattern='e'))



    # Save topic handler - Full text and so the last handler
    application.add_handler(save_topic)
    # application.add_handler(file_id_grabber)

    application.run_polling()
