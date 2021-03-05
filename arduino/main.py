import math
import time

from serial import Serial
import numpy as np
from sklearn.cluster import KMeans
import cli_ui

baud = 57600
accel_setting = 2
gyro_setting = 1
sampling_rate = 0.02
keys = ['ax', 'ay', 'az', 'gx', 'gy', 'gz']
fts = {}
testing = False
orientation = []
offset = [0, 0, 0]
points = []
self_test_passed = None
all_data = []
last_data = {}


# -------------------------------------------------
# TODO IMU möglichst nah an schwerpunkt
# TODO self_test_passed konsequenz
# -------------------------------------------------


def convert_accel_gyro(data):
    result = {}
    for i, key in enumerate(data.keys()):
        if i < 3:
            # in g
            result[key] = data[key] / (16384 / (2 ** accel_setting))
        else:
            # in grad pro sekunde
            result[key] = data[key] / (131 / (2 ** gyro_setting))
    return result


def init_self_test(values):
    global testing
    global fts
    ft = dict(zip(keys, [0] * 6))
    prefactor = -25
    for index, value in enumerate(values.values()):
        if value == 0:
            continue
        if index < 3:
            prefactor = prefactor * (-1)
            ft[keys[index]] = prefactor * 131 * (1.046 ** (value - 1))
        else:
            ft[keys[index]] = 4096 * 0.34 * ((0.92 * 0.34) ** ((value - 1) / ((2 ** 5) - 2)))
    fts = ft
    testing = True


def calc_diff_from_outputs(st_enabled_data, st_disabled_data):
    result = {}
    for key in st_enabled_data.keys():
        result[key] = st_enabled_data[key] - st_disabled_data[key]
    return result


def finish_self_test(values):
    global testing
    global offset
    global last_data
    st_response = calc_diff_from_outputs(last_data, values)
    result = {}
    for key in st_response.keys():
        result[key] = (st_response[key] - fts[key]) / fts[key]
    if any(map(lambda x: not (-14 <= x <= 14), result.values())):
        return False
    testing = False
    offset = list(convert_accel_gyro(values).values())[3:]
    return True


def convert(raw_data, timestamp):
    values = raw_data.decode().replace('\n', '').split(' ')
    if values[0] == 'B':
        # button got pressed
        return False
    if values[0] == 'I':
        global testing
        global last_data
        try:
            data = dict(zip(keys, list(map(int, values[1:]))))
            if testing:
                self_test_passed = finish_self_test(data)
            last_data = data
            all_data.append(data)
            return data
        except Exception as e:
            print(e)
            print('dismiss bc async')
    elif values[0] == 'S':
        data = dict(zip(keys, list(map(int, values[1:]))))
        init_self_test(data)
        return 'ST started'


def print_countdown_when_ready(seconds=3):
    user_is_ready = False
    while not user_is_ready:
        user_is_ready = cli_ui.ask_yes_no('Bereit?', default=True)
    for i in range(seconds)[::-1]:
        print(i + 1)
        time.sleep(1)
    print('LOS!')


def print_learning_for_activity(activity):
    print('Führen Sie nach dem Countdown 5 {} aus'.format(activity))
    print('Nach der Ausführung der {} drücken Sie STRG-C'.format(activity))


if __name__ == '__main__':
    print('LERNPHASE')
    print_learning_for_activity('Kniebeugen')
    print_countdown_when_ready()
    try:
        with Serial('/dev/cu.usbserial-1420', baud, timeout=10, write_timeout=5) as my_serial:
            in_progress = True
            while in_progress:
                line = my_serial.readline()
                button_pressed = convert(line, time.time())
    except KeyboardInterrupt:
        pass
    print_learning_for_activity('Situps')
    print_countdown_when_ready()
    try:
        with Serial('/dev/cu.usbserial-1420', baud, timeout=10, write_timeout=5) as my_serial:
            in_progress = True
            while in_progress:
                line = my_serial.readline()
                button_pressed = convert(line, time.time())
    except KeyboardInterrupt:
        pass
    print('Lernphase beendet')
    print()
    print('Erkennen ab jetzt möglich!')
    print_countdown_when_ready()
