"""
Record real-time HTML canvas/DOM execution of flight_booking_showcase.html
and save as docs/assets/flight_booking.gif
"""

import os
import time
from PIL import Image
from playwright.sync_api import sync_playwright

html_path = os.path.abspath("docs/assets/flight_booking_showcase.html")
file_url = f"file:///{html_path.replace('\\', '/')}"
output_gif = os.path.abspath("docs/assets/flight_booking.gif")

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
    # Capture 35 frames over 2 seconds
    for _ in range(35):
        png_bytes = page.screenshot(type="png")
        from io import BytesIO
        img = Image.open(BytesIO(png_bytes)).convert("RGB")
        frames.append(img)
        page.wait_for_timeout(60)

    browser.close()

    if frames:
        frames[0].save(
            output_gif,
            save_all=True,
            append_images=frames[1:],
            duration=70,
            loop=0
        )
        print(f"Recorded GIF successfully: {output_gif}")
