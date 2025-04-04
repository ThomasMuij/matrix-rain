import sys
import os


# ______________________hide_or_show_cursor______________________
def hide_or_show_cursor(hide=False, show=False) -> None:
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
def flush_stdin() -> None:
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