# BlackjackGUI.py
import threading
import tkinter as tk
from os import path

import BlackjackMain  # contains main()
import find_player
import NumberGrabber  # contains NumberGrabberTest function
import OCR  # contains ocr_card function
import ReadVars  # contains read_tuples_from_file, update_var_in_file, setBBox functions

path_to_dat = path.abspath(path.join(path.dirname(__file__)))

# --- Global Control Variables ---
main_thread = None
stop_event = threading.Event()

# --- Thread Control Functions ---


def run_main():
    """Run BlackjackMain.main() in a background thread so GUI stays responsive."""
    global main_thread, stop_event

    if main_thread and main_thread.is_alive():
        print("Main script is already running.")
        return

    stop_event.clear()
    main_thread = threading.Thread(target=main_runner)
    main_thread.daemon = True
    main_thread.start()
    print("Started BlackjackMain in a background thread.")


def main_runner():
    """Thread target to run BlackjackMain.main()."""
    try:
        BlackjackMain.main(
            stop_event=stop_event
        )  # expects your main() to respect stop_event
    except TypeError:
        # Fallback if main() doesn’t accept stop_event argument yet
        print("BlackjackMain.main() doesn’t support stop_event — running normally.")
        BlackjackMain.main()
    except Exception as e:
        print(f"Error in BlackjackMain thread: {e}")


def stop_main():
    """Signal BlackjackMain.main() to stop."""
    global stop_event
    if main_thread and main_thread.is_alive():
        stop_event.set()
        print("Stop signal sent to BlackjackMain.")
    else:
        print("No running BlackjackMain thread to stop.")


# --- BBox update functions ---
def update_dealer():
    ReadVars.setDealerBbox()


def update_player_table():
    ReadVars.setPlayerTableBbox()


def update_button_bbox():
    ReadVars.setButtonBbox()


def update_specific_card_bbox():
    ReadVars.setSpecificCardBbox()


# --- Refresh Displayed Vars ---
def refresh_vars():
    """Refresh and show current variable values from Vars.txt."""
    vars_dict = ReadVars.read_tuples_from_file("Vars.txt")
    print("Current Vars:", vars_dict)
    dealer_label.config(text=f"Dealer: {vars_dict.get('dealer')}")
    player_label.config(text=f"Player Table: {vars_dict.get('playerTable')}")
    button_label.config(text=f"Button: {vars_dict.get('buttonBbox')}")
    dynamic_dealer_label.config(
        text=f"Dynamic Dealer BBox: {vars_dict.get('dynamicDealer')} (1=Dynamic, 0=Static)"
    )
    specific_card_label.config(
        text=f"Specific Card BBox: {vars_dict.get('specificCard')}"
    )
    surrender_specific.config(
        text=f"Hit on 15 instead of surrender w/ 7 or 8: {vars_dict.get('surrender15Specific')} (1=Yes, 0=No)"
    )


# --- Testing Functions ---
def run_NumberGrabber():
    vars_dict = ReadVars.read_tuples_from_file("Vars.txt")
    NumberGrabber.NumberGrabberTest(
        playerTableBbox=vars_dict.get("playerTable"), DealerBbox=vars_dict.get("dealer")
    )


def run_OCR_Test():
    vars_dict = ReadVars.read_tuples_from_file("Vars.txt")
    player_text = OCR.ocr_card(
        find_player.detect_boxes(bbox=vars_dict["playerTable"], mode="player")[0][0],
        scale_factor=2,
    )

    if vars_dict.get("dynamicDealer") == 0:
        print("OCR Test, static dealer bbox")
        dealer_text = OCR.ocr_card(vars_dict["dealer"], mode="dealer", scale_factor=2)
    else:
        print("OCR Test, dynamic dealer bbox")
        dealer_bbox = find_player.detect_boxes(
            bbox=vars_dict.get("dealer"), mode="dealer"
        )[0][0]
        dealer_text = OCR.ocr_card(dealer_bbox, mode="dealer", scale_factor=2)

    print(f"Player OCR: {player_text}")
    print(f"Dealer OCR: {dealer_text}")


