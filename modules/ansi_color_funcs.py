import collections
from typing import Any


# ______________________parse_ansi_color______________________
def parse_ansi_color(ansi: str) -> tuple[tuple[int, int, int], bool] | None:
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
def extend_colors(original_colors: tuple[str], new_length: int, config: dict[str, Any]) -> tuple[str]:
    """
    Generate an extended gradient of ANSI color codes by interpolating between given colors.

    This function interpolates between the colors provided in `original_colors` to create
    a gradient with `new_length` colors. It caches results in the configuration's
    "extended_color_cache" to avoid redundant calculations.

    Args:
        original_colors (tuple): A tuple of ANSI escape codes representing colors.
        new_length (int): The desired number of colors in the extended gradient.
        config (dict): Configuration dictionary that includes caching information.

    Returns:
        list: A tuple of ANSI escape codes representing the extended color gradient.
    """
    max_cache_size = 250
    original_colors = tuple(original_colors)
    key = (original_colors, new_length)
    cache: collections.OrderedDict[tuple[tuple[str], int], tuple[str]] = config["extended_color_cache"]

    if key in cache:
        # Mark as recently used
        cache.move_to_end(key)
        return cache[key]

    if new_length <= 1:
        cache[key] = original_colors
        cache.move_to_end(key)
        if len(cache) > max_cache_size:
            cache.popitem(last=False)
        return original_colors

    extended = []
    n = len(original_colors)
    for i in range(new_length):
        t = i / (new_length - 1)  # relative position in the new color list
        pos = t * (n - 1)  # find index(float) in original colors that's at the same relative position as in the new one
        idx = int(pos)
        # Fractional distance between idx and the next color, used for interpolation (ranges from 0 to 1).
        # If idx is the last color, set t2 to 1.0 to avoid out-of-bounds errors.
        t2 = pos - idx if idx < n - 1 else 1.0
        # find the r, g, b components of the first color with a smaller index
        rgb1, is_bold1 = parse_ansi_color(original_colors[idx])
        # find the next color, if we are the end of the list take the last one itself
        rgb2, is_bold2 = parse_ansi_color(original_colors[min(idx + 1, n - 1)])
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
    return tuple(extended)