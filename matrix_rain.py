import random
import time
import os
import keyboard

NEW_SEQUENCE_CHANCE = 0.02  # Chance for a column to reset when it becomes empty (0 to 1)
TIME_BETWEEN_FRAMES = 0.06

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


def make_sequence():
    """
    Creates a new sequence with random characters and initializes the current final character index.

    Returns:
        dict: A dictionary with a list of random characters for the sequence and the current final character index.
    """
    return {'chars': [random.choice(CHARACTERS) for _ in range(len(COLORS))], 'cur_final_char': 0}


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
            sequence['chars'] = sequence['chars'][:-1]
            sequence['chars'].insert(0, random.choice(CHARACTERS))
        sequence['cur_final_char'] += 1

        if not (sequence['cur_final_char'] > (AMOUNT_OF_ROWS + len(sequence['chars']))): # erases sequences that are past the limit of rows
            new_column.append(sequence)

    if len(new_column) > 0: # if the column doesn't have any sequences, it would cause an error trying to find the index [0]
        first_sequence = new_column[0]

        if first_sequence['cur_final_char'] > len(COLORS) and random.random() < NEW_SEQUENCE_CHANCE: # chance for a new sequence to start
            new_column.insert(0, make_sequence())
        
    return new_column


def check_keyboard(count_stop, columns, extra_lines): 
    """
    Checks for keyboard input and updates relevant variables such as speed, mode, matrix dimensions, colors, and characters.

    Args:
        count_stop (int): A counter used to track the frequency of keypress checks.
        columns (list): The current list of columns.

    Returns:
        tuple: The updated count_stop value and the updated columns.
    """
    # keep in mind that arrows result in numbers also getting pressed: up = 8, right = 6, down = 2, left = 4
    # press h for help

    global TIME_BETWEEN_FRAMES, AMOUNT_OF_COLUMNS, AMOUNT_OF_ROWS, COLORS, NEW_SEQUENCE_CHANCE, CHARACTERS, MODE

    if keyboard.is_pressed('f'):
        TIME_BETWEEN_FRAMES -= TIME_BETWEEN_FRAMES * 0.05

    if keyboard.is_pressed('s'):
        TIME_BETWEEN_FRAMES += TIME_BETWEEN_FRAMES * 0.1

    count_stop += 1
    if keyboard.is_pressed('p') and count_stop > (1/TIME_BETWEEN_FRAMES)/10:
        time.sleep(0.15)
        count_stop = 0
        while True:
            if keyboard.is_pressed('p'):
                break

    if keyboard.is_pressed('q') and count_stop > (1/TIME_BETWEEN_FRAMES)/10:
        count_stop = 0
        if MODE:
            MODE = False
        else:
            MODE = True
    
    if keyboard.is_pressed('up') and AMOUNT_OF_ROWS > 0 and not keyboard.is_pressed('shift'):
        AMOUNT_OF_ROWS -= 1

    if keyboard.is_pressed('down') and not keyboard.is_pressed('shift'):
        AMOUNT_OF_ROWS += 1

    if keyboard.is_pressed('left') and AMOUNT_OF_COLUMNS > 0:
        AMOUNT_OF_COLUMNS -= 1
        columns.pop(-1)

    if keyboard.is_pressed('right'):
        AMOUNT_OF_COLUMNS += 1
        columns.append([])

    if keyboard.is_pressed('shift+up') and extra_lines > 0:
        extra_lines -= 1

    if keyboard.is_pressed('shift+down'):
        extra_lines += 1

    if keyboard.is_pressed('m'):
        COLORS[0] = "\033[0m" # white = Reset color (default terminal color)

    if keyboard.is_pressed('r'):
        COLORS = ["\033[38;2;255;64;64m",  # Brightest red with a slight glow effect
                  "\033[38;2;255;0;0m",    # Brightest red
                  "\033[38;2;240;0;0m",    # Slightly less bright red
                  "\033[38;2;224;0;0m",    # Brighter red
                  "\033[38;2;208;0;0m",    # Bright red
                  "\033[38;2;192;0;0m",    # Medium bright red
                  "\033[38;2;176;0;0m",    # Medium red
                  "\033[38;2;160;0;0m",    # Slightly dark red
                  "\033[38;2;144;0;0m"]    # Dark red
        
    if keyboard.is_pressed('g'):
        COLORS = ["\033[38;2;64;255;64m", # Brightest green with a slight glow effect
                  "\033[38;2;0;255;0m",   # Brightest green
                  "\033[38;2;0;208;0m",   # Brighter green
                  "\033[38;2;0;176;0m",   # Bright green
                  "\033[38;2;0;144;0m",   # Medium green
                  "\033[38;2;0;112;0m",   # Slightly dark green
                  "\033[38;2;0;80;0m",    # Dark green
                  "\033[38;2;0;48;0m",    # Darker green
                  "\033[38;2;0;16;0m"]    # Very dark green
        
    if keyboard.is_pressed('b'):
        COLORS = ["\033[38;2;64;255;255m", # Brightest cyan with a slight glow effect
                  "\033[38;2;0;255;255m",   # Brightest cyan
                  "\033[38;2;0;208;208m",   # Brighter cyan
                  "\033[38;2;0;176;176m",   # Bright cyan
                  "\033[38;2;0;144;144m",   # Medium cyan
                  "\033[38;2;0;112;112m",   # Slightly dark cyan
                  "\033[38;2;0;80;80m",     # Dark cyan
                  "\033[38;2;0;48;48m",     # Darker cyan
                  "\033[38;2;0;16;16m"]     # Very dark cyan
        
    if keyboard.is_pressed('0'):
        CHARACTERS = '01'

    if keyboard.is_pressed('1'):
        CHARACTERS = "ﾊﾐﾋｰｳｼﾅﾓﾆｻﾜﾂｵﾘｱﾎﾃﾏｹﾒｴｶｷﾑﾕﾗｾﾈｽﾀﾇﾍｦｲｸｺｿﾁﾄﾉﾌﾤﾨﾛﾝ012345789:.=*+-<>"

    if keyboard.is_pressed('9'):
        time.sleep(0.2)
        CHARACTERS = ''
        while len(CHARACTERS) < 100:
            char = keyboard.read_key()
            if char == 'enter' and len(CHARACTERS.strip()) > 0:
                break
            elif len(char) > 1:
                continue
            elif not (char in CHARACTERS):
                CHARACTERS += char

    if keyboard.is_pressed('8') and not keyboard.is_pressed('up'):
        time.sleep(0.2)
        while len(CHARACTERS) < 100:
            char = keyboard.read_key()
            if char == 'enter' and len(CHARACTERS.strip()) > 0:
                break
            elif len(char) > 1:
                continue
            elif not (char in CHARACTERS):
                CHARACTERS += char

    if keyboard.is_pressed('7'):
        # os.system('cls' if os.name == 'nt' else 'clear')
        while True:
            while True: # chars gets all written things in the terminal even enters before 7 seven is pressed put into as if it was there the entire time
                check = input('Press enter ')
                if '7' in check:
                    break
            chars = input('Characters: ')
            if len(chars.strip()) == 0:
                print('Need to add at least 1 character')
                continue
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
                CHARACTERS = chars
            break
    
    if keyboard.is_pressed('h'):
        os.system('cls' if os.name == 'nt' else 'clear')
        print('''Controls:
    f = speed up
    s = slow down
    p = (un)pause
    q = changes if the first letter of a sequence is random and others change to it or if the sequence doesn't change
    backspace = remove controls
              
    arrow up = shorten matrix length
    arrow down = increase matrix length
    arrow left = reduce number of columns
    arrow right = increase number of columns
    ctrl + arrow up = shorten extra lines after matrix
    ctrl + arrow down = increase extra lines after matrix
              
    m = make first character white
    b = change color to blue
    g = change color to green
    r = change color to red
              
    0 = change characters to "01"
    1 = change characters to original
    9 = change characters to what you press until you press "enter"
    8 = add characters you press to the current characters until you press "enter"
    7 = let's you input the characters you want to add or replace
    
    press enter to continue''')
        while True:
            if keyboard.is_pressed('enter'):
                break

        
    if keyboard.is_pressed('-'):
        NEW_SEQUENCE_CHANCE -= NEW_SEQUENCE_CHANCE/8

    if keyboard.is_pressed('+') or (keyboard.is_pressed('=') and keyboard.is_pressed('shift')):
        NEW_SEQUENCE_CHANCE += NEW_SEQUENCE_CHANCE/20

    if keyboard.is_pressed('backspace'):
        return 'stop', columns, extra_lines

    return count_stop, columns, extra_lines


if __name__ == '__main__':
    columns = [[] for _ in range(AMOUNT_OF_COLUMNS)] # Initialize columns
    count_stop = 0 # used for the pause and mode in check_keyboard so that they dont immediately switch
    extra_lines = 0

    # Main animation loop
    while True:

        rows = columns_to_rows(columns)
        
        os.system('cls' if os.name == 'nt' else 'clear')  # Clear the terminal
        for row in rows:
            print(row)

        print('\n' * extra_lines)
        
        if count_stop != 'stop': # backspace prevents controls so that user can use their keyboard without worrying
            count_stop, columns, extra_lines = check_keyboard(count_stop, columns, extra_lines)

        columns = [update_column(column) for column in columns]
        time.sleep(TIME_BETWEEN_FRAMES)
