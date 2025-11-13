from enum import Enum


class Action(Enum):
    """Possible blackjack actions"""

    HIT = "HIT"
    STAND = "STAND"
    DOUBLE = "DOUBLE"
    SPLIT = "SPLIT"
    SURRENDER = "SURRENDER"
    REBET = "REBET"
    NONE = "NONE"


class GamePhase(Enum):
    """Current phase of the game"""

    WAITING_FOR_REBET = "waiting_for_rebet"
    HAND_COMPLETE = "hand_complete"
    ACTIVE_GAME = "active_game"
    WAITING_FOR_CARD_CHANGE = "waiting_for_card_change"
