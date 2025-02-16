#!/usr/bin/env python3
import random
import time
import os
import sys
import json
import collections
import threading
try:
    import pathvalidate
    PATHVALIDATE_AVAILABLE = True
except ImportError:
    PATHVALIDATE_AVAILABLE = False

# if you saved your config in a file you can load it by putting the file name here
# if you want to use the default values, keep this variable as an emtpy string
CONFIG_FILE = ''

CONFIG_DIR_NAME = 'config'


# ______________________hide_or_show_cursor______________________
def hide_or_show_cursor(hide=False, show=False):
    """
    Toggle the visibility of the terminal cursor.

    Args:
        hide (bool): If True, hide the terminal cursor.
        show (bool): If True, show the terminal cursor.

    Note:
        Only one of `hide` or `show` should be True at a time.
    """
    if hide:
        sys.stdout.write("\u001b[?25l")
        sys.stdout.flush()
    elif show:
        sys.stdout.write("\u001b[?25h")
        sys.stdout.flush()


# ______________________flush_stdin______________________
def flush_stdin():
    """
    Flush the standard input buffer, discarding any pending input.

    This is useful before prompting the user to ensure no unintended keystrokes are processed.
    """
    if os.name == 'nt':
        import msvcrt
        while msvcrt.kbhit():
            msvcrt.getch()
    else:
        import termios
        termios.tcflush(sys.stdin, termios.TCIFLUSH)


# ______________________parse_ansi_color______________________
def parse_ansi_color(ansi: str):
    """
    Parse an ANSI escape code and extract its RGB color and boldness flag.

    Args:
        ansi (str): ANSI escape code string (e.g., "\u001b[38;2;R;G;Bm").

    Returns:
        tuple: A tuple containing a tuple of RGB values (R, G, B) as integers and a boolean
               indicating if the text is bold.
    """
    is_bold = False
    parts = ansi.split('[')[1].rstrip("m").split(";")
    if len(parts) == 6 and parts[0] in ['0', '1']:
        if parts[0] == '1':
            is_bold = True
        parts.pop(0)
    if parts[0] == "38" and parts[1] == "2" and len(parts) >= 5:
        return (int(parts[2]), int(parts[3]), int(parts[4])), is_bold


# ______________________extend_colors______________________
def extend_colors(default_colors: tuple, new_length: int, config: dict):
    """
    Generate an extended gradient of ANSI color codes by interpolating between given colors.

    This function interpolates between the colors provided in `default_colors` to create
    a gradient with `new_length` colors. It caches results in the configuration's 
    "extended_color_cache" to avoid redundant calculations.

    Args:
        default_colors (tuple): A tuple of ANSI escape codes representing colors.
        new_length (int): The desired number of colors in the extended gradient.
        config (dict): Configuration dictionary that includes caching information.

    Returns:
        list: A list of ANSI escape codes representing the extended color gradient.
    """
    max_cache_size = 250
    key = (tuple(default_colors), new_length)
    cache = config["extended_color_cache"]

    if key in cache:
        # Mark as recently used
        cache.move_to_end(key)
        return cache[key]

    if new_length <= 1:
        cache[key] = default_colors
        cache.move_to_end(key)
        if len(cache) > max_cache_size:
            cache.popitem(last=False)
        return default_colors

    extended = []
    n = len(default_colors)
    for i in range(new_length):
        t = i / (new_length - 1)  # relative position in the new color list
        pos = t * (n - 1)  # find index(float) in default colors that's at the same relative position as in the new one
        idx = int(pos)
        # Fractional distance between idx and the next color, used for interpolation (ranges from 0 to 1).
        # If idx is the last color, set t2 to 1.0 to avoid out-of-bounds errors.
        t2 = pos - idx if idx < n - 1 else 1.0
        # find the r, g, b components of the first color with a smaller index
        rgb1, is_bold1 = parse_ansi_color(default_colors[idx])
        # find the next color, if we are the end of the list take the last one itself
        rgb2, is_bold2 = parse_ansi_color(default_colors[min(idx + 1, n - 1)])
        # find the weighted average between the 2 colors based on the distance from the first one:
        r = int(round(rgb1[0] * (1 - t2) + rgb2[0] * t2))
        g = int(round(rgb1[1] * (1 - t2) + rgb2[1] * t2))
        b = int(round(rgb1[2] * (1 - t2) + rgb2[2] * t2))
        if is_bold1 and i == 0:
            extended.append(f"\u001b[1;38;2;{r};{g};{b}m")
        else:
            extended.append(f"\u001b[38;2;{r};{g};{b}m")

    cache[key] = extended
    cache.move_to_end(key)
    if len(cache) > max_cache_size:
        cache.popitem(last=False)
    return extended


# ______________________make_sequence______________________
def make_sequence(config: dict):
    """
    Create a new falling character sequence for a column.

    A sequence consists of a list of random characters, a speed, and color information.
    The sequence length, speed, and characters are determined based on the provided configuration.

    Args:
        config (dict): Configuration dictionary containing parameters such as sequence length,
                       speed, characters, and colors.

    Returns:
        dict: A dictionary representing a sequence with keys:
              - 'chars': list of characters,
              - 'final_char': current bottom position (as float),
              - 'speed': falling speed,
              - 'colors': base color tuple,
              - 'colors_extended': extended color gradient (initially empty).
    """
    seq_length = random.randint(config["min_sequence_length"], config["max_sequence_length"])
    if random.random() > config['background_chance']:
        colors = config['colors']
    else:
        colors = random.choice(tuple(config['background_colors'].keys()))
    return {'chars': [random.choice(config["characters"]) for _ in range(seq_length)],
            'final_char': 0,
            'speed': random.uniform(config["min_sequence_speed"], config["max_sequence_speed"]),
            'colors': colors,
            'colors_extended': []}


