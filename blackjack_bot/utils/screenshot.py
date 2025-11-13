import os
from datetime import datetime

import pyautogui


class ScreenshotManager:
    """Handles screenshot capture and saving"""

    def __init__(self, folder_name: str = "split_errors"):
        self.screenshot_folder = folder_name
        os.makedirs(self.screenshot_folder, exist_ok=True)

    def save_screenshot(self, error_type: str, details: str = ""):
        """Save a screenshot when an error occurs"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            filename = f"{error_type}_{details}_{timestamp}.png"
            filepath = os.path.join(self.screenshot_folder, filename)
            screenshot = pyautogui.screenshot()
            screenshot.save(filepath)
        except Exception as e:
            print(f"✗ Failed to save screenshot: {e}")
            import traceback

            traceback.print_exc()
