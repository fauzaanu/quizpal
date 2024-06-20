import os
import shutil
import uuid

import cv2
from PIL import Image
from playwright.async_api import async_playwright
from telegram import InputMediaPhoto, InputMediaVideo

from src.models import QuizQuestion


def get_html(question_i: QuizQuestion):
    """
    Helper function for get screenshot to retrieve the html for the question
    """
    with open("src/video_gen/quiz.html", "r") as f:
        question = question_i.question
        html_content = f.read()
        html_content = html_content.replace("#QUESTION", question)
        options_id = ["A", "B", "C", "D"]
        correct_option = str()
        current_option = 0
        for answer_i in question_i.answers:
            option = answer_i.answer
            html_content = html_content.replace(f"#OPTION{options_id[current_option]}", option, 1)
            if answer_i.is_correct:
                correct_option += options_id[current_option]
            current_option += 1
        return html_content, correct_option


async def get_screenshot(question: QuizQuestion, context=None, update=None, only_photo=True):
    """
    A function that takes an html content and returns a screenshot of the rendered html
    """
    assert question is not None, "Question cannot be None"
    assert context is not None or update is not None, "Either context or update must be provided"

    html_content, correct_option = get_html(question)
    unique_job_dir = f"jobs/images" + uuid.uuid4().hex
    os.makedirs(unique_job_dir, exist_ok=True)
    os.chdir(unique_job_dir)

    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir="browser-screenshot",
            headless=True,
            viewport={"width": 1080, "height": 1920},
        )
        page = await browser.new_page()
        await page.set_content(html_content)

        element = await page.query_selector("section")
        await element.screenshot(path="question.png")

        html_content = html_content.replace(f"bg-slate-900 #CORRECT{correct_option}",
                                            f"bg-green-500")

        await page.set_content(html_content)
        element = await page.query_selector("section")
        await element.screenshot(path="answer.png")
        await browser.close()

    # send the message to the user
    if update is not None and context is not None:
        if only_photo:
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open("question.png", "rb"))
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open("answer.png", "rb"))
        if not only_photo:
            # await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open("question.png", "rb"))
            # await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open("answer.png", "rb"))

            ordered_files = []
            for i in range(5):
                Image.open("question.png").save(f"1_question{i}.png")
                ordered_files.append(f"1_question{i}.png")
            for i in range(5):
                Image.open("answer.png").save(f"2_answer{i}.png")
                ordered_files.append(f"2_answer{i}.png")

            img_array = []
            # Read all images from the directory
            for filename in ordered_files:
                print(os.getcwd())
                file_path = filename
                img = cv2.imread(file_path)

                if img is None:
                    print(f"Warning: Unable to read {file_path}")
                    continue

                height, width, layers = img.shape
                size = (width, height)
                img_array.append(img)

            # Check if we have any valid images to write
            if not img_array:
                print("No valid images found. Exiting.")
                return

            # Calculate target duration and frame rate
            target_duration = 10  # seconds
            frame_rate = 60  # fps
            total_frames_needed = target_duration * frame_rate

            # Calculate how many times each frame should be repeated
            num_images = len(img_array)
            repeat_factors = [total_frames_needed // num_images] * num_images

            # Adjust the repeat factors to match the total frames needed exactly
            remaining_frames = total_frames_needed - sum(repeat_factors)
            for i in range(remaining_frames):
                repeat_factors[i] += 1

            # Write video
            out = cv2.VideoWriter('project.mp4', cv2.VideoWriter_fourcc(*'mp4v'), frame_rate, size)

            for img, repeat in zip(img_array, repeat_factors):
                for _ in range(repeat):
                    out.write(img)

            out.release()

            question = InputMediaPhoto(open("question.png", "rb"))
            answer = InputMediaPhoto(open("answer.png", "rb"))
            video = InputMediaVideo(open("project.mp4", "rb"))

            await context.bot.send_media_group(chat_id=update.effective_chat.id,
                                               media=[question, answer, video])

    os.chdir("../../")
    shutil.rmtree(unique_job_dir)

    return True


async def generate_video(directory, write_dir):
    """
    Generate a video from a directory of images.
    """


if __name__ == "__main__":
    # question = QuizQuestion.get(id=1)
    # get_screenshot(question)
    pass
