#!/usr/bin/env python3
from matrix_rain import run_matrix, get_config, hide_or_show_cursor, flush_stdin
import time
try:
    from pynput import keyboard
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False

# if you saved your config in a file you can load it by putting the file name here
# if you want to use the default values, keep this variable as an emtpy string
CONFIG_FILE = 'base_config_pynput'

CONFIG_DIR_NAME = 'config_pynput'


# ______________________make_canonical______________________
def make_canonical(key, listener):
    """
    Convert a key event to its canonical form using the listener's canonical() method.

    Args:
        key: A key event from pynput.
        listener: A pynput listener object that provides a canonical() method.

    Returns:
        The canonical key event if the types match; otherwise, returns the original key.
    """
    canonical_key = listener.canonical(key)
    # some keys get their names changed to None and change their type (for example esc, tab...), so we return the original
    if type(key) is type(canonical_key):
        return canonical_key
    else:
        return key


# ______________________key_to_str______________________
def key_to_str(key):
    """
    Convert a key event to its lowercase string representation.

    Args:
        key: A key event from pynput (can be a Key or KeyCode).

    Returns:
        str: The lowercase string representation of the key.
    """
    # For KeyCode (i.e. regular letter/number keys), return the character in lowercase.
    if hasattr(key, 'char') and key.char is not None:
        return key.char.lower()
    else:
        # For special keys (e.g. Key.shift, Key.ctrl), convert "Key.shift" -> "shift"
        s = str(key)  # e.g. "Key.space", "Key.shift"
        if s.startswith("Key."):
            return s[4:].lower()
        return s.lower()


# ______________________on_press______________________
def on_press(key, currently_pressed: set, lock):
    """
    Callback function for key press events.

    When a key is pressed, its string representation is added to the currently_pressed set.

    Args:
        key: The key event.
        currently_pressed (set): Set to store currently pressed keys.
        lock: A threading.Lock object for thread-safe access.
    """
    with lock:
        currently_pressed.add(key_to_str(key))


# ______________________on_release______________________
def on_release(key, currently_pressed: set, lock):
    """
    Callback function for key release events.

    When a key is released, its string representation is removed from the currently_pressed set.

    Args:
        key: The key event.
        currently_pressed (set): Set containing keys that are currently pressed.
        lock: A threading.Lock object for thread-safe access.
    """
    with lock:
        currently_pressed.discard(key_to_str(key))


# ______________________update_pressed_keys______________________
def update_pressed_keys(currently_pressed, lock):
    """
    Set up the pynput keyboard listener to update the set of currently pressed keys.

    This function starts a pynput keyboard listener that calls the on_press and on_release callbacks
    to maintain an updated set of pressed keys.

    Args:
        currently_pressed (set): Set to store currently pressed keys.
        lock: A threading.Lock object for thread-safe access.

    Returns:
        None
    """
    if PYNPUT_AVAILABLE:
        listener = keyboard.Listener(
            on_press=lambda key: on_press(make_canonical(key, listener), currently_pressed, lock),
            on_release=lambda key: on_release(make_canonical(key, listener), currently_pressed, lock)
        )
        listener.start()
    else:
        print("Pynput not installed; keyboard functionality is disabled.")
        hide_or_show_cursor(show=True)
        input('Press enter to continue...')
        hide_or_show_cursor(hide=True)


