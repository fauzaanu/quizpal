import json
import logging
import os
from pprint import pprint

from dotenv import load_dotenv
from telegram import LabeledPrice, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, \
    InputMediaPhoto
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, PreCheckoutQueryHandler, \
    CallbackQueryHandler

from constants import INTRO_MESSAGE
from decorators import balance_update, has_joined_channel
from helpers import balance_markup, alpha_space, remove_question_words, remove_verbs, alert_admin, \
    get_chat_id, semantic_scholar
from models import TelegramUser, Topic, StarPayment, QuizQuestion, SuggestedTopic, AnswerExplanation, StaticFile, \
    UserQuestionMultiplier
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
        user.star_balance = 25
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

    # is this a message sent by admin with a file_id tag
    if update.message.chat.id == int(os.environ['ADMIN_CHAT_ID']):
        pprint(update)
        if update.message.caption:
            if update.message.caption == "#S":
                # get the file_id
                file_id = update.message.photo[0].file_id
                # save the file_id to the database
                s, _ = StaticFile.get_or_create(
                    identifier="#S",
                )
                s.telegram_fileid = file_id
                s.save()

                return await context.bot.send_message(
                    chat_id=update.message.chat.id,
                    text='#S File updated successfully.'
                )
            elif update.message.caption == "#E":
                # get the file_id
                file_id = update.message.photo[0].file_id
                # save the file_id to the database
                s, _ = StaticFile.get_or_create(
                    identifier="#E",
                )
                s.telegram_fileid = file_id
                s.save()

                return await context.bot.send_message(
                    chat_id=update.message.chat.id,
                    text='#E File updated successfully.'
                )
            elif update.message.caption == "#G":
                # get the file_id
                file_id = update.message.photo[0].file_id
                # save the file_id to the database
                s, _ = StaticFile.get_or_create(
                    identifier="#G",
                )
                s.telegram_fileid = file_id
                s.save()

                return await context.bot.send_message(
                    chat_id=update.message.chat.id,
                    text='#G File updated successfully.'
                )
            elif update.message.caption == "#H":
                # get the file_id
                file_id = update.message.video.file_id
                # save the file_id to the database
                s, _ = StaticFile.get_or_create(
                    identifier="#H",
                )
                s.telegram_fileid = file_id
                s.save()

                return await context.bot.send_message(
                    chat_id=update.message.chat.id,
                    text='#H File updated successfully.'
                )

    # process only if TEXT
    if update.message.text is None:
        return

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
        await context.bot.send_message(
            chat_id=update.message.chat.id,
            text='You have 1 star left. Please purchase our premium plan to continue generating questions.'
                 'Our premium pack grants you 10,000 Quizpal stars and they never expire.'
                 'The cost of the premium plan is 1500 Telegram Stars. (Approx. $30)'
        )
        return await send_invoice(update, context, chat_id=update.message.chat.id)

    await generate_and_send_question(update.message.chat.id, topic, update, user, context)


async def generate_and_send_question(chat_id, topic, update, user, context):
    generating_msg = await context.bot.send_photo(
        chat_id=chat_id,
        photo=StaticFile.get(identifier='#G').telegram_fileid,
    )

    try:
        previous_questions = [question.question for question in topic.questions]
        quiz_question = await generate_quiz_question(update,
                                                     context,
                                                     topic.name,
                                                     previous_questions)
        print(json.dumps(quiz_question, indent=2))

        options = quiz_question['options']
        correct_option = quiz_question['correct_option']
        correct_option_id = options.index(correct_option)

        question_text = quiz_question['question']
        question = QuizQuestion.get(question=question_text)

        poll_question = await context.bot.send_poll(
            type='quiz',
            chat_id=chat_id,
            question=question_text,
            options=options,
            correct_option_id=correct_option_id,
            is_anonymous=False,
            protect_content=False,
        )

        context.job_queue.run_once(
            time_up_callback, 30,
            chat_id=chat_id,
            name=str(chat_id),
            data=poll_question.message_id
        )

        for topic in quiz_question['related_topics']:
            SuggestedTopic.create(
                stopic=topic,
                question=question
            )

        user.star_balance -= 1
        user.save()

        await context.bot.edit_message_media(
            chat_id=chat_id,
            message_id=generating_msg.message_id,
            media=InputMediaPhoto(
                media=StaticFile.get(identifier='#S').telegram_fileid,
            )
        )
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=user.state,
            text=INTRO_MESSAGE,
            parse_mode='MarkdownV2',
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton(text=f'You have {user.star_balance} ⭐', callback_data='balance')],
                ])
        )

    except Exception as e:
        await context.bot.edit_message_media(
            chat_id=chat_id,
            message_id=generating_msg.message_id,
            media=InputMediaPhoto(
                media=StaticFile.get(identifier='#E').telegram_fileid,
            )
        )
        await alert_admin(f"Error generating question: {e}", context, update)


