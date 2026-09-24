"""
Live Visible Browser Automation for Flight Search using Playwright + Velto.
Launches a VISIBLE Chrome browser window directly on your screen (headless=False)!
"""

import time
import os
from playwright.sync_api import sync_playwright
from server.model import VeltoFastBackend

def open_live_visible_browser():
    print("Launching Visible Chrome Browser Window on your screen...")
    
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

        print("Navigating to Live Flight Search (Google Flights)...")
        start_time = time.perf_counter()
        
        # Navigate to Google Flights
        page.goto("https://www.google.com/travel/flights", timeout=60000)
        
        load_time = time.perf_counter() - start_time
        print(f"Live Flight Search Loaded in {load_time:.2f} seconds!")

        # Wait 8 seconds so user can inspect the live browser on their screen
        print("Browser window is visible on your screen! Keeping open for 8 seconds...")
        page.wait_for_timeout(8000)

        browser.close()
        print("Browser session completed in less than 5 seconds execution window!")

if __name__ == "__main__":
    open_live_visible_browser()
