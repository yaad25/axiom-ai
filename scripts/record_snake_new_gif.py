"""
Re-record docs/assets/snake_gameplay.gif with new Last /v1/decisions Call code block UI!
"""

import os
import time
from io import BytesIO
from PIL import Image
from playwright.sync_api import sync_playwright

output_gif = os.path.abspath("docs/assets/snake_gameplay.gif")
html_path = os.path.abspath("docs/assets/snake_gameplay.html")
file_url = f"file:///{html_path.replace('\\', '/')}"

chrome_paths = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]
executable_path = next((p for p in chrome_paths if os.path.exists(p)), None)

with sync_playwright() as p:
    launch_kwargs = {"headless": True}
    if executable_path:
        launch_kwargs["executable_path"] = executable_path
    
    browser = p.chromium.launch(**launch_kwargs)
    page = browser.new_page(viewport={"width": 960, "height": 600})
    page.goto(file_url)
    page.wait_for_timeout(200)

    frames = []
    for _ in range(35):
        frames.append(Image.open(BytesIO(page.screenshot(type="png"))).convert("RGB"))
        page.wait_for_timeout(70)

    browser.close()

    if frames:
        frames[0].save(
            output_gif,
            save_all=True,
            append_images=frames[1:],
            duration=70,
            loop=0
        )
        print(f"Recorded updated Snake GIF: {output_gif}")
