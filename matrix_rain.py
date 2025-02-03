import random
import time
import os
import keyboard
import sys
import json
import pathvalidate

# if you saved your config in a file you can load it by putting the file name here
# if you want to use the global variables, keep this variable as an emtpy string
CONFIG_FILE = 'controls1'


CONTROLS_DIR_NAME = 'controls' # this shouldn't be changed

# Global constants (control keys, help messages, etc.) remain unchanged.
NEW_SEQUENCE_CHANCE = 0.02
RANDOM_CHAR_CHANGE_CHANCE = 0
TIME_BETWEEN_FRAMES = 0.045

MIN_SEQUENCE_LENGTH = 3
MAX_SEQUENCE_LENGTH = 15 

MIN_SEQUENCE_SPEED = 0.3  # 1/sequence_speed = frames to move the sequence; sequence_speed has a range from MIN_SEQUENCE_SPEED to MAX_SEQUENCE_SPEED
MAX_SEQUENCE_SPEED = 1

AMOUNT_OF_COLUMNS = 150
AMOUNT_OF_ROWS = 20

MODE = True  # If True, the first letter of a sequence is random and the rest follow; otherwise the sequence remains unchanged.
AUTO_SIZE = False

CHARACTERS = "ﾊﾐﾋｰｳｼﾅﾓﾆｻﾜﾂｵﾘｱﾎﾃﾏｹﾒｴｶｷﾑﾕﾗｾﾈｽﾀﾇﾍｦｲｸｺｿﾁﾄﾉﾌﾤﾨﾛﾝ012345789:.=*+-<>"

# Green gradient colors (8 shades, from brightest to darkest)
COLORS = [
    "\u001b[0m",              # White: Reset color (default terminal color)
    "\u001b[38;2;0;255;0m",   # Brightest green
    "\u001b[38;2;0;208;0m",   # Brighter green
    "\u001b[38;2;0;176;0m",   # Bright green
    "\u001b[38;2;0;144;0m",   # Medium green
    "\u001b[38;2;0;112;0m",   # Slightly dark green
    "\u001b[38;2;0;80;0m",    # Dark green
    "\u001b[38;2;0;48;0m",    # Darker green
    "\u001b[38;2;0;16;0m"    # Very dark green
]

# Control key assignments:
SPEED_UP = 'f'
SLOW_DOWN = 's'

CHANGE_SPEED_DIFF = 'c'

PAUSE = 'p'
MODE_CHAR = 'q'
AUTO_SIZE_CHAR = 'a'

MORE_RANDOM_CHAR = 'shift+up'
LESS_RANDOM_CHAR = 'shift+down'

SHORTEN_LENGTH = 'up'
INCREASE_LENGTH = 'down'

LESS_COLUMNS = 'left'
MORE_COLUMNS = 'right'

MORE_NEW_SEQUENCE_CHANCE = '+'
LESS_NEW_SEQUENCE_CHANCE = '-'

FIRST_BOLD = 'shift+b'
FIRST_WHITE = 'w'
FIRST_BRIGHT = 'shift+w'
BLUE = 'b'
GREEN = 'g'
RED = 'r'

CHANGE_SEQ_LENGTH = 'l'

CHARS_01 = '0'
CHARS_ORIGINAL = '1'
CHARS_ANY = '9'

SHOW_HELP_MESSAGE = 'h'
CUR_VALUES = 'v'

SAVE_CONFIG = 'shift+s'
LOAD_CONFIG = 'shift+l'

REMOVE_CONTROLS = 'backspace'
RETURN_CONTROLS = 'ctrl+shift+enter'

