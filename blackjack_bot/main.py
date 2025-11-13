import threading

import keyboard

import ReadVars

from .bot import BlackjackBot


def main(stop_event=None):
    variables = ReadVars.read_tuples_from_file("Vars.txt")
    bot = BlackjackBot(variables)
    keyboard.add_hotkey("F8", bot.toggle_running)
    print("Press F8 to start/stop script. Press ESC to exit.")

    bot_thread = threading.Thread(target=bot.run, daemon=True)
    bot_thread.start()

    try:
        bot_thread.join()
    except KeyboardInterrupt:
        print("Script interrupted")
