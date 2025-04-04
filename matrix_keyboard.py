#!/usr/bin/env python3
from typing import Any
try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False

from modules.terminal_control_funcs import hide_or_show_cursor, flush_stdin
from matrix_rain import run_matrix, get_config

# if you saved your config in a file you can load it by putting the file name here
# if you want to use the default values, keep this variable as an emtpy string
CONFIG_FILE = 'base_config_keyboard'

CONFIG_DIR_NAME = 'config_keyboard'


# ______________________on_key_event______________________
def on_key_event(currently_pressed: set[str], event: keyboard.KeyboardEvent, lock) -> None:
    """
    Handle keyboard events to update the set of currently pressed keys.

    Depending on the event type ('down' or 'up'), the function adds or removes the key from
    the currently_pressed set in a thread-safe manner.

    Args:
        currently_pressed (set): Set of keys currently pressed.
        event: An event object from the keyboard library.
        lock: A threading.Lock object for thread-safe access.

    Returns:
        None
    """
    # the up event does't necessarily have to be the same as the down event.
    # shift -> modified key on press
    # release shift -> unmodified key on release
    with lock:
        if event.event_type == 'down':
            currently_pressed.add(event.name)
        if event.event_type == 'up':
            currently_pressed.discard(event.name.lower())
            currently_pressed.discard(event.name.upper())


# ______________________update_pressed_keys______________________
def update_pressed_keys(currently_pressed: set[str], lock) -> None:
    """
    Register a global keyboard hook using the keyboard library to track pressed keys.

    This function hooks into keyboard events and updates the currently_pressed set accordingly.

    Args:
        currently_pressed (set): Set to store currently pressed keys.
        lock: A threading.Lock object for thread-safe access.

    Returns:
        None
    """
    if KEYBOARD_AVAILABLE:
        keyboard.hook(lambda event: on_key_event(currently_pressed, event, lock))
    else:
        print("Keyboard module not installed; keyboard functionality is disabled.")
        hide_or_show_cursor(show=True)
        input('Press enter to continue...')
        hide_or_show_cursor(hide=True)


# ______________________change_controls______________________
def change_controls(config: dict[str, Any]) -> None:
    """
    Interactive function to modify keyboard control mappings.

    This function allows the user to view current control mappings, modify them by entering new key combinations,
    and optionally save the changes to the configuration.

    Args:
        config (dict): Configuration dictionary containing current control mappings.

    Returns:
        None
    """
    flush_stdin()
    print()
    new_controls: dict[str, list[str]] = {}
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
        go_back = False
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
            print("\nEnter the keys you would like to use for this control.")
            print("If you want this control to be activated by multiple keys, separate them by a space: a b ctrl")
            print('Using shift is allowed but keep in mind that when you enter "shift a" the control will activate only if you press "a" and then "shift".')
            print('However, if you enter "shift A" the control will be activated if you press "shift" first and then you press "a"')
            print('Also make sure to add any keys needed to press your desired key (for example if you need to press "shift" to be able to press "+" make it: "shift +")')
            print(f"To keep the control the same, just enter the old keys ({' '.join(new_controls[control])})")
            new_keys = input('> ').strip()
            if new_keys:
                new_keys = new_keys.split(' ')
                for new_key in new_keys.copy():
                    try:
                        keyboard.is_pressed(new_key)  # check if key is valid in the keyboard library
                        while new_keys.count(new_key) > 1:  # remove duplicates
                            new_keys.remove(new_key)
                    except Exception as e:
                        print(f'"{new_key}" can not be used because: {e}')
                        go_back = True
                        break
                if go_back:
                    continue
                new_controls[control] = new_keys

                print("""\nControls like "ctrl a" and "a" could both be accidentally used when you press "ctrl" and "a" """)
                print("If you don't want this to happen, enter at least one other key of the control that has extra keys.")
                print("Keep this empty if you don't want to add any.")
                shared_keys = input('> ').strip()
                if shared_keys:
                    shared_keys = shared_keys.split(' ')
                    for shared_key in shared_keys.copy():
                        try:
                            keyboard.is_pressed(shared_key)
                        except Exception as e:
                            print(f'"{shared_key}" can not be used because: {e}')
                            go_back = True
                            break
                    if go_back:
                        continue
                    new_controls['check_if_pressed'] += shared_keys

                    for key in new_controls['check_if_pressed'].copy():
                        while new_controls['check_if_pressed'].count(key) > 1:
                            new_controls['check_if_pressed'].remove(key)

        else:
            print("Name wasn't found.")
    if save:
        config['controls'] = new_controls
    hide_or_show_cursor(hide=True)


# ______________________run_keyboard_matrix______________________
def run_keyboard_matrix() -> None:
    """
    Initialize and run the Matrix rain animation using the keyboard library for keyboard input.

    This function loads the configuration, sets up a keyboard hook to track key presses,
    and starts the main Matrix animation loop.

    Returns:
        None
    """
    config = get_config(file_name=CONFIG_FILE, dir_name=CONFIG_DIR_NAME)
    run_matrix(update_pressed_keys, change_controls, config)


if __name__ == '__main__':
    run_keyboard_matrix()