HELP_MESSAGE = f'''Controls:
    up --> arrow up,...

    {SPEED_UP} = speed up (relative to current speed)
    {SLOW_DOWN} = slow down (relative to current speed)

    {CHANGE_SPEED_DIFF} = make some sequences move slower or faster (for example once every 3 frames)

    {PAUSE} = (un)pause
    {MODE_CHAR} = toggles if the first letter of a sequence is random and the rest follow or if the sequence remains unchanged
    {AUTO_SIZE_CHAR} = adjusts matrix length and width based on the terminal's size

    {MORE_RANDOM_CHAR} = increase chance for characters to change mid-sequence
    {LESS_RANDOM_CHAR} = decrease chance for characters to change mid-sequence
              
    {SHORTEN_LENGTH} = shorten matrix length (rows)
    {INCREASE_LENGTH} = increase matrix length (rows)
    {LESS_COLUMNS} = reduce number of columns
    {MORE_COLUMNS} = increase number of columns
              
    plus("{MORE_NEW_SEQUENCE_CHANCE}") = increase the chance of a new sequence starting (relative chance)
    minus("{LESS_NEW_SEQUENCE_CHANCE}") = decrease the chance of a new sequence starting (relative chance)

    {FIRST_BOLD} = make the first character bold
    {FIRST_WHITE} = make first character white
    {FIRST_BRIGHT} = make first character white but in the shade of the other colors
    {BLUE} = change color to blue
    {GREEN} = change color to green
    {RED} = change color to red

    {CHANGE_SEQ_LENGTH} = set a new min and max length for sequences
              
    {CHARS_01} = change characters to "01"
    {CHARS_ORIGINAL} = reset characters to original set
    {CHARS_ANY} = prompt for input to add or replace characters

    {SAVE_CONFIG} = save current values (TIME_BETWEEN_FRAMES...)
    {LOAD_CONFIG} = load values from a file
              
    {CUR_VALUES} = display current values
    {REMOVE_CONTROLS} = disable keyboard controls temporarily
    {RETURN_CONTROLS} = re-enable keyboard controls
              
    ctrl+c = stop matrix rain
'''


# ______________________parse_ansi_color______________________
def parse_ansi_color(ansi):
    """
    Parse an ANSI color escape code of the form "\u001b[38;2;R;G;Bm" and return the RGB tuple.
    For the reset code ("\u001b[0m"), we return white (255,255,255).
    """
    if ansi == "\u001b[0m":
        return (255, 255, 255)
    try:
        parts = ansi.lstrip("\u001b[").rstrip("m").split(";")
        if len(parts) == 6:
            parts.pop(0)
        if parts[0] == "38" and parts[1] == "2" and len(parts) >= 5:
            return (int(parts[2]), int(parts[3]), int(parts[4]))
    except Exception:
        pass
    return (255, 255, 255)


# ______________________extend_colors______________________
def extend_colors(original_colors, new_length, config):
    """
    Return a color gradient of new_length using linear interpolation.
    Uses caching stored in config["extended_color_cache"].
    """
    key = (tuple(original_colors), new_length)
    if key in config["extended_color_cache"]:
        return config["extended_color_cache"][key]
    
    if new_length <= len(original_colors):
        config["extended_color_cache"][key] = original_colors
        return original_colors

    extended = []
    n = len(original_colors)
    for i in range(new_length):
        t = i / (new_length - 1)
        pos = t * (n - 1)
        idx = int(pos)
        t2 = pos - idx if idx < n - 1 else 1.0
        rgb1 = parse_ansi_color(original_colors[idx])
        rgb2 = parse_ansi_color(original_colors[min(idx + 1, n - 1)])
        r = int(round(rgb1[0] * (1 - t2) + rgb2[0] * t2))
        g = int(round(rgb1[1] * (1 - t2) + rgb2[1] * t2))
        b = int(round(rgb1[2] * (1 - t2) + rgb2[2] * t2))
        extended.append(f"\u001b[38;2;{r};{g};{b}m")
    config["extended_color_cache"][key] = extended
    return extended


# ______________________hide_or_show_cursor______________________
def hide_or_show_cursor(hide=False, show=False):
    if hide:
        sys.stdout.write("\u001b[?25l")
    elif show:
        sys.stdout.write("\u001b[?25h")


# ______________________make_sequence______________________
def make_sequence(config):
    """
    Create a new sequence for a column using parameters from config.
    """
    seq_length = random.randint(config["min_sequence_length"], config["max_sequence_length"])
    return {'chars': [random.choice(config["characters"]) for _ in range(seq_length)],
            'cur_final_char': 0,
            'speed': random.uniform(config["min_sequence_speed"], config["max_sequence_speed"])}


