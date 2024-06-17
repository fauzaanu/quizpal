from src.markdown_escaper import escape_dot

CHANNEL = "@aboutquizpal"
TELEGRAM_QUIZ_QUESTION_LIMIT = 300
TELEGRAM_QUIZ_OPTION_LIMIT = 100
TELEGRAM_QUIZ_EXPLANATION_LIMIT = 200

INTRO_MESSAGE = (
        escape_dot("🌟 *Welcome to Quizpal* 🌟\n\n") +
        escape_dot("📚 Send any topic to generate questions!\n") +
        escape_dot("💫 Each question costs 1 Quizpal Star.\n") +
        escape_dot("💫 You start with 25 Quizpal Stars.\n\n") +

        escape_dot("🌟 *Earn Stars:*\n") +
        escape_dot("🎉 Each correct answer refunds the cost.\n") +
        escape_dot("🌟 Get a win streak to earn more stars.\n") +
        escape_dot("❌ Incorrect answers resets the win streak.\n\n") +

        escape_dot("⚙️ *Commands:*\n") +
        escape_dot("🔹 /topics - Explore available topics.\n") +
        escape_dot("🔹 /balance - Check your star balance.\n") +
        escape_dot("🔹 /help - Watch the tutorial video.\n") +
        escape_dot("🔹 /topup - Add stars to your balance.\n\n") +

        escape_dot("🔍 *Examples of topics:*\n") +
        escape_dot("🔹 `Few Shot Learning with Prototypical Networks`\n") +
        escape_dot("🔹 `Cognitive Load Theory in Instructional Design`\n") +
        escape_dot("🔹 `Clinical Pharmacokinetics and Pharmacodynamics`\n\n") +
        escape_dot("📚 *Start by sending a topic!* 📚\n")
)
