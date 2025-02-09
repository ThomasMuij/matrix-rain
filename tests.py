import time
import keyboard
import random
import collections
import threading

def fun(a):
    pass

keyboard.hook(fun)

i = time.time()
try:
    while True:
        try:
            if time.time() - i > 10:
                break
            time.sleep(0.1)
        except KeyboardInterrupt:
            pass
except KeyboardInterrupt:
    print('here')





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