# ______________________columns_to_rows______________________
def columns_to_rows(columns, config):
    """
    Convert columns of sequences into rows for terminal display.
    """
    rows = []
    for row_index in range(config["amount_of_rows"]):
        row = []
        for column in columns:
            if not column:
                row.append(' ')
                continue

            # Find the first sequence that should be visible on this row.
            for i, sequence in enumerate(column):
                cur_final_char = int(sequence['cur_final_char'] + 0.5)
                if cur_final_char >= row_index:
                    break

            # Determine if there is a "next" sequence.
            char_index = cur_final_char - row_index
            try:
                next_sequence = column[i + 1]
                next_sequence_char_index = int(next_sequence['cur_final_char'] + 0.5) - row_index
                is_next = True
            except Exception:
                is_next = False

            if 0 <= char_index < len(sequence['chars']):
                seq_len = len(sequence['chars'])

                if seq_len > len(config["colors"]):
                    colors_extended = extend_colors(config["colors"], seq_len, config)
                else:
                    colors_extended = config["colors"]

                # Calculate color index ensuring it is within range.
                color = colors_extended[min(len(colors_extended) - 1, round(len(colors_extended) * char_index / seq_len))]
                char = sequence['chars'][char_index]
                row.append(f"{color}{char}\u001b[0m")

            elif is_next and 0 <= next_sequence_char_index < len(next_sequence['chars']):
                seq_len = len(next_sequence['chars'])

                if seq_len > len(config["colors"]):
                    colors_extended = extend_colors(config["colors"], seq_len, config)
                else:
                    colors_extended = config["colors"]

                color = colors_extended[round(len(colors_extended) * next_sequence_char_index / seq_len)]
                char = next_sequence['chars'][next_sequence_char_index]
                row.append(f"{color}{char}\u001b[0m")
            else:
                row.append(' ')
        rows.append(''.join(row))
    return rows


# ______________________update_column______________________
def update_column(column, config):
    """
    Update a single column of sequences using config.
    """
    new_column = []
    if len(column) == 0:
        return [make_sequence(config)] if random.random() < config["new_sequence_chance"] else []
    
    for sequence in column:
        if config["mode"]:
            # Shift the sequence.
            if int(sequence['cur_final_char'] + 0.5) != int(sequence['cur_final_char'] + sequence['speed'] + 0.5):
                sequence['chars'].pop()
                sequence['chars'].insert(0, random.choice(config["characters"]))
        
        if config["random_char_change_chance"]:
            for idx in range(len(sequence['chars'])):
                if random.random() < config["random_char_change_chance"] and idx != 0:
                    sequence['chars'][idx] = random.choice(config["characters"])
        
        sequence['cur_final_char'] += sequence['speed']
        
        if sequence['cur_final_char'] <= (config["amount_of_rows"] + len(sequence['chars'])):
            new_column.append(sequence)
    
    new_column.sort(key=lambda seq: seq['cur_final_char'])
    if new_column:
        first_sequence = new_column[0]
        if first_sequence['cur_final_char'] >= len(config["colors"]) and random.random() < config["new_sequence_chance"]:
            new_column.insert(0, make_sequence(config))
    return new_column


# ______________________flush_stdin______________________
def flush_stdin():
    """
    Flush the standard input buffer.
    """
    if os.name == 'nt':
        import msvcrt
        while msvcrt.kbhit():
            msvcrt.getch()
    else:
        import termios
        termios.tcflush(sys.stdin, termios.TCIFLUSH)


