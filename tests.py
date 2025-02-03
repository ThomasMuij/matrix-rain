import time
import threading
import keyboard

def fun(config):
    while True:
        if keyboard.is_pressed('up'):
            config['age'] += 1
        time.sleep(0.01)


def fun2():
    config = {'name': 'John', 'age': 5, 'days': [1, 3, 5]}

    run_fun = threading.Thread(target=fun, args=[config])
    run_fun.daemon = True
    run_fun.start()

    while True:
        if keyboard.is_pressed('down'):
            print(config)
        time.sleep(0.01)

fun2()