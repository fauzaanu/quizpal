import json
import os
from typing import List, Dict

from dotenv import load_dotenv
from openai import OpenAI
from telegram import Update

from constants import (TELEGRAM_QUIZ_QUESTION_LIMIT,
                       TELEGRAM_QUIZ_OPTION_LIMIT, TELEGRAM_QUIZ_EXPLANATION_LIMIT)
from helpers import alert_admin
from models import Topic, QuizQuestion, QuizAnswer, AnswerExplanation


async def update_db(json_response, topic):
    topic = Topic.get(name=topic)
    question = QuizQuestion.create(
        question=json_response['question'],
        topic=topic
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
        f'You have been asked to generate a challanging quiz question for a quiz competition. '
        f'Here are some previous questions to avoid repetition:\n'
    )
    for question in previous_questions:
        system_prompt += f'{question}\n'

    user_prompt = (
        "Generate an extremely challenging quiz question on the specified topic to test deep understanding and advanced knowledge. "
        "The response should be in JSON format as follows:\n"
        "{\n"
        "  'question': 'Question text',\n"
        "  'options': ['Option 1', 'Option 2', 'Option 3', 'Option 4'],\n"
        "  'correct_option': 'Correct option text',\n"
        "  'explanation': 'Explanation of the correct answer',\n"
        "  'related_topics': ['Related topic 1', 'Related topic 2', 'Related topic 3']\n"
        "}\n"
        "The question should be unique, complex, and concise (max 300 characters). "
        "Options should be concise (max 100 characters) and include the correct answer. "
        "Avoid phrases like 'In the context of', 'According to', etc.\n\n"

        "Good Example:\n"
        "{\n"
        "  'question': 'Which protein complex is crucial for separating sister chromatids during anaphase?',\n"
        "  'options': ['Condensin', 'Cohesin', 'Anaphase Promoting Complex (APC/C)', 'Kinetochores'],\n"
        "  'correct_option': 'Anaphase Promoting Complex (APC/C)',\n"
        "  'explanation': 'The Anaphase Promoting Complex (APC/C) triggers "
        "the separation of sister chromatids by targeting securin for degradation, "
        "thus activating separase to cleave cohesin complexes.',\n"
        "  'related_topics': ['Cell cycle regulation and checkpoints', "
        "'Mitosis and meiosis cycles, "
        "Chromosome structure and function']\n"
        "}\n\n"

        "Bad Example:\n"
        "{\n"
        "  'question': 'In the context of cell division, what does the Anaphase Promoting Complex (APC/C) do?',\n"
        "  'options': ['Starts mitosis', 'Ends mitosis', 'Separates chromatids', 'Repairs DNA'],\n"
        "  'correct_option': 'Separates chromatids',\n"
        "  'explanation': 'The Anaphase Promoting Complex (APC/C) triggers the separation of sister "
        "chromatids by targeting securin for degradation.',\n"
        "  'related_topics': ['Cell', 'Chromatids']\n"
        "}\n\n"
        "Note that the good example is specific, challenging, and requires deep understanding, whereas the bad example "
        "is too straightforward and lacks complexity and includes unnecessary phrases such as 'In the context of"
        "The Good example also gives more specefic related topics rather than short one word phrases'.\n\n"
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
            return False
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
        frequency_penalty=0.5,
        temperature=0.7,
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
    load_dotenv()
    topic = "Payments for physical goods and services and the bartar system"
    previous_questions = [
    ]

    try:
        quiz_question = generate_quiz_question(topic, previous_questions)
        print(json.dumps(quiz_question, indent=2))
    except ValueError as e:
        print(e)