async def time_up_callback(context):
    """Callback to be called when the time for the poll is up"""
    job = context.job
    poll = job.data

    multiplier, _ = UserQuestionMultiplier.get_or_create(
        user=TelegramUser.get(chat_id=job.chat_id)
    )

    poll = await context.bot.stop_poll(
        chat_id=job.chat_id,
        message_id=poll
    )

    user = TelegramUser.get(chat_id=job.chat_id)

    question = QuizQuestion.get(question=poll.question)
    topic = question.topic

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(text='🔍 Explain', callback_data=f'ex?q={question.id}'),
                InlineKeyboardButton(text='♾️ Next Question', callback_data=f'nq?t={topic.id}')
            ],
        ]
    )

    user_answer_id = int()
    correct_option_id = poll.correct_option_id

    if poll.total_voter_count == 0:
        multiplier.multiplier = 1
        multiplier.save()
        return await context.bot.send_message(
            chat_id=job.chat_id,
            text=(
                '👎 The question was not answered. You did not earn any stars. ❌\n\n'
                f'You still have {user.star_balance} ⭐️ left.\n\n'
                '🔄 Your win multiplier has been reset to 1.'
            ),
            reply_to_message_id=job.data,
            reply_markup=keyboard
        )

    itersx = 0
    for options in poll.options:
        print("text", options.text)
        print("voter_count", options.voter_count)

        if options.voter_count > 0:
            user_answer_id = itersx
        itersx += 1

    if user_answer_id == correct_option_id:
        earnings = 1 * multiplier.multiplier
        user.star_balance += earnings
        user.save()

        multiplier.multiplier += 1 if multiplier.multiplier < 5 else 1
        multiplier.save()

        await context.bot.send_message(
            chat_id=job.chat_id,
            text=(
                f'🎉 Your answer is correct! You earned +{earnings} ⭐️\n\n'
            ),
            reply_to_message_id=job.data,
            reply_markup=keyboard
        )

    else:
        multiplier.multiplier = 1
        multiplier.save()

        await context.bot.send_message(
            chat_id=job.chat_id,
            text=(
                '👎 Incorrect! You did not earn any stars. ❌\n\n'
            ),
            reply_to_message_id=job.data,
            reply_markup=keyboard
        )


async def explanation(update, context):
    query = update.callback_query
    question = query.data.split('=')[1]
    question_obj = QuizQuestion.get(id=question)
    topic = question_obj.topic

    keyboard = [
        [InlineKeyboardButton(text='♾️ Next Question', callback_data=f'nq?t={topic.id}'), ],
        [InlineKeyboardButton(text='Learn more', callback_data=f'lm?q={question_obj.id}'), ],
        [InlineKeyboardButton(text='Suggest Related Topics', callback_data=f'st?q={question_obj.id}'), ]
    ]

    journal_text = str()
    for stopic_obj in SuggestedTopic.filter(question=question_obj):
        j = semantic_scholar(stopic_obj.stopic)
        journal_text += j if j else ''

    if journal_text:
        journal_text = (f"*✨ Related Journal Articles*\n\n"
                        + journal_text)
    a_question = alpha_space(question_obj.question)
    a_explanation = alpha_space(AnswerExplanation.get(question=question_obj).explanation)

    explanation_text = (
        f"❓ _{a_question}_ \n\n"
        f"📖 *Answer*\n\n"
        f"||{a_explanation}|| \n\n"
        f"✏️💡\n\n"
        f"{journal_text if journal_text else ''}"
    )

    await context.bot.send_message(
        chat_id=query.message.chat.id,
        text=explanation_text,
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup(keyboard),
        disable_web_page_preview=True
    )


