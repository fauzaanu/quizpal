import datetime

from peewee import Model, SqliteDatabase, CharField, DateField, IntegerField, ForeignKeyField, BooleanField

db = SqliteDatabase('bot.db')


class TelegramUser(Model):
    chat_id = IntegerField(null=False)
    first_name = CharField(null=True)
    last_name = CharField(null=True)
    username = CharField(null=True)
    state = CharField(null=True)
    questions_generated = IntegerField(default=0)
    star_balance = IntegerField(default=0)
    created_at = DateField(default=datetime.datetime.now)

    class Meta:
        database = db


class StarPayment(Model):
    user = ForeignKeyField(TelegramUser, backref='payments')
    amount = IntegerField(null=False)
    telegram_charge_id = CharField(null=False)
    refunded = BooleanField(default=False)
    created_at = DateField(default=datetime.datetime.now)

    class Meta:
        database = db


class Topic(Model):
    name = CharField()
    user = ForeignKeyField(TelegramUser, backref='topics')
    created_at = DateField(default=datetime.datetime.now)

    class Meta:
        database = db


class QuizQuestion(Model):
    question = CharField()
    created_at = DateField(default=datetime.datetime.now)
    topic = ForeignKeyField(Topic, backref='questions')

    class Meta:
        database = db


class QuizAnswer(Model):
    answer = CharField()
    is_correct = BooleanField()
    created_at = DateField(default=datetime.datetime.now)
    question = ForeignKeyField(QuizQuestion, backref='answers')

    class Meta:
        database = db


class AnswerExplanation(Model):
    explanation = CharField()
    created_at = DateField(default=datetime.datetime.now)
    question = ForeignKeyField(QuizQuestion, backref='explanations')

    class Meta:
        database = db


if __name__ == '__main__':
    db.connect()
    db.create_tables([TelegramUser,
                      QuizQuestion,
                      QuizAnswer,
                      AnswerExplanation,
                      Topic,
                      StarPayment
                      ])

    db.close()
