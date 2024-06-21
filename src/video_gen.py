import os
import random
import shutil
import uuid

import cv2
from PIL import Image
from playwright.async_api import async_playwright
from telegram import InputMediaPhoto, InputMediaVideo, InlineKeyboardMarkup, InlineKeyboardButton

from models import QuizQuestion


def get_color():
    tw_colors = [
        "Slate",
        "Gray",
        "Zinc",
        "Neutral",
        "Stone",
        "Red",
        "Orange",
        "Amber",
        "Yellow",
        "Lime",
        "Green",
        "Emerald",
        "Teal",
        "Cyan",
        "Sky",
        "Blue",
        "Indigo",
        "Violet",
        "Purple",
        "Fuchsia",
        "Pink",
        "Rose",
    ]
    # pick two random colors
    color_1 = tw_colors[random.randint(0, len(tw_colors) - 1)]

    color_2_list = tw_colors.copy()
    color_2_list.remove(color_1)

    color_2 = color_2_list[random.randint(0, len(color_2_list) - 1)]

    color_3_list = color_2_list.copy()
    color_3_list.remove(color_2)

    color_3 = color_3_list[random.randint(0, len(color_3_list) - 1)]

    color_1 = color_1.lower()
    color_2 = color_2.lower()
    color_3 = color_3.lower()

    return color_1, color_2, color_3


def get_html(question_i: QuizQuestion):
    """
    Helper function for get screenshot to retrieve the html for the question
    """
    with open("src/quiz.html") as f:
        question = question_i.question
        html_content = f.read()

        # replace background gradient color
        color_1, color_2, color_3 = get_color()
        html_content = html_content.replace("#COLOR1", color_1)
        html_content = html_content.replace("#COLOR2", color_2)
        html_content = html_content.replace("#COLOR3", color_3)

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

    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=unique_job_dir,
            headless=True,
            viewport={"width": 1080, "height": 1920},
        )
        page = await browser.new_page()
        await page.set_content(html_content)

        element = await page.query_selector("section")
        await element.screenshot(path=unique_job_dir + "/question.png")

        html_content = html_content.replace(f"bg-slate-900 #CORRECT{correct_option}",
                                            f"bg-green-500")

        await page.set_content(html_content)
        element = await page.query_selector("section")
        await element.screenshot(path=unique_job_dir + "/answer.png")
        await browser.close()

    # send the message to the user
    if update is not None and context is not None:
        if not only_photo:
            ordered_files = []
            for i in range(5):
                Image.open(unique_job_dir + "/question.png").save(f"{unique_job_dir}/1_question{i}.png")
                ordered_files.append(f"{unique_job_dir}/1_question{i}.png")
            for i in range(5):
                Image.open(unique_job_dir + "/answer.png").save(f"{unique_job_dir}/2_answer{i}.png")
                ordered_files.append(f"{unique_job_dir}/2_answer{i}.png")

            img_array = []
            # Read all images from the directory
            for filename in ordered_files:
                # print(os.getcwd())
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

            # move the video to the directory
            shutil.move("project.mp4", unique_job_dir + "/project.mp4")

            question_img = InputMediaPhoto(open(unique_job_dir + "/question.png", "rb"))
            answer_img = InputMediaPhoto(open(unique_job_dir + "/answer.png", "rb"))
            video_file = InputMediaVideo(open(unique_job_dir + "/project.mp4", "rb"))

            topic = question.topic
            keyboard = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(text='♾️ Next Question', callback_data=f'nq?t={topic.id}')
                    ]
                ]
            )

            await context.bot.send_media_group(chat_id=update.effective_chat.id,
                                               caption="`{}`".format(question.question),
                                               media=[question_img, answer_img, video_file],
                                               parse_mode="MarkdownV2",
                                               )
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text="Please share these on tiktok and tag us @quizpalbot",
                                           reply_markup=keyboard)

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
