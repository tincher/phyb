import cli_ui
import pickle
from my_predictor import MyPredictor
from arduino_converter import *
from pretty_prints import *
from serial import Serial

# -------------------------------------------------
# TODO documentation
# -------------------------------------------------


if __name__ == '__main__':
    arduino_path = '/dev/cu.usbserial-1420'
    exercise_count = 2
    hidden_states = 5
    cluster_count = 5
    runs_per_exercise = 5

    learn_data = []
    print('LERNPHASE')
    for i in range(exercise_count):
        print_learning_for_activity(i, runs_per_exercise)
        print_countdown_when_ready(0)
        exercise_data = read_from_arduino(arduino_path, count=runs_per_exercise)
        learn_data.append(exercise_data)

    predictor = MyPredictor(learn_data, cluster_count=cluster_count, components_counts=[hidden_states] * exercise_count)

    print('Lernphase beendet')
    print()
    print('Erkennen ab jetzt möglich!')

    count = int(cli_ui.ask_string('Wie viele Ausführungen werden Sie machen?', default=5))
    print_countdown_when_ready(0)
    recognition_data = read_from_arduino(arduino_path, count=count)
    prediction, _ = predictor.predict(recognition_data, exercise_count)
    print_prediction(exercise_count, prediction)
