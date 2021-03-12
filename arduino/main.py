from hmmlearn import hmm
import cli_ui
import time
import pickle
import sys
from my_predictor import *

from serial import Serial
import numpy as np
from sklearn.cluster import KMeans

baud = 57600
accel_setting = 2
gyro_setting = 1
sampling_rate = 0.02
fts = []
testing = False
offset = [0, 0, 0]
all_data = []
exercises_data = []
last_data = []
model = None
kmeans = None

# -------------------------------------------------
# TODO documentation
# -------------------------------------------------


def convert_accel_gyro(data):
    result = []
    for i, elem in enumerate(data):
        if i < 3:
            # in g
            result.append(elem / (16384 / (2 ** accel_setting)))
        else:
            # in grad pro sekunde
            result.append(elem / (131 / (2 ** gyro_setting)))
    return result


def init_self_test(values):
    global testing
    global fts
    ft = [0] * 6
    prefactor = -25
    for index, value in enumerate(values):
        if value == 0:
            continue
        if index < 3:
            prefactor = prefactor * (-1)
            ft[index] = prefactor * 131 * (1.046 ** (value - 1))
        else:
            ft[index] = 4096 * 0.34 * ((0.92 * 0.34) ** ((value - 1) / ((2 ** 5) - 2)))
    fts = ft
    testing = True


def calc_diff_from_outputs(st_enabled_data, st_disabled_data):
    result = []
    for i in range(len(st_enabled_data)):
        result.append(st_enabled_data[i] - st_disabled_data[i])
    return result


def finish_self_test(values):
    global testing
    global offset
    global last_data
    st_response = calc_diff_from_outputs(last_data, values)
    result = []
    for i, elem in enumerate(st_response):
        result.append((st_response[i] - fts[i]) / fts[i])
    if any(map(lambda x: not (-14 <= x <= 14), result)):
        return False
    testing = False
    offset = list(convert_accel_gyro(values))[3:]
    return True


def convert(raw_data, timestamp):
    values = raw_data.decode().replace('\n', '').split(' ')
    if values[0] == 'D':
        global testing
        global last_data
        # try:
        data = list(map(int, values[1:]))
        if testing:
            self_test_passed = finish_self_test(data)
            testing = False
            return 'ST passed' if self_test_passed else 'ST failed'
        last_data = data
        return data
        # except Exception as e:
        #     print(e)
        #     print('dismiss bc async')
    elif values[0] == 'S':
        data = list(map(int, values[1:]))
        init_self_test(data)


def print_prediction(prediction):
    print('Ergebnis:')
    for key in prediction.keys():
        print('Übung: {}, Anzahl: {}'.format(key, prediction[key]))


def print_countdown_when_ready(seconds=3):
    user_is_ready = False
    while not user_is_ready:
        user_is_ready = cli_ui.ask_yes_no('Bereit?', default=True)
    for i in range(seconds)[::-1]:
        time.sleep(1)
        print(i + 1)
    print_circle(cli_ui.yellow)


def print_learning_for_activity(activity):
    print('Führen Sie sobald der grüne Kreis erscheint 3 {} aus'.format(activity))
    print('Nach der Ausführung der {} drücken Sie STRG-C'.format(activity))


def print_circle(color):
    big_dot = cli_ui.UnicodeSequence(color, '⬤', 'O')
    cli_ui.info(big_dot)


def read_from_arduino(count=5):
    current_exercise = []
    current_run = []
    for i in range(count):
        try:
            with Serial('/dev/cu.usbserial-1420', baud, timeout=10, write_timeout=5) as my_serial:
                while True:
                    line = my_serial.readline()
                    result = convert(line, time.time())
                    if result == 'ST passed':
                        print_circle(cli_ui.green)
                    elif result == 'ST failed':
                        print('Sensor self-test failed!')
                        exit()
                    elif result is not None:
                        current_run.append(result)
        except KeyboardInterrupt:
            current_exercise.append(current_run)
    return current_exercise


if __name__ == '__main__':
    learn_data = []
    print('LERNPHASE')

    print_learning_for_activity('Kniebeugen')
    print_countdown_when_ready(0)
    exercise_data = read_from_arduino(2)
    learn_data.append(exercise_data)

    print_learning_for_activity('Situps')
    print_countdown_when_ready(0)
    exercise_data = read_from_arduino(2)
    learn_data.append(exercise_data)

    predictor = MyPredictor(learn_data)

    print('Lernphase beendet')
    print()

    print('Erkennen ab jetzt möglich!')
    print_countdown_when_ready(0)
    data = read_from_arduino()
    prediction = predictor.predict(data)
    print_prediction(prediction)
