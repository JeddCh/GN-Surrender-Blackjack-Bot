import time
from typing import Dict, Tuple

import pyautogui

import ButtonChecker


class ButtonManager:
    """Handles all button detection and clicking operations"""

    GAMEPLAY_BUTTONS = [
        "HitAvailable.PNG",
        "StandAvailable.PNG",
        "DoubleAvailable.PNG",
        "SplitAvailable.PNG",
        "SurrenderAvailable.PNG",
    ]

    def __init__(self, button_bbox):
        self.button_bbox = button_bbox

    def check_buttons(self) -> Dict[str, Tuple[Tuple[int, int], Tuple[int, int]]]:
        """Check which buttons are available"""
        return ButtonChecker.check_buttons(bbox=self.button_bbox)

    def is_in_active_game(self, buttons: Dict) -> bool:
        """Check if we're in an active game"""
        return any(btn in buttons for btn in self.GAMEPLAY_BUTTONS)

    def click_button(self, button_location: Tuple[Tuple[int, int], Tuple[int, int]]):
        """Click a button at the given location"""
        abs_top_left = (
            button_location[0][0] + self.button_bbox[0],
            button_location[0][1] + self.button_bbox[1],
        )
        abs_bottom_right = (
            button_location[1][0] + self.button_bbox[0],
            button_location[1][1] + self.button_bbox[1],
        )
        midPoint = (
            (abs_top_left[0] + abs_bottom_right[0]) / 2,
            (abs_top_left[1] + abs_bottom_right[1]) / 2,
        )
        pyautogui.moveTo(midPoint[0], midPoint[1], duration=0)
        pyautogui.click()

    def safe_click_with_verification(
        self,
        buttons: Dict,
        target_button: str,
        action_name: str,
        avoid_button: str = "DoubleAvailable.PNG",
    ):
        """Click a button with verification to avoid misclicks"""
        time.sleep(0.15)
        buttons = self.check_buttons()
        if target_button in buttons:
            if avoid_button in buttons:
                print(
                    f"WARNING: Both {action_name} and DOUBLE available - verifying button location"
                )
                time.sleep(0.05)
            return buttons.get(target_button)
        return None
