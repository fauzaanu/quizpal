from markdown_escaper import escape_dot

CHANNEL = "@aboutquizpal"
TELEGRAM_QUIZ_QUESTION_LIMIT = 300
TELEGRAM_QUIZ_OPTION_LIMIT = 100
TELEGRAM_QUIZ_EXPLANATION_LIMIT = 200

INTRO_MESSAGE = (
    escape_dot("Hi, I'm QuizpalBot ??, Send me a topic to get started. ??\n\n")
)

COMMANDS = (
        escape_dot("⚙️ *Commands:*\n") +
        escape_dot("🔹 /topics - Explore available topics.\n") +
        escape_dot("🔹 /balance - Check your star balance.\n") +
        escape_dot("🔹 /help - Watch the tutorial video.\n") +
        escape_dot("🔹 /topup - Add stars to your balance.\n\n")
)

CELEBRATION_EFFECT_ID = 5046509860389126442
CRYING_EFFECT_ID = 5069111056337470630
WHY_EFFECT_ID = 5122846324185629167