
# základ kódu jsem vytvořil sám, ale drobné chybky, barvu a úpravu kódu jsem udělal pomocí chatgpt



import random
import time
import os

RESET_COLUMN_CHANCE = 0.03    # Chance for a column to reset when it becomes empty (0 to 1)
TIME_BETWEEN_FRAMES = 0.05

# Characters for the rain
CHARACTERS = "ﾊﾐﾋｰｳｼﾅﾓﾆｻﾜﾂｵﾘｱﾎﾃﾏｹﾒｴｶｷﾑﾕﾗｾﾈｽﾀﾇﾍｦｲｸｺｿﾁﾄﾉﾌﾤﾨﾛﾝ012345789:.=*+-<>"

# Number of columns and the maximum distance a character can fall
AMOUNT_OF_COLUMNS = 160
MAX_COLUMN_DISTANCE = 20

# Green gradient colors (8 shades, from darkest to brightest)
COLORS = [
    "\033[38;2;0;16;0m",   # Very dark green
    "\033[38;2;0;48;0m",   # Darker green
    "\033[38;2;0;80;0m",   # Dark green
    "\033[38;2;0;112;0m",  # Slightly dark green
    "\033[38;2;0;144;0m",  # Medium green
    "\033[38;2;0;176;0m",  # Bright green
    "\033[38;2;0;208;0m",  # Brighter green
    "\033[38;2;0;255;0m",  # Brightest green
    "\033[0m"              # Reset color (default terminal color)
]

# Clear the terminal screen
os.system('cls' if os.name == 'nt' else 'clear')

def make_column(is_empty=False):
    """Create a column with random characters or an empty one."""
    if is_empty:
        return {'chars': [], 'cur_final_char': 0, 'max_distance': 0}
    max_distance = MAX_COLUMN_DISTANCE
    chars = [random.choice(CHARACTERS) for _ in range(len(COLORS))]
    return {'chars': chars, 'cur_final_char': 0, 'max_distance': max_distance}

def columns_to_rows(columns):
    """Convert columns into rows for display."""
    rows = []
    for row_number in range(MAX_COLUMN_DISTANCE):
        row = ''
        for column in columns:
            if column['max_distance'] == 0:  # Empty column
                row += ' '
            elif 0 <= column['cur_final_char'] - row_number < len(COLORS):
                color_index = len(COLORS) - 1 - (column['cur_final_char'] - row_number)
                color = COLORS[color_index]
                char = column['chars'][color_index]
                row += f"{color}{char}\033[0m"
            else:
                row += ' '
        rows.append(row)
    return rows

def reset_column_if_needed(column):
    """Reset a column if it exceeds its maximum distance or if it becomes empty."""
    column['cur_final_char'] += 1
    if column['cur_final_char'] > column['max_distance']:
        return make_column() if random.random() < RESET_COLUMN_CHANCE else column
    return column

# Initialize columns
columns = [make_column(is_empty=True) for _ in range(AMOUNT_OF_COLUMNS)]

# Main animation loop
while True:
    rows = columns_to_rows(columns)

    os.system('cls' if os.name == 'nt' else 'clear')  # Clear the terminal
    for row in rows:
        print(row)

    columns = [reset_column_if_needed(column) for column in columns]
    time.sleep(TIME_BETWEEN_FRAMES)
