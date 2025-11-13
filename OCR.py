import os

import cv2
import numpy as np
from paddleocr import PaddleOCR
from PIL import Image, ImageGrab
from skimage.metrics import structural_similarity as ssim

import find_player
import resource_path

dealer = (983, 310, 1010, 330)

PLAYER_DIR = "captured_cards/player"
DEALER_DIR = "captured_cards/dealer"

PLAYER_DIR = resource_path.resource_path(PLAYER_DIR)
DEALER_DIR = resource_path.resource_path(DEALER_DIR)


def imageCheck():
    player_images = [f for f in os.listdir(PLAYER_DIR) if f.lower().endswith(".png")]
    dealer_images = [f for f in os.listdir(DEALER_DIR) if f.lower().endswith(".png")]
    required_player_images = [
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
        "10",
        "11",
        "12",
        "13",
        "14",
        "15",
        "16",
        "17",
        "18",
        "19",
        "20",
        "2_12",
        "3_13",
        "4_14",
        "5_15",
        "6_16",
        "7_17",
        "8_18",
        "9_19",
        "10_20",
    ]
    required_dealer_images = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "1_11"]
    missing_player = [
        img for img in required_player_images if f"{img}.png" not in player_images
    ]
    missing_dealer = [
        img for img in required_dealer_images if f"{img}.png" not in dealer_images
    ]
    return missing_player, missing_dealer


# OPTIMIZATION: Initialize PaddleOCR with minimal settings for speed
paddle_ocr_model = PaddleOCR(
    use_angle_cls=False,  # Disable angle classification (cards are always upright)
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    device="gpu",
    enable_mkldnn=True,
)

valid_values = set(
    [
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
        "10",
        "11",
        "12",
        "13",
        "14",
        "15",
        "16",
        "17",
        "18",
        "19",
        "20",
        "1_11",
        "2_12",
        "3_13",
        "4_14",
        "5_15",
        "6_16",
        "7_17",
        "8_18",
        "9_19",
        "10_20",
    ]
)

valid_specific_card = set(["K", "Q", "J", "10", "5", "6", "9", "8", "7"])

# OPTIMIZATION: Pre-compile correction mappings
DEALER_CORRECTIONS = {
    "1": "7",
    "0": "10",
    "|": "1",
    "L": "1",
    "I": "1",
    "O": "10",
}
PLAYER_CORRECTIONS = {
    "L": "1",
    "I": "1",
    "|": "1",
    "O": "0",
}


def normalize_ocr_result(text, mode="player"):
    """Normalize OCR result to valid format with common corrections."""
    if not text:
        return None

    text = text.strip().upper()

    # OPTIMIZATION: Direct dictionary lookup instead of nested structure
    if mode == "dealer" and text in DEALER_CORRECTIONS:
        text = DEALER_CORRECTIONS[text]
    elif mode == "player" and text in PLAYER_CORRECTIONS:
        text = PLAYER_CORRECTIONS[text]

    # Handle slash notation (1/11 -> 1_11)
    text = text.replace("/", "_")

    return text


