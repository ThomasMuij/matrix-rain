import random
import time
import os
import keyboard
import sys

NEW_SEQUENCE_CHANCE = 0.025  # Chance for a column to reset when it becomes empty (0 to 1)
RANDOM_CHAR_CHANGE_CHANCE = 0
TIME_BETWEEN_FRAMES = 0.045

AMOUNT_OF_COLUMNS = 150
AMOUNT_OF_ROWS = 20

MODE = True # changes if the first letter of a sequence is random and others change to it or if the sequence doesn't change

CHARACTERS = "ﾊﾐﾋｰｳｼﾅﾓﾆｻﾜﾂｵﾘｱﾎﾃﾏｹﾒｴｶｷﾑﾕﾗｾﾈｽﾀﾇﾍｦｲｸｺｿﾁﾄﾉﾌﾤﾨﾛﾝ012345789:.=*+-<>"

# Green gradient colors (8 shades, from brightest to darkest)
COLORS = ["\033[0m",             # white = Reset color (default terminal color)
          "\033[38;2;0;255;0m",  # Brightest green
          "\033[38;2;0;208;0m",  # Brighter green
          "\033[38;2;0;176;0m",  # Bright green
          "\033[38;2;0;144;0m",  # Medium green
          "\033[38;2;0;112;0m",  # Slightly dark green
          "\033[38;2;0;80;0m",   # Dark green
          "\033[38;2;0;48;0m",   # Darker green
          "\033[38;2;0;16;0m",   # Very dark green
]


# controls info:
# when chaning something, make sure it works with the keyboard module
SPEED_UP = 'f'
SLOW_DOWN = 's'
PAUSE = 'p'
MODE_CHAR = 'q'

MORE_RANDOM_CHAR = 'shift+up'
LESS_RANDOM_CHAR = 'shift+up'

# if changing to something else than an arrow, upade the HELP_MESSAGE:
SHORTEN_LENGTH ='up'
INCREASE_LENGTH = 'down'
LESS_COLUMNS = 'left'
MORE_COLUMNS = 'right'

# if changing update HELP_MESSAGE and if keyboard...:
MORE_NEW_SEQUENCE_CHANCE = '+'
LESS_NEW_SEQUENCE_CHANCE = '-'

FIRST_WHITE = 'm'
BLUE = 'b'
GREEN = 'g'
RED = 'r'

CHARS_01 = '0'
CHARS_ORIGINAL = '1'
CHARS_ANY = '9'

SHOW_HELP_MESSAGE = 'h'
CUR_VALUES = 'v'
REMOVE_CONTROLS = 'backspace'
RETURN_CONTROLS = 'ctrl+shift+enter'

# ctrl+c = stop matrix rain

HELP_MESSAGE = f'''Controls:
    {SPEED_UP} = speed up (relative to current speed)
    {SLOW_DOWN} = slow down (relative to current speed)
    {PAUSE} = (un)pause
    {MODE_CHAR} = changes if the first letter of a sequence is random and others change to it or if the sequence doesn't change

    {MORE_RANDOM_CHAR} = increase chance for characters to randomly change in a sequence
    {LESS_RANDOM_CHAR} = decrease chance for characters to randomly change in a sequence
              
    arrow {SHORTEN_LENGTH} = shorten matrix length
    arrow {INCREASE_LENGTH} = increase matrix length
    arrow {LESS_COLUMNS} = reduce number of columns
    arrow {MORE_COLUMNS} = increase number of columns
              
    plus("+") = increase the chance of a new sequence to start falling (relative to current chance)
    minus("-", "/" for english keyboard) = decreases the chance of a new sequence to start falling (relative to current chance)
              
    {FIRST_WHITE} = make first character white
    {BLUE} = change color to blue
    {GREEN} = change color to green
    {RED} = change color to red
              
    {CHARS_01} = change characters to "01"
    {CHARS_ORIGINAL} = change characters to original
    {CHARS_ANY} = let's you input the characters you want to add or replace
              
    {CUR_VALUES} = current values
    {REMOVE_CONTROLS} = remove controls
    {RETURN_CONTROLS} = bring controls back
              
    ctrl+c = stop matrix rain
'''


##############################################################
def make_sequence():
    """
    Creates a new sequence with random characters and initializes the current final character index.

    Returns:
        dict: A dictionary with a list of random characters for the sequence and the current final character index.
    """
    return {'chars': [random.choice(CHARACTERS) for _ in range(len(COLORS))], 'cur_final_char': 0}