# ______________________columns_to_rows______________________
def columns_to_rows(columns: list, config: dict):
    """
    Convert column sequences into a list of strings representing terminal rows.

    This function iterates over each row and column to build a string for display,
    taking into account sequence positions, visibility, spacing between columns, and color gradients.

    Args:
        columns (list): List of columns, where each column is a list of sequences.
        config (dict): Configuration dictionary containing display settings.

    Returns:
        list: A list of strings, each representing a row to be displayed in the terminal.
    """
    rows = []
    for row_index in range(config["amount_of_rows"]):
        row = []
        for i, column in enumerate(columns):
            if not column:
                row.append(' ')
                continue

            if config['space_between_columns'] and i % 2 == 1:
                row.append(' ')
                continue

            # Find the sequence in the column covering this row based with the highest visibility.
            seq_to_display = None
            seq_to_display_brightness = None
            for sequence in column:
                seq_len = len(sequence['chars'])
                # final_char is a float because of different speeds, this is the same as round()
                seq_bottom = int(sequence['final_char'] + 0.5)
                seq_top = seq_bottom - seq_len + 1
                if seq_top <= row_index <= seq_bottom:  # sequence covers this row
                    if sequence['colors'] == config['colors']:  # after finding first fully bright sequence, use it
                        seq_to_display = sequence
                        break

                    seq_brightness = config['background_colors'][sequence['colors']]

                    if not seq_to_display:
                        seq_to_display = sequence
                        seq_to_display_brightness = seq_brightness
                    else:
                        if seq_brightness > seq_to_display_brightness:  # if a sequence with higher brightness is found, use it
                            seq_to_display = sequence
                            seq_to_display_brightness = config['background_colors'][seq_to_display['colors']]

            if seq_to_display is None:
                row.append(' ')
            else:
                seq_len = len(seq_to_display['chars'])
                seq_bottom = int(seq_to_display['final_char'] + 0.5)
                # seq_top = seq_bottom - seq_len + 1 # this isn't used

                # Calculate display_index so that the head (index 0) is at the bottom.
                display_index = seq_bottom - row_index

                # prevents constant lookups if the extended color has already been found/made
                if not seq_to_display['colors_extended']:
                    # sequences can have different lengths than there are colors, so we need to extend the colors
                    colors_extended = extend_colors(seq_to_display["colors"], seq_len, config)
                    seq_to_display['colors_extended'] = colors_extended
                else:
                    colors_extended = seq_to_display['colors_extended']

                # Map display_index to the gradient.
                color_index = int((len(colors_extended) - 1) * (display_index / max(seq_len - 1, 1)))

                color = colors_extended[color_index]
                char = seq_to_display['chars'][display_index]
                row.append(f"{color}{char}\u001b[0m")  # \u001b[0m just resets the color (it isn't visible in the rain)
        rows.append(''.join(row))
    return rows


# ______________________update_column______________________
def update_column(column: list, config: dict):
    """
    Update the falling sequences within a single column.

    Each sequence's position is advanced based on its speed. Sequences that move completely
    off the display are removed. New sequences may be added based on a random chance.

    Args:
        column (list): A list of sequence dictionaries in a column.
        config (dict): Configuration dictionary with parameters for sequence behavior.

    Returns:
        list: The updated list of sequences for the column.
    """
    new_column = []
    if len(column) == 0:  # if the column is empty, create a new sequence with some probability
        return [make_sequence(config)] if random.random() < config["new_sequence_chance"] else []

    for sequence in column:
        # if the sequence is fully below the last row, we don't want to append it to the new column list
        if sequence['final_char'] > (config["amount_of_rows"] + len(sequence['chars'])):
            continue

        new_final_char = sequence['final_char'] + sequence['speed']

        if config["mode"] and int(sequence['final_char'] + 0.5) != int(new_final_char + 0.5):
            # Shift the sequence chars if it moves down this frame. (final_char from 2.3 to 2.4 would not move down)
            sequence['chars'].pop()
            sequence['chars'].insert(0, random.choice(config["characters"]))

        # chance to change a character that is not the first/lowest one to a new random character
        if config["random_char_change_chance"]:
            for idx in range(len(sequence['chars'])):
                if random.random() < config["random_char_change_chance"] and idx != 0:
                    sequence['chars'][idx] = random.choice(config["characters"])

        sequence['final_char'] = new_final_char
        new_column.append(sequence)

    # if the highest sequence is fully visible, create a new sequence with some chance
    if new_column:
        if config['visibility_priority'] == 'higher':
            first_sequence = new_column[0]
        elif config['visibility_priority'] == 'lower':
            first_sequence = new_column[-1]
        if first_sequence['final_char'] >= len(first_sequence["chars"]) and random.random() < config["new_sequence_chance"]:
            # changes the order in which valid sequences are checked in columns_to_rows
            if config['visibility_priority'] == 'higher':
                new_column.insert(0, make_sequence(config))
            elif config['visibility_priority'] == 'lower':
                new_column.append(make_sequence(config))
    return new_column


# ______________________update_columns______________________
def update_columns(columns: list, config: dict, clear: bool):
    """
    Update all columns and adjust the number of columns based on the configuration.

    This function updates each column's sequences and adds or removes columns if the configuration
    for the number of columns has changed. It also determines whether a full screen clear is required.

    Args:
        columns (list): List of columns (each a list of sequences).
        config (dict): Configuration dictionary with display and sequence settings.
        clear (bool): Flag indicating whether the display should be cleared.

    Returns:
        tuple: A tuple (new_columns, clear) where:
               - new_columns is the updated list of columns,
               - clear is a boolean indicating if a screen clear is needed.
    """
    # remove or add columns if config["amount_of_columns"] changed
    if len(columns) > config["amount_of_columns"]:
        columns = columns[:config["amount_of_columns"]]
        clear = True
    elif len(columns) < config["amount_of_columns"]:
        columns += [[] for _ in range(config["amount_of_columns"] - len(columns))]
        clear = True

    if config['space_between_columns']:
        new_columns = []
        for i, column in enumerate(columns):
            if i % 2 == 1:  # there is no need to update sequences if they aren't visible
                new_columns.append(column)
            else:
                new_columns.append(update_column(column, config))
    else:
        new_columns = [update_column(column, config) for column in columns]
    return new_columns, clear


# ______________________update_sequence_and_background_colors______________________
def update_sequence_and_background_colors(config: dict, columns: list):
    """
    Update the colors of sequences and background based on the current configuration.

    This function recalculates background colors by reducing brightness and applies changes to
    existing sequences, updating their extended color gradients if necessary.

    Args:
        config (dict): Configuration dictionary containing color settings.
        columns (list): List of columns with sequences to update.

    Returns:
        None
    """
    old_background_colors = list(config['background_colors'].keys())
    config['background_colors'] = {}
    make_random = False

    # create a background color by reducing all colors' rgb values using reduction_rate
    for reduction_rate in config['background_brightness_reduction']:
        new_colors = []
        for color in config['colors']:
            rgb, is_bold = parse_ansi_color(color)
            r, g, b = [int(value * reduction_rate) for value in rgb]
            if is_bold:
                new_colors.append(f"\u001b[1;38;2;{r};{g};{b}m")
            else:
                new_colors.append(f"\u001b[38;2;{r};{g};{b}m")

        # reduction_rate is used in columns_to_rows to determine which sequence to display
        config['background_colors'][tuple(new_colors)] = reduction_rate

    if len(config['background_colors']) != len(old_background_colors):
        make_random = True

    for column in columns:
        for sequence in column:
            sequence['colors_extended'] = []
            if sequence['colors'] in old_background_colors:  # sequence was a background color before color change
                if make_random:
                    sequence['colors'] = random.choice(tuple(config['background_colors'].keys()))
                else:
                    # if possible keep the background color's brightness the same
                    index = old_background_colors.index(sequence['colors'])
                    sequence['colors'] = tuple(config['background_colors'].keys())[index]
            else:
                sequence['colors'] = config['colors']  # update the sequences colors if it isn't a background color


