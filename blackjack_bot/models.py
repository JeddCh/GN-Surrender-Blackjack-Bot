import time
from dataclasses import dataclass
from typing import Optional

from .enums import Action


@dataclass
class GameState:
    """Encapsulates all game state in one place"""

    last_action: Action = Action.NONE
    in_split_hand: bool = False
    hand_complete_printed: bool = False
    last_player_value: Optional[str] = None
    waiting_for_change: bool = False
    change_start_time: float = 0
    cached_dealer: Optional[str] = None
    cached_dealer_hand_id: Optional[str] = None
    current_game_state: Optional[str] = None

    def reset_for_new_hand(self):
        """Reset state for a new hand"""
        self.last_action = Action.REBET
        self.in_split_hand = False
        self.cached_dealer = None
        self.cached_dealer_hand_id = None
        self.last_player_value = None
        self.waiting_for_change = False


@dataclass
class Statistics:
    """Track bot statistics"""

    bets_placed: int = 0
    hands_played: int = 0
    start_time: Optional[float] = None

    def print_stats(self):
        """Print current statistics"""
        if self.start_time:
            elapsed = time.time() - self.start_time
            hours = elapsed / 3600
            hands_per_hour = self.hands_played / hours if hours > 0 else 0
            print(f"Hands played: {self.hands_played}")
            print(f"Total bets placed: {self.bets_placed}")
            print(f"Elapsed time: {elapsed / 60:.2f} minutes")
            print(f"Hands/hour: {hands_per_hour:.2f}")
