import json
import os
from typing import List, Dict

from openai import OpenAI
from telegram import Update

from constants import (TELEGRAM_QUIZ_QUESTION_LIMIT,
                       TELEGRAM_QUIZ_OPTION_LIMIT)
from helpers import alert_admin
from models import Topic, QuizQuestion, QuizAnswer, AnswerExplanation


async def update_db(json_response, topic_obj):
    topic_obj = Topic.get(name=topic_obj)
    question = QuizQuestion.create(
        question=json_response['question'],
        topic=topic_obj
    )
    for option in json_response['options']:
        is_correct = (option == json_response['correct_option'])

        QuizAnswer.create(
            answer=option,
            is_correct=is_correct,
            question=question
        )

    AnswerExplanation.create(
        explanation=json_response['explanation'],
        question=question
    )
    return question


async def generate_quiz_question(update: Update, context, topic: str, previous_questions: List[str],
                                 attempt: int = 1) -> dict:
    """
    Generate a quiz question for the specified topic. Retries up to 5 times in case of invalid response.
    """
    if attempt > 5:
        raise ValueError("Maximum attempts reached. Unable to generate a valid quiz question.")

    system_prompt = (
        f'You are an expert in the topic: {topic}. '
        f'You have been asked to create an innovative, '
        f'highly concise and to the point, and challenging,'
        f'quiz question designed to rigorously assess '
        f'the highest levels of talent and expertise for a competition with'
        f'a grand prize of 27T$.'
        f'You will not be including any questions that were previously asked.\n'
        f'Previouse Questions:\n'
    )
    for question in previous_questions:
        system_prompt += f'{question}\n'

    user_prompt = (
        "The response should be in JSON format as follows:\n"
        "{\n"
        "  'question': 'Question text',\n"
        "  'options': ['Option 1', 'Option 2', 'Option 3', 'Option 4'],\n"
        "  'correct_option': 'Correct option text',\n"
        "  'explanation': 'Explanation of the correct answer',\n"
        "  'related_topics': ['Related topic 1', 'Related topic 2', 'Related topic 3']\n"
        "}\n"
    )

    response = await send_to_gpt(update, context, user_prompt, system_prompt, )
    try:
        json_response: dict = json.loads(response)
        if await validate_json(json_response):
            await update_db(json_response, topic)
            return json_response
        else:
            raise ValueError("Invalid JSON response received from GPT.")
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Attempt {attempt}: {e}")
        return await generate_quiz_question(update, context, topic, previous_questions, attempt + 1)


def validate_lengths(response):
    """
    Fail Json validation deleberately if the lengths are not in proportion to
    telegrams requested limits.
    """
    if len(response['question']) > TELEGRAM_QUIZ_QUESTION_LIMIT:
        raise ValueError("Question length exceeds Telegram limit.")

    for option in response['options']:
        if len(option) > TELEGRAM_QUIZ_OPTION_LIMIT:
            raise ValueError("Option length exceeds Telegram limit.")
    return True


async def validate_json(response: Dict[str, str]) -> bool:
    """
    Validate the JSON response.
    """
    required_keys = ['question', 'options', 'correct_option', 'explanation', 'related_topics']
    if not all(key in response for key in required_keys):
        return False
    if not response['question'] or not response['explanation']:
        return False
    if not isinstance(response['options'], list) or len(response['options']) < 2:
        return False
    if not isinstance(response['related_topics'], list):
        return False
    if response['correct_option'] not in response['options']:
        return False
    if len(response['options']) != 4:
        return False
    return validate_lengths(response)


async def send_to_gpt(update: Update, context, user_prompt: str, system_prompt: str,
                      model: str = "gpt-3.5-turbo") -> str:
    """
    Creates the OpenAI client and sends the request to the API.
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    completion = client.chat.completions.create(
        response_format={"type": "json_object"},
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        frequency_penalty=2,
        temperature=1,
    )
    print(completion.usage.prompt_tokens * (0.0005 / 1000) + completion.usage.completion_tokens * (0.0015 / 1000),
          "USD")

    # alert admin about cost
    try:
        cost = completion.usage.prompt_tokens * (0.0005 / 1000) + completion.usage.completion_tokens * (0.0015 / 1000)
        await alert_admin(f"{cost} USD\n{cost * 15.42} MVR", context, update)
    except Exception as e:
        print(e)

    return completion.choices[0].message.content


# Example usage:
if __name__ == "__main__":
    pass