# ______________________check_keyboard______________________
def check_keyboard(count, columns, config):
    """
    Check keyboard input and update config (and column data) accordingly.
    Returns (updated_count, updated_columns, clear_flag) or ('stop', columns, clear_flag) if controls are disabled.
    """
    cur_time = time.time()
    time_passed = [cur_time - t for t in count]
    time_used = 0
    clear = False

    # speed:
    if time_passed[time_used] > 0.08 and not keyboard.is_pressed('shift') and keyboard.is_pressed(SPEED_UP):
        count[time_used] = cur_time
        config["time_between_frames"] /= 1.02
    time_used += 1

    if time_passed[time_used] > 0.08 and not keyboard.is_pressed('shift') and keyboard.is_pressed(SLOW_DOWN):
        count[time_used] = cur_time
        config["time_between_frames"] *= 1.02
    time_used += 1

    # pause:
    if time_passed[time_used] > 0.25 and keyboard.is_pressed(PAUSE):
        time.sleep(0.25)
        while True:
            time.sleep(0.01)
            if keyboard.is_pressed(PAUSE):
                count[time_used] = time.time()
                break
    time_used += 1

    # mode:
    if time_passed[time_used] > 0.3 and keyboard.is_pressed(MODE_CHAR):
        count[time_used] = cur_time
        config["mode"] = not config["mode"]
    time_used += 1

    # auto size:
    if time_passed[time_used] > 0.3 and keyboard.is_pressed(AUTO_SIZE_CHAR):
        count[time_used] = cur_time
        config["auto_size"] = not config["auto_size"]
    time_used += 1

    # rows:
    if time_passed[time_used] > 0.09 and config["amount_of_rows"] > 0 and not keyboard.is_pressed('shift') and keyboard.is_pressed(SHORTEN_LENGTH):
        count[time_used] = cur_time
        config["amount_of_rows"] -= 1
        clear = True
    time_used += 1

    if time_passed[time_used] > 0.09 and config["amount_of_rows"] < 80 and not keyboard.is_pressed('shift') and keyboard.is_pressed(INCREASE_LENGTH):
        count[time_used] = cur_time
        config["amount_of_rows"] += 1
        clear = True
    time_used += 1

    # columns:
    if time_passed[time_used] > 0.05 and config["amount_of_columns"] > 0 and keyboard.is_pressed(LESS_COLUMNS):
        count[time_used] = cur_time
        config["amount_of_columns"] -= 1
        if columns:
            columns.pop(-1)
        clear = True
    time_used += 1

    if time_passed[time_used] > 0.05 and config["amount_of_columns"] < 200 and keyboard.is_pressed(MORE_COLUMNS):
        count[time_used] = cur_time
        config["amount_of_columns"] += 1
        columns.append([])
        clear = True
    time_used += 1

    # sequence chance:
    if time_passed[time_used] > 0.1 and keyboard.is_pressed(LESS_NEW_SEQUENCE_CHANCE):
        count[time_used] = cur_time
        config["new_sequence_chance"] /= 1.03
    time_used += 1

    if time_passed[time_used] > 0.1 and config["new_sequence_chance"] <= 1 and (keyboard.is_pressed('=+shift') or keyboard.is_pressed(MORE_NEW_SEQUENCE_CHANCE)):
        count[time_used] = cur_time
        config["new_sequence_chance"] *= 1.03
    time_used += 1

    # random char change:
    if time_passed[time_used] > 0.15 and keyboard.is_pressed(LESS_RANDOM_CHAR):
        count[time_used] = cur_time
        config["random_char_change_chance"] /= 1.05
        if config["random_char_change_chance"] < 0.005:
            config["random_char_change_chance"] = 0
        time_used += 1

    if time_passed[time_used] > 0.15 and config["random_char_change_chance"] <= 1 and keyboard.is_pressed(MORE_RANDOM_CHAR):
        count[time_used] = cur_time
        if config["random_char_change_chance"] == 0:
            config["random_char_change_chance"] = 0.005
        config["random_char_change_chance"] *= 1.05
    time_used += 1

    # save:
    if keyboard.is_pressed(SAVE_CONFIG):
        flush_stdin()
        print()
        hide_or_show_cursor(show=True)
        load = False
        while True:
            load_file = input(f'Do you want to save to a new file or update "{CONFIG_FILE}"?(new(n)/update(u)/exit(e)): ').lower().strip()

            if load_file in ['exit', 'e']:
                load = True
                break
            elif load_file in ['new', 'n']:
                load_file = True
                break
            elif load_file in ['update', 'u']:
                if not config['file_is_valid']:
                    print(f"The file you have entered ({CONFIG_FILE}) isn't valid.")
                    print('Please save to a new file or exit.')
                    continue
                load_file = False
                break
            else:
                print('Try again.')
        hide_or_show_cursor(hide=True)

        if load:
            pass
        elif load_file:
            save_config(config, update=False)
        else:
            save_config(config, update=True)
        clear = True

    # load:
    if keyboard.is_pressed(LOAD_CONFIG):
        load = True
        if not config['folder_is_valid']:
            print("You have not entered a valid folder to load files from")
            input('Press enter to continue...')
            load = False
        flush_stdin()
        print()
        hide_or_show_cursor(show=True)
        if load:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            controls_dir = os.path.join(script_dir, CONTROLS_DIR_NAME)
            os.makedirs(controls_dir, exist_ok=True)
            file_names = [f for f in os.listdir(controls_dir) if os.path.isfile(os.path.join(controls_dir, f))]
            while True:
                print('If you want to see all the files, enter "show(s)"')
                load_file = input(f'Enter the name of the file you want to load or enter "exit(e)" to exit: ').strip()

                if load_file.lower() in ['exit', 'e']:
                    break

                if load_file.lower() in ['show', 's']:
                    if len(file_names) == 0:
                        print('No files have been found.')
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
                    print("File wasn't found.")
                else:
                    new_config = get_config(file_name=load_file)
                    for key in config:
                        config[key] = new_config[key]
                    break
        hide_or_show_cursor(hide=True)
        clear = True
    
    # first color:
    if keyboard.is_pressed(FIRST_BOLD):
        parts = config["colors"][0].split('[')
        if parts[1][:2] == '1;':
            pass
        else:
            parts[1] = '1;' + parts[1]
        config["colors"][0] = '['.join(parts)

    if not keyboard.is_pressed('shift') and keyboard.is_pressed(FIRST_WHITE):
        config["colors"][0] = "\u001b[0m"  # Reset to default white

    if keyboard.is_pressed(FIRST_BRIGHT):
        first_color = parse_ansi_color(config["colors"][1])
        r, g, b = first_color
        if r == 255 and 255 not in (g, b):
            config["colors"][0] = "\u001b[38;2;255;190;190m"
        elif g == 255 and 255 not in (r, b):
            config["colors"][0] = "\u001b[38;2;210;255;210m"
        elif g == 255 and b == 255 and r != 255:
            config["colors"][0] = "\u001b[38;2;225;255;255m"

    # colors
    if keyboard.is_pressed(RED):
        config["colors"] = ["\u001b[38;2;255;64;64m",
                         "\u001b[38;2;255;0;0m",
                         "\u001b[38;2;240;0;0m",
                         "\u001b[38;2;224;0;0m",
                         "\u001b[38;2;208;0;0m",
                         "\u001b[38;2;192;0;0m",
                         "\u001b[38;2;176;0;0m",
                         "\u001b[38;2;160;0;0m",
                         "\u001b[38;2;144;0;0m"]

    if keyboard.is_pressed(GREEN):
        config["colors"] = ["\u001b[38;2;64;255;64m",
                         "\u001b[38;2;0;255;0m",
                         "\u001b[38;2;0;208;0m",
                         "\u001b[38;2;0;176;0m",
                         "\u001b[38;2;0;144;0m",
                         "\u001b[38;2;0;112;0m",
                         "\u001b[38;2;0;80;0m",
                         "\u001b[38;2;0;48;0m",
                         "\u001b[38;2;0;16;0m"]

    if not keyboard.is_pressed('shift') and keyboard.is_pressed(BLUE):
        config["colors"] = ["\u001b[38;2;64;255;255m",
                         "\u001b[38;2;0;255;255m",
                         "\u001b[38;2;0;208;208m",
                         "\u001b[38;2;0;176;176m",
                         "\u001b[38;2;0;144;144m",
                         "\u001b[38;2;0;112;112m",
                         "\u001b[38;2;0;80;80m",
                         "\u001b[38;2;0;48;48m",
                         "\u001b[38;2;0;16;16m"]

    # characters:
    if keyboard.is_pressed(CHARS_01):
        config["characters"] = '01'

    if keyboard.is_pressed(CHARS_ORIGINAL):
        config["characters"] = "ﾊﾐﾋｰｳｼﾅﾓﾆｻﾜﾂｵﾘｱﾎﾃﾏｹﾒｴｶｷﾑﾕﾗｾﾈｽﾀﾇﾍｦｲｸｺｿﾁﾄﾉﾌﾤﾨﾛﾝ012345789:.=*+-<>"

    if keyboard.is_pressed(CHARS_ANY):
        flush_stdin()
        print()
        hide_or_show_cursor(show=True)
        while True:
            chars = input('Characters: ')
            if len(chars) > 100:
                print("Too many characters")
                continue
            while True:
                add = input('Do you want to add to or replace the current characters? ("a" = add, "r" = replace): ').lower().strip()
                if add in ["a", "r"]:
                    break
            if add == 'a':
                if len(chars + config["characters"]) > 100:
                    print('Sorry that would result in too many characters')
                    continue
                config["characters"] += chars
            elif add == 'r':
                config["characters"] = chars if chars else ' '
            break
        
        hide_or_show_cursor(hide=True)
        clear = True

    # sequence speed:
    if not keyboard.is_pressed('ctrl') and keyboard.is_pressed(CHANGE_SPEED_DIFF):
        flush_stdin()
        print()
        hide_or_show_cursor(show=True)
        while True:
            try:
                min_speed = float(input(f'New min speed for sequences (previous: {config["min_sequence_speed"]}): '))
                max_speed = float(input(f'New max speed for sequences (previous: {config["max_sequence_speed"]}): '))
                if min_speed > max_speed:
                    print("Min speed can't be more than max speed")
                elif min_speed <= 0 or max_speed <= 0:
                    print("Min and max speed have to be greater than 0")
                else:
                    break
            except ValueError:
                print('Min and max speed have to be numbers')

        config["min_sequence_speed"] = min_speed
        config["max_sequence_speed"] = max_speed
        hide_or_show_cursor(hide=True)
        clear = True

    # sequence length:
    if keyboard.is_pressed(CHANGE_SEQ_LENGTH):
        flush_stdin()
        print()
        hide_or_show_cursor(show=True)
        while True:
            try:
                min_length = int(input(f'New min length for sequences (previous: {config["min_sequence_length"]}): '))
                max_length = int(input(f'New max length for sequences (previous: {config["max_sequence_length"]}): '))
                if min_length > max_length:
                    print("Min length can't be more than max length")
                elif min_length <= 0 or max_length <= 0:
                    print("Min and max length have to be greater than 0")
                elif max_length > 30:
                    print("Max length can't exceed 30")
                else:
                    break
            except ValueError:
                print('Min and max length have to be whole numbers')

        config["min_sequence_length"] = min_length
        config["max_sequence_length"] = max_length
        hide_or_show_cursor(hide=True)
        clear = True

    # print info:
    if keyboard.is_pressed(CUR_VALUES):
        flush_stdin()
        print(f'''
NEW_SEQUENCE_CHANCE = {round(config["new_sequence_chance"], 4)} (Chance for a column to reset when empty; range: 0 to 1)
RANDOM_CHAR_CHANGE_CHANCE = {round(config["random_char_change_chance"], 4)} (Chance for characters to change mid-sequence)

TIME_BETWEEN_FRAMES = {round(config["time_between_frames"], 4)} (Delay between frame updates)
MIN_SEQUENCE_SPEED = {round(config["min_sequence_speed"], 4)} (1/sequence_speed = frames to move the sequence)
MAX_SEQUENCE_SPEED = {round(config["max_sequence_speed"], 4)} (range(speed): MIN_SEQUENCE_SPEED to MAX_SEQUENCE_SPEED)

AMOUNT_OF_COLUMNS = {config["amount_of_columns"]}
AMOUNT_OF_ROWS = {config["amount_of_rows"]}

MAX_SEQUENCE_LENGTH = {config["max_sequence_length"]}
MIN_SEQUENCE_LENGTH = {config["min_sequence_length"]}

MODE = {config["mode"]} (Toggle for sequence update behavior)
AUTO_SIZE = {config["auto_size"]} (Toggle for automatic resizing)

CHARACTERS = {config["characters"]}
COLORS = {config["colors"]}
''')
        input('Press enter to continue...')
        clear = True

    if keyboard.is_pressed(SHOW_HELP_MESSAGE):
        flush_stdin()
        print()
        print(HELP_MESSAGE)
        input('Press enter to continue...')
        clear = True

    # remove controls:
    if keyboard.is_pressed(REMOVE_CONTROLS):
        return 'stop', columns, clear

    time.sleep(0.001)
    return count, columns, clear