def run_specific_card_OCR_Test():
    vars_dict = ReadVars.read_tuples_from_file("Vars.txt")
    specific_card_bbox = vars_dict.get("specificCard")
    if specific_card_bbox:
        specific_card_text = OCR.ocr_specific_card(specific_card_bbox)
        print(f"Specific Card OCR: {specific_card_text}")
    else:
        print("Specific Card BBox not set.")


# --- Tkinter GUI setup ---
root = tk.Tk()
root.title("Blackjack Controller")

frame = tk.Frame(root, padx=10, pady=10)
frame.pack()

# Run / Stop main buttons
run_button = tk.Button(
    frame, text="Start Blackjack Main", command=run_main, width=25, height=2
)
run_button.pack(pady=5)

stop_button = tk.Button(
    frame, text="Stop Blackjack Main", command=stop_main, width=25, height=2
)
stop_button.pack(pady=5)

# Update bbox buttons
dealer_button = tk.Button(
    frame,
    text="Set Dealer BBox",
    command=lambda: [update_dealer(), refresh_vars()],
    width=25,
)
dealer_button.pack(pady=5)

player_button = tk.Button(
    frame,
    text="Set Player Table BBox",
    command=lambda: [update_player_table(), refresh_vars()],
    width=25,
)
player_button.pack(pady=5)

button_bbox_button = tk.Button(
    frame,
    text="Set Button BBox",
    command=lambda: [update_button_bbox(), refresh_vars()],
    width=25,
)
button_bbox_button.pack(pady=5)

specific_card_button = tk.Button(
    frame,
    text="Set Specific Card BBox",
    command=lambda: [update_specific_card_bbox(), refresh_vars()],
    width=25,
)
specific_card_button.pack(pady=5)


# Dynamic dealer toggle
def toggle_dynamic_dealer():
    current_value = ReadVars.read_tuples_from_file("Vars.txt").get("dynamicDealer")
    new_value = 0 if current_value == 1 else 1
    ReadVars.update_var_in_file("dynamicDealer", new_value)
    refresh_vars()


dynamic_dealer_button = tk.Button(
    frame, text="Toggle Dynamic Dealer BBox", command=toggle_dynamic_dealer, width=25
)
dynamic_dealer_button.pack(pady=5)

# Labels showing current values
dealer_label = tk.Label(frame, text="Dealer: ")
dealer_label.pack()
player_label = tk.Label(frame, text="Player Table: ")
player_label.pack()
button_label = tk.Label(frame, text="Button: ")
button_label.pack()
dynamic_dealer_label = tk.Label(frame, text="Dynamic Dealer BBox: (1=Yes, 0=No)")
dynamic_dealer_label.pack()
specific_card_label = tk.Label(frame, text="Specific Card BBox: ")
specific_card_label.pack()
surrender_specific = tk.Label(frame, text="Hit on 15 instead of surrender w/ 7 or 8: ")
surrender_specific.pack()

# Test buttons
number_grabber_button = tk.Button(
    frame, text="Run NumberGrabber", command=run_NumberGrabber, width=25, height=2
)
number_grabber_button.pack(pady=5)

ocr_test_button = tk.Button(
    frame, text="Run OCR Test", command=run_OCR_Test, width=25, height=2
)
ocr_test_button.pack(pady=5)

specific_card_test = tk.Button(
    frame,
    text="Run Specific Card OCR Test",
    command=run_specific_card_OCR_Test,
    width=25,
    height=2,
)
specific_card_test.pack(pady=5)

# Instruction note
note_label = tk.Label(
    frame, text="Press F8 to start/stop script. Press ESC to exit.", fg="blue"
)
note_label.pack(pady=10)

# Refresh on start
refresh_vars()

root.mainloop()
