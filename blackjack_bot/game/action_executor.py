import time
from typing import Dict

from ..enums import Action
from ..models import GameState, Statistics
from ..utils.screenshot import ScreenshotManager
from .button_manager import ButtonManager
from .card_reader import CardReader


class ActionExecutor:
    """Executes strategic decisions"""

    def __init__(
        self,
        button_manager: ButtonManager,
        card_reader: CardReader,
        strategy_decider,
        stats: Statistics,
    ):
        self.buttons = button_manager
        self.cards = card_reader
        self.strategy = strategy_decider
        self.stats = stats
        self.screenshot_mgr = ScreenshotManager()

    def execute_rebet(self, buttons: Dict, game_state: GameState) -> bool:
        """Execute rebet action. Returns True if rebet was clicked."""
        if "RebetDealAvailable.PNG" in buttons:
            self.stats.bets_placed += 1
            game_state.reset_for_new_hand()
            game_state.current_game_state = "waiting"
            self.buttons.click_button(buttons["RebetDealAvailable.PNG"])
            time.sleep(0.05)
            return True
        return False

    def execute_split(
        self, buttons: Dict, game_state: GameState, pair_notation: str
    ) -> bool:
        """Execute split action. Returns True if split was executed."""
        time.sleep(0.15)
        buttons = self.buttons.check_buttons()

        if "SplitAvailable.PNG" in buttons:
            print(f"Strategy: SPLIT {pair_notation} | Action: SPLIT ✓")
            self.stats.bets_placed += 1
            game_state.last_action = Action.SPLIT
            game_state.current_game_state = None
            game_state.in_split_hand = True

            # Store current player value before split
            current_player_value = self.cards.read_player_cards()

            self.buttons.click_button(buttons["SplitAvailable.PNG"])

            time.sleep(0.5)
            validation_buttons = self.buttons.check_buttons()
            is_active_game = any(
                btn in validation_buttons for btn in self.buttons.GAMEPLAY_BUTTONS
            )

            if is_active_game:
                print("Split validated - continuing with split hand")

                # Poll until card changes or timeout
                start_time = time.time()
                timeout = 2.0
                card_changed = False
                while time.time() - start_time < timeout:
                    time.sleep(0.05)
                    player_value = self.cards.read_player_cards()
                    if player_value and player_value != current_player_value:
                        # Successfully detected card change
                        print(
                            f"[Split hand ready: {current_player_value} -> {player_value}]"
                        )
                        card_changed = True
                        break

                if not card_changed:
                    print("WARNING: Timeout waiting for split hand card change")

                return True
            else:
                # print(
                #     "WARNING: Split may have failed - no active game buttons detected"
                # )
                # self.screenshot_mgr.save_screenshot(
                #     "split_validation_failed", pair_notation
                # )
                game_state.last_action = Action.NONE
                game_state.in_split_hand = False
                game_state.current_game_state = None
                return False
        return False

    def execute_surrender(self, buttons: Dict, game_state: GameState) -> bool:
        """Execute surrender action. Returns True if surrendered."""
        time.sleep(0.3)
        buttons = self.buttons.check_buttons()
        if "SurrenderAvailable.PNG" in buttons:
            print("Strategy: SURRENDER | Action: SURRENDER ✓")
            game_state.last_action = Action.SURRENDER
            game_state.current_game_state = None
            self.buttons.click_button(buttons["SurrenderAvailable.PNG"])
            return True
        return False

    def execute_hit(
        self,
        buttons: Dict,
        game_state: GameState,
        player_text: str,
        hand_type: str = "",
    ) -> bool:
        """Execute hit action. Returns True if hit was executed."""
        button_loc = self.buttons.safe_click_with_verification(
            buttons, "HitAvailable.PNG", "HIT"
        )
        if button_loc:
            prefix = f" ({hand_type})" if hand_type else ""
            print(f"Strategy: HIT{prefix} | Action: HIT ✓")
            game_state.last_action = Action.HIT
            game_state.current_game_state = None
            self.buttons.click_button(button_loc)
            game_state.last_player_value = player_text
            game_state.waiting_for_change = True
            game_state.change_start_time = time.time()
            return True
        return False

    def execute_stand(
        self, buttons: Dict, game_state: GameState, hand_type: str = ""
    ) -> bool:
        """Execute stand action. Returns True if stand was executed."""
        button_loc = self.buttons.safe_click_with_verification(
            buttons, "StandAvailable.PNG", "STAND"
        )
        if button_loc:
            prefix = f" ({hand_type})" if hand_type else ""
            print(f"Strategy: STAND{prefix} | Action: STAND ✓")
            game_state.last_action = Action.STAND
            self.buttons.click_button(button_loc)
            time.sleep(0.2)
            if game_state.in_split_hand:
                game_state.last_action = Action.SPLIT
                print("[Split hand complete - ready for next split hand]")
            return True
        return False

    def execute_double(
        self, buttons: Dict, game_state: GameState, hand_type: str = ""
    ) -> bool:
        """Execute double action. Returns True if doubled."""
        time.sleep(0.3 if not hand_type or hand_type == "hard" else 0.05)
        buttons = self.buttons.check_buttons()
        if "DoubleAvailable.PNG" in buttons:
            prefix = f" ({hand_type})" if hand_type else ""
            print(f"Strategy: DOUBLE{prefix} | Action: DOUBLE ✓")
            self.stats.bets_placed += 1
            game_state.last_action = Action.DOUBLE
            game_state.current_game_state = None

            # Store current player value before double
            current_player_value = self.cards.read_player_cards()

            self.buttons.click_button(buttons["DoubleAvailable.PNG"])
            time.sleep(0.15 if hand_type == "soft" else 0.3)

            # For split hands, poll until card changes or timeout
            if game_state.in_split_hand:
                start_time = time.time()
                timeout = 2.0
                while time.time() - start_time < timeout:
                    time.sleep(0.05)
                    player_value = self.cards.read_player_cards()
                    if player_value and player_value != current_player_value:
                        # Successfully detected card change
                        print(
                            f"[Split hand card changed: {current_player_value} -> {player_value}]"
                        )
                        break
                else:
                    # Timeout reached
                    print("WARNING: Timeout waiting for next split hand after double")
            elif not hand_type or hand_type == "hard":
                self.cards.read_player_cards()

            return True
        return False