# ______________________clear_if_necessary______________________
def clear_if_necessary(clear, old_terminal_size, config):
    """
    Clear the terminal screen if necessary.
    """
    terminal_lines = os.get_terminal_size().lines
    if old_terminal_size != terminal_lines:
        clear = True

    terminal_size = terminal_lines
    if terminal_size <= config["amount_of_rows"]:
        clear = True

    if clear:
        os.system('cls' if os.name == 'nt' else 'clear')
    return clear


# ______________________adjust_size______________________
def adjust_size(columns, clear, config):
    """
    Adjust AMOUNT_OF_ROWS and AMOUNT_OF_COLUMNS based on the current terminal size.
    """
    terminal_size = os.get_terminal_size()
    terminal_lines, terminal_columns = terminal_size.lines, terminal_size.columns

    if config["amount_of_rows"] < terminal_lines:
        config["amount_of_rows"] = terminal_lines - 1
    else:
        config["amount_of_rows"] = terminal_lines

    config["amount_of_columns"] = terminal_columns

    if len(columns) > config["amount_of_columns"]:
        columns = columns[:config["amount_of_columns"]]
        clear = True
    elif len(columns) < config["amount_of_columns"]:
        columns += [[] for _ in range(config["amount_of_columns"] - len(columns))]
        clear = True

    return columns, clear


