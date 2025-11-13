import time
from typing import Dict

import keyboard

import resource_path

from .enums import Action, GamePhase
from .game.action_executor import ActionExecutor
from .game.button_manager import ButtonManager
from .game.card_reader import CardReader
from .models import GameState, Statistics
from .strategy.decider import StrategyDecider
from .strategy.tables import StrategyTables


class BlackjackBot:
    """Main bot controller that orchestrates all components"""

    def __init__(self, config: Dict):
        strategy_sheet = resource_path.resource_path("Strategy.xlsx")
        self.strategy_tables = StrategyTables(strategy_sheet)
        self.strategy_decider = StrategyDecider(
            self.strategy_tables, config.get("surrender15Specific", 0)
        )
        self.card_reader = CardReader(
            config.get("playerTable"),
            config.get("dealer"),
            config.get("dynamicDealer"),
            config.get("specificCard"),
        )
        self.button_manager = ButtonManager(config.get("buttonBbox"))
        self.stats = Statistics()
        self.executor = ActionExecutor(
            self.button_manager, self.card_reader, self.strategy_decider, self.stats
        )
        self.game_state = GameState()
        self.running = False

    def toggle_running(self):
        """Toggle bot on/off"""
        self.running = not self.running
        print("Script running:", self.running)
        if self.running and self.stats.start_time is None:
            self.stats.start_time = time.time()
        if not self.running and self.stats.start_time is not None:
            self.stats.print_stats()

    def handle_waiting_for_card_change(self) -> bool:
        """Handle waiting for card change after HIT or SPLIT. Returns True if still waiting."""
        if not self.game_state.waiting_for_change:
            return False
        current_player = self.card_reader.read_player_cards()
        if current_player and current_player != self.game_state.last_player_value:
            self.game_state.waiting_for_change = False
            self.game_state.current_game_state = None
            return False
        elif time.time() - self.game_state.change_start_time > 2.0:
            print("WARNING: Timeout waiting for card change")
            self.game_state.waiting_for_change = False
            self.game_state.current_game_state = None
            return False
        time.sleep(0.005)
        return True

    def get_game_phase(self, buttons: Dict) -> GamePhase:
        """Determine current game phase"""
        in_active_game = self.button_manager.is_in_active_game(buttons)
        if "RebetDealAvailable.PNG" in buttons and not in_active_game:
            return GamePhase.WAITING_FOR_REBET
        if self.game_state.waiting_for_change:
            return GamePhase.WAITING_FOR_CARD_CHANGE
        if "RebetDealUnavailable.PNG" in buttons and not in_active_game:
            return GamePhase.HAND_COMPLETE
        if in_active_game:
            return GamePhase.ACTIVE_GAME
        return GamePhase.HAND_COMPLETE

    def handle_hand_start(self, player_text: str, dealer_text: str):
        """Handle start of new hand"""
        current_game_state_id = f"{player_text}_{dealer_text}"
        if self.game_state.current_game_state != current_game_state_id:
            if self.game_state.current_game_state == "waiting":
                self.stats.hands_played += 1
                print(f"\n>>> Starting Hand #{self.stats.hands_played}")
                self.game_state.hand_complete_printed = False
            print(f"\nCards: Player={player_text} | Dealer={dealer_text}")
            if self.game_state.in_split_hand:
                print(
                    f"[Split hand - last_action: {self.game_state.last_action.value}]"
                )
            if self.game_state.current_game_state != "waiting":
                if self.game_state.last_action not in [Action.REBET, Action.SPLIT]:
                    self.game_state.last_action = Action.NONE
            self.game_state.current_game_state = current_game_state_id

    def handle_split_decision(
        self, player_text: str, dealer_text: str, buttons: Dict
    ) -> bool:
        """Handle split decision. Returns True if split was executed."""
        if (
            self.game_state.last_action == Action.NONE
            and not self.game_state.in_split_hand
        ):
            return False
        should_split, pair_notation = self.strategy_decider.should_split(
            player_text,
            dealer_text,
            self.game_state.last_action,
            self.game_state.in_split_hand,
        )
        if should_split and pair_notation:
            return self.executor.execute_split(buttons, self.game_state, pair_notation)
        return False

    def handle_surrender_decision(
        self, player_text: str, dealer_text: str, buttons: Dict
    ) -> bool:
        """Handle surrender decision. Returns True if action was taken."""
        specific_card = None
        if player_text == "15" and dealer_text == "10":
            specific_card = self.card_reader.read_specific_card()
        should_surrender, should_hit = self.strategy_decider.should_surrender(
            player_text, dealer_text, self.game_state.last_action, specific_card
        )
        if should_hit:
            print("Strategy: HIT (15v10 w/ 7-8) | Action: HIT ✓")
            return self.executor.execute_hit(buttons, self.game_state, player_text)
        if should_surrender:
            return self.executor.execute_surrender(buttons, self.game_state)
        return False

    def handle_soft_hand(
        self, player_text: str, dealer_text: str, buttons: Dict
    ) -> bool:
        """Handle soft hand decision. Returns True if action was taken."""
        action = self.strategy_decider.get_soft_action(player_text, dealer_text)
        if action == "D":
            if self.strategy_decider.can_double(
                self.game_state.last_action,
                self.game_state.in_split_hand,
                self.button_manager,
            ):
                if self.executor.execute_double(buttons, self.game_state, "soft"):
                    return True
                else:
                    print("Strategy: DOUBLE (soft) | Action: HIT (can't double)")
                    return self.executor.execute_hit(
                        buttons, self.game_state, player_text, "soft"
                    )
            else:
                print("Strategy: DOUBLE (soft) | Action: HIT (can't double)")
                return self.executor.execute_hit(
                    buttons, self.game_state, player_text, "soft"
                )
        elif action == "Ds":
            if self.strategy_decider.can_double(
                self.game_state.last_action,
                self.game_state.in_split_hand,
                self.button_manager,
            ):
                if self.executor.execute_double(buttons, self.game_state, "soft"):
                    return True
                else:
                    print(
                        "Strategy: DOUBLE/STAND (soft) | Action: STAND (can't double)"
                    )
                    return self.executor.execute_stand(buttons, self.game_state, "soft")
            else:
                print("Strategy: DOUBLE/STAND (soft) | Action: STAND (can't double)")
                return self.executor.execute_stand(buttons, self.game_state, "soft")
        elif action == "H":
            return self.executor.execute_hit(
                buttons, self.game_state, player_text, "soft"
            )
        elif action == "S":
            return self.executor.execute_stand(buttons, self.game_state, "soft")
        return False

    def handle_hard_hand(
        self, player_text: str, dealer_text: str, buttons: Dict
    ) -> bool:
        """Handle hard hand decision. Returns True if action was taken."""
        self.card_reader.read_player_cards()
        action = self.strategy_decider.get_hard_action(player_text, dealer_text)
        if action == "D":
            if self.strategy_decider.can_double(
                self.game_state.last_action,
                self.game_state.in_split_hand,
                self.button_manager,
            ):
                if self.executor.execute_double(buttons, self.game_state, "hard"):
                    return True
                else:
                    print("Strategy: DOUBLE | Action: HIT (button disappeared)")
                    return self.executor.execute_hit(
                        buttons, self.game_state, player_text
                    )
            else:
                print("Strategy: DOUBLE | Action: HIT (can't double - game state)")
                return self.executor.execute_hit(buttons, self.game_state, player_text)
        elif action == "H":
            return self.executor.execute_hit(buttons, self.game_state, player_text)
        elif action == "S":
            if self.executor.execute_stand(buttons, self.game_state):
                return True
            elif "RebetDealAvailable.PNG" in buttons:
                return False
        return False

    def run_one_iteration(self):
        """Run one iteration of the bot loop"""
        buttons = self.button_manager.check_buttons()
        phase = self.get_game_phase(buttons)

        if phase == GamePhase.WAITING_FOR_CARD_CHANGE:
            self.handle_waiting_for_card_change()
            return
        if phase == GamePhase.WAITING_FOR_REBET:
            self.executor.execute_rebet(buttons, self.game_state)
            return
        if phase == GamePhase.HAND_COMPLETE:
            if (
                not self.game_state.hand_complete_printed
                and self.game_state.current_game_state not in [None, "waiting"]
            ):
                print("=" * 50)
                print(f"Hand #{self.stats.hands_played} complete")
                print("=" * 50)
                print("Waiting for rebet...")
                self.game_state.hand_complete_printed = True
            time.sleep(0.01)
            return
        if phase != GamePhase.ACTIVE_GAME:
            if self.game_state.waiting_for_change:
                self.game_state.waiting_for_change = False
                self.game_state.last_player_value = None
            time.sleep(0.01)
            return

        player_text = self.card_reader.read_player_cards()
        if not player_text:
            time.sleep(0.01)
            return

        current_hand_id = (
            f"{self.game_state.last_action.value}_{self.stats.bets_placed}"
        )
        if (
            self.game_state.cached_dealer_hand_id == current_hand_id
            and self.game_state.cached_dealer
        ):
            dealer_text = self.game_state.cached_dealer
        else:
            dealer_text = self.card_reader.read_dealer_card(
                self.game_state.cached_dealer
            )
            if not dealer_text:
                time.sleep(0.01)
                return
            self.game_state.cached_dealer = dealer_text
            self.game_state.cached_dealer_hand_id = current_hand_id

        self.handle_hand_start(player_text, dealer_text)

        if self.handle_split_decision(player_text, dealer_text, buttons):
            return
        if self.handle_surrender_decision(player_text, dealer_text, buttons):
            return
        if "_" in player_text:
            if self.handle_soft_hand(player_text, dealer_text, buttons):
                return
        else:
            if self.handle_hard_hand(player_text, dealer_text, buttons):
                return
        time.sleep(0.005)

    def run(self):
        """Main bot loop"""
        while True:
            if not self.running:
                time.sleep(0.05)
                if keyboard.is_pressed("esc"):
                    print("Exiting script.")
                    break
                continue
            if keyboard.is_pressed("esc"):
                print("Exiting script.")
                break
            try:
                self.run_one_iteration()
            except Exception as e:
                print(f"ERROR in bot loop: {e}")
                time.sleep(0.1)