def ocr_card(bbox, scale_factor=2, mode="player", debug=False):
    """
    OPTIMIZED: OCR card detection with single-pass approach.
    Removed max_retries parameter (not used) and multiple preprocessing attempts.
    """
    screen_shot = ImageGrab.grab(bbox=bbox)
    img = np.array(screen_shot)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    if debug:
        cv2.imwrite(f"debug_{mode}_bbox.png", img_rgb)
        print(f"Debug: Saved image | size: {img_rgb.shape} | bbox: {bbox}")

    height, width = img_rgb.shape[:2]

    # Early exit for invalid images
    if height < 10 or width < 10:
        print(f"ERROR: Image too small ({width}x{height}) from bbox {bbox}")
        return None

    # OPTIMIZATION: Only resize once with optimal settings
    img_resized = cv2.resize(
        img_rgb,
        (width * scale_factor, height * scale_factor),
        interpolation=cv2.INTER_CUBIC,
    )

    if debug:
        cv2.imwrite(f"debug_{mode}_resized.png", img_resized)
        print(f"Debug: Resized to {img_resized.shape}")

    # OPTIMIZATION: Try only the best preprocessing method first (OTSU)
    # Most cards read well with OTSU thresholding
    gray = cv2.cvtColor(img_resized, cv2.COLOR_BGR2GRAY)
    _, thresh_otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    thresh_otsu_bgr = cv2.cvtColor(thresh_otsu, cv2.COLOR_GRAY2BGR)

    if debug:
        cv2.imwrite(f"debug_{mode}_otsu.png", thresh_otsu_bgr)

    try:
        result = paddle_ocr_model.predict(thresh_otsu_bgr)

        if debug:
            print(f"Debug: OCR result: {result}")

        if result and result[0] and result[0].get("rec_texts"):
            raw_text = result[0]["rec_texts"][0]
            confidence = (
                result[0].get("rec_scores", [0])[0]
                if result[0].get("rec_scores")
                else 0
            )

            if debug:
                print(f"Debug: Raw text: '{raw_text}' (confidence: {confidence:.3f})")

            normalized_text = normalize_ocr_result(raw_text, mode)

            if debug:
                print(f"Debug: Normalized: '{normalized_text}'")

            # OPTIMIZATION: Return immediately if valid (most common case)
            if normalized_text and normalized_text in valid_values:
                if debug:
                    print(f"Debug: Valid result: '{normalized_text}'")
                return normalized_text

    except Exception as e:
        if debug:
            print(f"Debug: OTSU OCR error: {e}")

    # OPTIMIZATION: Only try fallback methods if OTSU failed
    # This happens rarely, so we only pay the cost when needed
    if debug:
        print("Debug: OTSU failed, trying fallback methods...")

    fallback_methods = [
        ("original", img_resized),
        (
            "adaptive",
            cv2.cvtColor(
                cv2.adaptiveThreshold(
                    gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
                ),
                cv2.COLOR_GRAY2BGR,
            ),
        ),
    ]

    for method_name, processed_img in fallback_methods:
        if debug:
            cv2.imwrite(f"debug_{mode}_{method_name}.png", processed_img)

        try:
            result = paddle_ocr_model.predict(processed_img)

            if result and result[0] and result[0].get("rec_texts"):
                raw_text = result[0]["rec_texts"][0]
                normalized_text = normalize_ocr_result(raw_text, mode)

                if normalized_text and normalized_text in valid_values:
                    if debug:
                        print(
                            f"Debug: Fallback success ({method_name}): '{normalized_text}'"
                        )
                    return normalized_text
        except Exception:
            continue

    if debug:
        print("Debug: All OCR attempts failed")

    return None


def ocr_specific_card(bbox, scale_factor=5, debug=False):
    """OPTIMIZED: Simplified specific card OCR."""
    screen_shot = ImageGrab.grab(bbox=bbox)
    img = np.array(screen_shot)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    if debug:
        cv2.imwrite("debug_specific_card_bbox.png", img_rgb)

    height, width = img_rgb.shape[:2]
    img_resized = cv2.resize(
        img_rgb,
        (width * scale_factor, height * scale_factor),
        interpolation=cv2.INTER_CUBIC,
    )

    if debug:
        cv2.imwrite("debug_specific_card_resized.png", img_resized)

    try:
        result = paddle_ocr_model.predict(img_resized)

        if debug:
            print(f"Debug: OCR result: {result}")

        if not result or not result[0] or not result[0].get("rec_texts"):
            if debug:
                print(f"ERROR: No text detected at bbox {bbox}")
            return None

        ret = result[0]["rec_texts"][0].strip()

        if debug:
            print(f"Debug: Detected text: '{ret}'")

        # OPTIMIZATION: Combined correction logic
        if ret == "1":
            ret = "7"
            if debug:
                print("Debug: Auto-corrected '1' to '7'")
        elif ret in ["K", "Q", "J"]:
            ret = "10"
            if debug:
                print("Debug: Converted face card to '10'")

        if ret in valid_specific_card:
            return ret
        else:
            if debug:
                print(f"ERROR: Invalid specific card: '{ret}'")
            return None

    except Exception as e:
        if debug:
            print(f"ERROR: OCR exception: {e}")
        return None