# ______________________get_config______________________
def get_config(file_name=CONFIG_FILE, dir_name=CONTROLS_DIR_NAME):
    try:
        if file_name:
            try:
                pathvalidate.validate_filename(filename=dir_name)
                folder_is_valid = True
            except pathvalidate.ValidationError as e:
                folder_is_valid = False
                print("The folder you have chosen isn't valid.")
                print(f"{e}\n")
                print('The global variables will be used instead.')
                input('Press enter to continue...') 

            if folder_is_valid:
                if not file_name.endswith(".json"):
                    file_name += ".json"

                try:
                    pathvalidate.validate_filename(filename=file_name)

                    script_dir = os.path.dirname(os.path.abspath(__file__))
                    controls_dir = os.path.join(script_dir, dir_name)
                    os.makedirs(controls_dir, exist_ok=True)
                    file_path = os.path.join(controls_dir, file_name)

                    with open(file_path, 'r', encoding="utf-8") as file:
                        config = json.load(file)
                        config["extended_color_cache"] = {}
                        config['file_is_valid'] = True
                        config['folder_is_valid'] = folder_is_valid
                        return config
                    
                except pathvalidate.ValidationError as e:
                    print("The file you have chosen isn't valid.")
                    print(f"{e}\n")
                    print('The global variables will be used instead.')
                    input('Press enter to continue...')
    except FileNotFoundError:
        print(f'''The file "{file_name}" wasn't found.''')
        print('The global variables will be used instead.')
        input('Press enter to continue...')

    return {
        "new_sequence_chance": NEW_SEQUENCE_CHANCE,
        "random_char_change_chance": RANDOM_CHAR_CHANGE_CHANCE,
        "time_between_frames": TIME_BETWEEN_FRAMES,
        "min_sequence_length": MIN_SEQUENCE_LENGTH,
        "max_sequence_length": MAX_SEQUENCE_LENGTH,
        "min_sequence_speed": MIN_SEQUENCE_SPEED,
        "max_sequence_speed": MAX_SEQUENCE_SPEED,
        "amount_of_columns": AMOUNT_OF_COLUMNS,
        "amount_of_rows": AMOUNT_OF_ROWS,
        "mode": MODE,
        "auto_size": AUTO_SIZE,
        "characters": CHARACTERS,
        "colors": COLORS.copy(),
        "extended_color_cache": {},
        'file_is_valid': False,
        'folder_is_valid': folder_is_valid
    }