##############################################################
def columns_to_rows(columns):
    """
    Converts columns of characters into rows for rendering on the terminal.

    Args:
        columns (list): A list of columns, each containing sequences of characters.

    Returns:
        list: A list of strings representing each row to be displayed.
    """
    rows = []
    for row_index in range(AMOUNT_OF_ROWS):
        row = ''
        for column in columns:
            if len(column) == 0: # the column doesn't have any sequences at the moment
                row += ' '
                continue

            for sequence in column: # selects the sequences that is on this row
                if sequence['cur_final_char'] >= row_index:
                    break

            if 0 <= sequence['cur_final_char'] - row_index < len(sequence['chars']):
                color_index = sequence['cur_final_char'] - row_index # = char_index
                color = COLORS[color_index]
                char = sequence['chars'][color_index]
                row += f"{color}{char}\033[0m"
            else: # keeps distance from previous sequence
                row += ' '
        rows.append(row)
    return rows


##############################################################
def update_column(column):
    """
    Updates a given column by removing characters, shifting sequences, and potentially adding new sequences.

    Args:
        column (list): A list of sequences in a single column.

    Returns:
        list: The updated list of sequences for the column.
    """
    new_column = []
    
    if len(column) == 0: # if the column is empty keep the same chance for a sequence to form without breaking the following code
        return [make_sequence()] if random.random() < NEW_SEQUENCE_CHANCE else []

    for i, sequence in enumerate(column):
        if MODE: # changes if the first letter of a sequence is random and others change to it or if the sequence doesn't change
            sequence['chars'].pop()
            sequence['chars'].insert(0, random.choice(CHARACTERS))

        if RANDOM_CHAR_CHANGE_CHANCE: # if isn't necessary
            for char_index, char in enumerate(sequence['chars'].copy()):
                sequence['chars'][char_index] = random.choice(CHARACTERS) if random.random() < RANDOM_CHAR_CHANGE_CHANCE else char

        sequence['cur_final_char'] += 1

        if not (sequence['cur_final_char'] > (AMOUNT_OF_ROWS + len(sequence['chars']))): # erases sequences that are past the limit of rows
            new_column.append(sequence)

    if len(new_column) > 0: # if the column doesn't have any sequences, it would cause an error trying to find the index [0]
        first_sequence = new_column[0]

        if first_sequence['cur_final_char'] >= len(COLORS) and random.random() < NEW_SEQUENCE_CHANCE: # chance for a new sequence to start
            new_column.insert(0, make_sequence())
        
    return new_column