async def suggested_topics(update, context):
    query = update.callback_query
    question = query.data.split('=')[1]
    question_obj = QuizQuestion.get(id=question)
    topic = question_obj.topic

    keyboard = [
        [
            InlineKeyboardButton(text='Learn more', callback_data=f'lm?q={question_obj.id}'),
            InlineKeyboardButton(text='♾️ Next Question', callback_data=f'nq?t={topic.id}')
        ],
    ]

    topic_text = str()
    for stopic_obj in SuggestedTopic.filter(question=question_obj):
        topic_text += f'🔗 `{stopic_obj.stopic}`\n'

    # PEP 8: W605 invalid escape sequence '\('
    suggested_text = (
        f"*✨ Suggested Topics*\n"
        f"_\(click to copy, & then just send me to switch to that topic\)_\n\n"
        f"{topic_text}\n\n"
    )

    await context.bot.send_message(
        chat_id=query.message.chat.id,
        text=suggested_text,
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup(keyboard),
        disable_web_page_preview=True
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

    await generate_and_send_question(query.message.chat.id, topic, update, user, context)


@balance_update
@has_joined_channel
async def topics(update, context):
    """
    displays a list of topics to pick from, includes all the topics the user has created
    """
    user = TelegramUser.get(chat_id=update.message.chat.id)
    users_topics = user.topics

    if not users_topics:
        await context.bot.send_message(
            chat_id=update.message.chat.id,
            text='You have not created any topics yet. Please create a topic first.'
        )
    else:
        # get the last 3 topics
        topic_names = [topic.name for topic in users_topics[-3:]]
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
async def send_invoice(update, context):
    chat_id = get_chat_id(update)

    await context.bot.send_invoice(
        chat_id=chat_id,
        title='Quizpal Yearly',
        description='You will recieve 10,000 Quizpal stars Valid forever.',
        payload='WPBOT-PYLD',
        currency='XTR',
        prices=[
            LabeledPrice('Basic', 1500)
        ],
        provider_token='',
    )

    await context.bot.send_message(
        chat_id=chat_id,
        text='Unfortunately, we dont have plans that are less than 1500 stars. '
             'However, if you are a student who cannot afford this '
             'please reach out to us and we will give you some free stars.'
             'You can contact us at:\n\n'
             '@fauzaanu'
    )


async def precheckout_callback(update):
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

    user.star_balance += 10000
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
        video=StaticFile.get(identifier='#H').telegram_fileid,
        caption='📽️ Here is a video demo of how to use the bot.'
    )


if __name__ == '__main__':
    load_dotenv(override=True)
    token = os.environ['TELEGRAM_BOT_TOKEN']

    application = ApplicationBuilder().token(token).build()
    job_queue = application.job_queue

    # Handlers
    start_cmd = CommandHandler('start', start_command)
    application.add_handler(start_cmd)

    topics_cmd = CommandHandler('topics', topics)
    application.add_handler(topics_cmd)

    topup_cmd = CommandHandler('topup', send_invoice)
    application.add_handler(topup_cmd)

    # withdraw_cmd = CommandHandler('withdraw', withdraw_stars)
    # application.add_handler(withdraw_cmd)

    balance_cmd = CommandHandler('balance', get_balance)
    application.add_handler(balance_cmd)

    help_cmd = CommandHandler('help', get_video)
    application.add_handler(help_cmd)

    successful_payment = MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback)

    # payments
    application.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    application.add_handler(successful_payment)

    # callbacks
    application.add_handler(CallbackQueryHandler(next_question_callback, pattern='nq'))
    application.add_handler(CallbackQueryHandler(explanation, pattern='ex'))
    application.add_handler(CallbackQueryHandler(learn_more, pattern='lm'))
    application.add_handler(CallbackQueryHandler(suggested_topics, pattern='st'))

    save_topic = MessageHandler(filters.ALL, save_topic)
    application.add_handler(save_topic)

    application.run_polling()