# ______________________save_config______________________
def save_config(config, update=False):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    controls_dir = os.path.join(script_dir, CONTROLS_DIR_NAME)
    os.makedirs(controls_dir, exist_ok=True)

    if not config['folder_is_valid']:
        print("The folder you have entered isn't valid.")
        print("You won't be able to save your config")
        input('Press enter to continue...')
        return

    s_config = {}
    for key in config:
        s_config[key] = config[key]
    s_config['extended_color_cache'] = {}

    if update:
        try:
            file_name = CONFIG_FILE
            if not file_name.endswith(".json"):
                file_name += ".json"
            
            file_path = os.path.join(controls_dir, file_name)

            with open(file_path, 'w', encoding="utf-8") as file:
                json.dump(s_config, file, indent=4)

        except FileNotFoundError:
            print(f'''The file "{CONFIG_FILE}" wasn't found.''')
            print('Try to make a new file to save your config.')
            input('Press enter to continue...')
    else:
        file_names = [f for f in os.listdir(controls_dir) if os.path.isfile(os.path.join(controls_dir, f))]
        
        numbers_used = []
        for file in file_names:
            file = file.replace('.json', '')
            if file.startswith('controls'):
                numbers_used.append(file[len('controls'):])

        new_number = 1
        while True:
            if str(new_number) not in numbers_used:
                break
            new_number += 1
        
        file_name = f'controls{new_number}.json'

        hide_or_show_cursor(show=True)
        while True:
            make_custom_name = input(f'Do you want to save in "{file_name}"?(y/n): ').lower().strip()

            if make_custom_name == 'y':
                make_custom_name = False
                break
            elif make_custom_name == 'n':
                make_custom_name = True
                break
        
        if make_custom_name:
            while True:
                new_name = input('\nPlease enter the new name: ').strip()
                if not new_name.endswith(".json"):
                    new_name += ".json"

                try:
                    pathvalidate.validate_filename(filename=new_name)
                except pathvalidate.ValidationError as e:
                    print(f"{e}\n")
                    continue

                if new_name in file_names:
                    print(f'\n{new_name} already exists.')
                    print('You can save to this file but that will cause the data on this file to be erased.')
                    save_anyway = input('Do you want to save anyway?(y/n): ').lower().strip()
                    if save_anyway == 'y':
                        break
                else:
                    break
            file_path = os.path.join(controls_dir, new_name)
        else:
            file_path = os.path.join(controls_dir, file_name)

        with open(file_path, 'w', encoding="utf-8") as file:
            json.dump(s_config, file, indent=4)
        hide_or_show_cursor(hide=True)


