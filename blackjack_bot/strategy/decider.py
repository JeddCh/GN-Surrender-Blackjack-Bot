import time
from typing import Optional, Tuple

from ..enums import Action
from .tables import StrategyTables


class StrategyDecider:
    """Makes strategic decisions based on cards and strategy tables"""

    PAIR_NOTATIONS = {
        "4": "4",
        "6": "6",
        "8": "8",
        "12": "12",
        "14": "14",
        "16": "16",
        "18": "18",
        "2_12": "2_12",
    }

    def __init__(self, strategy_tables: StrategyTables, surrender15_specific: int):
        self.strategy = strategy_tables
        self.surrender15_specific = surrender15_specific

    def should_split(
        self, player: str, dealer: str, last_action: Action, in_split_hand: bool
    ) -> Tuple[bool, Optional[str]]:
        """Determine if we should split"""
        if last_action == Action.HIT and not in_split_hand:
            return False, None
        pair_notation = self.PAIR_NOTATIONS.get(player)
        if not pair_notation:
            return False, None
        should_split = self.strategy.split_cache.get((pair_notation, dealer), False)
        return should_split, pair_notation

    def should_surrender(
        self,
        player: str,
        dealer: str,
        last_action: Action,
        specific_card_value: Optional[str] = None,
    ) -> Tuple[bool, bool]:
        """Determine if we should surrender. Returns (should_surrender, should_hit_instead)"""
        if last_action != Action.REBET or "_" in player:
            return False, False
        should_surrender = self.strategy.surrender_cache.get((player, dealer), False)
        if (
            should_surrender
            and player == "15"
            and dealer == "10"
            and self.surrender15_specific == 1
            and specific_card_value in ["7", "8"]
        ):
            return False, True
        return should_surrender, False

    def get_soft_action(self, player: str, dealer: str) -> str:
        """Get action for soft hands"""
        return self.strategy.soft_cache.get((player, dealer), "S")

    def get_hard_action(self, player: str, dealer: str) -> str:
        """Get action for hard hands"""
        return self.strategy.hard_cache.get((player, dealer), "S")

    def can_double(
        self, last_action: Action, in_split_hand: bool, button_manager
    ) -> bool:
        """Check if doubling is allowed"""
        if not in_split_hand and last_action != Action.REBET:
            return False
        max_attempts = 3
        for attempt in range(max_attempts):
            buttons = button_manager.check_buttons()
            if "DoubleAvailable.PNG" in buttons:
                return True
            if attempt < max_attempts - 1:
                time.sleep(0.1)
        return False