# ______________________keys_are_pressed______________________
def keys_are_pressed(currently_pressed: set, lock, config: dict, keys):
    """
    Check if the specified keys are currently pressed.

    This function verifies that all keys in the provided `keys` list are pressed, while ensuring
    that no interfering keys (as defined in the configuration under 'check_if_pressed') are active.

    Args:
        currently_pressed (set): Set of keys currently pressed.
        lock: A threading.Lock instance for thread-safe access.
        config (dict): Configuration dictionary containing control key settings.
        keys (list or str): The key or list of keys to check for.

    Returns:
        bool: True if all required keys are pressed and no interfering keys are active; False otherwise.
    """
    with lock:
        # prevents accidentally using multiple controls that share keys
        for prevent_key in config['controls']['check_if_pressed']:
            if prevent_key not in keys and prevent_key in currently_pressed:
                return False

        for key in keys:
            if key not in currently_pressed:
                return False
        return True


# ______________________check_keys______________________
def check_keys(currently_pressed: set, lock, count: list, columns: list, config: dict, change_controls: callable):
    """
    Process keyboard input and update configuration and sequences accordingly.

    This function handles various keyboard commands to control aspects such as speed, color, sequence
    length, and more. It returns updated timing counters, column states, and flags indicating whether
    a screen clear or color update is needed.

    Args:
        currently_pressed (set): Set of keys currently pressed.
        lock: A threading.Lock instance for thread-safe access.
        count (list): List of timestamp counters for debouncing key presses.
        columns (list): List of columns containing sequences.
        config (dict): Configuration dictionary with various settings.
        change_controls (callable): Function to change control key mappings. (requires "config" as a parameter)

    Returns:
        tuple: A tuple (count, columns, clear, update_colors) where:
               - count: Updated debounce timestamp list.
               - columns: Updated columns list.
               - clear (bool): Flag indicating if the screen should be cleared.
               - update_colors (bool): Flag indicating if color updates are required.
    """
    cur_time = time.time()
    time_passed = [cur_time - t for t in count]
    time_used = 0
    clear = False
    update_colors = False

    if keys_are_pressed(currently_pressed, lock, config, ['ctrl', 'c']):
        raise KeyboardInterrupt

    # more speed:
    if time_passed[time_used] > 0.08 and config['time_between_frames'] > 0.001 and keys_are_pressed(currently_pressed, lock, config, config['controls']['speed_up']):
        count[time_used] = cur_time
        config["time_between_frames"] /= 1.03
    time_used += 1

    # less speed
    if time_passed[time_used] > 0.08 and keys_are_pressed(currently_pressed, lock, config, config['controls']['slow_down']):
        count[time_used] = cur_time
        config["time_between_frames"] *= 1.03
    time_used += 1

    # pause:
    if time_passed[time_used] > 0.3 and keys_are_pressed(currently_pressed, lock, config, config['controls']['pause']):
        while keys_are_pressed(currently_pressed, lock, config, config['controls']['pause']):
            time.sleep(0.01)
        while True:
            time.sleep(0.01)
            if keys_are_pressed(currently_pressed, lock, config, config['controls']['pause']):
                count[time_used] = time.time()
                break
    time_used += 1

    # mode:
    if time_passed[time_used] > 0.3 and keys_are_pressed(currently_pressed, lock, config, config['controls']['mode_char']):
        count[time_used] = cur_time
        config["mode"] = not config["mode"]
    time_used += 1

    # space between columns:
    if time_passed[time_used] > 0.3 and keys_are_pressed(currently_pressed, lock, config, config['controls']['make_space_between_columns']):
        count[time_used] = cur_time
        config["space_between_columns"] = not config["space_between_columns"]
    time_used += 1

    # reverse priority:
    if time_passed[time_used] > 0.3 and keys_are_pressed(currently_pressed, lock, config, config['controls']['change_visibility_priority']):
        count[time_used] = cur_time
        for i in range(len(columns)):
            columns[i] = columns[i][::-1]
        if config['visibility_priority'] == 'lower':
            config['visibility_priority'] = 'higher'
        else:
            config['visibility_priority'] = 'lower'
    time_used += 1

    # auto size:
    if time_passed[time_used] > 0.3 and keys_are_pressed(currently_pressed, lock, config, config['controls']['auto_size_char']):
        count[time_used] = cur_time
        config["auto_size"] = not config["auto_size"]
    time_used += 1

    # less rows:
    if time_passed[time_used] > 0.09 and config["amount_of_rows"] > 0 and keys_are_pressed(currently_pressed, lock, config, config['controls']['less_rows']):
        count[time_used] = cur_time
        config["amount_of_rows"] -= 1
        clear = True
    time_used += 1

    # more rows
    if time_passed[time_used] > 0.09 and config["amount_of_rows"] < 100 and keys_are_pressed(currently_pressed, lock, config, config['controls']['more_rows']):
        count[time_used] = cur_time
        config["amount_of_rows"] += 1
        clear = True
    time_used += 1

    # less columns:
    if time_passed[time_used] > 0.05 and config["amount_of_columns"] > 0 and keys_are_pressed(currently_pressed, lock, config, config['controls']['less_columns']):
        count[time_used] = cur_time
        config["amount_of_columns"] -= 1
        clear = True
    time_used += 1

    # more columns:
    if time_passed[time_used] > 0.05 and config["amount_of_columns"] < 220 and keys_are_pressed(currently_pressed, lock, config, config['controls']['more_columns']):
        count[time_used] = cur_time
        config["amount_of_columns"] += 1
        clear = True
    time_used += 1

    # less sequence chance:
    if time_passed[time_used] > 0.1 and keys_are_pressed(currently_pressed, lock, config, config['controls']['less_new_sequence_chance']):
        count[time_used] = cur_time
        config["new_sequence_chance"] /= 1.045
    time_used += 1

    # more sequence chance:
    if time_passed[time_used] > 0.1 and config["new_sequence_chance"] <= 1 and keys_are_pressed(currently_pressed, lock, config, config['controls']['more_new_sequence_chance']):
        count[time_used] = cur_time
        config["new_sequence_chance"] *= 1.045
    time_used += 1

    # less random char change:
    if time_passed[time_used] > 0.15 and keys_are_pressed(currently_pressed, lock, config, config['controls']['less_random_char']):
        count[time_used] = cur_time
        config["random_char_change_chance"] /= 1.05
        if config["random_char_change_chance"] < 0.005:
            config["random_char_change_chance"] = 0
        time_used += 1

    # more random char change
    if time_passed[time_used] > 0.15 and config["random_char_change_chance"] <= 1 and keys_are_pressed(currently_pressed, lock, config, config['controls']['more_random_char']):
        count[time_used] = cur_time
        if config["random_char_change_chance"] == 0:
            config["random_char_change_chance"] = 0.005
        config["random_char_change_chance"] *= 1.05
    time_used += 1

    # save:
    if keys_are_pressed(currently_pressed, lock, config, config['controls']['save_config']):
        flush_stdin()
        print()
        hide_or_show_cursor(show=True)
        save_to_new = False
        update = False
        if not config['folder_is_valid']:
            print(f'''\nThe folder "{config['dir_name']}" isn't valid.''')
            print("You won't be able to save your config")
            input('Press enter to continue...')
            hide_or_show_cursor(hide=True)
        else:
            print("\nYou have chosen to save your current config.\n")
            print('new/n = save to a new file')
            print(f'update/u = update "{config['file_name']}"')
            print('exit/e = leave without saving your config')

            while True:
                command = input('> ').lower().strip()

                if command in ['exit', 'e']:
                    break
                elif command in ['new', 'n']:
                    save_to_new = True
                    break
                elif command in ['update', 'u']:
                    if not config['file_is_valid']:
                        print(f"\nThe file you have entered ({config['file_name']}) isn't valid.")
                        print('Please save to a new file or exit.')
                        continue
                    update = True
                    break
                else:
                    print('Please enter one of the given commands: new/e, update/u, exit/e')

            hide_or_show_cursor(hide=True)

            if save_to_new:
                save_config(config, update=False)
            elif update:
                save_config(config, update=True)
        clear = True

    # load:
    if keys_are_pressed(currently_pressed, lock, config, config['controls']['load_config']):
        flush_stdin()
        print()
        hide_or_show_cursor(show=True)

        if not config['folder_is_valid']:
            print(f'''\nThe folder "{config['dir_name']}" isn't valid.''')
            print("You won't be able to load your config from any file")
            input('Press enter to continue...')
            hide_or_show_cursor(hide=True)
        else:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            config_dir = os.path.join(script_dir, config['dir_name'])
            os.makedirs(config_dir, exist_ok=True)
            file_names = [f for f in os.listdir(config_dir) if os.path.isfile(os.path.join(config_dir, f))]
            print("\nYou have chosen to load a config from a file\n")
            print('show/s = show all available files')
            print('exit/e = keep current config')
            print('Enter the name of the file you want to load your config from.')
            while True:
                load_file = input('> ').strip()

                if load_file.lower() in ['exit', 'e']:
                    break

                if load_file.lower() in ['show', 's']:
                    if len(file_names) == 0:
                        print('No files have been found.\n')
                        continue

                    print('\nFiles:')

                    line = file_names[0]
                    i = 2
                    for file_name in file_names[1:]:
                        if i <= 3:
                            line += ', ' + file_name
                        else:
                            i = 1
                            print(line + ',')
                            line = file_name
                        i += 1
                    print(line + '\n')
                    continue

                if not load_file.endswith('.json'):
                    load_file += '.json'

                if load_file not in file_names:
                    print("File wasn't found.\n")
                else:
                    new_config = get_config(file_name=load_file, dir_name=config['dir_name'])
                    for key in config:
                        config[key] = new_config[key]
                    break
        hide_or_show_cursor(hide=True)
        clear = True
        update_colors = True

    # first bold:
    if keys_are_pressed(currently_pressed, lock, config, config['controls']['first_bold']):
        colors = list(config["colors"])
        parts = colors[0].split('[')
        if parts[1][:2] == '1;':
            pass
        else:
            parts[1] = '1;' + parts[1]
        colors[0] = '['.join(parts)
        config["colors"] = tuple(colors)
        update_colors = True

    # first white
    if keys_are_pressed(currently_pressed, lock, config, config['controls']['first_white']):
        colors = list(config["colors"])
        colors[0] = "\u001b[38;2;255;255;255m"
        config["colors"] = tuple(colors)
        update_colors = True

    # first bright
    if keys_are_pressed(currently_pressed, lock, config, config['controls']['first_bright']):
        # this doesn't work on custom colors
        colors = list(config["colors"])
        first_color, is_bold = parse_ansi_color(colors[1])
        r, g, b = first_color
        if r == 255 and 255 not in (g, b):
            colors[0] = "\u001b[38;2;255;190;190m"
        elif g == 255 and 255 not in (r, b):
            colors[0] = "\u001b[38;2;210;255;210m"
        elif g == 255 and b == 255 and r != 255:
            colors[0] = "\u001b[38;2;225;255;255m"
        config["colors"] = tuple(colors)
        update_colors = True

    # red
    if keys_are_pressed(currently_pressed, lock, config, config['controls']['red']):
        config["colors"] = ("\u001b[38;2;255;64;64m",
                            "\u001b[38;2;255;0;0m",
                            "\u001b[38;2;218;0;0m",
                            "\u001b[38;2;185;0;0m",
                            "\u001b[38;2;152;0;0m",
                            "\u001b[38;2;124;0;0m",
                            "\u001b[38;2;90;0;0m",
                            "\u001b[38;2;56;0;0m",
                            "\u001b[38;2;30;0;0m")
        update_colors = True

    # green
    if keys_are_pressed(currently_pressed, lock, config, config['controls']['green']):
        config["colors"] = ("\u001b[38;2;64;255;64m",
                            "\u001b[38;2;0;255;0m",
                            "\u001b[38;2;0;218;0m",
                            "\u001b[38;2;0;186;0m",
                            "\u001b[38;2;0;154;0m",
                            "\u001b[38;2;0;122;0m",
                            "\u001b[38;2;0;90;0m",
                            "\u001b[38;2;0;58;0m",
                            "\u001b[38;2;0;34;0m")
        update_colors = True

    # blue
    if keys_are_pressed(currently_pressed, lock, config, config['controls']['blue']):
        config["colors"] = ("\u001b[38;2;64;255;255m",
                            "\u001b[38;2;0;255;255m",
                            "\u001b[38;2;0;208;208m",
                            "\u001b[38;2;0;176;176m",
                            "\u001b[38;2;0;144;144m",
                            "\u001b[38;2;0;112;112m",
                            "\u001b[38;2;0;80;80m",
                            "\u001b[38;2;0;48;48m",
                            "\u001b[38;2;0;24;24m")
        update_colors = True

    # create color:
    if keys_are_pressed(currently_pressed, lock, config, config['controls']['create_color']):
        flush_stdin()
        print()
        hide_or_show_cursor(show=True)
        print("\nYou have chosen to create a new color or use your created colors.")
        print('\nnew/n = create a new color')
        print('use/u = use a previously created color')
        print('delete/d = delete a previous created color')
        print('exit/e = leave without doing anything\n')

        while True:
            command = input('> ').strip().lower()
            print()

            if command in ['new', 'n', 'use', 'u', 'delete', 'd', 'exit', 'e']:
                break
            else:
                print("Please enter a valid command")

        if command in ['new', 'n'] and command not in ['exit', 'e']:
            if len(config['custom_colors']) >= 10:
                print('You can only create 10 custom colors.')
                input('Press enter to continue...')
            else:
                print('show/s = show current color names')
                while True:
                    print("\nEnter a name for your color:")
                    name = input('> ').strip()

                    if name.lower() in ['show', 's']:
                        print('\nNames:')
                        print(', '.join(config['custom_colors'].keys()))
                        continue
                    if name:
                        if name in config['custom_colors']:
                            print('Name is already in use.')
                        elif len(name) >= 30:
                            print("Name is too long")
                        else:
                            break

                print("\nTo create a new list of colors you will enter each colors' RGB values like this: R, G, B.")
                print('exit/e = leave when you are done creating individual colors')
                i = 1
                colors = []
                make_color = True
                while True:
                    print(f'\nColor {i}:')
                    user_input = input('> ').replace(' ', '').lower()

                    if user_input in ['e', 'exit']:
                        if len(colors) == 0:
                            make_color = False
                        if len(colors) == 1:  # if color length were 1, it would cause indexing issues in some places
                            colors.append(colors[0])
                        break

                    rgb = user_input.split(',')
                    if len(rgb) != 3:
                        print("Please enter 3 values: R, G, B (for example: 150, 255, 0)")
                        continue
                    go_back = False

                    try:
                        for value in rgb:
                            value = float(value)
                            if not 0 <= value <= 255:
                                print('Values have to range from 0 to 255')
                                go_back = True
                                break
                    except ValueError:
                        print("RGB values have to be numbers")
                        continue
                    if go_back:
                        continue

                    r, g, b = rgb
                    colors.append(f"\u001b[38;2;{r};{g};{b}m")
                    i += 1

                    if i > 12:
                        print("Maximum number of colors reached (12).")
                        break
                if make_color:
                    config['custom_colors'][name] = tuple(colors)
                    print('Color has been added successfully.')
                    input('Press enter to continue...')

        elif command in ['delete', 'd'] and command not in ['exit', 'e']:
            print('show/s = show current color names')
            print('exit/e = leave without deleting a color')
            while True:
                print("\nEnter the name of the color you want to delete:")
                name = input('> ').strip()

                if name.lower() in ['exit', 'e']:
                    break
                if name.lower() in ['show', 's']:
                    print('\nNames:')
                    print(', '.join(config['custom_colors'].keys()))
                    continue
                if name in config['custom_colors']:
                    config['custom_colors'].pop(name)
                    print('Color has been deleted successfully.')
                    input('Press enter to continue...')
                    break
                else:
                    print("Color wasn't found")

        elif command in ['use', 'u'] and command not in ['exit', 'e']:
            print('show/s = show current color names')
            print('exit/e = keep current color')
            while True:
                print("\nEnter the name of the color you want to use:")
                name = input('> ').strip()

                if name.lower() in ['show', 's']:
                    print('\nNames:')
                    print(', '.join(config['custom_colors'].keys()))
                    continue
                if name.lower() in ['exit', 'e']:
                    break
                if name in config['custom_colors']:
                    config['colors'] = config['custom_colors'][name]
                    break
                else:
                    print("Color wasn't found")

        update_colors = True
        hide_or_show_cursor(hide=True)
        clear = True

    # background:
    if keys_are_pressed(currently_pressed, lock, config, config['controls']['change_background_brightness']):
        flush_stdin()
        print()
        hide_or_show_cursor(show=True)
        old_values = config['background_brightness_reduction']
        config['background_brightness_reduction'] = []

        print('\nYou have chosen to change the background.\n')
        print(f"Old background brightness multipliers: {', '.join([str(value) for value in old_values])}")
        print('Enter the value for reduction in brightness for each background color from 0 to 1 (0.6 --> brightness will reduce to 60%)')
        print("exit/e = if you dont't want to make any more backgrounds (if you haven't entered any new values, the old values will be kept)")
        i = 1
        while True:
            print(f'\nBackground {i} reduction rate:')
            reduction_rate = input('> ').strip().lower()
            if reduction_rate in ['e', 'exit']:
                if len(config['background_brightness_reduction']) != 0:
                    break
                else:
                    config['background_brightness_reduction'] = old_values
                    break
            
            try:
                reduction_rate = float(reduction_rate)
            except ValueError:
                print('Reduction rate has to be a number.')
                continue

            if not 0 < reduction_rate < 1:
                print('Reduction rate has to be between 0 and 1.')
                continue
            config['background_brightness_reduction'].append(reduction_rate)
            i += 1

            if i > 3:
                print("You have entered all 3 available background colors.")
                break

        while True:
            print(f"\nEnter the chance for a sequence to become part of the background(previous: {config['background_chance']}): ")
            try:
                background_chance = float(input('> '))
            except ValueError:
                print('Background chance has to be a number.')
                continue                    
            if not 0 <= background_chance <= 1:
                print('Background chance has to be from 0 to 1.')
                continue
            config['background_chance'] = background_chance
            break

        hide_or_show_cursor(hide=True)
        update_colors = True
        clear = True

    # chars 01
    if keys_are_pressed(currently_pressed, lock, config, config['controls']['chars_01']):
        config["characters"] = '01'

    # chars orig
    if keys_are_pressed(currently_pressed, lock, config, config['controls']['chars_default']):
        config["characters"] = "ﾊﾐﾋｰｳｼﾅﾓﾆｻﾜﾂｵﾘｱﾎﾃﾏｹﾒｴｶｷﾑﾕﾗｾﾈｽﾀﾇﾍｦｲｸｺｿﾁﾄﾉﾌﾤﾨﾛﾝ012345789:.=*+-<>"

    # chars any
    if keys_are_pressed(currently_pressed, lock, config, config['controls']['set_any_chars']):
        flush_stdin()
        print()
        hide_or_show_cursor(show=True)
        while True:
            print("\nEnter the characters you want to use (keep it empty and add them if you don't want to change anything)")
            chars = input('> ')
            if len(chars) > 100:
                print("The maximum amount of characters is 100.")
                continue
            while True:
                print('\nadd/a = add the chosen characters to the current character set')
                print('replace/r = use only chosen characters')
                add = input('> ').lower().strip()
                if add in ["a", "add", "r", "replace"]:
                    break
            if add in ["a", "add"]:
                if len(chars + config["characters"]) > 100:
                    print('The combined number of characters would exceed 100.')
                    continue
                config["characters"] += chars
            elif add == 'r':
                config["characters"] = chars if chars else ' '
            break

        hide_or_show_cursor(hide=True)
        clear = True

    # sequence speed:
    if keys_are_pressed(currently_pressed, lock, config, config['controls']['change_speed_diff']):
        flush_stdin()
        print()
        hide_or_show_cursor(show=True)
        print('\nYou have chosen to change individual sequence speeds.')
        print("It is recommended not to go over 1")
        while True:
            try:
                print(f'\nNew min speed for sequences (previous: {config["min_sequence_speed"]}):')
                min_speed = float(input('> '))
                print(f'\nNew max speed for sequences (previous: {config["max_sequence_speed"]}):')
                max_speed = float(input('> '))
            except ValueError:
                print('Min and max speed have to be numbers.')
                continue

            if min_speed > max_speed:
                print("Min speed can't be more than max speed.")
            elif min_speed <= 0 or max_speed <= 0:
                print("Min and max speed have to be greater than 0.")
            else:
                break

        config["min_sequence_speed"] = min_speed
        config["max_sequence_speed"] = max_speed
        hide_or_show_cursor(hide=True)
        clear = True

    # sequence length:
    if keys_are_pressed(currently_pressed, lock, config, config['controls']['change_seq_length']):
        flush_stdin()
        print()
        hide_or_show_cursor(show=True)
        print('\nYou have chosen to change individual sequence lengths')
        while True:
            try:
                print(f'\nNew min length for sequences (previous: {config["min_sequence_length"]}):')
                min_length = int(input('> '))
                print(f'\nNew max length for sequences (previous: {config["max_sequence_length"]}):')
                max_length = int(input('> '))
            except ValueError:
                print('Min and max length have to be whole numbers.')
                continue

            if min_length > max_length:
                print("Min length can't be more than max length.")
            elif min_length <= 0 or max_length <= 0:
                print("Min and max length have to be greater than 0.")
            elif max_length > 40:
                print("Max length can't exceed 40.")
            else:
                break

        config["min_sequence_length"] = min_length
        config["max_sequence_length"] = max_length
        hide_or_show_cursor(hide=True)
        clear = True

    # change controls
    if keys_are_pressed(currently_pressed, lock, config, config['controls']['change_controls']):
        change_controls(config)
        clear = True

    # print values:
    if keys_are_pressed(currently_pressed, lock, config, config['controls']['cur_values']):
        flush_stdin()
        hide_or_show_cursor(show=True)
        print(f'''
new_sequence_chance = {round(config["new_sequence_chance"], 4)} (Chance for a new sequence to start if there is space; range: 0 to 1)
random_char_change_chance = {round(config["random_char_change_chance"], 4)} (Chance for characters to change mid-sequence)

time_between_frames = {round(config["time_between_frames"], 4)} (Delay between frame updates)

min_sequence_speed = {round(config["min_sequence_speed"], 4)} (1/sequence_speed = frames to move the sequence)
max_sequence_speed = {round(config["max_sequence_speed"], 4)} (range(speed): MIN_SEQUENCE_SPEED to MAX_SEQUENCE_SPEED)

min_sequence_length = {config["min_sequence_length"]}
max_sequence_length = {config["max_sequence_length"]}

AMOUNT_OF_COLUMNS = {config["amount_of_columns"]}
AMOUNT_OF_ROWS = {config["amount_of_rows"]}

mode = {config["mode"]} (Toggle for sequence update behavior)
auto_size = {config["auto_size"]} (Toggle for automatic resizing of columns and rows)
space_between_columns = {config['space_between_columns']}
visibility_priority = {config['visibility_priority']}

background_brightness_reduction = {config['background_brightness_reduction']}
characters = {config["characters"]}
colors = {config["colors"]}
background_colors = {config["background_colors"]}
''')
        input('Press enter to continue...')
        hide_or_show_cursor(hide=True)
        clear = True

    # print help
    if keys_are_pressed(currently_pressed, lock, config, config['controls']['show_help_message']):
        flush_stdin()
        print()
        hide_or_show_cursor(show=True)
        print(f'''Controls:

    {', '.join(config['controls']['show_help_message'])} = show help message
    {', '.join(config['controls']['cur_values'])} = display current values

    {', '.join(config['controls']['speed_up'])} = speed up (relative to current speed)
    {', '.join(config['controls']['slow_down'])} = slow down (relative to current speed)

    {', '.join(config['controls']['change_speed_diff'])} = make some sequences move slower or faster (for example once every 3 frames)
    {', '.join(config['controls']['change_seq_length'])} = set a new min and max length for sequences

    {', '.join(config['controls']['pause'])} = (un)pause
    {', '.join(config['controls']['mode_char'])} = toggles if the first letter of a sequence is random and the rest follow or if the sequence remains unchanged
    {', '.join(config['controls']['auto_size_char'])} = adjusts matrix length and width based on the terminal's size
    {', '.join(config['controls']['make_space_between_columns'])} = create a space in between all columns
    {', '.join(config['controls']['change_visibility_priority'])} = changes priority of displaying sequences on the same row if the sequences have the same brightness

    {', '.join(config['controls']['more_random_char'])} = increase chance for characters to change mid-sequence
    {', '.join(config['controls']['less_random_char'])} = decrease chance for characters to change mid-sequence

    {', '.join(config['controls']['less_rows'])} = shorten matrix length (rows)
    {', '.join(config['controls']['more_rows'])} = increase matrix length (rows)
    {', '.join(config['controls']['less_columns'])} = reduce number of columns
    {', '.join(config['controls']['more_columns'])} = increase number of columns

    {', '.join(config['controls']['more_new_sequence_chance'])} = increase the chance of a new sequence starting (relative to current chance)
    {', '.join(config['controls']['less_new_sequence_chance'])} = decrease the chance of a new sequence starting (relative to current chance)

    {', '.join(config['controls']['first_bold'])} = make the first character bold
    {', '.join(config['controls']['first_white'])} = make first character white
    {', '.join(config['controls']['first_bright'])} = make first character white but in the shade of the other colors (doesn't work for custom colors)
    {', '.join(config['controls']['blue'])} = change color to blue
    {', '.join(config['controls']['green'])} = change color to green
    {', '.join(config['controls']['red'])} = change color to red
    {', '.join(config['controls']['create_color'])} = create a new color or use your created colors
    {', '.join(config['controls']['change_background_brightness'])} = create a background by making some sequences less bright

    {', '.join(config['controls']['chars_01'])} = change characters to "01"
    {', '.join(config['controls']['chars_default'])} = reset characters to default set
    {', '.join(config['controls']['set_any_chars'])} = prompt for input to add or replace characters

    {', '.join(config['controls']['save_config'])} = save current values and controls (rows, color...)
    {', '.join(config['controls']['load_config'])} = load values and controls from a file

    {', '.join(config['controls']['change_controls'])} = change your controls
    {', '.join(config['controls']['disable_controls'])} = disable keyboard controls temporarily
    {', '.join(config['controls']['enable_controls'])} = re-enable keyboard controls

    ctrl+c = stop matrix rain
''')
        input('Press enter to continue...')
        hide_or_show_cursor(hide=True)
        clear = True

    # remove controls:
    if keys_are_pressed(currently_pressed, lock, config, config['controls']['disable_controls']):
        config['controls_activated'] = False

    return count, columns, clear, update_colors