# ______________________run_matrix______________________
def run_matrix():
    """
    Run the Matrix rain animation.
    """
    try:
        # Create local configuration dictionary from the globals.
        config = get_config()

        columns = [[] for _ in range(config["amount_of_columns"])]
        count = [time.time() for _ in range(14)]
        old_terminal_size = os.get_terminal_size().lines
        clear = True
        hide_or_show_cursor(hide=True)

        while True:
            start_time = time.time()

            if config["auto_size"]:
                columns, clear = adjust_size(columns, clear, config)

            # Update columns.
            columns = [update_column(column, config) for column in columns]

            rows = "\n".join(columns_to_rows(columns, config))

            clear = clear_if_necessary(clear, old_terminal_size, config)
            clear = False
            old_terminal_size = os.get_terminal_size().lines

            sys.stdout.write("\u001b[H" + rows + "\n")
            sys.stdout.flush()

            while True:
                if count != 'stop':
                    count, columns, check_clear = check_keyboard(count, columns, config)
                    if check_clear:
                        clear = True
                elif keyboard.is_pressed(RETURN_CONTROLS):
                    count = [time.time() for _ in range(14)]

                if time.time() - start_time > config["time_between_frames"]:
                    break

    except KeyboardInterrupt:
        pass
    finally:
        hide_or_show_cursor(show=True)
        print('\nMatrix rain stopped')


if __name__ == '__main__':
    run_matrix()
