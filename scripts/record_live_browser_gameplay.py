import os
import io
import time
from PIL import Image
from playwright.sync_api import sync_playwright

def record_gameplay(html_path, gif_output_path, num_frames=35, delay=0.08):
    abs_path = "file:///" + os.path.abspath(html_path).replace("\\", "/")
    print(f"Recording live browser gameplay from: {abs_path}")

    frames = []
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            headless=True
        )
        page = browser.new_page(viewport={"width": 960, "height": 540})
        page.goto(abs_path)
        page.wait_for_timeout(500)  # wait for JS loop to initialize

        for i in range(num_frames):
            screenshot_bytes = page.locator("#c").screenshot()
            img = Image.open(io.BytesIO(screenshot_bytes)).convert("RGB")
            frames.append(img)
            time.sleep(delay)

        browser.close()

    if frames:
        frames[0].save(
            gif_output_path,
            save_all=True,
            append_images=frames[1:],
            duration=100,
            loop=0
        )
        print(f"Saved real recorded gameplay GIF to {gif_output_path} ({len(frames)} frames)")

if __name__ == "__main__":
    record_gameplay("docs/assets/snake_gameplay.html", "docs/assets/snake_gameplay.gif")
    record_gameplay("docs/assets/ping_pong_gameplay.html", "docs/assets/ping_pong.gif")
    record_gameplay("docs/assets/space_defense_gameplay.html", "docs/assets/space_defense.gif")
    record_gameplay("docs/assets/maze_runner_gameplay.html", "docs/assets/maze_runner.gif")
