from hmmlearn import hmm
import cli_ui
import time


from serial import Serial
import numpy as np
from sklearn.cluster import KMeans

baud = 57600
accel_setting = 2
gyro_setting = 1
sampling_rate = 0.02
keys = ['ax', 'ay', 'az', 'gx', 'gy', 'gz']
fts = {}
testing = False
offset = [0, 0, 0]
all_data = []
exercises_data = []
last_data = {}
model = None
kmeans = None

# -------------------------------------------------
# TODO documentation
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
    if values[0] == 'D':
        global testing
        global last_data
        try:
            data = dict(zip(keys, list(map(int, values[1:]))))
            if testing:
                self_test_passed = finish_self_test(data)
                testing = False
                return 'ST passed' if self_test_passed else 'ST failed'
            last_data = data
            return data
        except Exception as e:
            print(e)
            print('dismiss bc async')
    elif values[0] == 'S':
        data = dict(zip(keys, list(map(int, values[1:]))))
        init_self_test(data)


def init_kmeans(data, cluster_count=4):
    X = [list(x.values()) for x in data]
    kmeans = KMeans(n_clusters=cluster_count).fit(X)
    return kmeans


def learn(data, components_count=10, cluster_count=10):
    all_data = np.concatenate(data)

    kmeans = init_kmeans(all_data, cluster_count=cluster_count)
    model = hmm.MultinomialHMM(n_components=components_count, n_iter=100)

    labels = kmeans.predict([list(x.values()) for x in all_data])
    X = labels.reshape((-1, 1))
    lengths = [len(x) for x in data]
    # TODO sollte man öfters laufen lassen und das beste nehmen
    model.fit(X, lengths)

    init_states = []
    for i, exercise_data in enumerate(data):
        exercise_labels = kmeans.predict([list(x.values()) for x in exercise_data])
        exercise_states = model.predict(exercise_labels.reshape((-1, 1)))

        init_states.append(exercise_states[0])

        with open('states_{}.txt'.format(i), 'w') as states_file:
            states_file.write(str(exercise_states))
    with open('init_states.txt', 'w') as init_states_file:
        init_states_file.write(str(init_states))
    return kmeans, model


def predict(kmeans, model, data):
    result = {'Kniebeuge': 0, 'Situp': 0}

    # nur training data
    labels = kmeans.predict([list(x.values()) for x in data])
    labels = labels.reshape((-1, 1))
    prediction = model.predict(labels)
    with open('prediction.txt', 'w') as prediction_file:
        prediction_file.write(str(prediction))
    return result


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
    big_dot = cli_ui.UnicodeSequence(color, "⬤", "O")
    cli_ui.info(big_dot)


def read_from_arduino():
    current_exercise = []
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
                    current_exercise.append(result)
    except KeyboardInterrupt:
        return current_exercise


if __name__ == '__main__':
    learn_data = []
    print('LERNPHASE')

    print_learning_for_activity('Kniebeugen')
    print_countdown_when_ready(0)
    exercise_data = read_from_arduino()
    learn_data.append(exercise_data)

    print_learning_for_activity('Situps')
    print_countdown_when_ready(0)
    exercise_data = read_from_arduino()
    learn_data.append(exercise_data)

    kmeans, model = learn(learn_data, cluster_count=10, components_count=10)

    print('Lernphase beendet')
    print()

    print('Erkennen ab jetzt möglich!')
    print_countdown_when_ready(0)
    data = read_from_arduino()
    prediction = predict(kmeans, model, data)
    print_prediction(prediction)
