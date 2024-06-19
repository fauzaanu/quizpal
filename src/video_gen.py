"""
Tested aproaches:
PIL and text generation ( Too time consuming )
Matplotlib and text generation ( cannot get resolutions right )
Playwright and html to image ( much easier, only problem is the extra server load )

Lot more todo:
- Creating variations
- multiple color schemes
- using images to let users share with friends
- adding watermark and our branding
- adding voice, background effect?
- Pictures? - zzzzzzz
"""
import os

import cv2
from PIL import Image
from playwright.sync_api import sync_playwright

html_content_inp = """
<section class="bg-gradient-to-br from-blue-800 to-blue-900 w-[1080px] h-[1920px] p-5 flex flex-col items-center justify-center">
            <h1 class="text-7xl text-balance text-white font-extrabold my-5 px-10 
            place-content-center place-items-center leading-normal flex place-self-center justify-between text-center">
           Which famous internet cat, known for its grumpy expression, is speculated by some conspiracy theorists to be a key figure in controlling the online world?
            </h1>
            
            <div class="grid grid-cols-2 gap-2 my-24">
                <button class="bg-white text-gray-800 p-5 rounded-xl flex 
                items-center w-full text-7xl font-bold border-8 border-blue-500">
                    <span>A. Paris</span>
                </button>
                <button class="bg-white  text-gray-800 p-5 rounded-xl flex 
                items-center w-full text-7xl font-bold border-8 border-blue-500">
                    <span>B. London</span>
                </button>
                <button class="bg-white text-gray-800 p-5 rounded-xl flex 
                items-center w-full text-7xl font-bold border-8 border-blue-500">
                    <span>C. Berlin</span>
                </button>
                <button class="bg-white  text-gray-800 p-5 rounded-xl flex 
                items-center w-full text-7xl font-bold border-8 border-blue-500">
                    <span>D. Madrid</span>
                </button>
            </div>
</section>
"""


def playwright_screenshot(html_content_inp):
    """
    A function that takes an html content and returns a screenshot of the rendered html
    """
    tailwind_script = "<script src='https://cdn.tailwindcss.com'></script>"
    html_content = tailwind_script + html_content_inp

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir="browser-screenshot",
            headless=True,
            viewport={"width": 1080, "height": 1920},
        )
        page = browser.new_page()
        page.set_content(html_content)

        # take a screenshot of the element (section)
        element = page.query_selector("section")
        element.screenshot(path="screenshot.png")
        browser.close()

    screenshot = Image.open("screenshot.png")
    return screenshot


def generate_video(directory):
    """
    Generate a video from a directory of images.
    """
    img_array = []
    abs_path = os.path.join(os.getcwd(), directory)
    # Check if the directory exists
    if not os.path.exists(abs_path):
        print(f"Directory {abs_path} does not exist.")
        exit()
    for filename in os.listdir(abs_path):
        file_path = os.path.join(abs_path, filename)
        print(f"Reading file: {file_path}")

        img = cv2.imread(file_path)

        if img is None:
            print(f"Warning: Unable to read {file_path}")
            continue

        height, width, layers = img.shape
        size = (width, height)
        img_array.append(img)
    # Check if we have any images to write
    if not img_array:
        print("No valid images found. Exiting.")
        exit()
    # Write video
    out = cv2.VideoWriter('project.mp4', cv2.VideoWriter_fourcc(*'mp4v'), 1, size)
    for img in img_array:
        out.write(img)
    out.release()
    print("Video created successfully.")


playwright_screenshot(html_content_inp)
