"""Peewee migrations -- 001_initial.py.

Some examples (model - class or model name)::

    > Model = migrator.orm['table_name']            # Return model in current state by name
    > Model = migrator.ModelClass                   # Return model in current state by name

    > migrator.sql(sql)                             # Run custom SQL
    > migrator.run(func, *args, **kwargs)           # Run python function with the given args
    > migrator.create_model(Model)                  # Create a model (could be used as decorator)
    > migrator.remove_model(model, cascade=True)    # Remove a model
    > migrator.add_fields(model, **fields)          # Add fields to a model
    > migrator.change_fields(model, **fields)       # Change fields
    > migrator.remove_fields(model, *field_names, cascade=True)
    > migrator.rename_field(model, old_field_name, new_field_name)
    > migrator.rename_table(model, new_table_name)
    > migrator.add_index(model, *col_names, unique=False)
    > migrator.add_not_null(model, *field_names)
    > migrator.add_default(model, field_name, default)
    > migrator.add_constraint(model, name, sql)
    > migrator.drop_index(model, *col_names)
    > migrator.drop_not_null(model, *field_names)
    > migrator.drop_constraints(model, *constraints)

"""

from contextlib import suppress

import peewee as pw
from peewee_migrate import Migrator

with suppress(ImportError):
    pass


def migrate(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your migrations here."""

    @migrator.create_model
    class TelegramUser(pw.Model):
        id = pw.AutoField()
        chat_id = pw.IntegerField()
        first_name = pw.CharField(max_length=255, null=True)
        last_name = pw.CharField(max_length=255, null=True)
        username = pw.CharField(max_length=255, null=True)
        state = pw.CharField(max_length=255, null=True)
        questions_generated = pw.IntegerField(default=0)
        star_balance = pw.IntegerField(default=0)
        created_at = pw.DateField()

        class Meta:
            table_name = "telegramuser"

    @migrator.create_model
    class Topic(pw.Model):
        id = pw.AutoField()
        name = pw.CharField(max_length=255)
        user = pw.ForeignKeyField(column_name='user_id', field='id', model=migrator.orm['telegramuser'])
        created_at = pw.DateField()

        class Meta:
            table_name = "topic"

    @migrator.create_model
    class QuizQuestion(pw.Model):
        id = pw.AutoField()
        question = pw.CharField(max_length=255)
        created_at = pw.DateField()
        topic = pw.ForeignKeyField(column_name='topic_id', field='id', model=migrator.orm['topic'])

        class Meta:
            table_name = "quizquestion"

    @migrator.create_model
    class AnswerExplanation(pw.Model):
        id = pw.AutoField()
        explanation = pw.CharField(max_length=255)
        created_at = pw.DateField()
        question = pw.ForeignKeyField(column_name='question_id', field='id', model=migrator.orm['quizquestion'])

        class Meta:
            table_name = "answerexplanation"

    @migrator.create_model
    class QuizAnswer(pw.Model):
        id = pw.AutoField()
        answer = pw.CharField(max_length=255)
        is_correct = pw.BooleanField()
        created_at = pw.DateField()
        question = pw.ForeignKeyField(column_name='question_id', field='id', model=migrator.orm['quizquestion'])

        class Meta:
            table_name = "quizanswer"

    @migrator.create_model
    class StarPayment(pw.Model):
        id = pw.AutoField()
        user = pw.ForeignKeyField(column_name='user_id', field='id', model=migrator.orm['telegramuser'])
        amount = pw.IntegerField()
        telegram_charge_id = pw.CharField(max_length=255)
        refunded = pw.BooleanField(default=False)
        created_at = pw.DateField()

        class Meta:
            table_name = "starpayment"

    @migrator.create_model
    class StaticFile(pw.Model):
        id = pw.AutoField()
        telegram_fileid = pw.CharField(max_length=255, null=True)
        identifier = pw.CharField(max_length=255)
        created_at = pw.DateField()

        class Meta:
            table_name = "staticfile"

    @migrator.create_model
    class SuggestedTopic(pw.Model):
        id = pw.AutoField()
        stopic = pw.CharField(max_length=255)
        question = pw.ForeignKeyField(column_name='question_id', field='id', model=migrator.orm['quizquestion'])
        created_at = pw.DateField()

        class Meta:
            table_name = "suggestedtopic"

    @migrator.create_model
    class UserQuestionMultiplier(pw.Model):
        id = pw.AutoField()
        user = pw.ForeignKeyField(column_name='user_id', field='id', model=migrator.orm['telegramuser'])
        multiplier = pw.IntegerField(default=1, null=True)
        created_at = pw.DateField()

        class Meta:
            table_name = "userquestionmultiplier"


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your rollback migrations here."""

    migrator.remove_model('userquestionmultiplier')

    migrator.remove_model('suggestedtopic')

    migrator.remove_model('staticfile')

    migrator.remove_model('starpayment')

    migrator.remove_model('quizanswer')

    migrator.remove_model('answerexplanation')

    migrator.remove_model('quizquestion')

    migrator.remove_model('topic')

    migrator.remove_model('telegramuser')
