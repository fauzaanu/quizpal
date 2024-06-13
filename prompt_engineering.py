import json
import os
from typing import List, Dict
from dotenv import load_dotenv
from openai import OpenAI

from models import Topic, QuizQuestion, QuizAnswer, AnswerExplanation


def update_db(json_response, topic):
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


def generate_quiz_question(topic: str, previous_questions: List[str], attempt: int = 1) -> dict:
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
        "Generate an extremely challenging and difficult quiz question on the specified topic. "
        "The question should be designed to test deep understanding and advanced knowledge. "
        "The response should be in JSON format as follows:"
        "The response should be in JSON format as follows:\n"
        "{\n"
        "  'question': 'Question text',\n"
        "  'options': ['Option 1', 'Option 2', 'Option 3', 'Option 4'],\n"
        "  'correct_option': 'Correct option text',\n"
        "  'explanation': 'Explanation of the correct answer'\n"
        "}\n"
        "Make sure the question is unique, highly complex, "
        "and not similar to previously asked questions. "
        "The correct option must be included among the options. "
        "The question should be concise yet demanding, "
        "requiring thorough comprehension of the topic"
        "Poll options length must not exceed 100 characters."
        "Question length must not exceed 300 characters."
    )

    response = send_to_gpt(user_prompt, system_prompt)
    try:
        json_response: dict = json.loads(response)
        if validate_json(json_response):
            update_db(json_response, topic)
            return json_response
        else:
            raise ValueError("Invalid JSON response received from GPT.")
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Attempt {attempt}: {e}")
        return generate_quiz_question(topic, previous_questions, attempt + 1)


def validate_json(response: Dict[str, str]) -> bool:
    """
    Validate the JSON response.
    """
    required_keys = ['question', 'options', 'correct_option', 'explanation']
    if not all(key in response for key in required_keys):
        return False
    if not response['question'] or not response['explanation']:
        return False
    if not isinstance(response['options'], list) or len(response['options']) < 2:
        return False
    if response['correct_option'] not in response['options']:
        return False
    return True


def send_to_gpt(user_prompt: str, system_prompt: str, model: str = "gpt-3.5-turbo") -> str:
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
    return completion.choices[0].message.content


# Example usage:
if __name__ == "__main__":
    load_dotenv()
    topic = "coca cola origins"
    previous_questions = [
    ]

    try:
        quiz_question = generate_quiz_question(topic, previous_questions)
        print(json.dumps(quiz_question, indent=2))
    except ValueError as e:
        print(e)