##############################################################
def check_keyboard(count, columns): 
    """
    Checks for keyboard input and updates relevant variables such as speed, mode, matrix dimensions, colors, and characters.

    Args:
        count (int): A counter used to track the frequency of keypress checks.
        columns (list): The current list of columns.

    Returns:
        tuple: The updated count value and the updated columns.
    """
    # keep in mind that arrows result in numbers also getting pressed: up = 8, right = 6, down = 2, left = 4
    # press h for help

    global TIME_BETWEEN_FRAMES, AMOUNT_OF_COLUMNS, AMOUNT_OF_ROWS, COLORS, NEW_SEQUENCE_CHANCE, CHARACTERS, MODE, RANDOM_CHAR_CHANGE_CHANCE
    cur_time = time.monotonic()
    time_passed = [cur_time - i for i in count]
    time_used = 0
    clear = False

    if time_passed[time_used] > 0.05 and keyboard.is_pressed(SPEED_UP):
        count[time_used] = cur_time
        TIME_BETWEEN_FRAMES /= 1.015
    time_used += 1

    if time_passed[time_used] > 0.05 and keyboard.is_pressed(SLOW_DOWN):
        count[time_used] = cur_time
        TIME_BETWEEN_FRAMES *= 1.015
    time_used += 1

    if time_passed[time_used] > 0.25 and keyboard.is_pressed(PAUSE):
        time.sleep(0.25)
        while True:
            time.sleep(0.01)
            if keyboard.is_pressed(PAUSE):
                count[time_used] = time.monotonic()
                break
    time_used += 1

    if time_passed[time_used] > 0.3 and keyboard.is_pressed(MODE_CHAR):
        count[time_used] = cur_time
        MODE = not MODE
    time_used += 1
    
    if time_passed[time_used] > 0.09 and keyboard.is_pressed(SHORTEN_LENGTH) and AMOUNT_OF_ROWS > 0 and not keyboard.is_pressed('shift'):
        count[time_used] = cur_time
        AMOUNT_OF_ROWS -= 1
        clear = True
    time_used += 1

    if time_passed[time_used] > 0.09 and keyboard.is_pressed(INCREASE_LENGTH) and not keyboard.is_pressed('shift') and AMOUNT_OF_ROWS < 70:
        count[time_used] = cur_time
        AMOUNT_OF_ROWS += 1
        clear = True
    time_used += 1

    if time_passed[time_used] > 0.05 and keyboard.is_pressed(LESS_COLUMNS) and AMOUNT_OF_COLUMNS > 0:
        count[time_used] = cur_time
        AMOUNT_OF_COLUMNS -= 1
        columns.pop(-1)
        clear = True
    time_used += 1

    if  time_passed[time_used] > 0.05 and keyboard.is_pressed(MORE_COLUMNS) and AMOUNT_OF_COLUMNS < 200:
        count[time_used] = cur_time
        AMOUNT_OF_COLUMNS += 1
        columns.append([])
        clear = True
    time_used += 1

    if time_passed[time_used] and keyboard.is_pressed(LESS_NEW_SEQUENCE_CHANCE) > 0.1:
        count[time_used] = cur_time
        NEW_SEQUENCE_CHANCE /= 1.05
    time_used += 1

    if time_passed[time_used] and (keyboard.is_pressed(MORE_NEW_SEQUENCE_CHANCE) or keyboard.is_pressed('=+shift') and NEW_SEQUENCE_CHANCE <= 1) > 0.1:
        count[time_used] = cur_time
        NEW_SEQUENCE_CHANCE *= 1.05
    time_used += 1

    if time_passed[time_used] and keyboard.is_pressed(LESS_RANDOM_CHAR) > 0.15:
        count[time_used] = cur_time
        RANDOM_CHAR_CHANGE_CHANCE *= 1.05
        if RANDOM_CHAR_CHANGE_CHANCE < 0.01:
            RANDOM_CHAR_CHANGE_CHANCE = 0
        time_used += 1

    if time_passed[time_used] and keyboard.is_pressed(MORE_RANDOM_CHAR) and RANDOM_CHAR_CHANGE_CHANCE <= 1 > 0.15:
        count[time_used] = cur_time
        if RANDOM_CHAR_CHANGE_CHANCE == 0:
            RANDOM_CHAR_CHANGE_CHANCE = 0.01
        RANDOM_CHAR_CHANGE_CHANCE /= 1.05
    # time_used += 1

    if keyboard.is_pressed(FIRST_WHITE):
        COLORS[0] = "\033[0m" # white = Reset color (default terminal color)

    if keyboard.is_pressed(RED):
        COLORS = ["\033[38;2;255;64;64m",  # Brightest red with a slight glow effect
                  "\033[38;2;255;0;0m",    # Brightest red
                  "\033[38;2;240;0;0m",    # Slightly less bright red
                  "\033[38;2;224;0;0m",    # Brighter red
                  "\033[38;2;208;0;0m",    # Bright red
                  "\033[38;2;192;0;0m",    # Medium bright red
                  "\033[38;2;176;0;0m",    # Medium red
                  "\033[38;2;160;0;0m",    # Slightly dark red
                  "\033[38;2;144;0;0m"]    # Dark red
        
    if keyboard.is_pressed(GREEN):
        COLORS = ["\033[38;2;64;255;64m", # Brightest green with a slight glow effect
                  "\033[38;2;0;255;0m",   # Brightest green
                  "\033[38;2;0;208;0m",   # Brighter green
                  "\033[38;2;0;176;0m",   # Bright green
                  "\033[38;2;0;144;0m",   # Medium green
                  "\033[38;2;0;112;0m",   # Slightly dark green
                  "\033[38;2;0;80;0m",    # Dark green
                  "\033[38;2;0;48;0m",    # Darker green
                  "\033[38;2;0;16;0m"]    # Very dark green
        
    if keyboard.is_pressed(BLUE):
        COLORS = ["\033[38;2;64;255;255m", # Brightest cyan with a slight glow effect
                  "\033[38;2;0;255;255m",   # Brightest cyan
                  "\033[38;2;0;208;208m",   # Brighter cyan
                  "\033[38;2;0;176;176m",   # Bright cyan
                  "\033[38;2;0;144;144m",   # Medium cyan
                  "\033[38;2;0;112;112m",   # Slightly dark cyan
                  "\033[38;2;0;80;80m",     # Dark cyan
                  "\033[38;2;0;48;48m",     # Darker cyan
                  "\033[38;2;0;16;16m"]     # Very dark cyan
        
    if keyboard.is_pressed(CHARS_01):
        CHARACTERS = '01'

    if keyboard.is_pressed(CHARS_ORIGINAL):
        CHARACTERS = "ﾊﾐﾋｰｳｼﾅﾓﾆｻﾜﾂｵﾘｱﾎﾃﾏｹﾒｴｶｷﾑﾕﾗｾﾈｽﾀﾇﾍｦｲｸｺｿﾁﾄﾉﾌﾤﾨﾛﾝ012345789:.=*+-<>"

    # if keyboard.is_pressed('9'):
    #     time.sleep(0.2)
    #     CHARACTERS = ''
    #     while len(CHARACTERS) < 100:
    #         char = keyboard.read_key()
    #         if char == 'enter' and len(CHARACTERS.strip()) > 0:
    #             break
    #         elif len(char) > 1:
    #             continue
    #         elif not (char in CHARACTERS):
    #             CHARACTERS += char

    # if keyboard.is_pressed('8') and not keyboard.is_pressed('up'):
    #     time.sleep(0.2)
    #     while len(CHARACTERS) < 100:
    #         char = keyboard.read_key()
    #         if char == 'enter' and len(CHARACTERS.strip()) > 0:
    #             break
    #         elif len(char) > 1:
    #             continue
    #         elif not (char in CHARACTERS):
    #             CHARACTERS += char

    if keyboard.is_pressed(CHARS_ANY):
        # os.system('cls' if os.name == 'nt' else 'clear')
        while True: # chars gets all written things in the terminal even enters before 7 seven is pressed put into as if it was there the entire time
                check = input('Enter "9" and then press enter: ')
                if '9' in check:
                    break
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
                    print('Sorry that would result in too many chararacters')
                    continue
                CHARACTERS += chars
            elif add == 'r':
                if len(chars) == 0:
                    chars = ' '
                CHARACTERS = chars
            break
        clear = True

    if keyboard.is_pressed(CUR_VALUES):
        print(f'''
NEW_SEQUENCE_CHANCE = {round(NEW_SEQUENCE_CHANCE, 4)} (Chance for a column to reset when it becomes empty (0 to 1))
RANDOM_CHAR_CHANGE_CHANCE = {round(RANDOM_CHAR_CHANGE_CHANCE, 4)} (chance for chars to change in the middle of the sequence)
TIME_BETWEEN_FRAMES = {round(TIME_BETWEEN_FRAMES, 4)} (how fast the the characters fall)

AMOUNT_OF_COLUMNS = {AMOUNT_OF_COLUMNS}
AMOUNT_OF_ROWS = {AMOUNT_OF_ROWS}

MODE = {MODE} (changes if the first letter of a sequence is random and others change to it or if the sequence doesn't change)

CHARACTERS = {CHARACTERS}

COLORS = {COLORS}
''')
        input('Press enter to continue...')
        clear = True

    if keyboard.is_pressed(SHOW_HELP_MESSAGE):
        # os.system('cls' if os.name == 'nt' else 'clear')
        print(HELP_MESSAGE)
        input('Press enter to continue...')
        clear = True

    if keyboard.is_pressed(REMOVE_CONTROLS):
        return 'stop', columns, clear

    time.sleep(0.01)
    return count, columns, clear


