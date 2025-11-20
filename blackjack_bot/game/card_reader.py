from typing import Optional

import OCR


class CardReader:
    """Handles all OCR card reading operations"""

    VALID_DEALER = {"2", "3", "4", "5", "6", "7", "8", "9", "10", "1_11"}

    def __init__(self, player_bbox, dealer_bbox, dynamic_dealer, specific_card):
        self.player_bbox = player_bbox
        self.dealer_bbox = dealer_bbox
        self.dynamic_dealer = dynamic_dealer
        self.specific_card = specific_card

    def read_player_cards(self) -> Optional[str]:
        """Read player cards and return the value, or None if failed"""
        try:
            player_boxes = OCR.find_player.detect_boxes(
                bbox=self.player_bbox, mode="player"
            )
            if not player_boxes or len(player_boxes) == 0:
                return None
            playerLoc = player_boxes[0][0]
            player_text = str(OCR.ocr_card(playerLoc, mode="player"))
            if player_text == "None":
                return None
            return player_text
        except Exception:
            return None

    def read_dealer_card(self, cached_dealer: Optional[str] = None) -> Optional[str]:
        """Read dealer card, using cache if available"""
        if cached_dealer:
            return cached_dealer
        try:
            if self.dynamic_dealer == 1:
                dealer_boxes = OCR.find_player.detect_boxes(
                    bbox=self.dealer_bbox, mode="dealer"
                )
                if not dealer_boxes or len(dealer_boxes) == 0:
                    return None
                dealer_text = str(OCR.ocr_card(dealer_boxes[0][0], mode="dealer"))
            else:
                dealer_text = str(OCR.ocr_card(self.dealer_bbox, mode="dealer"))

            if dealer_text == "None":
                return None

            # Convert "11" to "1_11" for ace
            if dealer_text == "11":
                dealer_text = "1_11"

            if dealer_text not in self.VALID_DEALER:
                return None

            return dealer_text
        except Exception:
            return None

    def read_specific_card(self) -> Optional[str]:
        """Read specific card for special rules (e.g., 15v10 with 7-8)"""
        try:
            return OCR.ocr_specific_card(self.specific_card)
        except Exception:
            return None
