import random
import time
import os
import keyboard
import sys

NEW_SEQUENCE_CHANCE = 0.02
RANDOM_CHAR_CHANGE_CHANCE = 0
TIME_BETWEEN_FRAMES = 0.045

MIN_SEQUENCE_LENGTH = 3 ######## controls, help_message, check_controls, ?
MAX_SEQUENCE_LENGTH = 15 

MIN_SEQUENCE_SPEED = 0.3 # 1/sequence_speed = frames to move the sequence; sequence_speed has a range from MIN_SEQUENCE_SPEED to MAX_SEQUENCE_SPEED
MAX_SEQUENCE_SPEED = 1

AMOUNT_OF_COLUMNS = 150
AMOUNT_OF_ROWS = 20

MODE = True  # If True, the first letter of a sequence is random and the rest follow; otherwise the sequence remains unchanged.
AUTO_SIZE = False

CHARACTERS = "ﾊﾐﾋｰｳｼﾅﾓﾆｻﾜﾂｵﾘｱﾎﾃﾏｹﾒｴｶｷﾑﾕﾗｾﾈｽﾀﾇﾍｦｲｸｺｿﾁﾄﾉﾌﾤﾨﾛﾝ012345789:.=*+-<>"

# Green gradient colors (8 shades, from brightest to darkest)
COLORS = [
    "\033[0m",              # White: Reset color (default terminal color)
    "\033[38;2;0;255;0m",   # Brightest green
    "\033[38;2;0;208;0m",   # Brighter green
    "\033[38;2;0;176;0m",   # Bright green
    "\033[38;2;0;144;0m",   # Medium green
    "\033[38;2;0;112;0m",   # Slightly dark green
    "\033[38;2;0;80;0m",    # Dark green
    "\033[38;2;0;48;0m",    # Darker green
    "\033[38;2;0;16;0m",    # Very dark green
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
              
    {CUR_VALUES} = display current values
    {REMOVE_CONTROLS} = disable keyboard controls temporarily
    {RETURN_CONTROLS} = re-enable keyboard controls
              
    ctrl+c = stop matrix rain
'''


def parse_ansi_color(ansi):
    """
    Parse an ANSI color escape code of the form "\033[38;2;R;G;Bm" and return the RGB tuple.
    For the reset code ("\033[0m"), we return white (255,255,255).
    """
    if ansi == "\033[0m":
        return (255, 255, 255)
    try:
        # Remove the "\033[" prefix and the trailing "m", then split by semicolon.
        parts = ansi.lstrip("\033[").rstrip("m").split(";")
        if len(parts) == 6:
            parts.pop(0)
        # Expecting parts like ["38", "2", "R", "G", "B"]
        if parts[0] == "38" and parts[1] == "2" and len(parts) >= 5:
            return (int(parts[2]), int(parts[3]), int(parts[4]))
    except Exception:
        pass
    # Fallback to white if parsing fails.
    return (255, 255, 255)


def extend_colors(original_colors, new_length):
    """
    Given a list of ANSI color codes (original_colors) and a desired new length,
    return a new list of color codes of length new_length. This function
    uses piecewise linear interpolation on the RGB values.
    """
    if new_length <= len(original_colors):
        return original_colors

    extended = []
    n = len(original_colors)
    # For each new index, determine its position between the original colors.
    for i in range(new_length):
        t = i / (new_length - 1)  # Normalized [0,1]
        # Map t to a position in the original colors list:
        pos = t * (n - 1)
        idx = int(pos)
        if idx >= n - 1:
            idx = n - 2
            t2 = 1.0
        else:
            t2 = pos - idx

        rgb1 = parse_ansi_color(original_colors[idx])
        rgb2 = parse_ansi_color(original_colors[idx + 1])
        r = int(round(rgb1[0] * (1 - t2) + rgb2[0] * t2))
        g = int(round(rgb1[1] * (1 - t2) + rgb2[1] * t2))
        b = int(round(rgb1[2] * (1 - t2) + rgb2[2] * t2))
        extended.append(f"\033[38;2;{r};{g};{b}m")
    return extended


def make_sequence():
    """
    Create a new sequence for a column.

    This function creates a dictionary representing a new falling sequence. The dictionary
    contains a list of random characters (one for each color level) and initializes the
    current final character index to 0.

    Returns:
        dict: A dictionary with the following keys:
            - 'chars': list of characters for each color level.
            - 'cur_final_char': int index of the current final character in the sequence.
    """
    seq_length = random.randint(MIN_SEQUENCE_LENGTH, MAX_SEQUENCE_LENGTH)
    return {'chars': [random.choice(CHARACTERS) for _ in range(seq_length)],
             'cur_final_char': 0,
             'speed': random.uniform(MIN_SEQUENCE_SPEED, MAX_SEQUENCE_SPEED)}


def columns_to_rows(columns):
    """
    Convert columns of sequences into rows for terminal display.

    This function iterates over each row index and then over each column. For each column,
    it finds the sequence whose 'cur_final_char' is at or beyond the current row and uses it
    to determine which character (and color) to display. If no sequence is present in a column
    for a given row, a blank space is used.

    Args:
        columns (list): List of columns, where each column is a list of sequence dictionaries.

    Returns:
        list: A list of strings, each representing one row of output for display.
    """
    rows = []
    for row_index in range(AMOUNT_OF_ROWS):
        row = ''
        for column in columns:
            if not column:  # Column is empty; display blank space.
                row += ' '
                continue

            # Find the first sequence in the column that should be visible on this row.
            for i, sequence in enumerate(column):
                if round(sequence['cur_final_char']) >= row_index:
                    break

            # Determine if the sequence has a character for this row.
            char_index = round(sequence['cur_final_char']) - row_index
            try:
                next_sequence = column[i + 1]
                next_sequence_char_index = round(next_sequence['cur_final_char']) - row_index
                is_next = True
            except:
                is_next = False

            if 0 <= char_index < len(sequence['chars']):
                # If the sequence length is greater than the number of COLORS,
                # create an extended color gradient (only for this one sequence).
                seq_len = len(sequence['chars'])
                if seq_len > len(COLORS):
                    colors_extended = extend_colors(COLORS, seq_len)
                else:
                    colors_extended = COLORS
                # Now, using colors_extended so that the index is always in range.
                color = colors_extended[round(len(colors_extended) * char_index / seq_len)]
                char = sequence['chars'][char_index]
                row += f"{color}{char}\033[0m"

            elif is_next and 0 <= next_sequence_char_index < len(next_sequence['chars']):
                # If the sequence length is greater than the number of COLORS,
                # create an extended color gradient (only for this one sequence).
                seq_len = len(next_sequence['chars'])
                if seq_len > len(COLORS):
                    colors_extended = extend_colors(COLORS, seq_len)
                else:
                    colors_extended = COLORS
                # Now, using colors_extended so that the index is always in range.
                color = colors_extended[round(len(colors_extended) * next_sequence_char_index / seq_len)]
                char = next_sequence['chars'][char_index]
                row += f"{color}{char}\033[0m"
            else:
                row += ' '  # Blank if no character is visible.
        rows.append(row)
    return rows


def update_column(column):
    """
    Update a single column of sequences.
    
    For each sequence in the column, update its character sequence (shifting or randomly changing
    characters as appropriate) and increment its 'cur_final_char' counter. Remove sequences that have
    fallen beyond the display area. Additionally, with some probability, start a new sequence at the top
    of the column if the conditions are met.
    
    Args:
        column (list): A list of sequence dictionaries representing the current sequences in a column.
    
    Returns:
        list: The updated (and sorted) list of sequences for the column.
    """
    new_column = []
    
    # If the column is empty, possibly start a new sequence.
    if len(column) == 0:
        return [make_sequence()] if random.random() < NEW_SEQUENCE_CHANCE else []
    
    # Update each sequence.
    for sequence in column:
        if MODE:
            # Shift the sequence: remove the last char and insert a new random char at the beginning.
            if round(sequence['cur_final_char']) != round(sequence['cur_final_char'] + sequence['speed']):
                sequence['chars'].pop()
                sequence['chars'].insert(0, random.choice(CHARACTERS))
        
        if RANDOM_CHAR_CHANGE_CHANCE:
            # For each character, possibly change it based on the random chance.
            for char_index in range(len(sequence['chars'])):
                if random.random() < RANDOM_CHAR_CHANGE_CHANCE:
                    sequence['chars'][char_index] = random.choice(CHARACTERS)
        
        # Increment the sequence's position.
        sequence['cur_final_char'] += sequence['speed']
        
        # Keep sequences that are still within the visible range.
        if sequence['cur_final_char'] <= (AMOUNT_OF_ROWS + len(sequence['chars'])):
            new_column.append(sequence)
    
    # Sort the column so that the sequence with the lowest cur_final_char is at the front.
    new_column.sort(key=lambda seq: seq['cur_final_char'])
    
    # Possibly add a new sequence at the top of the column.
    if new_column:
        first_sequence = new_column[0]
        if first_sequence['cur_final_char'] >= len(COLORS) and random.random() < NEW_SEQUENCE_CHANCE:
            new_column.insert(0, make_sequence())
        
    return new_column


def flush_stdin():
    """
    Flush the standard input buffer.

    This function clears any buffered input from the terminal. On Windows, it uses the msvcrt module;
    on Unix-like systems, it uses the termios module.

    Note:
        On Windows, ensure that the msvcrt module is available.
    """
    if os.name == 'nt':
        # Windows: Drain any pending keystrokes.
        import msvcrt
        while msvcrt.kbhit():
            msvcrt.getch()
    else:
        # Unix-like systems: Flush the input buffer.
        import termios
        termios.tcflush(sys.stdin, termios.TCIFLUSH)


def check_keyboard(count, columns):
    """
    Check keyboard input and update global settings and column data accordingly.

    This function uses the keyboard module to detect key presses and adjusts variables such as
    animation speed, mode, display dimensions, colors, and the character set. It also manages debouncing
    using a list of timestamps.

    Args:
        count (list): A list of timestamps used to debounce keypress events.
        columns (list): The current list of columns for the matrix rain.

    Returns:
        tuple: A tuple (updated_count, updated_columns, clear_flag) where:
            - updated_count: The possibly updated list of timestamps.
            - updated_columns: The possibly updated list of columns.
            - clear_flag (bool): True if the terminal should be cleared due to a change.
            - If the controls have been disabled (via REMOVE_CONTROLS), the function returns ('stop', columns, clear_flag).
    """
    global TIME_BETWEEN_FRAMES, AMOUNT_OF_COLUMNS, AMOUNT_OF_ROWS, COLORS, NEW_SEQUENCE_CHANCE, CHARACTERS
    global MIN_SEQUENCE_LENGTH, MAX_SEQUENCE_LENGTH, MODE, RANDOM_CHAR_CHANGE_CHANCE, AUTO_SIZE, MIN_SEQUENCE_SPEED, MAX_SEQUENCE_SPEED
    cur_time = time.time()
    time_passed = [cur_time - t for t in count]
    time_used = 0
    clear = False

    if time_passed[time_used] > 0.08 and not keyboard.is_pressed('shift') and keyboard.is_pressed(SPEED_UP):
        count[time_used] = cur_time
        TIME_BETWEEN_FRAMES /= 1.02
    time_used += 1

    if time_passed[time_used] > 0.08 and not keyboard.is_pressed('shift') and keyboard.is_pressed(SLOW_DOWN):
        count[time_used] = cur_time
        TIME_BETWEEN_FRAMES *= 1.02
    time_used += 1

    if time_passed[time_used] > 0.25 and keyboard.is_pressed(PAUSE):
        time.sleep(0.25)
        while True:
            time.sleep(0.01)
            if keyboard.is_pressed(PAUSE):
                count[time_used] = time.time()
                break
    time_used += 1

    if time_passed[time_used] > 0.3 and keyboard.is_pressed(MODE_CHAR):
        count[time_used] = cur_time
        MODE = not MODE
    time_used += 1

    if time_passed[time_used] > 0.3 and keyboard.is_pressed(AUTO_SIZE_CHAR):
        count[time_used] = cur_time
        AUTO_SIZE = not AUTO_SIZE
    time_used += 1

    if time_passed[time_used] > 0.09 and AMOUNT_OF_ROWS > 0 and not keyboard.is_pressed('shift') and keyboard.is_pressed(SHORTEN_LENGTH):
        count[time_used] = cur_time
        AMOUNT_OF_ROWS -= 1
        clear = True
    time_used += 1

    if time_passed[time_used] > 0.09 and AMOUNT_OF_ROWS < 80 and not keyboard.is_pressed('shift') and keyboard.is_pressed(INCREASE_LENGTH):
        count[time_used] = cur_time
        AMOUNT_OF_ROWS += 1
        clear = True
    time_used += 1

    if time_passed[time_used] > 0.05 and AMOUNT_OF_COLUMNS > 0 and keyboard.is_pressed(LESS_COLUMNS):
        count[time_used] = cur_time
        AMOUNT_OF_COLUMNS -= 1
        columns.pop(-1)
        clear = True
    time_used += 1

    if time_passed[time_used] > 0.05 and AMOUNT_OF_COLUMNS < 200 and keyboard.is_pressed(MORE_COLUMNS):
        count[time_used] = cur_time
        AMOUNT_OF_COLUMNS += 1
        columns.append([])
        clear = True
    time_used += 1

    if time_passed[time_used] > 0.1 and keyboard.is_pressed(LESS_NEW_SEQUENCE_CHANCE):
        count[time_used] = cur_time
        NEW_SEQUENCE_CHANCE /= 1.03
    time_used += 1

    if time_passed[time_used] > 0.1 and NEW_SEQUENCE_CHANCE <= 1 and (keyboard.is_pressed('=+shift') or keyboard.is_pressed(MORE_NEW_SEQUENCE_CHANCE)):
        count[time_used] = cur_time
        NEW_SEQUENCE_CHANCE *= 1.03
    time_used += 1

    if time_passed[time_used] > 0.15 and keyboard.is_pressed(LESS_RANDOM_CHAR):
        count[time_used] = cur_time
        RANDOM_CHAR_CHANGE_CHANCE /= 1.05
        if RANDOM_CHAR_CHANGE_CHANCE < 0.005:
            RANDOM_CHAR_CHANGE_CHANCE = 0
        time_used += 1

    if time_passed[time_used] > 0.15 and RANDOM_CHAR_CHANGE_CHANCE <= 1 and keyboard.is_pressed(MORE_RANDOM_CHAR):
        count[time_used] = cur_time
        if RANDOM_CHAR_CHANGE_CHANCE == 0:
            RANDOM_CHAR_CHANGE_CHANCE = 0.005
        RANDOM_CHAR_CHANGE_CHANCE *= 1.05
    time_used += 1

    if time_passed[time_used] > 0.3 and keyboard.is_pressed(FIRST_BOLD):
        count[time_used] = cur_time
        parts = COLORS[0].split('[')

        if parts[1][:2] == '1;':
            parts[1] = parts[1].replace('1;', '')
        else:
            parts[1] = '1;' + parts[1]

        COLORS[0] = '['.join(parts)
    time_used += 1

    if not keyboard.is_pressed('shift') and keyboard.is_pressed(FIRST_WHITE):
        COLORS[0] = "\033[0m"  # Reset to default white

    if keyboard.is_pressed(FIRST_BRIGHT):
        first_color = parse_ansi_color(COLORS[1])
        r, g, b, = first_color

        if r == 255 and 255 not in (g, b):
            COLORS[0] = "\033[38;2;255;200;200m"

        elif g == 255 and 255 not in (r, b):
            COLORS[0] = "\033[38;2;200;255;200m"

        elif g == 255 and b == 255 and not 255 == r:
            COLORS[0] = "\033[38;2;225;255;255m"


    if keyboard.is_pressed(RED):
        COLORS = ["\033[38;2;255;64;64m",  # Brightest red with slight glow
                  "\033[38;2;255;0;0m",
                  "\033[38;2;240;0;0m",
                  "\033[38;2;224;0;0m",
                  "\033[38;2;208;0;0m",
                  "\033[38;2;192;0;0m",
                  "\033[38;2;176;0;0m",
                  "\033[38;2;160;0;0m",
                  "\033[38;2;144;0;0m"]

    if keyboard.is_pressed(GREEN):
        COLORS = ["\033[38;2;64;255;64m",  # Brightest green with slight glow
                  "\033[38;2;0;255;0m",
                  "\033[38;2;0;208;0m",
                  "\033[38;2;0;176;0m",
                  "\033[38;2;0;144;0m",
                  "\033[38;2;0;112;0m",
                  "\033[38;2;0;80;0m",
                  "\033[38;2;0;48;0m",
                  "\033[38;2;0;16;0m"]

    if not keyboard.is_pressed('shift') and keyboard.is_pressed(BLUE):
        COLORS = ["\033[38;2;64;255;255m",  # Brightest cyan with slight glow
                  "\033[38;2;0;255;255m",
                  "\033[38;2;0;208;208m",
                  "\033[38;2;0;176;176m",
                  "\033[38;2;0;144;144m",
                  "\033[38;2;0;112;112m",
                  "\033[38;2;0;80;80m",
                  "\033[38;2;0;48;48m",
                  "\033[38;2;0;16;16m"]

    if keyboard.is_pressed(CHARS_01):
        CHARACTERS = '01'

    if keyboard.is_pressed(CHARS_ORIGINAL):
        CHARACTERS = "ﾊﾐﾋｰｳｼﾅﾓﾆｻﾜﾂｵﾘｱﾎﾃﾏｹﾒｴｶｷﾑﾕﾗｾﾈｽﾀﾇﾍｦｲｸｺｿﾁﾄﾉﾌﾤﾨﾛﾝ012345789:.=*+-<>"

    if not keyboard.is_pressed('ctrl') and keyboard.is_pressed(CHANGE_SPEED_DIFF):
        flush_stdin()  # Remove any pending input from the terminal.
        print()
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()
        while True:
            try:
                min_speed = float(input(f'New min speed for sequences(previous: {MIN_SEQUENCE_SPEED}): '))
                max_speed = float(input(f'New max speed for sequences(previous: {MAX_SEQUENCE_SPEED}): '))
                if min_speed > max_speed:
                    print("Min speed can't be more than max speed")
                elif min_speed <= 0 or max_speed <= 0:
                    print("Min and max speed have to greater than 0")
                else:
                    break
            except ValueError:
                print('Min and max speed have to be numbers')

        MIN_SEQUENCE_SPEED = min_speed
        MAX_SEQUENCE_SPEED = max_speed

        sys.stdout.write("\033[?25l")
        sys.stdout.flush()
        clear = True

    if keyboard.is_pressed(CHANGE_SEQ_LENGTH):
        flush_stdin()  # Remove any pending input from the terminal.
        print()
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()
        while True:
            try:
                min_length = int(input(f'New min length for sequences(previous: {MIN_SEQUENCE_LENGTH}): '))
                max_length = int(input(f'New max length for sequences(previous: {MAX_SEQUENCE_LENGTH}): '))
                if min_length > max_length:
                    print("Min length can't be more than max length")
                elif min_length <= 0 or max_length <= 0:
                    print("Min and max length have to greater than 0")
                elif max_length > 20:
                    print("Max length can't exceed 20")
                else:
                    break
            except ValueError:
                print('Min and max length have to be whole numbers')

        MIN_SEQUENCE_LENGTH = min_length
        MAX_SEQUENCE_LENGTH = max_length

        sys.stdout.write("\033[?25l")
        sys.stdout.flush()
        clear = True

    # Character set modification using CHARS_ANY
    if keyboard.is_pressed(CHARS_ANY):
        flush_stdin()  # Remove any pending input from the terminal.
        print()
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()
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
                if len(chars + CHARACTERS) > 100:
                    print('Sorry that would result in too many characters')
                    continue
                CHARACTERS += chars
            elif add == 'r':
                CHARACTERS = chars if chars else ' '
            break
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()
        clear = True

    if keyboard.is_pressed(CUR_VALUES):
        flush_stdin()
        print(f'''
NEW_SEQUENCE_CHANCE = {round(NEW_SEQUENCE_CHANCE, 4)} (Chance for a column to reset when empty; range: 0 to 1)
RANDOM_CHAR_CHANGE_CHANCE = {round(RANDOM_CHAR_CHANGE_CHANCE, 4)} (Chance for characters to change mid-sequence)

TIME_BETWEEN_FRAMES = {round(TIME_BETWEEN_FRAMES, 4)} (Delay between frame updates)
MIN_SEQUENCE_SPEED = {round(MIN_SEQUENCE_SPEED, 4)} (1/sequence_speed = frames to move the sequence)
MAX_SEQUENCE_SPEED = {round(MAX_SEQUENCE_SPEED, 4)} (range(speed): MIN_SEQUENCE_SPEED to MAX_SEQUENCE_SPEED))