# ______________________clear_if_necessary______________________
def clear_if_necessary(clear: bool, config: dict, terminal_size=None, old_terminal_size=None):
    """
    Clear the terminal screen if conditions indicate that a refresh is needed.

    The screen will be cleared if a change in terminal size is detected or if the current number
    of rows exceeds the terminal dimensions.

    Args:
        clear (bool): Initial flag indicating if a clear has been requested.
        config (dict): Configuration dictionary containing display settings.
        terminal_size (os.terminal_size, optional): Current terminal size.
        old_terminal_size (os.terminal_size, optional): Previous terminal size.

    Returns:
        None
    """
    if not (terminal_size and old_terminal_size):
        return

    if old_terminal_size != terminal_size:
        clear = True

    # if the rows reach below the terminal size, keep clearing
    # if this didn't happen, it would result in the terminal having all previous frames
    # the multiplication ensures that when there are too many columns the terminal will also be cleared because they increase the amount of rows
    if terminal_size.lines <= config["amount_of_rows"] * (1 + (config["amount_of_columns"] - 1)//terminal_size.columns):
        clear = True

    if clear:
        os.system('cls' if os.name == 'nt' else 'clear')


# ______________________adjust_size______________________
def adjust_size(config: dict, terminal_size=None):
    """
    Adjust the configuration's row and column settings based on the terminal size.

    This function sets the number of rows to the terminal's line count minus one (to avoid constant clearing)
    and sets the number of columns to the terminal's column count.

    Args:
        config (dict): Configuration dictionary.
        terminal_size (os.terminal_size, optional): Current terminal size.

    Returns:
        None
    """
    if terminal_size:
        # - 1 ensures that constant clearing doesn't happen and that typing into the terminal doesn't cause issues by moving it
        config["amount_of_rows"] = terminal_size.lines - 1
        config["amount_of_columns"] = terminal_size.columns


# ______________________get_config______________________
def get_config(file_name=CONFIG_FILE, dir_name=CONFIG_DIR_NAME):
    """
    Load the configuration from a JSON file, or return the default configuration if the file is not found.

    The function validates the folder and file names if the pathvalidate module is available.
    If the file is found and valid, its contents are loaded and merged into the configuration; otherwise,
    default configuration settings are used.

    Args:
        file_name (str): Name of the configuration file (without path).
        dir_name (str): Name of the directory where configuration files are stored.

    Returns:
        dict: A configuration dictionary with settings for the Matrix rain animation.
    """
    hide_or_show_cursor(show=True)
    if PATHVALIDATE_AVAILABLE:
        try:
            pathvalidate.validate_filename(filename=dir_name)
            folder_is_valid = True
        except pathvalidate.ValidationError as e:
            folder_is_valid = False
            print(f'''\nThe folder "{dir_name}" isn't valid. Reason:''')
            print(f"{e}\n")
            print('The default values will be used instead.')
            input('Press enter to continue...')
    else:
        print("pathvalidate not installed; skipping folder validation.")
        input('Press enter to continue...')
        folder_is_valid = True

    if file_name and folder_is_valid:
        if not file_name.endswith(".json"):
            file_name += ".json"

        if PATHVALIDATE_AVAILABLE:
            try:
                pathvalidate.validate_filename(filename=file_name)
                file_is_valid = True
            except pathvalidate.ValidationError as e:
                print("The file you have chosen isn't valid.")
                print(f"{e}\n")
                print('The default values will be used instead.')
                input('Press enter to continue...')
                file_is_valid = True
        else:
            print("pathvalidate not installed; skipping file validation.")
            input('Press enter to continue...')
            file_is_valid = True

        if file_is_valid:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            config_dir = os.path.join(script_dir, dir_name)
            os.makedirs(config_dir, exist_ok=True)  # make the folder if it doesn't exist
            file_path = os.path.join(config_dir, file_name)

            try: 
                with open(file_path, 'r', encoding="utf-8") as file:
                    config = json.load(file)
                    config["extended_color_cache"] = collections.OrderedDict()
                    config['file_is_valid'] = True
                    config['folder_is_valid'] = folder_is_valid
                    config['file_name'] = file_name
                    config['dir_name'] = dir_name
                    config['background_colors'] = {}
                    config['colors'] = tuple(config['colors'])

                    for key in config['custom_colors']:
                        config['custom_colors'][key] = tuple(config['custom_colors'][key])

                    for control in config['controls'].copy():
                        try:
                            config['controls'][control] = config['controls'][control].split(' ')
                        except AttributeError:
                            pass

                    hide_or_show_cursor(hide=True)
                    return config

            except FileNotFoundError:
                print(f'''The file "{file_name}" wasn't found.''')
                print('The default values will be used instead.')
                input('Press enter to continue...')
            hide_or_show_cursor(hide=True)

    controls = {
        "speed_up": "f",
        "slow_down": "s",
        "change_speed_diff": "d",
        "pause": "p",
        "mode_char": "q",
        "auto_size_char": "a",
        "make_space_between_columns": "shift space",
        "change_visibility_priority": "v",
        "more_random_char": "shift up",
        "less_random_char": "shift down",
        "less_rows": "up",
        "more_rows": "down",
        "less_columns": "left",
        "more_columns": "right",
        "more_new_sequence_chance": "shift =",
        "less_new_sequence_chance": "-",
        "first_bold": "b shift",
        "first_white": "w",
        "first_bright": "w shift",
        "blue": "b",
        "green": "g",
        "red": "r",
        "change_background_brightness": "8",
        "create_color": "9",
        "change_seq_length": "l",
        "chars_01": "0",
        "chars_default": "1",
        "set_any_chars": "2",
        "change_controls": "shift c",
        "show_help_message": "h",
        "cur_values": "shift h",
        "save_config": "s shift",
        "load_config": "l shift",
        "disable_controls": "shift backspace",
        "enable_controls": "ctrl shift enter",
        "check_if_pressed": "shift ctrl"
    }
    for control in controls.copy():
        try:
            controls[control] = controls[control].split(' ')
        except AttributeError:
            pass
    return {
        "controls": controls,
        "new_sequence_chance": 0.018,
        "random_char_change_chance": 0.01,
        "time_between_frames": 0.045,
        "min_sequence_length": 3,
        "max_sequence_length": 20,
        "min_sequence_speed": 0.2,
        "max_sequence_speed": 0.8,
        "amount_of_columns": 140,
        "amount_of_rows": 20,
        "mode": True,
        "auto_size": True,
        "space_between_columns": True,
        "visibility_priority": 'higher',
        "characters": "ﾊﾐﾋｰｳｼﾅﾓﾆｻﾜﾂｵﾘｱﾎﾃﾏｹﾒｴｶｷﾑﾕﾗｾﾈｽﾀﾇﾍｦｲｸｺｿﾁﾄﾉﾌﾤﾨﾛﾝ012345789:.=*+-<>",
        "colors": (
            "\u001b[38;2;255;255;255m",  # White: Reset color (default terminal color)
            "\u001b[38;2;0;255;0m",      # Brightest green
            "\u001b[38;2;0;208;0m",      # Brighter green
            "\u001b[38;2;0;176;0m",      # Bright green
            "\u001b[38;2;0;144;0m",      # Medium green
            "\u001b[38;2;0;112;0m",      # Slightly dark green
            "\u001b[38;2;0;80;0m",       # Dark green
            "\u001b[38;2;0;48;0m",       # Darker green
            "\u001b[38;2;0;24;0m"        # Very dark green
        ),
        "custom_colors": {},
        'background_brightness_reduction': [0.6],
        'background_colors': {},
        'background_chance': 0.5,
        "extended_color_cache": collections.OrderedDict(),
        'file_is_valid': False,
        'folder_is_valid': folder_is_valid,
        'file_name': file_name,
        'dir_name': dir_name,
        "controls_activated": True
    }


# ______________________save_config______________________
def save_config(config: dict, update=False, dir_name=None):
    """
    Save the current configuration to a JSON file.

    If `update` is True, the existing configuration file is overwritten; otherwise, a new file is created.
    The function performs validation on the folder and file names if possible, and excludes transient data
    (such as caches) from being saved.

    Args:
        config (dict): The configuration dictionary to save.
        update (bool): Whether to update an existing configuration file (True) or create a new one (False).
        dir_name (str, optional): The directory to save the configuration file in. If None, uses the directory
                                  specified in the config.

    Returns:
        None
    """
    if dir_name is None:
        dir_name = config['dir_name']
    if PATHVALIDATE_AVAILABLE:
        try:
            pathvalidate.validate_filename(filename=dir_name)
        except pathvalidate.ValidationError as e:
            print(f'''\nThe folder "{dir_name}" isn't valid. Reason:''')
            print(f"{e}\n")
            print("You won't be able to save your config")
            input('Press enter to continue...')
            hide_or_show_cursor(hide=True)
            return
    else:
        print("pathvalidate not installed; skipping folder validation.")
        input('Press enter to continue...')

    hide_or_show_cursor(show=True)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_dir = os.path.join(script_dir, dir_name)
    os.makedirs(config_dir, exist_ok=True)

    # makes sure not change config when modifying it to save:
    s_config = {}
    for key in config:
        try:
            s_config[key] = config[key].copy()
        except AttributeError:
            s_config[key] = config[key]
    s_config.pop('extended_color_cache', None)
    s_config.pop('background_colors', None)
    s_config.pop('file_name', None)
    s_config.pop('dir_name', None)
    s_config.pop('folder_is_valid', None)
    s_config.pop('file_is_valid', None)
    for control in s_config['controls'].copy():
        try:
            s_config['controls'][control] = ' '.join(s_config['controls'][control])
        except AttributeError:
            pass

    if update:
        file_name = config['file_name']
        if not file_name.endswith(".json"):
            file_name += ".json"

        file_path = os.path.join(config_dir, file_name)

        with open(file_path, 'w', encoding="utf-8") as file:
            json.dump(s_config, file, indent=4)
    else:
        file_names = [f for f in os.listdir(config_dir) if os.path.isfile(os.path.join(config_dir, f))]

        numbers_used = []
        for file in file_names:
            file = file.replace('.json', '')
            if file.startswith('config'):
                numbers_used.append(file[len('config'):])
        # create an original file name
        new_number = 1
        while True:
            if str(new_number) not in numbers_used:
                break
            new_number += 1

        file_name = f'config{new_number}.json'

        while True:
            print(f'\nDo you want to save to "{file_name}"?')
            print('yes/y = save to this file')
            print('no/n = create a new name')
            make_custom_name = input('> ').lower().strip()

            if make_custom_name in ['y', 'yes']:
                make_custom_name = False
                break
            elif make_custom_name in ['n', 'no']:
                make_custom_name = True
                break

        if make_custom_name:
            while True:
                print('\nEnter the name you would like to use. ')
                new_name = input('> ').strip()
                if not new_name.endswith(".json"):
                    new_name += ".json"

                if PATHVALIDATE_AVAILABLE:
                    try:
                        pathvalidate.validate_filename(filename=new_name)
                    except pathvalidate.ValidationError as e:
                        print("The name you have entered isn't valid. Reason:")
                        print(f"{e}\n")
                        continue
                else:
                    print("pathvalidate not installed; skipping file validation.")
                    input('Press enter to continue...')

                if new_name in file_names:
                    print(f'\n{new_name} already exists.')
                    print('You can save to this file but that will cause the current data on this file to be erased.')
                    print('Do you want to save to this file anyway?')
                    save_anyway = input('> ').lower().strip()
                    if save_anyway in ['y', 'yes']:
                        break
                else:
                    break
            file_path = os.path.join(config_dir, new_name)
        else:
            file_path = os.path.join(config_dir, file_name)

        with open(file_path, 'w', encoding="utf-8") as file:
            json.dump(s_config, file, indent=4)
    hide_or_show_cursor(hide=True)


# ______________________run_matrix______________________
def run_matrix(update_pressed_keys: callable, change_controls: callable, config=None):
    """
    Run the Matrix rain animation in the terminal.

    This function loads the configuration, initializes the columns for the animation,
    sets up keyboard input handling, and enters the main animation loop. The animation
    can be controlled via various keyboard commands.

    Args:
        update_pressed_keys (callable): Function to update the set of currently pressed keys. (requires "currently_pressed, lock" as parameters)
        change_controls (callable): Function to change keyboard control mappings. (requires "config" as a parameter)
        config (dict, optional): Configuration dictionary. If None, the configuration is loaded via get_config().

    Returns:
        None
    """
    try:
        if config is None:
            config = get_config()  # load config from a file or use default config

        columns = [[] for _ in range(config["amount_of_columns"])]  # initialize columns
        # intialize count, make sure to update range() when adding new controls that use this
        count = [time.time() for _ in range(15)]
        try:
            old_terminal_size = os.get_terminal_size()
        except OSError:
            old_terminal_size = None
        clear = True
        update_colors = True
        hide_or_show_cursor(hide=True)

        currently_pressed = set()
        lock = threading.Lock()
        update_pressed_keys(currently_pressed, lock)

        while True:
            start_time = time.time()
            try:
                terminal_size = os.get_terminal_size()
            except OSError:
                terminal_size = None

            if update_colors:
                update_sequence_and_background_colors(config, columns)

            if config["auto_size"] and terminal_size:
                adjust_size(config, terminal_size)

            columns, clear = update_columns(columns, config, clear)

            rows = "\n".join(columns_to_rows(columns, config))

            clear_if_necessary(clear, config, terminal_size, old_terminal_size)
            old_terminal_size = terminal_size
            clear = False

            sys.stdout.write("\u001b[H" + rows + "\n")  # \u001b[H moves the cursor to row and column 0
            sys.stdout.flush()

            end_time = start_time + config["time_between_frames"]
            while True:
                if config['controls_activated'] and currently_pressed:
                    count, columns, check_clear, check_update_colors = check_keys(currently_pressed, lock, count, columns, config, change_controls)
                    if check_clear:
                        clear = True
                    if check_update_colors:
                        update_colors = True
                elif currently_pressed and keys_are_pressed(currently_pressed, lock, config, config['controls']['enable_controls']):
                    config['controls_activated'] = True

                remaining = end_time - time.time()
                time.sleep(min(0.008, max(remaining, 0.001)))
                if time.time() > end_time:
                    break

    except KeyboardInterrupt:
        t = time.time()
        while True:
            try:
                if time.time() - t > 0.1:
                    break
                time.sleep(0.1)
            except KeyboardInterrupt:
                continue
    finally:
        flush_stdin()
        hide_or_show_cursor(show=True)
        print('\nMatrix rain stopped')


def filler_func(*args, **kwargs):
    """This function is used when no keyboard input is necessary."""
    pass


if __name__ == '__main__':
    run_matrix(filler_func, filler_func)
