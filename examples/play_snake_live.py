"""
Launch Live Snake Game in Visible Chrome Browser for Recording / Play!
Launches a VISIBLE Chrome browser window directly on your screen (headless=False).
"""

import os
import time
from playwright.sync_api import sync_playwright

def play_snake_in_browser():
    print("Launching Visible Chrome Browser with Snake Game on your screen...")
    
    html_path = os.path.abspath("docs/assets/snake_gameplay.html")
    file_url = f"file:///{html_path.replace('\\', '/')}"

    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    executable_path = next((p for p in chrome_paths if os.path.exists(p)), None)

    with sync_playwright() as p:
        launch_kwargs = {
            "headless": False, # Open REAL visible window on screen!
            "args": ["--start-maximized"]
        }
        if executable_path:
            launch_kwargs["executable_path"] = executable_path

        browser = p.chromium.launch(**launch_kwargs)
        context = browser.new_context(no_viewport=True)
        page = context.new_page()

        print(f"Opening Snake Game: {file_url}")
        page.goto(file_url)

        # Click Start button automatically if present
        try:
            start_btn = page.query_selector("button:has-text('Start'), #start-btn, .btn-primary")
            if start_btn:
                start_btn.click()
        except Exception:
            pass

        print("Snake game is playing live on your screen! Keeping browser open for 30 seconds for your video recording...")
        page.wait_for_timeout(30000)

        browser.close()
        print("Browser game session completed!")

if __name__ == "__main__":
    play_snake_in_browser()
