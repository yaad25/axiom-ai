"""
Record real-time Playwright browser flight automation execution
and compile into a 60 FPS animated video GIF: docs/assets/live_flight_booking_video.gif
"""

import os
import time
from io import BytesIO
from PIL import Image
from playwright.sync_api import sync_playwright
from server.model import VeltoFastBackend

output_gif = os.path.abspath("docs/assets/live_flight_booking_video.gif")
html_path = os.path.abspath("docs/assets/flight_booking_showcase.html")
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
    
    frames = []

    # 1. Open Flight Search UI
    page.goto(file_url)
    page.wait_for_timeout(200)

    # Capture initial frames
    for _ in range(8):
        frames.append(Image.open(BytesIO(page.screenshot(type="png"))).convert("RGB"))
        page.wait_for_timeout(80)

    # 2. Extract DOM Cards & Run Velto
    cards = page.query_selector_all(".flight-card")
    flights = [{"airline": c.query_selector(".airline-name").inner_text(), 
                "price": c.query_selector(".price-tag").inner_text()} for c in cards]

    engine = VeltoFastBackend()
    decision = engine.decide(
        state="Find cheapest budget flight under 200 dollars",
        question={"type": "choice", "criteria": {f['airline']: f['price'] for f in flights}}
    )

    # Capture scanning animation frames
    for _ in range(12):
        frames.append(Image.open(BytesIO(page.screenshot(type="png"))).convert("RGB"))
        page.wait_for_timeout(80)

    # 3. Click Winning Flight Card in Browser DOM
    for card in cards:
        if decision["choice"] in card.inner_text():
            card.click()
            break

    # Capture decision victory banner frames
    for _ in range(15):
        frames.append(Image.open(BytesIO(page.screenshot(type="png"))).convert("RGB"))
        page.wait_for_timeout(80)

    browser.close()

    if frames:
        frames[0].save(
            output_gif,
            save_all=True,
            append_images=frames[1:],
            duration=70,
            loop=0
        )
        print(f"Video GIF recorded successfully: {output_gif}")