##############################################################
def clear_if_necessary(clear, rows, old_terminal_size, old_rows, old_columns):
    if old_terminal_size != os.get_terminal_size().lines: # if you change the terminal size, it can cause lines to duplicate
        clear = True

    terminal_size = os.get_terminal_size().lines
    if terminal_size <= len(rows): # if the terminal size is smaller than the amount of rows, the prints don't disappear
        clear = True

    if clear:
        os.system('cls' if os.name == 'nt' else 'clear')

    return terminal_size


##############################################################
def run_matrix():
    columns = [[] for _ in range(AMOUNT_OF_COLUMNS)] # Initialize columns
    count = [time.monotonic() for _ in range(12)] # prevents some controls from doing things too fast
    old_terminal_size = os.get_terminal_size().lines
    clear = True
    old_rows = AMOUNT_OF_ROWS
    old_columns = AMOUNT_OF_COLUMNS

    # Main animation loop
    try:
        while True:
            start_time = time.monotonic() # using delay would cause the controls to act differently when TIME_BETWEEN_FRAMES changes
            rows = columns_to_rows(columns)

            old_terminal_size = clear_if_necessary(clear, rows, old_terminal_size, old_rows, old_columns)
            clear = False
            old_rows = AMOUNT_OF_ROWS
            old_columns = AMOUNT_OF_COLUMNS

            output = "\033[H" + "\n".join(rows) + "\n"
            sys.stdout.write(output)
            sys.stdout.flush()

            columns = [update_column(column) for column in columns]

            while True: # while time.monotonic() - start_time < TIME_BETWEEN_FRAMES could cause the controls to not be called at all

                if count != 'stop': # backspace prevents controls so that user can use their keyboard without worrying
                    count, columns, check_clear = check_keyboard(count, columns)

                    if check_clear:
                        clear = True

                elif keyboard.is_pressed(RETURN_CONTROLS):
                    count = [time.monotonic() for _ in range(12)]

                if time.monotonic() - start_time > TIME_BETWEEN_FRAMES:
                    break

    except KeyboardInterrupt:
        # os.system('cls' if os.name == 'nt' else 'clear')
        # for row in rows:
        #     print(row)
        print('Matrix rain stopped')


if __name__ == '__main__':
    run_matrix()