AMOUNT_OF_COLUMNS = {AMOUNT_OF_COLUMNS}
AMOUNT_OF_ROWS = {AMOUNT_OF_ROWS}

MAX_SEQUENCE_LENGTH = {MAX_SEQUENCE_LENGTH}
MIN_SEQUENCE_LENGTH = {MIN_SEQUENCE_LENGTH}

MODE = {MODE} (Toggle for sequence update behavior)
AUTO_SIZE = {AUTO_SIZE} (Toggle for automatic resizing)

CHARACTERS = {CHARACTERS}
COLORS = {COLORS}
''')
        input('Press enter to continue...')
        clear = True

    if keyboard.is_pressed(SHOW_HELP_MESSAGE):
        flush_stdin()
        print()
        print(HELP_MESSAGE)
        input('Press enter to continue...')
        clear = True

    if keyboard.is_pressed(REMOVE_CONTROLS):
        return 'stop', columns, clear

    time.sleep(0.001)
    return count, columns, clear


def clear_if_necessary(clear, old_terminal_size):
    """
    Clear the terminal screen if necessary.

    This function checks if the terminal size has changed or if a control event has flagged a clear.
    If so, it clears the screen using the appropriate command for the operating system.

    Args:
        clear (bool): Flag indicating whether a clear is requested.
        old_terminal_size (int): The previous terminal size (number of lines).

    Returns:
        None
    """
    if old_terminal_size != os.get_terminal_size().lines:
        clear = True

    terminal_size = os.get_terminal_size().lines
    if terminal_size <= AMOUNT_OF_ROWS:
        clear = True

    if clear:
        os.system('cls' if os.name == 'nt' else 'clear')


def ADJUST_SIZE(columns, clear):
    global AMOUNT_OF_COLUMNS, AMOUNT_OF_ROWS
    lines = os.get_terminal_size().lines
    if AMOUNT_OF_ROWS < lines:
        AMOUNT_OF_ROWS = os.get_terminal_size().lines - 1
    else:
        AMOUNT_OF_ROWS = os.get_terminal_size().lines

    AMOUNT_OF_COLUMNS = os.get_terminal_size().columns

    if AMOUNT_OF_COLUMNS < len(columns):
        columns = columns[:AMOUNT_OF_COLUMNS]
        clear = True
    elif AMOUNT_OF_COLUMNS == len(columns):
        pass
    else:
        columns.append([] * (AMOUNT_OF_COLUMNS - len(columns)))
        clear = True

    return columns, clear


def run_matrix():
    """
    Run the Matrix rain animation.

    This is the main animation loop. It initializes the columns and debouncing timers,
    then continuously updates and displays the falling character sequences. Keyboard input
    is checked between frame updates to adjust settings and behavior in real-time.

    Returns:
        None
    """
    columns = [[] for _ in range(AMOUNT_OF_COLUMNS)]  # Initialize columns.
    count = [time.time() for _ in range(14)]  # Debounce timers for key presses.
    old_terminal_size = os.get_terminal_size().lines
    clear = True
    sys.stdout.write("\033[?25l") # Hide the cursor
    sys.stdout.flush()

    try:
        while True:
            start_time = time.time()  # Track the frame start time.

            if AUTO_SIZE:
                columns, clear = ADJUST_SIZE(columns, clear)

            # Update each column.
            columns = [update_column(column) for column in columns]

            rows = "\n".join(columns_to_rows(columns))

            clear_if_necessary(clear, old_terminal_size)
            clear = False
            old_terminal_size = os.get_terminal_size().lines

            # Move cursor to top left and output the frame.
            sys.stdout.write("\033[H" + rows + "\n")
            sys.stdout.flush()

            # Process keyboard events until the frame delay has passed.
            while True:
                if count != 'stop':  # If controls are active.
                    count, columns, check_clear = check_keyboard(count, columns)
                    if check_clear:
                        clear = True
                elif keyboard.is_pressed(RETURN_CONTROLS):
                    count = [time.time() for _ in range(14)]

                if time.time() - start_time > TIME_BETWEEN_FRAMES:
                    break

    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\033[?25h") # restore the cursor
        sys.stdout.flush()
        print('\nMatrix rain stopped')


if __name__ == '__main__':
    run_matrix()