# ______________________change_controls______________________
def change_controls(config: dict):
    """
    Interactive function to modify the control key mappings.

    This function prompts the user to view, change, or save control mappings for the Matrix rain animation.
    It allows capturing new key combinations via the pynput listener and updating the configuration accordingly.

    Args:
        config (dict): Configuration dictionary containing current control mappings.

    Returns:
        None
    """
    flush_stdin()
    print()
    new_controls = dict()
    hide_or_show_cursor(show=True)
    for dict_key in config['controls']:
        try:
            new_controls[dict_key] = config['controls'][dict_key].copy()
        except AttributeError:
            new_controls[dict_key] = config['controls'][dict_key]
    save = False
    print('\nYou have chosen to change your controls')
    print('\nold/o = show controls without new changes')
    print('new/n = show controls with new changes')
    print('save/s = save changes')
    print('exit/e = exit without chaning controls')
    while True:
        print('\nEnter the name of the control you would like to change:')
        control = input('> ').lower().strip()
        if control in ['o', 'old']:
            for key in config['controls']:
                print(f"{key}: {' '.join(config['controls'][key])}")
            continue
        elif control in ['new', 'n']:
            for key in new_controls:
                print(f"{key}: {' '.join(new_controls[key])}")
            continue
        elif control in ['save', 's']:
            save = True
            break
        elif control in ['exit', 'e']:
            break

        elif control in config['controls'].keys():
            print("\nlisten/l = let the program register any keys pressed until a cutoff key is pressed")
            print("exit/e = choose a different control")
            command = input('> ').strip().lower()
            if command in ['exit', 'e']:
                continue

            elif command in ['listen', 'l']:
                def listen_for_stop(key, stop_key):
                    stop_key.append(key_to_str(key))
                    return False

                while True:
                    stop_key = []
                    print("\nPress the key that will stop the listening.")
                    time.sleep(0.3)
                    with keyboard.Listener(on_press=lambda key: listen_for_stop(listen_stop.canonical(key) if isinstance(key, keyboard.KeyCode) else key, stop_key)) as listen_stop:
                        listen_stop.join()

                    stop_key = stop_key[0]
                    flush_stdin()
                    print(f'\n"{stop_key}" will be used to stop listening for keys.')
                    print("again/a = choose a different key to stop")
                    print("continue/c = start listening for keys for the controls")

                    while True:
                        command = input('> ').strip().lower()
                        if command in ['again', 'a']:
                            listen_again = True
                            break
                        elif command in ['continue', 'c']:
                            listen_again = False
                            break
                        else:
                            print("Unknown command\n")
                    if not listen_again:
                        break

                while True:
                    captured_keys = set()

                    def on_press_with_stop(key):
                        key = key_to_str(key)
                        if key == stop_key:
                            return False
                        captured_keys.add(key)
                        print(f"keys pressed so far: {', '.join(captured_keys)}")

                    time.sleep(0.2)
                    print("\nListening for keys")
                    with keyboard.Listener(on_press=lambda key: on_press_with_stop(make_canonical(key, listen))) as listen:
                        listen.join()

                    flush_stdin()
                    replace = True
                    if control == "check_if_pressed":
                        print('\nYou have chosen the control "check_if_pressed".')
                        print('Therefore you can replace it or just append to it.')
                        print('Enter "append/a" or "replace/r"')
                        while True:
                            request = input('> ').strip().lower()
                            if request in ['append', 'a']:
                                replace = False
                                break
                            elif request in ['replace', 'r']:
                                replace = True
                                break
                            else:
                                print('\nUnknown command')

                    print(f"\nDo you want to use these keys for the control? ({', '.join(captured_keys)})")

                    while True:
                        command = input('> ').strip().lower()
                        if command in ['yes', 'y']:
                            use_keys = True
                            break
                        elif command in ['no', 'n']:
                            use_keys = False
                            break
                        else:
                            print("\nPlease enter yes/y or no/n")
                    if use_keys:
                        if captured_keys:
                            if replace:
                                new_controls[control] = list(captured_keys)
                            else:
                                new_controls[control].extend(list(captured_keys))
                            print("""\nControls like "ctrl a" and "a" could both be accidentally used when you press "ctrl" and "a" """)
                            print('''If you don't want this to happen, make sure to change "check_if_pressed"''')
                            print("so that at least one extra key of the control that has extra keys is there.")
                            break
                        else:
                            print("No keys have been registered.")
                            continue
            else:
                print("\nUnknown command. Try again.")
        else:
            print("Name wasn't found.")
    if save:
        config['controls'] = new_controls
    hide_or_show_cursor(hide=True)


# ______________________run_pynput_matrix______________________
def run_pynput_matrix():
    """
    Initialize and run the Matrix rain animation using the pynput library for keyboard input.

    This function loads the configuration, sets up keyboard listeners with pynput, and starts the
    main Matrix animation loop.

    Returns:
        None
    """
    config = get_config(file_name=CONFIG_FILE, dir_name=CONFIG_DIR_NAME)
    run_matrix(update_pressed_keys, change_controls, config)


if __name__ == '__main__':
    run_pynput_matrix()