def ocr_card_old(
    bbox, mode, resize_dim=(200, 200), show_images=False, ssim_threshold=0.05
):
    """
    Legacy SSIM-based card detection. Only use this if you specifically want SSIM method.
    """
    if mode not in ["player", "dealer"]:
        raise ValueError(f"Invalid mode: {mode}. Must be 'player' or 'dealer'")

    screen_shot = ImageGrab.grab(bbox=bbox)
    img = np.array(screen_shot)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    img_resized = cv2.resize(img_rgb, resize_dim, interpolation=cv2.INTER_CUBIC)

    folder = PLAYER_DIR if mode == "player" else DEALER_DIR

    if mode == "dealer":
        valid_results = set(["2", "3", "4", "5", "6", "7", "8", "9", "10", "1_11"])
    else:
        valid_results = set(
            [
                "4",
                "5",
                "6",
                "7",
                "8",
                "9",
                "10",
                "11",
                "12",
                "13",
                "14",
                "15",
                "16",
                "17",
                "18",
                "19",
                "20",
                "2_12",
                "3_13",
                "4_14",
                "5_15",
                "6_16",
                "7_17",
                "8_18",
                "9_19",
                "10_20",
            ]
        )

    best_score = -1
    best_match_label = None
    second_best_score = -1
    second_best_label = None

    for file in os.listdir(folder):
        if not file.lower().endswith(".png"):
            continue

        card_img = np.array(Image.open(os.path.join(folder, file)))
        card_bgr = cv2.cvtColor(card_img, cv2.COLOR_RGB2BGR)
        card_resized = cv2.resize(card_bgr, resize_dim, interpolation=cv2.INTER_CUBIC)

        score = ssim(
            cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB),
            cv2.cvtColor(card_resized, cv2.COLOR_BGR2RGB),
            channel_axis=-1,
        )

        if show_images:
            print(f"Comparing with {file}: SSIM = {score:.4f}")
            combined = np.hstack((img_resized, card_resized))
            cv2.putText(
                combined,
                f"SSIM: {score:.3f}",
                (10, 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 0, 255),
                2,
            )
            cv2.imshow(f"Comparing {file}", combined)
            cv2.waitKey(500)
            cv2.destroyAllWindows()

        if score > best_score:
            second_best_score, second_best_label = best_score, best_match_label
            best_score, best_match_label = score, os.path.splitext(file)[0]
        elif score > second_best_score:
            second_best_score, second_best_label = score, os.path.splitext(file)[0]

    # Tie-breaker check
    if second_best_label and abs(best_score - second_best_score) < ssim_threshold:
        print(
            f"SSIM too close: {best_match_label} ({best_score:.4f}) vs {second_best_label} ({second_best_score:.4f})"
        )
        print("Running template matching as tie-breaker...")

        best_match_score = -1
        best_label_final = best_match_label
        for candidate_label in [best_match_label, second_best_label]:
            candidate_img = cv2.imread(os.path.join(folder, f"{candidate_label}.png"))
            candidate_resized = cv2.resize(
                candidate_img, resize_dim, interpolation=cv2.INTER_CUBIC
            )

            result = cv2.matchTemplate(
                img_resized, candidate_resized, cv2.TM_CCOEFF_NORMED
            )
            _, match_score, _, _ = cv2.minMaxLoc(result)
            print(f"Template match score for {candidate_label}: {match_score:.4f}")

            if show_images:
                combined = np.hstack((img_resized, candidate_resized))
                cv2.putText(
                    combined,
                    f"T-Score: {match_score:.3f}",
                    (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 0, 0),
                    2,
                )
                cv2.imshow(f"Tie-break {candidate_label}", combined)
                cv2.waitKey(500)
                cv2.destroyAllWindows()

            if match_score > best_match_score:
                best_match_score = match_score
                best_label_final = candidate_label

        if best_label_final and best_label_final not in valid_results:
            print(
                f"WARNING: Tie-breaker returned invalid {mode} value: {best_label_final}"
            )
            return None

        return best_label_final

    if best_match_label and best_match_label not in valid_results:
        print(f"WARNING: SSIM returned invalid {mode} value: {best_match_label}")
        return None

    return best_match_label


if __name__ == "__main__":
    import ReadVars

    vars_dict = ReadVars.read_tuples_from_file("Vars.txt")

    print("=" * 50)
    print("PLAYER OCR TEST")
    print("=" * 50)
    player_text = ocr_card(
        find_player.detect_boxes(bbox=vars_dict["playerTable"], mode="player")[0][0],
        scale_factor=2,
        mode="player",
        debug=True,
    )
    print(f"Player OCR Result: {player_text}")

    print("\n" + "=" * 50)
    print("DEALER OCR TEST")
    print("=" * 50)
    print(f"Dealer bbox from vars: {vars_dict['dealer']}")
    dealer_text = ocr_card(
        find_player.detect_boxes(bbox=vars_dict["dealer"], mode="dealer")[0][0],
        scale_factor=2,
        mode="dealer",
        debug=True,
    )
    print(f"Dealer OCR Result: {dealer_text}")

    print("\n" + "=" * 50)
    print("SPECIFIC CARD OCR TEST")
    print("=" * 50)
    specific_result = ocr_specific_card((899, 689, 914, 716), debug=True)
    print(f"Specific Cards OCR Result: {specific_result}")
