import time
import keyboard
import random
import collections
import threading
from pynput import keyboard



def on_press(key):
    print('-----------')
    print(type(key))
    print(key)
    print(key.name)
    print(key.value)
    print(repr(key))
    print(key.__dict__)
    key = listener.canonical(key)
    print('---')
    print(type(key))
    print(key)
    try:
        print(key.name)
        print(key.value)
    except AttributeError:
        print(key.char)
        print(key.vk)
        print('herrreee' * 10)
    
    print(repr(key))
    print(key.__dict__)
    try:
        print('alphanumeric key {0} pressed'.format(
            key.char))
    except AttributeError:
        print('special key {0} pressed'.format(
            key))

def on_release(key):
    print('{0} released'.format(
        key))
    if key == keyboard.Key.esc:
        # Stop listener
        return False

# Collect events until released
# with keyboard.Listener(
#         on_press=on_press,
#         on_release=on_release) as listener:
#     listener.join()

# ...or, in a non-blocking fashion:
listener = keyboard.Listener(
    on_press=on_press,
    on_release=on_release)
listener.start()
time.sleep(50)
"""
def on_event(event, keys, lock):
    with lock:
        if event.event_type == 'down':
            keys.add(event.name)
        elif event.event_type == 'up':
            keys.discard(event.name.lower())
            keys.discard(event.name.upper())
        print(event)


def check_key(key, keys, lock):
    with lock:
        if key in keys:
            if key.isupper():
                if 'shift' in keys:
                    return True
            else:
                return True
        return False


def check(keys, lock):
    a = 'A ctrl shift'
    a = a.split(' ')

    with lock:
        if 's' in keys:
            print('s')
        if 'F' in keys:
            print('big F')
        if 'f' in keys:
            print('small f')
        # if 'shift' in keys:
        #     print('shift')
        if 'b' in keys and 'c' in keys:
            print('b and c')
        if '1' in keys:
            print('1')
        if 'up' in keys:
            print('up')

        do = True
        for key in a:
            if key not in keys:
                do = False
                break
        if do:
            print('HERE')

def main():
    keys = set()
    lock = threading.Lock()

    # Create a partial function that binds keys and lock.

    # Now, keyboard.hook receives a callable that expects a single event argument.
    keyboard.hook(lambda event: on_event(event, keys, lock))
    start_time = time.time()
    while time.time() - start_time < 30:
        check(keys, lock)
        time.sleep(0.2)

main()
"""
"""
# Global state for currently pressed keys
currently_pressed = set()
lock = threading.Lock()

def on_key_event(event):
    # This function is called whenever a key is pressed or released.
    with lock:
        if event.event_type == 'down':
            currently_pressed.add(event.name)
        elif event.event_type == 'up':
            currently_pressed.discard(event.name)

# Register the keyboard hook
keyboard.hook(on_key_event)

def check_keys():
    # Check the keys without doing a lot of polling
    with lock:
        keys = set(currently_pressed)
    # Example: if both 'f' and 's' are pressed at the same time:
    if 'f' in keys and 's' in keys:
        print("Both 'f' and 's' are pressed!")
    # Add more key logic as needed

# Main animation loop
while True:
    # Do your animation updates here...
    
    # Check the keyboard state
    check_keys()
    
    # Sleep for a short period to keep the loop efficient
    time.sleep(0.01)
"""