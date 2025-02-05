import time
import threading
import keyboard


config = {'name': 'Old', 'age': 0, 'days': {'jan': [1, 2], 'feb': [2, 3]}}

copy = {}
for key in config:
    try:
        copy[key] = config[key].copy()
    except AttributeError:
        copy[key] = config[key]
# copy = config.copy()

copy['name'] = 'New'
copy['age'] += 1

copy['days']['mar'] = [6, 7]
copy['days']['jan'] = ['new', 'list']

copy['days']['feb'][0] += 10

print(config)

