import datetime

from peewee import Model, SqliteDatabase, CharField, DateField, IntegerField, ForeignKeyField, BooleanField

db = SqliteDatabase('databases/bot.db')


class TelegramUser(Model):
    chat_id = IntegerField()
    first_name = CharField(null=True)
    last_name = CharField(null=True)
    username = CharField(null=True)
    state = CharField(null=True)
    questions_generated = IntegerField(default=0)
    star_balance = IntegerField(default=0)
    created_at = DateField(default=datetime.datetime.now)
    total_money_spent = IntegerField(default=0)

    class Meta:
        database = db


class StarPayment(Model):
    user = ForeignKeyField(TelegramUser, backref='payments')
    amount = IntegerField()
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
    cost_in_usd = IntegerField(default=0)

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


class SuggestedTopic(Model):
    stopic = CharField()
    question = ForeignKeyField(QuizQuestion, backref='suggested_topics')
    created_at = DateField(default=datetime.datetime.now)

    class Meta:
        database = db


class StaticFile(Model):
    telegram_fileid = CharField(null=True)
    identifier = CharField(null=False)
    created_at = DateField(default=datetime.datetime.now)

    class Meta:
        database = db


if __name__ == '__main__':
    import os
    import uuid
    # print(os.getcwd())
    #
    # os.chdir('src')
    # run command to create migration file
    random_name = uuid.uuid4().hex
    os.system('pw_migrate create --auto --auto-source models --database sqlite:/../databases/bot.db {}'.format(random_name))
    # pw_migrate create --auto --auto-source models --database sqlite:/../databases/bot.db add_total_money_spent
    # pw_migrate migrate --database sqlite:/../databases/bot.db
    pass