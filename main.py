import random
import time
import os

# Characters for the rain
CHARACTERS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
AMOUNT_OF_COLUMNS = 20
MAX_COLUMN_DISTANCE = 15 # amount of rows 30

# Green gradient colors (bright green to dark green)
COLORS = [
    "\033[92m",  # Bright green
    "\033[32m",  # Slightly dimmer green
    "\033[2;32m",  # Dark green
    "\033[90m",  # Almost black-green (dim gray)
    "\033[0m",    # Reset (black/transparent)
]

COLORS = ["\033[0m",    # Reset (black/transparent)
          "\033[90m",  # Almost black-green (dim gray)
          "\033[2;32m",  # Dark green
          "\033[32m",  # Slightly dimmer green
          "\033[92m",  # Bright green
]

os.system('cls')

######################################
def hex_to_rgb(hex_color):
    """Convert hex color (#RRGGBB) to an (R, G, B) tuple."""
    return tuple(int(hex_color[i:i+2], 16) for i in (1, 3, 5))


######################################
def make_column(is_empty=False):
    chars = []

    if is_empty:
        max_distance = 0
    else:
        max_distance = random.randint(len(COLORS), MAX_COLUMN_DISTANCE)

        for _ in range(len(COLORS)):
            chars.append(random.choice(CHARACTERS))
    
    return {'chars' : chars,
            'cur_char' : 0,
            'cur_final_char' : 0,
            'max_distance' : max_distance}


######################################
def columns_to_rows(columns):
    rows = []

    for row_number in range(MAX_COLUMN_DISTANCE):
        row = ''

        for column_number, column in enumerate(columns):
            if column['max_distance'] == 0:
                row += ' '
                continue

                # if 0.85 < random.random(): do this later in the code
                #     columns[column_number] = make_column(is_empty=True)
        
            
            # if column['max_distance'] < row_number:
            #     columns[column_number] = make_column(is_empty=True)
            #     continue

            if 0 < column['max_distance'] - row_number <= len(COLORS) and column['cur_final_char'] >= column['cur_char']:
                row += column['chars'][column['cur_char']]
                column['cur_char'] += 1

            # if column['cur_final_char_distance'] - row_number < len(COLORS):
            #     print('too far')
            #     row += ' '
            #     continue
            
        
        rows.append(row)

    return rows


columns = []

# columns = [{'chars' : ['b', 'c'], 'cur_char' : 1, 'max_distance' : 14}]

for _ in range(AMOUNT_OF_COLUMNS):
    if 0.5 > random.random():    # if 0.8 > random.random():
        columns.append(make_column(is_empty=True))
    else:
        columns.append(make_column(is_empty=False))


a = 0
while True:
    a += 1
    if a > 10:
        break


    rows = columns_to_rows(columns)

    for row in rows:
        print(row)
    
    for column_index, column in enumerate(columns):
        if column['max_distance'] == 0:
            if 0.2 > random.random():
                columns[column_index] = make_column(is_empty=False)

            continue

        for char_index in range(len(column['chars'])):
            if 0.1 > random.random():
                column['chars'][char_index] = random.choice(CHARACTERS)

        column['cur_char'] = 0
        column['cur_final_char'] += 1

        if column['cur_final_char'] > len(COLORS):
            column = make_column(is_empty=True)

        columns[column_index] = column
    
    time.sleep(1)
    os.system('cls')