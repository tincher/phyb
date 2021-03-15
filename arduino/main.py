import cli_ui
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
    current_run = []
    for i in range(count):
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
