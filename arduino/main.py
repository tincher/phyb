import cli_ui
import pickle
from my_predictor import MyPredictor
from arduino_converter import ArduinoConverter
from pretty_prints import *
from serial import Serial

# -------------------------------------------------
# TODO documentation
# -------------------------------------------------


def read_from_arduino(count=5):
    accel_setting = 2
    gyro_setting = 1
    converter = ArduinoConverter(accel_setting, gyro_setting)
    baud = 57600

    current_exercise = []
    for i in range(count):
        current_run = []
        try:
            with Serial('/dev/cu.usbserial-1420', baud, timeout=10, write_timeout=5) as my_serial:
                while True:
                    line = my_serial.readline()
                    result = converter.convert(line)
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
    exercise_count = 2
    learning_runs_per_exercise = 5
    learn_data = []

    print('LERNPHASE')
    for name in exercise_names:
        print_learning_for_activity(name, learning_runs_per_exercise)
        print_countdown_when_ready(0)
        exercise_data = read_from_arduino(learning_runs_per_exercise)
        learn_data.append(exercise_data)

    predictor = MyPredictor(learn_data, cluster_count=5, components_counts=[5, 5])

    print('Lernphase beendet')
    print()
    print('Erkennen ab jetzt möglich!')

    count = int(cli_ui.ask_string('Wie viele Ausführungen werden Sie machen?', default=5))
    print_countdown_when_ready(0)
    recognition_data = read_from_arduino(count)
    prediction = predictor.predict(recognition_data, exercise_count)
    print_prediction(exercise_count, prediction)
