# QuizpalBot - Infinite learning for any topic

[![Telegram Bot CI/CD](https://github.com/fauzaanu/quizpal/actions/workflows/deploy_vps.yml/badge.svg)](https://github.com/fauzaanu/quizpal/actions/workflows/deploy_vps.yml)

Quizpal transforms learning into an engaging experience by generating custom quizzes on any topic you choose.

## Libraries and Tools
- Python
- Telegram Bot API
- OpenAI GPT-3
- SQLite with Peewee ORM

## Some cool stuff in play

![img.png](assets/img.png)
> If you add an Inline Button into a pinned message the pinned messsage has a button, so this bot uses this to display 
> the current star balance of the user. And we update that message as the balance changes to always show the current 
> balance.

> Creating this bot was done for the sole purpose of experimenting with processing payments through stars, processing 
> refunds and maintaining the charge_ids in the database. Something interesting that I found was if you click the 
> service message about the payment, it will show the charge_id as transaction id. 
> Could be useful if you are in a situation where you forgot to save the charge_id for some reason like me initially lol.

> Hi @durov, can you please lower the fee for custom emojis in bots

## How Quizpal works
1. Click start and send a topic you want to learn about.
2. The longer the topic the better
3. The prompts are designed to keep the quiz as hard as possible
4. The bot is really cheap as we use GPT-3 to generate the quiz
5. The bot doesn't maintain a score or anything, the focus is on learning new stuff and not on competition.
6. The bot has a learn more button which appears in the short explanation of the answer
7. Clicking this button will give you a set of buttons to chatgpt, tiktok, google, youtube, etc. to learn more about the topic
8. New information: Tiktok is an insanely good search engine
9. Each telegram id gets assigned 4 in-game stars and each question consumes 1 star
10. When you have a balance of 1 star, you need to topup stars to continue playing
11. The balance system doesnt work at all, this is intentional so users can use it for free for sometime
12. All users are also required to join our channel, which will come very handy in the future for announcements
